"""融资材料预审 API：只输出材料核验与人工复核建议。"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.services.finance_precheck import finance_precheck_service
from app.services.finance_precheck_evaluation import public_evaluation_disclosure
from app.services.finance_regulation_catalog import search_regulations
from app.storage.sqlite import db


router = APIRouter(
    prefix="/api/finance-precheck",
    tags=["finance-precheck"],
    dependencies=[Depends(get_current_user)],
)


class FinancePrecheckRequest(BaseModel):
    document_ids: list[str] = Field(min_length=1, max_length=20)
    product_type: Literal["working_capital"] = "working_capital"


class FollowUpRequest(BaseModel):
    run_id: str = Field(min_length=8, max_length=80)
    message: str = Field(min_length=2, max_length=1000)


@router.get("/eligible-documents")
async def eligible_documents(user: dict = Depends(get_current_user)):
    """仅暴露当前用户私有上传材料，避免把共享法规误用于企业材料预审。"""
    user_id = str(user["id"])
    docs = db.list_documents(limit=500, user_id=user_id, include_all=False)
    return [
        {
            "id": doc.id,
            "name": doc.name,
            "size": doc.size,
            "status": doc.status.value,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
        for doc in docs
        if doc.visibility == "private" and doc.owner_user_id == user_id and doc.status.value == "ready"
    ]


@router.post("/review")
async def review_materials(request: FinancePrecheckRequest, user: dict = Depends(get_current_user)):
    user_id = str(user["id"])
    documents = []
    for doc_id in dict.fromkeys(request.document_ids):
        document = db.get_document(doc_id, user_id=user_id, include_all=False)
        if not document or document.visibility != "private" or document.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="材料不存在、尚未入库或无权使用")
        if document.status.value != "ready":
            raise HTTPException(status_code=409, detail=f"材料尚未准备完成：{document.name}")
        documents.append(document)

    result = finance_precheck_service.review(documents, request.product_type)
    run_id = db.save_finance_precheck_run(user_id, request.product_type, [doc.id for doc in documents], result)
    return {"run_id": run_id, **result}


@router.get("/runs")
async def list_runs(user: dict = Depends(get_current_user)):
    return db.list_finance_precheck_runs(str(user["id"]), limit=30)


@router.delete("/runs/{run_id}")
async def delete_run(run_id: str, user: dict = Depends(get_current_user)):
    """用户可删除自己的预审结果；原始材料需在资料库单独删除。"""
    if not db.delete_finance_precheck_run(run_id, str(user["id"])):
        raise HTTPException(status_code=404, detail="预审记录不存在或无权删除")
    return {"status": "deleted", "run_id": run_id}


@router.post("/follow-up")
async def follow_up(request: FollowUpRequest, user: dict = Depends(get_current_user)):
    """基于同一次预审记录回答补件问题；不脱离已核验材料作专业结论。"""
    run = db.get_finance_precheck_run(request.run_id, str(user["id"]))
    if not run:
        raise HTTPException(status_code=404, detail="预审记录不存在或无权访问")
    result = run["result"]
    missing = [item["name"] for item in result.get("material_checklist", []) if item.get("required") and item.get("status") == "missing"]
    text = request.message.strip()
    if missing:
        answer = f"本次记录仍缺少：{'、'.join(missing)}。请在资料库补充后重新运行预审；系统会沿用本次问题作为上下文，但不会据此作出授信结论。"
    else:
        answer = "基础材料已识别。请补充说明你希望核实的字段或机构要求；系统只能基于已上传材料定位证据，并会把最终判断交由人工复核。"
    return {"run_id": run["id"], "context_created_at": run["created_at"], "answer": answer, "boundary": result.get("decision_boundary"), "question_echo": text}


@router.get("/evaluation")
async def evaluation_disclosure():
    """公开展示评测范围和未满足的发布前置条件，避免把内部样本夸大为真实准确率。"""
    return public_evaluation_disclosure()


@router.get("/regulations")
async def regulations(query: str = "企业流动资金材料预审"):
    return search_regulations(query)
