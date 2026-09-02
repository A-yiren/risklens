"""RiskLens 可复现评测 CLI。

设计目标：
1. 法院公开材料是唯一事实标准；
2. 缺少完整目标输出或两名独立裁判时，不生成综合正确率；
3. 密钥只从环境变量读取；
4. 每次运行保存数据集哈希、模型信息、延迟、原始输出和失败原因。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = ROOT / "official_cases_pilot_v1.jsonl"
DEFAULT_PROMPT = ROOT / "judge_prompt.md"
SCORE_FIELDS = (
    "issue_identification",
    "legal_basis_accuracy",
    "decision_direction",
    "reasoning_groundedness",
    "completeness",
)
SCORE_WEIGHTS = {
    "issue_identification": 0.20,
    "legal_basis_accuracy": 0.20,
    "decision_direction": 0.25,
    "reasoning_groundedness": 0.20,
    "completeness": 0.15,
}


class EvalError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise EvalError(f"{path}:{line_no} 不是有效 JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise EvalError(f"{path}:{line_no} 必须是 JSON 对象")
        rows.append(value)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_dataset(cases: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    allowed_domains = ("court.gov.cn",)

    if not cases:
        errors.append("数据集为空")

    for index, case in enumerate(cases, 1):
        prefix = f"记录 {index}"
        case_id = str(case.get("case_id", "")).strip()
        if not case_id:
            errors.append(f"{prefix}: 缺少 case_id")
        elif case_id in seen:
            errors.append(f"{prefix}: case_id 重复: {case_id}")
        seen.add(case_id)

        source = case.get("source") or {}
        url = str(source.get("url", ""))
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https":
            errors.append(f"{case_id}: 来源必须使用 HTTPS")
        if not any(parsed.hostname == d or (parsed.hostname or "").endswith("." + d) for d in allowed_domains):
            errors.append(f"{case_id}: 来源不是法院官方域名: {parsed.hostname}")
        if source.get("authority") != "official_court":
            errors.append(f"{case_id}: authority 必须为 official_court")
        for field in ("publisher", "title", "accessed_at"):
            if not source.get(field):
                errors.append(f"{case_id}: source.{field} 不能为空")

        facts = str((case.get("input") or {}).get("facts", "")).strip()
        if len(facts) < 30:
            errors.append(f"{case_id}: 案情过短")
        for token in (case.get("leakage") or {}).get("forbidden_tokens", []):
            if token and token in facts:
                errors.append(f"{case_id}: 测试输入泄漏禁止标识: {token}")

        gold = case.get("gold") or {}
        for field in ("issues", "decision", "holdings", "evidence"):
            if not gold.get(field):
                errors.append(f"{case_id}: gold.{field} 不能为空")
        evidence = gold.get("evidence") or []
        evidence_ids = [str(x.get("id", "")) for x in evidence if isinstance(x, dict)]
        if len(evidence_ids) != len(set(evidence_ids)):
            errors.append(f"{case_id}: evidence id 重复")
        if len(evidence) < 2:
            warnings.append(f"{case_id}: 证据项少于 2 条")

    digest = sha256_text("\n".join(canonical_json(case) for case in cases))
    return {
        "status": "VALID" if not errors else "INVALID",
        "case_count": len(cases),
        "dataset_sha256": digest,
        "errors": errors,
        "warnings": warnings,
    }


def http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 300.0,
) -> tuple[int, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request_headers = {"Accept": "application/json", **(headers or {})}
    if data is not None:
        request_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body: Any = json.loads(raw)
        except json.JSONDecodeError:
            body = {"raw": raw[:2000]}
        return exc.code, body


def verify_sources(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """在线核验官方来源可访问性并记录响应哈希，不保存网页全文。"""
    validation = validate_dataset(cases)
    if validation["status"] != "VALID":
        raise EvalError(f"数据集校验失败: {validation['errors']}")
    checks: list[dict[str, Any]] = []
    try:
        import certifi

        tls_context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        tls_context = ssl.create_default_context()
    for case in cases:
        url = case["source"]["url"]
        started = time.perf_counter()
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "RiskLens-Evaluation/1.0 (+source-verification)"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=30, context=tls_context) as response:
                body = response.read()
                checks.append({
                    "case_id": case["case_id"],
                    "status": "VERIFIED" if response.status == 200 else "FAILED",
                    "http_status": response.status,
                    "final_url": response.geturl(),
                    "content_type": response.headers.get("Content-Type"),
                    "content_length": len(body),
                    "content_sha256": hashlib.sha256(body).hexdigest(),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                })
        except Exception as exc:
            checks.append({
                "case_id": case["case_id"],
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            })
    return {
        "schema_version": "risklens-source-verification-v1",
        "created_at": utc_now(),
        "dataset_sha256": validation["dataset_sha256"],
        "verified_count": sum(item["status"] == "VERIFIED" for item in checks),
        "total_count": len(checks),
        "checks": checks,
    }


def login(base_url: str, username: str, password: str) -> str:
    status, body = http_json(
        "POST",
        f"{base_url.rstrip('/')}/api/auth/login",
        {"username": username, "password": password},
        timeout=30,
    )
    if status != 200 or not isinstance(body, dict) or not body.get("access_token"):
        raise EvalError(f"登录失败，HTTP {status}: {body}")
    return str(body["access_token"])


def run_target(
    cases: list[dict[str, Any]],
    base_url: str,
    username: str,
    password: str,
    mode: str,
) -> dict[str, Any]:
    validation = validate_dataset(cases)
    if validation["status"] != "VALID":
        raise EvalError(f"数据集校验失败: {validation['errors']}")

    token = login(base_url, username, password)
    auth = {"Authorization": f"Bearer {token}"}
    health_status, health = http_json("GET", f"{base_url.rstrip('/')}/api/health", headers=auth, timeout=30)
    outputs: list[dict[str, Any]] = []

    for case in cases:
        item: dict[str, Any] = {"case_id": case["case_id"]}
        facts = case["input"]["facts"]
        if mode in {"retrieval", "both"}:
            started = time.perf_counter()
            status, body = http_json(
                "POST",
                f"{base_url.rstrip('/')}/api/cases/search",
                {"query": facts, "top_k": 5},
                auth,
            )
            item["retrieval"] = {
                "http_status": status,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                "response": body,
                "response_sha256": sha256_text(canonical_json(body)),
            }
        if mode in {"analysis", "both"}:
            started = time.perf_counter()
            status, body = http_json(
                "POST",
                f"{base_url.rstrip('/')}/api/analyze",
                {"case_description": facts, "top_k": 8, "stream": False},
                auth,
                timeout=360,
            )
            item["analysis"] = {
                "http_status": status,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                "response": body,
                "response_sha256": sha256_text(canonical_json(body)),
            }
        outputs.append(item)

    return {
        "schema_version": "risklens-eval-run-v1",
        "created_at": utc_now(),
        "dataset_sha256": validation["dataset_sha256"],
        "case_count": len(cases),
        "mode": mode,
        "target": {
            "base_url": base_url,
            "health_http_status": health_status,
            "health": health,
        },
        "outputs": outputs,
    }


def _judge_config(prefix: str) -> dict[str, str]:
    required = ("BASE_URL", "API_KEY", "MODEL")
    values = {name.lower(): os.getenv(f"{prefix}_{name}", "").strip() for name in required}
    missing = [f"{prefix}_{name}" for name in required if not values[name.lower()]]
    if missing:
        raise EvalError("缺少裁判模型配置: " + ", ".join(missing))
    return values


def _candidate_for_case(run_item: dict[str, Any]) -> Any:
    analysis = run_item.get("analysis") or {}
    if analysis.get("http_status") != 200:
        raise EvalError(f"目标分析未成功，HTTP {analysis.get('http_status')}")
    return analysis.get("response")


def validate_judgment(value: dict[str, Any], evidence_ids: set[str]) -> list[str]:
    errors: list[str] = []
    for field in SCORE_FIELDS:
        score = value.get(field)
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= float(score) <= 1:
            errors.append(f"{field} 必须是 0 到 1 的数字")
    for field in ("unsupported_claims", "wrong_citations", "missing_points", "evidence_ids"):
        if not isinstance(value.get(field), list):
            errors.append(f"{field} 必须是数组")
    if value.get("verdict") not in {"pass", "borderline", "fail"}:
        errors.append("verdict 非法")
    cited = set(str(x) for x in value.get("evidence_ids", []))
    if not cited:
        errors.append("必须引用至少一个 evidence id")
    if not cited.issubset(evidence_ids):
        errors.append("引用了 reference 中不存在的 evidence id")
    return errors


def run_judge(
    cases: list[dict[str, Any]],
    run: dict[str, Any],
    prefix: str,
    judge_name: str,
    prompt_path: Path,
) -> dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise EvalError("缺少 openai Python 包，无法调用兼容接口") from exc

    validation = validate_dataset(cases)
    if run.get("dataset_sha256") != validation["dataset_sha256"]:
        raise EvalError("运行结果与当前数据集哈希不一致")
    config = _judge_config(prefix)
    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"], timeout=180)
    system_prompt = prompt_path.read_text(encoding="utf-8")
    run_by_id = {item["case_id"]: item for item in run.get("outputs", [])}
    judgments: list[dict[str, Any]] = []

    for case in cases:
        case_id = case["case_id"]
        record: dict[str, Any] = {"case_id": case_id}
        try:
            candidate = _candidate_for_case(run_by_id.get(case_id, {}))
            reference = {"facts": case["input"]["facts"], **case["gold"]}
            user_payload = canonical_json({"reference": reference, "candidate": candidate})
            response = client.chat.completions.create(
                model=config["model"],
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_payload},
                ],
            )
            raw = response.choices[0].message.content or ""
            parsed = json.loads(raw)
            evidence_ids = {str(x["id"]) for x in case["gold"]["evidence"]}
            errors = validate_judgment(parsed, evidence_ids)
            record.update({
                "status": "VALID" if not errors else "INVALID",
                "judgment": parsed,
                "validation_errors": errors,
                "raw_sha256": sha256_text(raw),
            })
        except Exception as exc:  # 单例失败必须记录，不能伪造默认分数
            record.update({"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"})
        judgments.append(record)

    parsed_url = urllib.parse.urlparse(config["base_url"])
    return {
        "schema_version": "risklens-eval-judge-v1",
        "created_at": utc_now(),
        "dataset_sha256": validation["dataset_sha256"],
        "target_run_sha256": sha256_text(canonical_json(run)),
        "judge": {
            "name": judge_name,
            "model": config["model"],
            "provider_host": parsed_url.hostname,
            "prompt_sha256": sha256_text(system_prompt),
            "temperature": 0,
        },
        "judgments": judgments,
    }


def retrieval_metrics(cases: list[dict[str, Any]], run: dict[str, Any]) -> dict[str, Any]:
    run_by_id = {item["case_id"]: item for item in run.get("outputs", [])}
    ranks: list[int | None] = []
    details: list[dict[str, Any]] = []
    for case in cases:
        expected = set(case.get("retrieval_expectation", {}).get("known_relevant_case_ids", []))
        response = (run_by_id.get(case["case_id"], {}).get("retrieval") or {}).get("response") or {}
        ids = [str(x.get("case_id")) for x in response.get("results", []) if isinstance(x, dict)]
        rank = next((i for i, value in enumerate(ids, 1) if value in expected), None)
        ranks.append(rank)
        details.append({"case_id": case["case_id"], "rank": rank, "returned_ids": ids})
    n = len(ranks) or 1
    return {
        "note": "仅衡量当前库中人工标注的语义近邻，不代表外部原案精确召回。",
        "recall_at_1": sum(rank is not None and rank <= 1 for rank in ranks) / n,
        "recall_at_3": sum(rank is not None and rank <= 3 for rank in ranks) / n,
        "recall_at_5": sum(rank is not None and rank <= 5 for rank in ranks) / n,
        "mrr_at_5": sum(1 / rank for rank in ranks if rank is not None and rank <= 5) / n,
        "details": details,
    }


def _judgment_score(judgment: dict[str, Any]) -> float:
    return sum(float(judgment[field]) * SCORE_WEIGHTS[field] for field in SCORE_FIELDS)


def aggregate_report(
    cases: list[dict[str, Any]],
    run: dict[str, Any],
    judges: list[dict[str, Any]],
    source_verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validation = validate_dataset(cases)
    dataset_hash = validation["dataset_sha256"]
    reasons: list[str] = []
    if run.get("dataset_sha256") != dataset_hash:
        reasons.append("目标运行与数据集哈希不一致")
    if not source_verification:
        reasons.append("缺少在线官方来源核验记录")
    else:
        if source_verification.get("dataset_sha256") != dataset_hash:
            reasons.append("来源核验与数据集哈希不一致")
        if source_verification.get("verified_count") != len(cases):
            reasons.append(
                f"官方来源仅核验通过 {source_verification.get('verified_count', 0)}/{len(cases)}"
            )

    analysis_requested = run.get("mode") in {"analysis", "both"}
    analysis_success = sum(
        (item.get("analysis") or {}).get("http_status") == 200 for item in run.get("outputs", [])
    )
    if analysis_requested and analysis_success != len(cases):
        reasons.append(f"目标分析仅成功 {analysis_success}/{len(cases)}")
    if not analysis_requested:
        reasons.append("本次运行未执行案件分析")

    if len(judges) < 2:
        reasons.append("少于两名独立裁判")
    identities = {
        (j.get("judge", {}).get("provider_host"), j.get("judge", {}).get("model")) for j in judges
    }
    if len(judges) >= 2 and len(identities) < 2:
        reasons.append("裁判模型并非来自两个不同的 provider/model 身份")
    for judge in judges:
        if judge.get("dataset_sha256") != dataset_hash:
            reasons.append(f"裁判 {judge.get('judge', {}).get('name')} 数据集哈希不一致")
        if judge.get("target_run_sha256") != sha256_text(canonical_json(run)):
            reasons.append(f"裁判 {judge.get('judge', {}).get('name')} 目标运行哈希不一致")

    case_scores: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    if len(judges) >= 2:
        judge_maps = [
            {x["case_id"]: x for x in judge.get("judgments", [])} for judge in judges
        ]
        for case in cases:
            records = [mapping.get(case["case_id"]) for mapping in judge_maps]
            if any(not record or record.get("status") != "VALID" for record in records):
                reasons.append(f"{case['case_id']} 缺少有效裁判结果")
                continue
            per_judge = [_judgment_score(record["judgment"]) for record in records if record]
            mean_score = statistics.fmean(per_judge)
            spread = max(per_judge) - min(per_judge)
            entry = {
                "case_id": case["case_id"],
                "judge_scores": per_judge,
                "mean_score": mean_score,
                "spread": spread,
            }
            case_scores.append(entry)
            if spread > 0.20:
                disagreements.append(entry)

    complete = not reasons and len(case_scores) == len(cases)
    return {
        "schema_version": "risklens-eval-report-v1",
        "created_at": utc_now(),
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "publishable_overall_score": (
            statistics.fmean(x["mean_score"] for x in case_scores) if complete else None
        ),
        "incomplete_reasons": sorted(set(reasons)),
        "dataset": {
            "case_count": len(cases),
            "sha256": dataset_hash,
            "official_source_count": len({case["source"]["url"] for case in cases}),
        },
        "source_verification": source_verification,
        "target": run.get("target"),
        "retrieval": retrieval_metrics(cases, run) if run.get("mode") in {"retrieval", "both"} else None,
        "analysis_success_count": analysis_success,
        "judge_identities": [judge.get("judge") for judge in judges],
        "case_scores": case_scores,
        "judge_disagreements_over_0_20": disagreements,
        "weights": SCORE_WEIGHTS,
    }


def render_markdown(report: dict[str, Any], cases: list[dict[str, Any]]) -> str:
    status = report["status"]
    score = report.get("publishable_overall_score")
    lines = [
        "# RiskLens 独立评测报告",
        "",
        f"- 状态：**{status}**",
        f"- 数据集案例数：{report['dataset']['case_count']}",
        f"- 数据集 SHA-256：`{report['dataset']['sha256']}`",
        f"- 法院官方来源数：{report['dataset']['official_source_count']}",
        f"- 可发布综合分：{'未生成' if score is None else f'{score:.3f}'}",
        "",
    ]
    if report.get("incomplete_reasons"):
        lines.extend(["## 未完成原因", ""])
        lines.extend(f"- {reason}" for reason in report["incomplete_reasons"])
        lines.append("")
    retrieval = report.get("retrieval")
    if retrieval:
        lines.extend([
            "## 检索基线",
            "",
            f"- Recall@1：{retrieval['recall_at_1']:.3f}",
            f"- Recall@3：{retrieval['recall_at_3']:.3f}",
            f"- Recall@5：{retrieval['recall_at_5']:.3f}",
            f"- MRR@5：{retrieval['mrr_at_5']:.3f}",
            f"- 说明：{retrieval['note']}",
            "",
        ])
    lines.extend(["## 官方来源", ""])
    for case in cases:
        lines.append(f"- [{case['source']['title']}]({case['source']['url']}) — {case['case_id']}")
    lines.extend([
        "",
        "## 审计声明",
        "",
        "综合分只有在全部案例分析成功、数据集和运行哈希一致、且至少两名不同身份的裁判模型均返回有效结构化结果时才会生成。任何条件不满足时，报告状态固定为 INCOMPLETE。",
        "",
    ])
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RiskLens 可复现评测")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    source_parser = sub.add_parser("verify-sources")
    source_parser.add_argument("--output", type=Path, required=True)

    run_parser = sub.add_parser("run")
    run_parser.add_argument("--base-url", default="https://fangzhou.chat/risklens")
    run_parser.add_argument("--username-env", default="RISK_EVAL_USERNAME")
    run_parser.add_argument("--password-env", default="RISK_EVAL_PASSWORD")
    run_parser.add_argument("--mode", choices=("retrieval", "analysis", "both"), default="both")
    run_parser.add_argument("--output", type=Path, required=True)

    judge_parser = sub.add_parser("judge")
    judge_parser.add_argument("--run", type=Path, required=True)
    judge_parser.add_argument("--prefix", required=True, help="例如 JUDGE_A")
    judge_parser.add_argument("--name", required=True)
    judge_parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    judge_parser.add_argument("--output", type=Path, required=True)

    report_parser = sub.add_parser("report")
    report_parser.add_argument("--run", type=Path, required=True)
    report_parser.add_argument("--judge", type=Path, action="append", default=[])
    report_parser.add_argument("--source-verification", type=Path)
    report_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    cases = load_jsonl(args.dataset)
    if args.command == "validate":
        result = validate_dataset(cases)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "VALID" else 2

    if args.command == "verify-sources":
        result = verify_sources(cases)
        write_json(args.output, result)
        print(args.output)
        return 0 if result["verified_count"] == result["total_count"] else 4

    if args.command == "run":
        username = os.getenv(args.username_env, "")
        password = os.getenv(args.password_env, "")
        if not username or not password:
            raise EvalError(f"需要环境变量 {args.username_env} 和 {args.password_env}")
        result = run_target(cases, args.base_url, username, password, args.mode)
        write_json(args.output, result)
        print(args.output)
        return 0

    if args.command == "judge":
        run = json.loads(args.run.read_text(encoding="utf-8"))
        result = run_judge(cases, run, args.prefix, args.name, args.prompt)
        write_json(args.output, result)
        print(args.output)
        return 0

    if args.command == "report":
        run = json.loads(args.run.read_text(encoding="utf-8"))
        judges = [json.loads(path.read_text(encoding="utf-8")) for path in args.judge]
        source_verification = (
            json.loads(args.source_verification.read_text(encoding="utf-8"))
            if args.source_verification
            else None
        )
        result = aggregate_report(cases, run, judges, source_verification)
        write_json(args.output, result)
        md_path = args.output.with_suffix(".md")
        md_path.write_text(render_markdown(result, cases), encoding="utf-8")
        print(args.output)
        print(md_path)
        return 0 if result["status"] == "COMPLETE" else 3

    raise EvalError("未知命令")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EvalError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
