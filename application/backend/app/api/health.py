"""健康检查"""
from fastapi import APIRouter
from app.config import settings
from app.storage.sqlite import db
from app.storage.qdrant_client import vector_store
from app.services.embedding import embedding_service


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    """健康检查"""
    qdrant_status = "error"
    vector_count = 0
    try:
        # 健康接口无需登录，只公开共享/旧版公共向量数量，不泄露私有上传的存在。
        vector_count = vector_store.count(filters={"_access_user_id": "__shared_health__"})
        qdrant_status = "ok"
    except Exception:
        qdrant_status = "error"

    doc_count = len(db.list_documents(limit=10000))

    llm_configured = bool(settings.llm_api_key.strip())
    embedding_state = embedding_service.state
    embedding_dependency_available = embedding_service.dependency_available
    jwt_secure = settings.jwt_secret != "change-me" and len(settings.jwt_secret) >= 32
    degraded = (
        qdrant_status != "ok"
        or embedding_state == "error"
        or not embedding_dependency_available
        or not llm_configured
        or not jwt_secure
    )

    return {
        "status": "degraded" if degraded else "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "qdrant": qdrant_status,
        "qdrant_mode": vector_store.mode if vector_store.mode != "unknown" else settings.qdrant_mode,
        "vector_count": vector_count,
        "doc_count": doc_count,
        "embedding_model": settings.embedding_model,
        "embedding_state": embedding_state,
        "embedding_dependency_available": embedding_dependency_available,
        "llm_model": settings.llm_model,
        "llm_provider": settings.llm_provider,
        "llm_configured": llm_configured,
        "jwt_secure": jwt_secure,
    }


@router.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
