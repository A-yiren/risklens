"""类案 + 合同审查 + 用户案件库 API"""
import asyncio
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel

from app.services.case_retrieval import case_retrieval
from app.services.contract_review import contract_reviewer
from app.services.contract_review_v2 import contract_reviewer_v2
from app.services.contract_template_matcher import match_contract_template
from app.config import settings
from app.storage.sqlite import db
from app.utils.logging import log
from app.api.deps import get_current_user, require_admin

router = APIRouter(
    prefix="/api",
    tags=["cases"],
    dependencies=[Depends(get_current_user)],
)


class CaseSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    cause: Optional[str] = None
    court_level: Optional[str] = None


class ContractReviewRequest(BaseModel):
    contract_text: str
    contract_type: str = "general"  # general/labor/sale/lease/service/finance
    user_role: str = "中立"  # 我方/对方/中立


class CreateCaseRequest(BaseModel):
    """创建/更新用户案件"""
    title: str
    case_no: Optional[str] = None
    client: Optional[str] = None
    case_type: Optional[str] = None  # 案件类型：金融借款/理财销售/保险理赔/...
    description: Optional[str] = None
    amount: Optional[float] = None
    court: Optional[str] = None
    status: str = "draft"  # draft/processing/done/closed
    metadata: Optional[Dict[str, Any]] = None


class UpdateCaseRequest(BaseModel):
    """更新用户案件"""
    title: Optional[str] = None
    case_no: Optional[str] = None
    client: Optional[str] = None
    case_type: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    court: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/cases")
