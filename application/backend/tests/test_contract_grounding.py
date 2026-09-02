from app.services.contract_review import ContractReviewService


CITATIONS = [
    {"law_name": "测试法", "article_no": "第一条", "article_text": "当事人应当诚信履行合同义务。"},
]


def test_contract_claim_requires_exact_quote():
    claims = [{
        "claim": "当事人应诚信履约",
        "citation_ids": [1],
        "supporting_quotes": [{"citation_id": 1, "quote": "应当诚信履行合同义务"}],
    }]
    assert ContractReviewService._validate_legal_claims(claims, CITATIONS) == claims


def test_contract_claim_with_fabricated_quote_is_rejected():
    claims = [{
        "claim": "可以任意解除合同",
        "citation_ids": [1],
        "supporting_quotes": [{"citation_id": 1, "quote": "可以任意解除合同"}],
    }]
    assert ContractReviewService._validate_legal_claims(claims, CITATIONS) == []


def test_contract_claim_with_unknown_citation_is_rejected():
    claims = [{
        "claim": "未知结论",
        "citation_ids": [99],
        "supporting_quotes": [{"citation_id": 99, "quote": "未知"}],
    }]
    assert ContractReviewService._validate_legal_claims(claims, CITATIONS) == []

