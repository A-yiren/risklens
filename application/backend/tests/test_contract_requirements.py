import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import contracts
from app.api.deps import get_current_user
from app.config import settings
from app.main import app
from app.models.contract_generation import ContractGenerationRequest
from app.services.contract_requirements import contract_requirement_service


def complete_request(**overrides) -> ContractGenerationRequest:
    payload = {
        "requirements": "我是承租人，租赁用途为居住。",
        "user_role": "tenant",
        "party_a": {"name": "测试出租人"},
        "party_b": {"name": "测试承租人"},
        "known_terms": {
            "property_address": "测试市测试区测试路1号",
            "lease_start_date": "2027-01-01",
            "lease_end_date": "2027-12-31",
            "rent_amount": 3000,
            "rent_frequency": "每月",
            "payment_due": "每月5日前",
        },
    }
    payload.update(overrides)
    return ContractGenerationRequest.model_validate(payload)


def test_natural_language_is_not_promoted_to_verified_facts():
    request = ContractGenerationRequest(
        requirements="我是承租人，月租3000元，从2027年1月开始，其他内容你补上。"
    )
    result = contract_requirement_service.analyze(request)

    assert result.status.value == "needs_clarification"
    assert result.can_generate_draft is False
    assert result.known_facts == {}
    assert result.assumptions == []
    blocking_fields = {q.field for q in result.clarification_questions if q.blocking}
    assert "known_terms.rent_amount" in blocking_fields
    assert "known_terms.lease_start_date" in blocking_fields


def test_complete_structured_core_facts_are_ready_without_assumptions():
    result = contract_requirement_service.analyze(complete_request())

    assert result.status.value == "ready_for_drafting"
    assert result.can_generate_draft is True
    assert result.assumptions == []
    assert not [q for q in result.clarification_questions if q.blocking]
    assert result.known_facts["known_terms"]["rent_amount"] == "3000"
    assert result.unverified_narrative == "我是承租人，租赁用途为居住。"


def test_explicit_placeholder_opt_in_never_creates_fake_values():
    request = ContractGenerationRequest(requirements="先出带待确认项的版本", allow_placeholders=True)
    result = contract_requirement_service.analyze(request)

    assert result.status.value == "ready_for_drafting"
    assert result.can_generate_draft is True
    assert result.known_facts == {}
    assert result.assumptions == []
    assert len(result.unresolved_items) == 9
    assert all(item.placeholder.startswith("【待确认：") for item in result.unresolved_items)


def test_default_currency_is_not_reported_without_a_rent_amount():
    request = ContractGenerationRequest(requirements="租金还没谈好")
    result = contract_requirement_service.analyze(request)
    assert "known_terms" not in result.known_facts


@pytest.mark.asyncio
async def test_preview_endpoint_is_hidden_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "contract_generation_v1_preview_enabled", False)
    with pytest.raises(HTTPException) as exc:
        await contracts.preview_contract_requirements(
            complete_request(),
            _user={"id": 1, "role": "user"},
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_preview_endpoint_returns_only_requirement_analysis(monkeypatch):
    monkeypatch.setattr(settings, "contract_generation_v1_preview_enabled", True)
    result = await contracts.preview_contract_requirements(
        complete_request(),
        _user={"id": 1, "role": "user"},
    )
    assert result.status.value == "ready_for_drafting"
    dumped = result.model_dump(mode="json")
    assert "rendered_contract" not in dumped
    assert "sections" not in dumped


def test_preview_endpoint_allows_authenticated_test_user(monkeypatch):
    monkeypatch.setattr(settings, "contract_generation_v1_preview_enabled", True)
    app.dependency_overrides[get_current_user] = lambda: {"id": 9, "role": "user"}
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/contracts/requirements-preview",
                json={"requirements": "我想租房"},
            )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["status"] == "needs_clarification"
