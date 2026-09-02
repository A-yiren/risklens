"""可复现的融资材料预审内部规则评测。

不依赖 LLM，不生成授信结论。若数据集未完成双专家复核，报告保持 INTERNAL_ONLY。
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models import DocumentInfo, DocumentStatus, SourceType  # noqa: E402
from app.services.finance_precheck import MATERIAL_RULES, finance_precheck_service  # noqa: E402


def _metrics(expected: set[str], predicted: set[str]) -> dict[str, Any]:
    tp = len(expected & predicted)
    fp = len(predicted - expected)
    fn = len(expected - predicted)
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "recall": round(tp / (tp + fn), 4) if tp + fn else None,
        "precision": round(tp / (tp + fp), 4) if tp + fp else None,
    }


def _traditional_keyword_baseline(case: dict[str, Any]) -> set[str]:
    """传统检索基线：只检索关键词命中，不做字段抽取或跨材料比对。"""
    corpus = "\n".join(f"{doc['name']}\n{doc['text']}" for doc in case["documents"]).lower()
    return {
        f"missing:{rule.key}"
        for rule in MATERIAL_RULES
        if rule.required and not any(keyword.lower() in corpus for keyword in rule.keywords)
    }


def _risk_tokens(result: dict[str, Any]) -> set[str]:
    tokens = {
        f"missing:{item['key']}"
        for item in result["material_checklist"]
        if item["required"] and item["status"] == "missing"
    }
    for flag in result["risk_flags"]:
        if flag.get("type") == "cross_document_inconsistency":
            for field in ("enterprise_name", "legal_representative", "credit_code"):
                if finance_precheck_service._field_label(field) in flag["title"]:
                    tokens.add(f"inconsistency:{field}")
    return tokens


def _citation_errors(result: dict[str, Any], source_by_name: dict[str, str]) -> int:
    """证据摘录必须能在它声称的原材料中精确找到。"""
    evidence = []
    for checklist in result["material_checklist"]:
        evidence.extend(checklist.get("evidence", []))
    for flag in result["risk_flags"]:
        evidence.extend(flag.get("evidence", []))
    return sum(
        1 for item in evidence
        if item.get("excerpt") and item["excerpt"] not in source_by_name.get(item.get("document_name", ""), "")
    )


def _run_product(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        docs = []
        source_by_name = {}
        for index, source in enumerate(case["documents"]):
            path = root / source["name"]
            path.write_text(source["text"], encoding="utf-8")
            source_by_name[source["name"]] = source["text"]
            docs.append(DocumentInfo(
                id=f"{case['id']}-{index}", name=source["name"], source=SourceType.UPLOAD,
                file_path=str(path), status=DocumentStatus.READY, visibility="private", owner_user_id="eval",
            ))
        return finance_precheck_service.review(docs), source_by_name


def evaluate_cases(cases: Iterable[dict[str, Any]]) -> dict[str, Any]:
    product_expected: set[str] = set()
    product_predicted: set[str] = set()
    baseline_predicted: set[str] = set()
    citation_errors = citation_total = 0
    rows = []
    for case in cases:
        expected = set(case["expected_major_risks"])
        result, source_by_name = _run_product(case)
        product = _risk_tokens(result)
        baseline = _traditional_keyword_baseline(case)
        product_expected |= {f"{case['id']}:{token}" for token in expected}
        product_predicted |= {f"{case['id']}:{token}" for token in product}
        baseline_predicted |= {f"{case['id']}:{token}" for token in baseline}
        errors = _citation_errors(result, source_by_name)
        item_evidence = [e for c in result["material_checklist"] for e in c.get("evidence", [])]
        item_evidence += [e for flag in result["risk_flags"] for e in flag.get("evidence", [])]
        citation_errors += errors
        citation_total += len(item_evidence)
        rows.append({"case_id": case["id"], "expected": sorted(expected), "baseline": sorted(baseline), "product": sorted(product), "citation_errors": errors})
    product_metrics = _metrics(product_expected, product_predicted)
    baseline_metrics = _metrics(product_expected, baseline_predicted)
    return {
        "summary": {
            "cases": len(rows),
            "traditional_keyword_baseline": baseline_metrics,
            "risklens_rule_precheck": product_metrics,
            "evidence_citation_error_rate": round(citation_errors / citation_total, 4) if citation_total else None,
            "major_risk_miss_rate": round(product_metrics["false_negatives"] / len(product_expected), 4) if product_expected else 0.0,
        },
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("finance_precheck_benchmark_v1.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    report = {"dataset_name": dataset["dataset_name"], "dataset_version": dataset["version"], "review_status": dataset["review_status"], **evaluate_cases(dataset["cases"])}
    report["publication_status"] = "PUBLISHABLE" if dataset["review_status"] == "DOUBLE_EXPERT_REVIEWED" else "INTERNAL_ONLY"
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
