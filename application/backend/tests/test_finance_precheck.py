from pathlib import Path

from app.models import DocumentInfo, DocumentStatus, SourceType
from app.services.finance_precheck import finance_precheck_service


def _doc(tmp_path: Path, doc_id: str, name: str, text: str) -> DocumentInfo:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return DocumentInfo(
        id=doc_id,
        name=name,
        source=SourceType.UPLOAD,
        file_path=str(path),
        status=DocumentStatus.READY,
        visibility="private",
        owner_user_id="user-1",
    )


def test_precheck_finds_missing_materials_and_keeps_decision_boundary(tmp_path):
    result = finance_precheck_service.review([
        _doc(tmp_path, "doc-license", "营业执照.txt", "企业名称：测试科技有限公司\n法定代表人：李四\n统一社会信用代码：91310000ABCDEFGH12"),
    ])

    missing = {item["key"] for item in result["material_checklist"] if item["status"] == "missing"}
    assert {"loan_application", "financial_statements", "tax_material"} <= missing
    assert result["status"] == "needs_human_review"
    assert "不构成授信审批" in result["decision_boundary"]
    assert result["summary"]["manual_review_required"] is True


def test_precheck_detects_cross_document_inconsistency_with_evidence(tmp_path):
    docs = [
        _doc(tmp_path, "doc-license", "营业执照.txt", "营业执照\n企业名称：测试科技有限公司\n法定代表人：李四\n统一社会信用代码：91310000ABCDEFGH12"),
        _doc(tmp_path, "doc-application", "融资申请书.txt", "融资申请\n申请人：测试科技有限公司\n法定代表人：张三\n申请金额：100万元"),
        _doc(tmp_path, "doc-finance", "财务报表.txt", "2025年度资产负债表\n利润表\n现金流量表"),
        _doc(tmp_path, "doc-tax", "完税证明.txt", "完税证明 纳税申报"),
        _doc(tmp_path, "doc-bank", "银行流水.txt", "银行流水 账户交易明细"),
        _doc(tmp_path, "doc-contract", "销售合同.txt", "销售合同 合同编号：S-2026-01"),
        _doc(tmp_path, "doc-ar", "应收账款账龄表.txt", "应收账款账龄 客户名称 回款计划"),
    ]

    result = finance_precheck_service.review(docs)

    conflicts = [flag for flag in result["risk_flags"] if flag["type"] == "cross_document_inconsistency"]
    assert any("法定代表人" in flag["title"] for flag in conflicts)
    assert all(flag["evidence"] for flag in conflicts)
    assert result["summary"]["required_materials_present"] == result["summary"]["required_materials_total"]
