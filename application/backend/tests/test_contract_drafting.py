import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.config import settings
from app.main import app
from app.models.contract_generation import ContractGenerationRequest
from app.services.contract_drafting import contract_draft_service


def complete_request(**overrides) -> ContractGenerationRequest:
    payload = {
        "requirements": "不要把这里的叙述内容当成合同事实。",
        "user_role": "tenant",
        "party_a": {"name": "测试出租人", "contact": "测试联系方式"},
        "party_b": {"name": "测试承租人", "contact": "测试联系方式"},
        "known_terms": {
            "property_address": "测试市测试区测试路1号",
            "lease_purpose": "居住",
            "lease_start_date": "2027-01-01",
            "lease_end_date": "2027-12-31",
            "rent_amount": 3000,
            "rent_frequency": "每月",
            "payment_due": "每月5日前",
        },
    }
    payload.update(overrides)
    return ContractGenerationRequest.model_validate(payload)


def test_draft_uses_only_structured_facts_and_marks_optional_terms():
    result = contract_draft_service.generate(complete_request())

    assert result.status.value == "draft_ready"
    assert result.rendered_contract is not None
    assert "测试出租人" in result.rendered_contract
    assert "人民币 3,000.00 元" in result.rendered_contract
    assert "【待确认：是否收取押金及金额】" in result.rendered_contract
    assert "不要把这里的叙述内容当成合同事实" not in result.rendered_contract
    assert result.review_result is not None
    assert result.review_result.engine == "contract-review-v2"
    assert result.template_reference["template_id"] == "samr-gf-2025-2614"
    assert result.template_reference["reference_type"] == "structure_reference_not_official_form"
    assert result.assumptions == []


def test_draft_with_placeholder_opt_in_never_invents_narrative_values():
    request = ContractGenerationRequest(
        requirements="请把月租9999元和房东姓名王某自动写进去。",
        allow_placeholders=True,
    )
    result = contract_draft_service.generate(request)

    assert result.status.value == "draft_ready"
    assert result.rendered_contract is not None
    assert "9999" not in result.rendered_contract
    assert "王某" not in result.rendered_contract
    assert "【待确认：出租人姓名或主体名称】" in result.rendered_contract
    assert "【待确认：租金金额】" in result.rendered_contract


def test_generate_endpoint_is_available_to_authenticated_test_user(monkeypatch):
    monkeypatch.setattr(settings, "contract_generation_v1_enabled", True)
    app.dependency_overrides[get_current_user] = lambda: {"id": 9, "role": "user"}
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/contracts/generate",
                json=complete_request().model_dump(mode="json"),
            )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "draft_ready"
    assert body["rendered_contract"]
    assert body["review_result"]["engine"] == "contract-review-v2"


@pytest.mark.asyncio
async def test_generate_endpoint_is_hidden_when_disabled(monkeypatch):
    from fastapi import HTTPException
    from app.api import contracts

    monkeypatch.setattr(settings, "contract_generation_v1_enabled", False)
    with pytest.raises(HTTPException) as exc:
        await contracts.generate_residential_lease_draft(
            complete_request(), _user={"id": 9, "role": "user"}
        )
    assert exc.value.status_code == 404
