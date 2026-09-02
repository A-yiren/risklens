import pytest
from fastapi import HTTPException

from app.api import cases
from app.services.contract_template_matcher import match_contract_template


RESIDENTIAL_LEASE_TEXT = (
    "出租人甲方与承租人乙方签订房屋租赁合同。房屋坐落于测试市，"
    "租赁期限自2027年1月1日起至2027年12月31日止。"
    "月租金3000元，乙方按月支付。押金3000元。水电物业费由乙方承担，"
    "房屋维修由双方按约定负责。交付时验收，返还时核验；转租须经书面同意。"
    "提前解除及违约责任另行约定。"
)


def test_residential_lease_matches_registered_template_structure():
    result = match_contract_template(RESIDENTIAL_LEASE_TEXT, "lease")

    assert result["status"] == "precise_structure_match"
    assert result["review_action"] == "allow"
    assert result["best_candidate"]["template_id"] == "samr-gf-2025-2614"
    assert result["best_candidate"]["score"] == 100


def test_mismatched_manual_type_is_blocked_before_review():
    result = match_contract_template(RESIDENTIAL_LEASE_TEXT, "labor")

    assert result["status"] == "mismatch"
    assert result["review_action"] == "block"
    assert result["recommended_contract_type"] == "lease"


def test_labor_and_sale_profiles_require_domain_specific_signals():
    labor = match_contract_template(
        "用人单位甲方与劳动者乙方签订劳动合同。合同期限三年。"
        "工作内容和工作地点为测试岗位。工作时间按标准工时执行。"
        "工资按月支付并缴纳社会保险，提供劳动保护，试用期两个月。",
        "labor",
    )
    automobile = match_contract_template(
        "出卖人甲方将汽车出售给买受人乙方。车辆车架号和发动机号见附件。"
        "车辆总价款10万元，交付时验收并移交随车文件。质量保修按三包执行，"
        "违约争议由双方协商。",
        "sale",
    )
    generic_sale = match_contract_template(
        "甲方将设备出售给乙方，价款10万元，交付后付款。",
        "sale",
    )

    assert labor["status"] == "precise_structure_match"
    assert labor["best_candidate"]["template_id"] == "mohrss-labor-contract-required-terms"
    assert automobile["status"] == "precise_structure_match"
    assert automobile["best_candidate"]["template_id"] == "samr-xinjiang-auto-sale"
    assert generic_sale["status"] != "precise_structure_match"


@pytest.mark.asyncio
async def test_review_endpoint_returns_a_clear_type_mismatch_instead_of_503():
    with pytest.raises(HTTPException) as exc:
        await cases.review_contract(
            cases.ContractReviewRequest(
                contract_text=RESIDENTIAL_LEASE_TEXT,
                contract_type="labor",
            ),
            user={"id": 1, "role": "user"},
        )

    assert exc.value.status_code == 422
    assert exc.value.detail["template_match"]["recommended_contract_type"] == "lease"
