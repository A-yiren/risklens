import copy

from evals.eval_cli import aggregate_report, canonical_json, sha256_text, validate_dataset


def _case(case_id: str = "case-a") -> dict:
    return {
        "case_id": case_id,
        "split": "test",
        "source": {
            "publisher": "最高人民法院",
            "authority": "official_court",
            "title": "公开案例",
            "url": "https://www.court.gov.cn/example",
            "accessed_at": "2026-08-26",
        },
        "input": {"facts": "这是一个长度足够且已经去除案号和当事人姓名的案件事实描述，用于独立盲测。"},
        "gold": {
            "issues": ["争议焦点"],
            "legal_bases": ["法律依据"],
            "decision": "支持请求",
            "holdings": ["裁判要点"],
            "evidence": [
                {"id": "e1", "text": "证据一"},
                {"id": "e2", "text": "证据二"},
            ],
        },
        "leakage": {"forbidden_tokens": ["（2026）案号"]},
        "retrieval_expectation": {
            "known_relevant_case_ids": ["seed-1"],
            "relevant_topics": ["测试"],
        },
    }


def _run(cases: list[dict], mode: str = "both") -> dict:
    validation = validate_dataset(cases)
    return {
        "dataset_sha256": validation["dataset_sha256"],
        "mode": mode,
        "target": {"health": {"version": "test"}},
        "outputs": [
            {
                "case_id": case["case_id"],
                "retrieval": {
                    "http_status": 200,
                    "response": {"results": [{"case_id": "seed-1"}]},
                },
                "analysis": {"http_status": 200, "response": {"answer": "ok"}},
            }
            for case in cases
        ],
    }


def _judge(cases: list[dict], run: dict, host: str, model: str) -> dict:
    judgment = {
        "issue_identification": 1.0,
        "legal_basis_accuracy": 1.0,
        "decision_direction": 1.0,
        "reasoning_groundedness": 1.0,
        "completeness": 1.0,
        "unsupported_claims": [],
        "wrong_citations": [],
        "missing_points": [],
        "evidence_ids": ["e1"],
        "verdict": "pass",
        "reason": "与标准答案一致",
    }
    return {
        "dataset_sha256": validate_dataset(cases)["dataset_sha256"],
        "target_run_sha256": sha256_text(canonical_json(run)),
        "judge": {"name": model, "provider_host": host, "model": model},
        "judgments": [
            {"case_id": case["case_id"], "status": "VALID", "judgment": copy.deepcopy(judgment)}
            for case in cases
        ],
    }


def test_dataset_rejects_leaked_identifier():
    case = _case()
    case["input"]["facts"] += "（2026）案号"
    result = validate_dataset([case])
    assert result["status"] == "INVALID"
    assert any("泄漏" in error for error in result["errors"])


def test_report_refuses_score_without_two_judges():
    cases = [_case()]
    run = _run(cases)
    report = aggregate_report(cases, run, [])
    assert report["status"] == "INCOMPLETE"
    assert report["publishable_overall_score"] is None


def test_report_refuses_same_judge_identity():
    cases = [_case()]
    run = _run(cases)
    judge_a = _judge(cases, run, "same.example", "same-model")
    judge_b = _judge(cases, run, "same.example", "same-model")
    report = aggregate_report(cases, run, [judge_a, judge_b])
    assert report["status"] == "INCOMPLETE"
    assert report["publishable_overall_score"] is None


def test_report_publishes_only_with_complete_independent_evidence():
    cases = [_case()]
    run = _run(cases)
    judge_a = _judge(cases, run, "provider-a.example", "model-a")
    judge_b = _judge(cases, run, "provider-b.example", "model-b")
    source_verification = {
        "dataset_sha256": validate_dataset(cases)["dataset_sha256"],
        "verified_count": 1,
        "total_count": 1,
        "checks": [{"case_id": "case-a", "status": "VERIFIED"}],
    }
    report = aggregate_report(cases, run, [judge_a, judge_b], source_verification)
    assert report["status"] == "COMPLETE"
    assert report["publishable_overall_score"] == 1.0
    assert report["retrieval"]["recall_at_1"] == 1.0
