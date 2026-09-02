from app.services.contract_templates import contract_template_service


def test_catalog_exposes_common_contracts_with_review_mapping():
    templates = contract_template_service.list_templates()
    ids = {item["id"] for item in templates}

    assert {
        "labor_contract", "labor_service_contract", "residential_lease", "goods_sale_contract",
        "service_contract", "entrustment_contract", "equipment_lease_contract",
        "vehicle_sale_contract", "renovation_contract", "technology_service_contract",
    } <= ids
    assert all(item["review_contract_type"] for item in templates)
    assert all(item["source_url"] for item in templates)
    assert all(len(item["review_checkpoints"]) >= 4 for item in templates)
    assert all(any(field["key"] == "dispute_resolution" for field in item["fields"]) for item in templates)


def test_draft_requires_confirmed_facts_unless_placeholders_allowed():
    result = contract_template_service.build_draft("labor_contract", {})

    assert result["status"] == "needs_clarification"
    assert result["missing"]

    placeholder_result = contract_template_service.build_draft(
        "labor_contract", {}, allow_placeholders=True
    )
    assert placeholder_result["status"] == "draft_ready"
    assert "【待确认：用人单位】" in placeholder_result["rendered_contract"]


def test_labor_draft_uses_only_explicit_form_facts():
    result = contract_template_service.build_draft(
        "labor_contract",
        {
            "employer": "北京示例科技有限公司",
            "employee": "张三",
            "term_type": "固定期限",
            "start_date": "2026-09-01",
            "end_date": "2027-08-31",
            "position": "产品经理",
            "workplace": "北京市",
            "working_hours": "标准工时",
            "salary": "18000",
            "payday": "每月 15 日",
            "social_insurance": "依法缴纳社会保险。",
            "rest_leave": "依法执行双休和法定节假日制度。",
            "labor_protection": "提供符合岗位要求的劳动条件和防护用品。",
            "signing_date": "2026-08-28",
            "signing_place": "北京市",
            "dispute_resolution": "发生争议先协商，协商不成依法申请劳动仲裁。",
        },
    )

    assert result["status"] == "draft_ready"
    assert "北京示例科技有限公司" in result["rendered_contract"]
    assert "【待确认：试用期约定】" in result["rendered_contract"]
    assert "依法申请劳动仲裁" in result["rendered_contract"]
    assert "第五条 休息休假、劳动保护及培训" in result["rendered_contract"]
