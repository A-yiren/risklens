"""离线评测 Contract Review V2 的漏报、错报和证据完整性。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Set


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.contract_rules_v2 import scan_contract_rules_v2  # noqa: E402


def _classification_metrics(tp: int, fp: int, fn: int) -> Dict[str, Any]:
    """分母为零的 precision/recall 是未定义，不用 100% 掩盖无预测。"""
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else 0.0
    )
    return {
        "precision": round(precision, 4) if precision is not None else None,
        "recall": round(recall, 4) if recall is not None else None,
        "f1": round(f1, 4),
    }


def evaluate_cases(cases: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    tp = fp = fn = 0
    evidence_failures = []
    rows = []
    for case in cases:
        findings = scan_contract_rules_v2(case["text"], case["contract_type"])
        predicted: Set[str] = {item["rule_id"] for item in findings}
        expected: Set[str] = set(case["expected_rule_ids"])
        case_tp = predicted & expected
        case_fp = predicted - expected
        case_fn = expected - predicted
        tp += len(case_tp)
        fp += len(case_fp)
        fn += len(case_fn)
        for finding in findings:
            evidence = finding["contract_evidence"]
            quote = evidence["quote"]
            exact_contract_quote = (
                case["text"][evidence["start"]:evidence["end"]] == quote
            )
            legal = finding["legal_basis"]
            if not exact_contract_quote or not all(
                str(legal.get(key, "")).strip()
                for key in ("law_name", "article_no", "quote", "source_url")
            ):
                evidence_failures.append({"case_id": case["id"], "rule_id": finding["rule_id"]})
        rows.append({
            "case_id": case["id"],
            "expected": sorted(expected),
            "predicted": sorted(predicted),
            "false_positives": sorted(case_fp),
            "false_negatives": sorted(case_fn),
        })
    metrics = _classification_metrics(tp, fp, fn)
    return {
        "summary": {
            "cases": len(rows),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            **metrics,
            "evidence_failures": len(evidence_failures),
            "passed": fp == 0 and fn == 0 and not evidence_failures,
        },
        "cases": rows,
        "evidence_failures": evidence_failures,
    }


def evaluate_v1_targeted_recall(cases: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """用同一金标评估 V1；只比较本数据集定义的四类确定性风险。"""
    from app.services.contract_review import contract_reviewer

    # 当前 V1 没有稳定 rule_id。若后续 V1 新增同类规则，只需扩充此映射。
    name_to_rule_id = {
        "试用期超过法定上限": "labor.probation_duration.exceeds_cap",
        "试用期工资比例低于 80%": "labor.probation_wage.below_80_percent",
        "定金比例超过主合同标的额 20%": "general.earnest_money.exceeds_20_percent",
        "租赁期限超过二十年": "lease.term.exceeds_20_years",
    }
    adapted = []
    for case in cases:
        predicted = {
            name_to_rule_id[item["name"]]
            for item in contract_reviewer._scan_risks(case["text"])
            if item.get("name") in name_to_rule_id
        }
        adapted.append({**case, "_v1_predicted": predicted})
    tp = fp = fn = 0
    for case in adapted:
        expected = set(case["expected_rule_ids"])
        predicted = case["_v1_predicted"]
        tp += len(expected & predicted)
        fp += len(predicted - expected)
        fn += len(expected - predicted)
    metrics = _classification_metrics(tp, fp, fn)
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        **metrics,
        "scope": "仅限本合成数据集的四类确定性风险，不代表 V1 总体能力",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).with_name("contract_review_v2_cases.json"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--compare-v1", action="store_true")
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    report = {
        "dataset_name": dataset["dataset_name"],
        "dataset_version": dataset["version"],
        **evaluate_cases(dataset["cases"]),
    }
    if args.compare_v1:
        report["v1_targeted_baseline"] = evaluate_v1_targeted_recall(dataset["cases"])
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
