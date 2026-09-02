"""知识库 API"""
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.models import DocumentInfo, DocumentStatus, SourceType, SearchResult
from app.services.ingestion import ingestion_service
from app.services.retrieval import retrieval_service
from app.storage.sqlite import db
from app.utils.logging import log
from app.api.deps import get_current_user, require_admin


router = APIRouter(
    prefix="/api/knowledge",
    tags=["knowledge"],
    dependencies=[Depends(get_current_user)],
)


class RenameDocumentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=180)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form(default="upload"),
    law_name: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default=None),
    user: dict = Depends(get_current_user),
):
    """上传文档入库

    Args:
        file: 文件
        source: 管理员可指定来源；普通用户固定为 upload
        law_name: 法律名称（可选，覆盖自动识别）
        tags: 标签，逗号分隔
    """
    # 校验
    if not file.filename:
        raise HTTPException(400, "文件名为空")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".pdf", ".docx", ".md", ".markdown", ".txt"):
        raise HTTPException(400, f"不支持的文件类型: {ext}")

    # 保存到临时位置
    file_id = uuid.uuid4().hex[:12]
    save_name = f"{file_id}_{file.filename}"
    save_path = settings.upload_dir / save_name
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.parent.chmod(0o750)

    try:
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        written = 0
        with save_path.open("wb") as f:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(
                        413,
                        f"文件超过 {settings.max_file_size_mb} MB 限制",
                    )
                f.write(chunk)
        # 上传文档可能包含案情或个人信息，不应默认对服务器其他账号可读。
        save_path.chmod(0o640)
    except HTTPException:
        save_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        save_path.unlink(missing_ok=True)
        log.exception(f"保存文件失败: {e}")
        raise HTTPException(500, "保存文件失败")

    # 入库
    extra = {}
    if law_name:
        extra["law_name"] = law_name
    if tags:
        extra["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

    is_admin = user.get("role") in {"admin", "superadmin"}
    if is_admin:
        try:
            source_enum = SourceType(source)
        except ValueError:
            source_enum = SourceType.UPLOAD
    else:
        source_enum = SourceType.UPLOAD
    visibility = "shared" if is_admin else "private"
    owner_user_id = None if is_admin else str(user["id"])

    try:
        doc = await ingestion_service.ingest_file(
            save_path,
            source=source_enum,
            extra_metadata=extra,
            owner_user_id=owner_user_id,
            visibility=visibility,
        )
        return {
            "doc_id": doc.id,
            "name": doc.name,
            "chunks_count": doc.chunks_count,
            "status": doc.status.value,
            "law_name": doc.metadata.get("law_name"),
            "visibility": doc.visibility,
        }
    except Exception as e:
        save_path.unlink(missing_ok=True)
        log.exception(f"入库失败: {e}")
        raise HTTPException(500, "文档入库失败")


@router.get("/documents")
async def list_documents(
    source: Optional[str] = None,
    limit: int = Query(100, le=500),
    user: dict = Depends(get_current_user),
):
    """列出文档"""
    source_enum = None
    if source:
        try:
            source_enum = SourceType(source)
        except ValueError:
            pass
    docs = db.list_documents(
        source=source_enum,
        limit=limit,
        user_id=str(user["id"]),
        include_all=False,
    )
    return [
        {
            "id": d.id,
            "name": d.name,
            "source": d.source.value,
            "size": d.size,
            "chunks_count": d.chunks_count,
            "status": d.status.value,
            "uploaded_at": d.uploaded_at.isoformat(),
            "metadata": d.metadata,
            # Phase 2: 顶层 source_url 方便 UI 直接显示
            "source_url": (d.metadata or {}).get("source_url"),
            "publisher": (d.metadata or {}).get("publisher"),
            "law_status": (d.metadata or {}).get("law_status"),
            "decree": (d.metadata or {}).get("decree"),
            "effective_date": (d.metadata or {}).get("effective_date"),
            "has_error": bool(d.error),
            "visibility": d.visibility,
            "is_owner": d.owner_user_id == str(user["id"]),
        }
        for d in docs
    ]


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    preview: bool = Query(False, description="是否返回文件前 500 字符预览"),
    preview_chars: int = Query(500, ge=50, le=5000, description="预览字符数"),
    user: dict = Depends(get_current_user),
):
    """获取文档详情

    preview=true 时返回文件前 preview_chars 字符的纯文本预览，
    用于知识库页快速查看新增法律内容。
    """
    doc = db.get_document(
        doc_id,
        user_id=str(user["id"]),
        include_all=False,
    )
    if not doc:
        raise HTTPException(404, "文档不存在")

    result = {
        "id": doc.id,
        "name": doc.name,
        "source": doc.source.value,
        "size": doc.size,
        "chunks_count": doc.chunks_count,
        "status": doc.status.value,
        "uploaded_at": doc.uploaded_at.isoformat(),
        "metadata": doc.metadata,
        # Phase 2: 顶层 source_url 方便 UI 直接显示
        "source_url": (doc.metadata or {}).get("source_url"),
        "publisher": (doc.metadata or {}).get("publisher"),
        "law_status": (doc.metadata or {}).get("law_status"),
        "decree": (doc.metadata or {}).get("decree"),
        "effective_date": (doc.metadata or {}).get("effective_date"),
        "has_error": bool(doc.error),
        "visibility": doc.visibility,
        "is_owner": doc.owner_user_id == str(user["id"]),
    }

    if preview and doc.file_path:
        try:
            p = Path(doc.file_path)
            if p.exists() and p.is_file():
                # 文本类文件直接读前 N 字符
                if p.suffix.lower() in (".md", ".markdown", ".txt"):
                    text = p.read_text(encoding="utf-8", errors="ignore")
                elif p.suffix.lower() == ".docx":
                    # docx 简单提取前几段
                    try:
                        from docx import Document
                        d = Document(str(p))
                        text = "\n\n".join(par.text for par in d.paragraphs if par.text.strip())
                    except Exception:
                        text = ""
                elif p.suffix.lower() == ".pdf":
                    text = "(PDF 文件暂不支持在线预览，请下载查看)"
                else:
                    text = p.read_text(encoding="utf-8", errors="ignore")

                truncated = text[:preview_chars]
                result["preview"] = {
                    "text": truncated,
                    "total_chars": len(text),
                    "is_truncated": len(text) > preview_chars,
                    "truncated_at": min(preview_chars, len(text)),
                }
            else:
                result["preview"] = {"text": "(文件不存在或已被移动)", "total_chars": 0, "is_truncated": False, "truncated_at": 0}
        except Exception as e:
            log.exception(f"读取预览失败: {e}")
            result["preview"] = {"text": "(读取失败)", "total_chars": 0, "is_truncated": False, "truncated_at": 0}
    elif preview and doc_id.startswith("case-"):
        # 案件类（.case 文件）: 没有 file_path，从 Qdrant legal_cases 集合读 chunks
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            from app.storage.qdrant_client import vector_store
            points, _ = vector_store.client.scroll(
                collection_name="legal_cases",
                scroll_filter=Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]),
                limit=20,
                with_payload=True,
                with_vectors=False,
            )
            # 按 chunk_index 排序
            points.sort(key=lambda p: p.payload.get("chunk_index", 0))
            # 拼接 facts / reasoning / judgment 三段
            parts = []
            for p in points:
                chunk_type = p.payload.get("chunk_type", "")
                text = p.payload.get("text", "").strip()
                if text:
                    label = {"facts": "【事实】", "reasoning": "【理由】", "judgment": "【判决】"}.get(chunk_type, f"【{chunk_type}】")
                    parts.append(f"{label}\n{text}")
            text = "\n\n".join(parts) if parts else "(案件暂无内容)"
            truncated = text[:preview_chars]
            result["preview"] = {
                "text": truncated,
                "total_chars": len(text),
                "is_truncated": len(text) > preview_chars,
                "truncated_at": min(preview_chars, len(text)),
            }
        except Exception as e:
            log.exception(f"读取案件预览失败: {e}")
            result["preview"] = {"text": "(读取失败)", "total_chars": 0, "is_truncated": False, "truncated_at": 0}

    return result


