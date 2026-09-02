"""合同生成相关的受控预览接口。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import get_current_user
from app.config import settings
from app.models.contract_generation import (
    ContractGenerationRequest,
    ContractGenerationResponse,
    ContractRequirementAnalysis,
)
from app.services.contract_drafting import contract_draft_service
from app.services.contract_requirements import contract_requirement_service
from app.services.contract_templates import contract_template_service


router = APIRouter(
    prefix="/api/contracts",
    tags=["contract-generation"],
    dependencies=[Depends(get_current_user)],
)


class TemplateDraftRequest(BaseModel):
    """仅接受表单中明确输入的事实，拒绝额外字段。"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    facts: dict[str, str] = Field(default_factory=dict, max_length=80)
    allow_placeholders: bool = False


@router.get("/templates")
async def list_contract_templates(
    _user: dict = Depends(get_current_user),
):
    """合同制作与审查共用的模板目录。"""
    return {"templates": contract_template_service.list_templates()}


@router.get("/templates/{template_id}")
async def get_contract_template(
    template_id: str,
    _user: dict = Depends(get_current_user),
):
    try:
        template = contract_template_service.get_template(template_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return contract_template_service.public_template(template)


@router.post("/templates/{template_id}/requirements")
async def preview_template_requirements(
    template_id: str,
    request: TemplateDraftRequest,
    _user: dict = Depends(get_current_user),
):
    try:
        return contract_template_service.analyze(template_id, request.facts)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/templates/{template_id}/draft")
async def generate_template_draft(
    template_id: str,
    request: TemplateDraftRequest,
    _user: dict = Depends(get_current_user),
):
    try:
        return contract_template_service.build_draft(
            template_id, request.facts, request.allow_placeholders
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/requirements-preview", response_model=ContractRequirementAnalysis)
async def preview_contract_requirements(
    request: ContractGenerationRequest,
    _user: dict = Depends(get_current_user),
) -> ContractRequirementAnalysis:
    """测试用户可用的事实确认；不调用模型，也不生成合同。"""
    if not settings.contract_generation_v1_preview_enabled:
        raise HTTPException(status_code=404, detail="合同生成 V1 需求预览未启用")
    return contract_requirement_service.analyze(request)


@router.post("/generate", response_model=ContractGenerationResponse)
async def generate_residential_lease_draft(
    request: ContractGenerationRequest,
    _user: dict = Depends(get_current_user),
) -> ContractGenerationResponse:
    """生成固定模板草稿；只使用已确认字段，未确认事实保留为可见占位符。"""
    if not settings.contract_generation_v1_enabled:
        raise HTTPException(status_code=404, detail="合同生成 V1 未启用")
    return contract_draft_service.generate(request)
