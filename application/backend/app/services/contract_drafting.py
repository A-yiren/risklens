"""住宅租赁合同 V1 的确定性草稿服务。

本服务不调用模型、不读取知识库，也不从自然语言需求中提取事实。
它只将用户明确填写的结构化字段放进固定模板；未确认内容一律以可见
占位符保留，供测试用户逐项确认。
"""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.models.contract_generation import (
    ContractGenerationRequest,
    ContractGenerationResponse,
    ContractSection,
    GenerationStatus,
    ReviewSummary,
    UnresolvedItem,
)
from app.services.contract_requirements import contract_requirement_service
from app.services.contract_rules_v2 import scan_contract_rules_v2
from app.services.contract_template_matcher import residential_lease_draft_reference


def _placeholder(label: str) -> str:
    return f"【待确认：{label}】"


def _money(value: Decimal | None) -> str:
    return f"人民币 {value:,.2f} 元" if value is not None else _placeholder("租金金额")


def _term_value(value: object | None, label: str) -> str:
    if value is None or value == "":
        return _placeholder(label)
    return str(value)


class ContractDraftService:
    """生成仅限住宅租赁、可审阅且不补造事实的测试草稿。"""

    COVERAGE_NOTICE = (
        "本草稿由固定模板和已确认字段组成；未填写内容以【待确认】标出。"
        "它没有读取用户选择的知识库文档、没有生成或验证法律引用，且仅执行"
        "Contract Review V2 当前已实现的四类确定性检查。"
    )
    DISCLAIMER = (
        "这是供测试与事实确认使用的合同草稿，不构成律师审核意见、法律意见或"
        "签署建议。请在签署前逐项确认占位内容并由具备相应资质的专业人士复核。"
    )

    def generate(self, request: ContractGenerationRequest) -> ContractGenerationResponse:
        analysis = contract_requirement_service.analyze(request)
        if not analysis.can_generate_draft:
            return ContractGenerationResponse(
                status=GenerationStatus.NEEDS_CLARIFICATION,
                contract_type=request.contract_type,
                known_facts=analysis.known_facts,
                clarification_questions=analysis.clarification_questions,
                unresolved_items=analysis.unresolved_items,
                assumptions=[],
                coverage_notice=self.COVERAGE_NOTICE,
                disclaimer=self.DISCLAIMER,
            )

        unresolved = list(analysis.unresolved_items)
        unresolved.extend(
            UnresolvedItem(
                field=question.field,
                reason=question.question,
                placeholder=_placeholder(question.field),
            )
            for question in analysis.clarification_questions
            if not question.blocking
        )
        sections = self._build_sections(request)
        rendered_contract = self._render(sections)
        findings = scan_contract_rules_v2(rendered_contract, contract_type="lease")
        review_result = ReviewSummary(
            checks_executed=[
                "lease.term.exceeds_20_years",
                "general.earnest_money.exceeds_20_percent",
            ],
            findings=findings,
            uncovered_areas=[
                "租赁登记、房屋权属、税费及当地监管要求",
                "未填写或以占位符保留的条款",
                "除当前确定性规则外的全部法律风险",
            ],
            coverage_notice=(
                "未发现当前规则命中不表示草稿无风险；该复审不能替代逐条法律审阅。"
            ),
        )
        return ContractGenerationResponse(
            status=GenerationStatus.DRAFT_READY,
            draft_id=f"lease-draft-{uuid4().hex}",
            contract_type=request.contract_type,
            known_facts=analysis.known_facts,
            clarification_questions=[],
            unresolved_items=unresolved,
            assumptions=[],
            sections=sections,
            rendered_contract=rendered_contract,
            review_result=review_result,
            template_reference=residential_lease_draft_reference(),
            coverage_notice=self.COVERAGE_NOTICE,
            disclaimer=self.DISCLAIMER,
        )

    def _build_sections(self, request: ContractGenerationRequest) -> list[ContractSection]:
        terms = request.known_terms
        party_a = request.party_a
        party_b = request.party_b
        landlord = _term_value(party_a.name if party_a else None, "出租人姓名或主体名称")
        tenant = _term_value(party_b.name if party_b else None, "承租人姓名或主体名称")
        landlord_contact = _term_value(party_a.contact if party_a else None, "出租人联系方式")
        tenant_contact = _term_value(party_b.contact if party_b else None, "承租人联系方式")
        property_address = _term_value(terms.property_address, "租赁房屋地址")
        purpose = _term_value(terms.lease_purpose, "租赁用途")
        start = _term_value(terms.lease_start_date.isoformat() if terms.lease_start_date else None, "租赁开始日期")
        end = _term_value(terms.lease_end_date.isoformat() if terms.lease_end_date else None, "租赁结束日期")
        rent_frequency = _term_value(terms.rent_frequency, "租金支付周期")
        payment_due = _term_value(terms.payment_due, "租金支付时间")
        deposit = (
            "双方明确约定不收取押金。"
            if terms.deposit_amount == 0
            else (
                f"押金为人民币 {terms.deposit_amount:,.2f} 元。"
                if terms.deposit_amount is not None
                else _placeholder("是否收取押金及金额")
            )
        )
        sections = [
            ContractSection(
                section_id="parties",
                title="第一条 合同双方",
                text=(
                    f"出租人（甲方）：{landlord}\n联系方式：{landlord_contact}\n\n"
                    f"承租人（乙方）：{tenant}\n联系方式：{tenant_contact}"
                ),
            ),
            ContractSection(
                section_id="property",
                title="第二条 房屋与用途",
                text=(
                    f"甲方将位于{property_address}的住宅出租给乙方使用。"
                    f"房屋用途：{purpose}。房屋现状、附属设施及交付清单："
                    f"{_term_value(terms.property_description, '房屋现状及附属设施清单')}。"
                ),
            ),
            ContractSection(
                section_id="term",
                title="第三条 租赁期限",
                text=(
                    f"租赁期限自 {start} 起至 {end} 止。双方确认，单次约定的租赁"
                    "期限不得超过二十年；续租应另行书面确认。"
                ),
            ),
            ContractSection(
                section_id="rent",
                title="第四条 租金与支付",
                text=(
                    f"租金为{_money(terms.rent_amount)}，按{rent_frequency}支付。"
                    f"乙方应于{payment_due}前向甲方支付当期租金。支付账户、收款凭证"
                    f"和支付方式：{_placeholder('收款账户与支付方式')}。"
                ),
            ),
            ContractSection(
                section_id="deposit",
                title="第五条 押金",
                text=(
                    f"{deposit}\n押金退还条件和期限："
                    f"{_term_value(terms.deposit_return_terms, '押金退还条件和期限')}。"
                ),
            ),
            ContractSection(
                section_id="fees_and_maintenance",
                title="第六条 费用与维修",
                text=(
                    f"费用承担：{_term_value(terms.fee_allocation, '水电燃气物业网络等费用分配')}。\n"
                    f"维修责任：{_term_value(terms.maintenance_terms, '房屋及设施维修责任分配')}。"
                ),
            ),
            ContractSection(
                section_id="handover",
                title="第七条 交付、返还与转租",
                text=(
                    f"交付、验收和返还安排："
                    f"{_term_value(terms.handover_and_return_terms, '交付验收及返还安排')}。\n"
                    f"转租、装修及改造须经甲方书面同意，具体约定：{_placeholder('转租装修约定')}。"
                ),
            ),
            ContractSection(
                section_id="termination",
                title="第八条 提前解除与违约责任",
                text=(
                    f"提前解除条件：{_term_value(terms.early_termination_terms, '提前解除条件')}。\n"
                    f"违约责任：{_term_value(terms.breach_terms, '违约责任与违约金计算方式')}。"
                ),
            ),
            ContractSection(
                section_id="disputes",
                title="第九条 争议解决与其他",
                text=(
                    f"争议解决方式：{_term_value(terms.dispute_resolution, '争议解决方式及管辖')}。\n"
                    "本合同一式【待确认：份数】份，甲乙双方各执【待确认：份数】份；"
                    "双方签字或盖章后生效。"
                ),
            ),
        ]
        return sections

    def _render(self, sections: list[ContractSection]) -> str:
        body = "\n\n".join(f"{section.title}\n{section.text}" for section in sections)
        return "住宅租赁合同（测试版草稿）\n\n" + body + "\n\n---\n" + self.DISCLAIMER


contract_draft_service = ContractDraftService()
