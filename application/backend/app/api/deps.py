"""FastAPI 公共依赖"""
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.aipath_auth import aipath_auth
from app.utils.security import decode_token

security = HTTPBearer(auto_error=False)


def _resolve_user(payload: dict) -> Optional[dict]:
    """从 JWT payload 解析用户信息"""
    user_id = payload.get("sub")
    if not user_id:
        return None
    # aipath 的 id 是整数，token.sub 是字符串
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        uid = user_id
    return aipath_auth.get_user_by_id(uid)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """从 Authorization: Bearer <jwt> 解析当前用户（从 aipath 库）"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = _resolve_user(payload)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已停用")
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """可选登录 — 没 token 返回 None 而非 401"""
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return _resolve_user(payload)
    except Exception:
        return None


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """仅允许管理员执行知识库与本地集成等高风险操作。"""
    if user.get("role") not in {"admin", "superadmin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user