@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str, user: dict = Depends(get_current_user)):
    """下载自己上传的原始文件；共享法规仅提供官方来源链接。"""
    doc = db.get_document(doc_id, user_id=str(user["id"]), include_all=False)
    if not doc:
        raise HTTPException(404, "文档不存在")
    if doc.visibility != "private" or doc.owner_user_id != str(user["id"]):
        raise HTTPException(403, "共享知识库文档不能在此下载")
    file_path = Path(doc.file_path or "")
    if not file_path.is_file():
        raise HTTPException(404, "原始文件不可用")
    return FileResponse(file_path, filename=doc.name)


@router.patch("/documents/{doc_id}")
async def rename_document(
    doc_id: str,
    request: RenameDocumentRequest,
    user: dict = Depends(get_current_user),
):
    """重命名自己的私有文档，不改变索引内容。"""
    renamed = db.rename_document(doc_id, request.name.strip(), str(user["id"]))
    if not renamed:
        raise HTTPException(404, "文档不存在或无权重命名")
    return {"id": doc_id, "name": request.name.strip(), "ok": True}


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    """仅允许用户删除自己的私有文档；共享知识库保持只增不删。"""
    doc = db.get_document(doc_id, user_id=str(user["id"]), include_all=False)
    if not doc:
        raise HTTPException(404, "文档不存在")
    if doc.visibility == "shared":
        raise HTTPException(409, "共享知识库为只增不删，拒绝删除")
    if doc.owner_user_id != str(user["id"]):
        raise HTTPException(404, "文档不存在")
    ok = ingestion_service.delete_document(
        doc_id,
        user_id=str(user["id"]),
        include_all=False,
    )
    if not ok:
        raise HTTPException(404, "文档不存在或删除失败")
    return {"status": "deleted", "doc_id": doc_id}


@router.post("/search")
async def search_knowledge(
    query: str,
    top_k: int = Query(5, ge=1, le=50),
    law_name: Optional[str] = None,
    source: Optional[str] = None,
    use_rerank: bool = True,
    user: dict = Depends(get_current_user),
):
    """知识库检索

    Args:
        query: 查询文本
        top_k: 返回数量
        law_name: 按法律名过滤
        source: 按来源过滤
        use_rerank: 是否使用重排序
    """
    filters = {}
    if law_name:
        filters["law_name"] = law_name
    if source:
        filters["source"] = source
    filters["_access_user_id"] = str(user["id"])

    results = await retrieval_service.search(
        query=query,
        top_k=top_k,
        filters=filters if filters else None,
        use_rerank=use_rerank,
    )

    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "chunk_id": r.chunk_id,
                "text": r.text,
                "score": r.score,
                "law_name": r.law_name,
                "article_no": r.article_no,
                "citation": r.citation,
                "category": r.category,  # 知识库分类: law (法规) / case (案例)
                "metadata": r.metadata,
                "doc_id": (r.metadata or {}).get("doc_id"),
            }
            for r in results
        ]
    }


@router.post("/reindex")
async def reindex_all(_admin: dict = Depends(require_admin)):
    """重建索引（重新生成所有向量）

    警告：会清空 Qdrant collection 并重建
    """
    raise HTTPException(409, "共享知识库已启用只增不删策略，破坏性重建接口已禁用")