async def list_cases(
    status: Optional[str] = Query(None, description="按状态过滤: draft/processing/done/closed"),
    search: Optional[str] = Query(None, description="按案件名称/案号/客户模糊搜索"),
    limit: int = Query(200, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    """列出所有用户案件（案件库页面用）"""
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    sql = "SELECT id, case_no, title, client, case_type, amount, court, status, description, created_at, updated_at, metadata FROM cases WHERE user_id = ?"
    params = [str(user["id"])]
    if status:
        sql += " AND status = ?"
        params.append(status)
    if search:
        sql += " AND (title LIKE ? OR case_no LIKE ? OR client LIKE ?)"
        kw = f"%{search}%"
        params.extend([kw, kw, kw])
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    rows = c.execute(sql, params).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        # metadata 是 JSON 字符串，前端需要 dict
        try:
            d["metadata"] = json.loads(d.get("metadata") or "{}")
        except Exception:
            d["metadata"] = {}
        out.append(d)
    return out


@router.post("/cases")
async def create_case(req: CreateCaseRequest, user: dict = Depends(get_current_user)):
    """创建用户案件（案件库）

    用于：
    - case-analysis.html 分析完案情后自动保存
    - case-list.html 手动创建空案件
    - 任何其他业务调用方
    """
    case_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    case_no = req.case_no or f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{case_id[:8]}"
    meta_json = json.dumps(req.metadata or {}, ensure_ascii=False)
    user_id = str(user["id"])

    conn = sqlite3.connect(db.db_path)
    try:
        conn.execute("""
            INSERT INTO cases (id, user_id, case_no, title, client, case_type, amount, court, status, description, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id, user_id, case_no, req.title, req.client or "", req.case_type or "",
            req.amount, req.court or "", req.status,
            req.description or "", now, now, meta_json,
        ))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        # 案号冲突：把自动案号加上随机后缀重试
        if "UNIQUE" in str(e) and "case_no" in str(e):
            case_no = f"{case_no}-{uuid.uuid4().hex[:6]}"
            conn = sqlite3.connect(db.db_path)
            conn.execute("""
                INSERT INTO cases (id, user_id, case_no, title, client, case_type, amount, court, status, description, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (case_id, user_id, case_no, req.title, req.client or "", req.case_type or "",
                  req.amount, req.court or "", req.status, req.description or "", now, now, meta_json))
            conn.commit()
        else:
            log.exception(f"创建案件失败: {e}")
            raise HTTPException(400, "创建案件失败")
    finally:
        conn.close()

    log.info(f"创建案件: {case_id} {case_no} {req.title[:30]}")
    return {
        "id": case_id,
        "case_no": case_no,
        "title": req.title,
        "client": req.client or "",
        "case_type": req.case_type or "",
        "status": req.status,
        "created_at": now,
        "updated_at": now,
        "metadata": req.metadata or {},
    }


@router.get("/cases/{case_id}")
async def get_case(case_id: str, user: dict = Depends(get_current_user)):
    """获取单个案件详情"""
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, case_no, title, client, case_type, amount, court, status, description, created_at, updated_at, metadata FROM cases WHERE id = ? AND user_id = ?",
        (case_id, str(user["id"])),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, f"案件不存在: {case_id}")
    d = dict(row)
    try:
        d["metadata"] = json.loads(d.get("metadata") or "{}")
    except Exception:
        d["metadata"] = {}
    return d


@router.put("/cases/{case_id}")
async def update_case(
    case_id: str,
    req: UpdateCaseRequest,
    user: dict = Depends(get_current_user),
):
    """更新案件"""
    conn = sqlite3.connect(db.db_path)
    try:
        # 检查存在
        user_id = str(user["id"])
        row = conn.execute(
            "SELECT id FROM cases WHERE id = ? AND user_id = ?",
            (case_id, user_id),
        ).fetchone()
        if not row:
            raise HTTPException(404, f"案件不存在: {case_id}")

        # 动态构建更新 SQL
        fields = []
        params = []
        for field in ["title", "case_no", "client", "case_type", "description", "amount", "court", "status"]:
            v = getattr(req, field)
            if v is not None:
                fields.append(f"{field} = ?")
                params.append(v)
        if req.metadata is not None:
            fields.append("metadata = ?")
            params.append(json.dumps(req.metadata, ensure_ascii=False))
        if not fields:
            raise HTTPException(400, "无更新字段")
        fields.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.extend([case_id, user_id])
        conn.execute(
            f"UPDATE cases SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()
    return {"id": case_id, "ok": True}


@router.delete("/cases/{case_id}")
async def delete_case(case_id: str, user: dict = Depends(get_current_user)):
    """删除案件（同时删除关联的 analyses）"""
    conn = sqlite3.connect(db.db_path)
    try:
        # 删 analyses
        user_id = str(user["id"])
        conn.execute(
            "DELETE FROM analyses WHERE case_id = ? AND user_id = ?",
            (case_id, user_id),
        )
        # 删 case
        cur = conn.execute(
            "DELETE FROM cases WHERE id = ? AND user_id = ?",
            (case_id, user_id),
        )
        conn.commit()
        deleted = cur.rowcount > 0
    finally:
        conn.close()
    if not deleted:
        raise HTTPException(404, f"案件不存在: {case_id}")
    return {"id": case_id, "deleted": True}


@router.post("/cases/search")
async def search_cases(req: CaseSearchRequest):
    """类案检索"""
    try:
        results = await case_retrieval.search_similar_cases(
            query=req.query,
            top_k=req.top_k,
            cause=req.cause,
            court_level=req.court_level,
        )
        return {
            "query": req.query,
            "total": len(results),
            "results": [r.model_dump() for r in results],
        }
    except Exception as e:
        log.exception(f"类案检索失败: {e}")
        raise HTTPException(503, "类案检索服务暂不可用")


@router.post("/contract/review")
async def review_contract(req: ContractReviewRequest, user: dict = Depends(get_current_user)):
    """合同审查：先校验所选类型与示范文本结构是否错配，再运行规则。"""
    if not req.contract_text.strip():
        raise HTTPException(400, "合同内容不能为空")
    if len(req.contract_text) > 50000:
        raise HTTPException(400, "合同内容过长（>50000 字符）")
    try:
        template_match = match_contract_template(req.contract_text, req.contract_type)
        if template_match["review_action"] == "block":
            raise HTTPException(
                422,
                {"message": template_match["message"], "template_match": template_match},
            )
        review_kwargs = {
            "contract_text": req.contract_text,
            "contract_type": req.contract_type,
            "user_role": req.user_role,
            "user_id": str(user["id"]),
        }
        if settings.contract_review_v2_enabled:
            result = await contract_reviewer_v2.review(**review_kwargs)
        elif settings.contract_review_v2_shadow_enabled:
            # 影子模式会增加延迟，必须显式开启。V2 失败不影响用户收到 V1。
            v1_task = contract_reviewer.review(**review_kwargs)
            v2_task = contract_reviewer_v2.review(**review_kwargs)
            result, shadow_result = await asyncio.gather(
                v1_task, v2_task, return_exceptions=True
            )
            if isinstance(result, Exception):
                raise result
            if isinstance(shadow_result, Exception):
                log.warning(f"合同审查 V2 影子运行失败（V1 正常返回）: {shadow_result}")
            else:
                log.info(
                    "[合同审查影子比较] V1风险={} V2规则风险={} V1等级={} V2等级={}",
                    len(result.get("risks", [])),
                    len(shadow_result.get("risks", [])),
                    result.get("risk_level"),
                    shadow_result.get("risk_level"),
                )
        else:
            result = await contract_reviewer.review(**review_kwargs)
        result.setdefault(
            "review_engine",
            "contract-review-v2" if settings.contract_review_v2_enabled else "contract-review-v1",
        )
        result["template_match"] = template_match
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"合同审查失败: {e}")
        raise HTTPException(503, "合同审查服务暂不可用")


@router.post("/contract/review-v2-preview")
async def preview_contract_review_v2(
    req: ContractReviewRequest,
    admin: dict = Depends(require_admin),
):
    """管理员受控预览；生产环境需显式打开预览开关。"""
    if not settings.contract_review_v2_preview_enabled:
        raise HTTPException(404, "合同审查 V2 预览未启用")
    if not req.contract_text.strip():
        raise HTTPException(400, "合同内容不能为空")
    if len(req.contract_text) > 50000:
        raise HTTPException(400, "合同内容过长（>50000 字符）")
    try:
        template_match = match_contract_template(req.contract_text, req.contract_type)
        if template_match["review_action"] == "block":
            raise HTTPException(
                422,
                {"message": template_match["message"], "template_match": template_match},
            )
        result = await contract_reviewer_v2.review(
            contract_text=req.contract_text,
            contract_type=req.contract_type,
            user_role=req.user_role,
            user_id=str(admin["id"]),
        )
        result["template_match"] = template_match
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"合同审查 V2 预览失败: {e}")
        raise HTTPException(503, "合同审查 V2 暂不可用")
