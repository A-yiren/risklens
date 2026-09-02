from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api import cases
from app.config import settings


@pytest.mark.asyncio
async def test_contract_review_defaults_to_v1(monkeypatch):
    monkeypatch.setattr(settings, "contract_review_v2_enabled", False)
    monkeypatch.setattr(settings, "contract_review_v2_shadow_enabled", False)
    v1 = AsyncMock(return_value={"risk_level": "low"})
    v2 = AsyncMock(return_value={"risk_level": "high"})
    monkeypatch.setattr(cases.contract_reviewer, "review", v1)
    monkeypatch.setattr(cases.contract_reviewer_v2, "review", v2)

    result = await cases.review_contract(
        cases.ContractReviewRequest(contract_text="测试合同"),
        user={"id": 1},
    )

    v1.assert_awaited_once()
    v2.assert_not_awaited()
    assert result["review_engine"] == "contract-review-v1"


@pytest.mark.asyncio
async def test_contract_review_can_switch_to_v2(monkeypatch):
    monkeypatch.setattr(settings, "contract_review_v2_enabled", True)
    monkeypatch.setattr(settings, "contract_review_v2_shadow_enabled", False)
    v1 = AsyncMock(return_value={"risk_level": "low"})
    v2 = AsyncMock(return_value={"risk_level": "high"})
    monkeypatch.setattr(cases.contract_reviewer, "review", v1)
    monkeypatch.setattr(cases.contract_reviewer_v2, "review", v2)

    result = await cases.review_contract(
        cases.ContractReviewRequest(contract_text="测试合同"),
        user={"id": 1},
    )

    v1.assert_not_awaited()
    v2.assert_awaited_once()
    assert result["review_engine"] == "contract-review-v2"


@pytest.mark.asyncio
async def test_shadow_runs_both_but_returns_v1(monkeypatch):
    monkeypatch.setattr(settings, "contract_review_v2_enabled", False)
    monkeypatch.setattr(settings, "contract_review_v2_shadow_enabled", True)
    v1 = AsyncMock(return_value={"risk_level": "low", "risks": []})
    v2 = AsyncMock(return_value={"risk_level": "high", "risks": [{"rule_id": "x"}]})
    monkeypatch.setattr(cases.contract_reviewer, "review", v1)
    monkeypatch.setattr(cases.contract_reviewer_v2, "review", v2)

    result = await cases.review_contract(
        cases.ContractReviewRequest(contract_text="测试合同"),
        user={"id": 1},
    )

    v1.assert_awaited_once()
    v2.assert_awaited_once()
    assert result["risk_level"] == "low"
    assert result["review_engine"] == "contract-review-v1"


@pytest.mark.asyncio
async def test_v2_preview_is_hidden_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "contract_review_v2_preview_enabled", False)

    with pytest.raises(HTTPException) as exc:
        await cases.preview_contract_review_v2(
            cases.ContractReviewRequest(contract_text="测试合同"),
            admin={"id": 1, "role": "admin"},
        )

    assert exc.value.status_code == 404
