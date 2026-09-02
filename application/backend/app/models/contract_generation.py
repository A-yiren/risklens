"""合同生成 V1 的输入输出边界。

本模块只定义可验证的数据结构，不调用模型、不生成合同，也不持久化草稿。
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class StrictModel(BaseModel):
    """拒绝未知字段并清理字符串两端空白。"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ContractType(str, Enum):
    """V1 只开放住宅租赁，避免未经验证地泛化到其他合同。"""

    RESIDENTIAL_LEASE = "residential_lease"


class UserRole(str, Enum):
    LANDLORD = "landlord"
    TENANT = "tenant"


class GenerationStatus(str, Enum):
    NEEDS_CLARIFICATION = "needs_clarification"
    DRAFT_READY = "draft_ready"


class RequirementAnalysisStatus(str, Enum):
    NEEDS_CLARIFICATION = "needs_clarification"
    READY_FOR_DRAFTING = "ready_for_drafting"


class PartyInput(StrictModel):
    name: Optional[str] = Field(default=None, max_length=200)
    identifier: Optional[str] = Field(default=None, max_length=100)
    contact: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=500)


class LeaseTermsInput(StrictModel):
    property_address: Optional[str] = Field(default=None, max_length=500)
    property_description: Optional[str] = Field(default=None, max_length=1000)
    lease_purpose: Optional[str] = Field(default=None, max_length=200)
    lease_start_date: Optional[date] = None
    lease_end_date: Optional[date] = None
    rent_amount: Optional[Decimal] = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    currency: Literal["CNY"] = "CNY"
    rent_frequency: Optional[str] = Field(default=None, max_length=100)
    payment_due: Optional[str] = Field(default=None, max_length=200)
    deposit_amount: Optional[Decimal] = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    deposit_return_terms: Optional[str] = Field(default=None, max_length=1000)
    fee_allocation: Optional[str] = Field(default=None, max_length=2000)
    maintenance_terms: Optional[str] = Field(default=None, max_length=2000)
    early_termination_terms: Optional[str] = Field(default=None, max_length=2000)
    breach_terms: Optional[str] = Field(default=None, max_length=2000)
    handover_and_return_terms: Optional[str] = Field(default=None, max_length=2000)
    dispute_resolution: Optional[str] = Field(default=None, max_length=1000)
    jurisdiction_province: Optional[str] = Field(default=None, max_length=100)
    jurisdiction_city: Optional[str] = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_lease_dates(self):
        if self.lease_start_date and self.lease_end_date:
            if self.lease_end_date <= self.lease_start_date:
                raise ValueError("lease_end_date must be later than lease_start_date")
            try:
                latest_end = self.lease_start_date.replace(
                    year=self.lease_start_date.year + 20
                )
            except ValueError:
                # 2 月 29 日起算时，非闰年按 2 月 28 日作为二十年边界。
                latest_end = self.lease_start_date.replace(
                    year=self.lease_start_date.year + 20, day=28
                )
            if self.lease_end_date > latest_end:
                raise ValueError("residential lease term must not exceed 20 years")
        return self


class ContractGenerationRequest(StrictModel):
    contract_type: ContractType = ContractType.RESIDENTIAL_LEASE
    requirements: str = Field(min_length=1, max_length=10_000)
    user_role: Optional[UserRole] = None
    party_a: Optional[PartyInput] = None
    party_b: Optional[PartyInput] = None
    known_terms: LeaseTermsInput = Field(default_factory=LeaseTermsInput)
    knowledge_document_ids: list[str] = Field(default_factory=list, max_length=20)
    allow_placeholders: bool = False


class ClarificationQuestion(StrictModel):
    field: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=500)
    blocking: bool = True


class UnresolvedItem(StrictModel):
    field: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)
    placeholder: Optional[str] = Field(default=None, max_length=200)


class ContractRequirementAnalysis(StrictModel):
    """起草前的信息完整性结果；不包含任何生成合同。"""

    status: RequirementAnalysisStatus
    contract_type: ContractType = ContractType.RESIDENTIAL_LEASE
    analysis_method: Literal["deterministic_structured_fields_v1"] = (
        "deterministic_structured_fields_v1"
    )
    unverified_narrative: str = Field(min_length=1, max_length=10_000)
    known_facts: dict[str, object] = Field(default_factory=dict)
    clarification_questions: list[ClarificationQuestion] = Field(default_factory=list)
    unresolved_items: list[UnresolvedItem] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list, max_length=100)
    can_generate_draft: bool = False
    notice: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_analysis_state(self):
        if self.assumptions:
            raise ValueError("requirement analysis must not add assumptions")

        blocking = [question for question in self.clarification_questions if question.blocking]
        if self.status == RequirementAnalysisStatus.NEEDS_CLARIFICATION:
            if not blocking or self.can_generate_draft:
                raise ValueError("needs_clarification requires blocking questions")
        if self.status == RequirementAnalysisStatus.READY_FOR_DRAFTING:
            if blocking or not self.can_generate_draft:
                raise ValueError("ready_for_drafting cannot contain blocking questions")
        return self


class SourceCitation(StrictModel):
    citation_id: str = Field(min_length=1, max_length=128)
    source_name: str = Field(min_length=1, max_length=500)
    source_document_id: str = Field(min_length=1, max_length=128)
    exact_quote: str = Field(min_length=1, max_length=2000)
    locator: Optional[str] = Field(default=None, max_length=500)
    source_url: Optional[HttpUrl] = None
    is_official_source: bool = False


class ContractSection(StrictModel):
    section_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=10_000)
    citations: list[SourceCitation] = Field(default_factory=list, max_length=20)


class ReviewSummary(StrictModel):
    engine: Literal["contract-review-v2"] = "contract-review-v2"
    checks_executed: list[str] = Field(default_factory=list, max_length=100)
    findings: list[dict] = Field(default_factory=list, max_length=100)
    uncovered_areas: list[str] = Field(default_factory=list, max_length=100)
    coverage_notice: str = Field(min_length=1, max_length=1000)


class ContractGenerationResponse(StrictModel):
    status: GenerationStatus
    draft_id: Optional[str] = Field(default=None, max_length=128)
    contract_type: ContractType = ContractType.RESIDENTIAL_LEASE
    known_facts: dict[str, object] = Field(default_factory=dict)
    clarification_questions: list[ClarificationQuestion] = Field(default_factory=list)
    unresolved_items: list[UnresolvedItem] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list, max_length=100)
    sections: list[ContractSection] = Field(default_factory=list, max_length=100)
    rendered_contract: Optional[str] = Field(default=None, max_length=100_000)
    review_result: Optional[ReviewSummary] = None
    template_reference: dict[str, object] = Field(default_factory=dict)
    coverage_notice: str = Field(min_length=1, max_length=1000)
    disclaimer: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_status_payload(self):
        if self.assumptions:
            raise ValueError("assumptions must stay empty; unresolved facts require clarification or placeholders")

        if self.status == GenerationStatus.NEEDS_CLARIFICATION:
            if not self.clarification_questions:
                raise ValueError("needs_clarification requires clarification_questions")
            if self.rendered_contract is not None or self.sections or self.review_result is not None:
                raise ValueError("needs_clarification cannot contain a generated contract or review result")

        if self.status == GenerationStatus.DRAFT_READY:
            if not self.draft_id or not self.sections or not self.rendered_contract:
                raise ValueError("draft_ready requires draft_id, sections and rendered_contract")
            if self.clarification_questions:
                raise ValueError("draft_ready cannot contain blocking clarification questions")

        return self
