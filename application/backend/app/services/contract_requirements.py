"""合同生成前的确定性信息整理。

这里故意不解析自然语言。只有请求中的结构化字段被视为已确认事实，
从而避免在模型接入前把推测误当成姓名、金额、日期或地址。
"""

from dataclasses import dataclass
from typing import Callable

from app.models.contract_generation import (
    ClarificationQuestion,
    ContractGenerationRequest,
    ContractRequirementAnalysis,
    RequirementAnalysisStatus,
    UnresolvedItem,
)


@dataclass(frozen=True)
class RequiredFact:
    field: str
    question: str
    placeholder_label: str
    present: Callable[[ContractGenerationRequest], bool]


REQUIRED_FACTS = (
    RequiredFact("user_role", "您是出租人还是承租人？", "用户立场", lambda req: req.user_role is not None),
    RequiredFact(
        "party_a.name",
        "请填写出租人的姓名或主体名称。",
        "出租人姓名或主体名称",
        lambda req: bool(req.party_a and req.party_a.name),
    ),
    RequiredFact(
        "party_b.name",
        "请填写承租人的姓名或主体名称。",
        "承租人姓名或主体名称",
        lambda req: bool(req.party_b and req.party_b.name),
    ),
    RequiredFact(
        "known_terms.property_address",
        "请填写租赁房屋的地址或可识别描述。",
        "租赁房屋地址",
        lambda req: bool(req.known_terms.property_address),
    ),
    RequiredFact(
        "known_terms.lease_start_date",
        "租赁开始日期是哪一天？",
        "租赁开始日期",
        lambda req: req.known_terms.lease_start_date is not None,
    ),
    RequiredFact(
        "known_terms.lease_end_date",
        "租赁结束日期是哪一天？",
        "租赁结束日期",
        lambda req: req.known_terms.lease_end_date is not None,
    ),
    RequiredFact(
        "known_terms.rent_amount",
        "租金金额是多少？",
        "租金金额",
        lambda req: req.known_terms.rent_amount is not None,
    ),
    RequiredFact(
        "known_terms.rent_frequency",
        "租金按月、按季还是按其他周期支付？",
        "租金支付周期",
        lambda req: bool(req.known_terms.rent_frequency),
    ),
    RequiredFact(
        "known_terms.payment_due",
        "每个支付周期应在什么时候支付租金？",
        "租金支付时间",
        lambda req: bool(req.known_terms.payment_due),
    ),
)


OPTIONAL_QUESTIONS = (
    ("known_terms.deposit_amount", "是否收取押金？如收取，金额是多少？"),
    ("known_terms.deposit_return_terms", "押金在什么条件和期限内退还？"),
    ("known_terms.fee_allocation", "水、电、燃气、物业和网络等费用由谁承担？"),
    ("known_terms.maintenance_terms", "房屋和设施的维修责任如何分配？"),
    ("known_terms.early_termination_terms", "双方可以在什么情况下提前解除合同？"),
    ("known_terms.breach_terms", "违约责任和违约金如何约定？"),
    ("known_terms.handover_and_return_terms", "房屋如何交付、验收和返还？"),
    ("known_terms.dispute_resolution", "发生争议时采用诉讼还是其他方式解决？"),
    ("known_terms.jurisdiction_province", "合同适用地所在省份是什么？"),
    ("known_terms.jurisdiction_city", "合同适用地所在城市是什么？"),
)


class ContractRequirementService:
    NOTICE = (
        "本结果只检查明确填写的结构化字段。自然语言描述仅作为未核实原文保留，"
        "不会自动提取或补造姓名、地址、金额、日期及法律依据。"
    )

    def analyze(self, request: ContractGenerationRequest) -> ContractRequirementAnalysis:
        missing = [fact for fact in REQUIRED_FACTS if not fact.present(request)]
        questions: list[ClarificationQuestion] = []
        unresolved: list[UnresolvedItem] = []

        if request.allow_placeholders:
            unresolved = [
                UnresolvedItem(
                    field=fact.field,
                    reason="用户尚未明确提供该项事实",
                    placeholder=f"【待确认：{fact.placeholder_label}】",
                )
                for fact in missing
            ]
        else:
            questions = [
                ClarificationQuestion(field=fact.field, question=fact.question, blocking=True)
                for fact in missing
            ]

        questions.extend(self._optional_questions(request))
        ready = not any(question.blocking for question in questions)

        return ContractRequirementAnalysis(
            status=(
                RequirementAnalysisStatus.READY_FOR_DRAFTING
                if ready
                else RequirementAnalysisStatus.NEEDS_CLARIFICATION
            ),
            unverified_narrative=request.requirements,
            known_facts=self._known_facts(request),
            clarification_questions=questions,
            unresolved_items=unresolved,
            assumptions=[],
            can_generate_draft=ready,
            notice=self.NOTICE,
        )

    @staticmethod
    def _known_facts(request: ContractGenerationRequest) -> dict[str, object]:
        facts: dict[str, object] = {}
        if request.user_role is not None:
            facts["user_role"] = request.user_role.value
        if request.party_a is not None:
            party_a = request.party_a.model_dump(mode="json", exclude_none=True)
            if party_a:
                facts["party_a"] = party_a
        if request.party_b is not None:
            party_b = request.party_b.model_dump(mode="json", exclude_none=True)
            if party_b:
                facts["party_b"] = party_b
        terms = request.known_terms.model_dump(mode="json", exclude_none=True)
        # 默认币种只有在用户明确给出金额时才作为事实返回。
        if request.known_terms.rent_amount is None:
            terms.pop("currency", None)
        if terms:
            facts["known_terms"] = terms
        if request.knowledge_document_ids:
            facts["knowledge_document_ids"] = request.knowledge_document_ids
        return facts

    @staticmethod
    def _optional_questions(request: ContractGenerationRequest) -> list[ClarificationQuestion]:
        terms = request.known_terms
        values = {
            "known_terms.deposit_amount": terms.deposit_amount,
            "known_terms.deposit_return_terms": terms.deposit_return_terms,
            "known_terms.fee_allocation": terms.fee_allocation,
            "known_terms.maintenance_terms": terms.maintenance_terms,
            "known_terms.early_termination_terms": terms.early_termination_terms,
            "known_terms.breach_terms": terms.breach_terms,
            "known_terms.handover_and_return_terms": terms.handover_and_return_terms,
            "known_terms.dispute_resolution": terms.dispute_resolution,
            "known_terms.jurisdiction_province": terms.jurisdiction_province,
            "known_terms.jurisdiction_city": terms.jurisdiction_city,
        }
        return [
            ClarificationQuestion(field=field, question=question, blocking=False)
            for field, question in OPTIONAL_QUESTIONS
            if values[field] is None
        ]


contract_requirement_service = ContractRequirementService()
