import json
from pathlib import Path

from app.services.contract_rules_v2 import scan_contract_rules_v2


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATASETS = (
    BACKEND_DIR / "evals" / "contract_review_v2_cases.json",
    BACKEND_DIR.parent / "outputs" / "contract-review-v2-official-derived-cases.json",
    BACKEND_DIR / "evals" / "contract_review_v2_regression_cases.json",
)


def _all_cases():
    for dataset in DATASETS:
        yield from json.loads(dataset.read_text(encoding="utf-8"))["cases"]


def test_contract_v2_baseline_dataset_has_no_misses_or_false_alarms():
    for case in _all_cases():
        findings = scan_contract_rules_v2(case["text"], case["contract_type"])
        assert {item["rule_id"] for item in findings} == set(case["expected_rule_ids"]), case["id"]


def test_every_v2_finding_has_exact_contract_and_legal_evidence():
    for case in _all_cases():
        for finding in scan_contract_rules_v2(case["text"], case["contract_type"]):
            evidence = finding["contract_evidence"]
            assert case["text"][evidence["start"]:evidence["end"]] == evidence["quote"]
            assert finding["decision_mode"] == "deterministic"
            assert finding["confidence"] == "high"
            assert all(finding["legal_basis"].get(key) for key in (
                "law_name", "article_no", "quote", "source_url"
            ))
