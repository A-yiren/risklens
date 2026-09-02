"""日志配置"""
import os
import sys
from loguru import logger
from app.config import settings


def _secure_log_opener(path: str, flags: int) -> int:
    """日志可能含运行诊断信息，创建时不授予其他本机用户读取权限。"""
    return os.open(path, flags, 0o640)


def setup_logging():
    """统一日志格式"""
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    # 文件日志
    log_file = settings.storage_root / "logs" / "app.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    if log_file.exists():
        log_file.chmod(0o640)
    logger.add(
        str(log_file),
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        opener=_secure_log_opener,
    )
    return logger


log = setup_logging()
