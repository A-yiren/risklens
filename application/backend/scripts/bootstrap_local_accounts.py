"""增量初始化本地管理员和 Demo 账号，不删除任何现有业务数据。"""
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings
from app.utils.security import hash_password


def _required_env(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"缺少环境变量 {name}")
    return value


def _upsert_account(
    conn: sqlite3.Connection,
    username: str,
    password: str,
    role: str,
    display_name: str,
) -> str:
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    now = datetime.now(timezone.utc).isoformat()
    password_hash = hash_password(password)
    if row:
        user_id = str(row[0])
        conn.execute(
            """UPDATE users
               SET password_hash = ?, display_name = ?, role = ?
               WHERE id = ?""",
            (password_hash, display_name, role, user_id),
        )
    else:
        user_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO users
               (id, username, password_hash, display_name, role, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, '{}')""",
            (user_id, username, password_hash, display_name, role, now),
        )
    return user_id


def main() -> None:
    if settings.auth_backend.lower() != "local":
        raise RuntimeError("此脚本只允许 AUTH_BACKEND=local")

    admin_username = os.getenv("RISK_ADMIN_USERNAME", "risklens_admin")
    demo_username = os.getenv("RISK_DEMO_USERNAME", "demo_risklens")
    admin_password = _required_env("RISK_ADMIN_PASSWORD")
    demo_password = _required_env("RISK_DEMO_PASSWORD")

    conn = sqlite3.connect(str(settings.sqlite_path))
    try:
        conn.execute("BEGIN IMMEDIATE")
        admin_id = _upsert_account(
            conn, admin_username, admin_password, "admin", "RiskLens 管理员"
        )
        demo_id = _upsert_account(
            conn, demo_username, demo_password, "user", "RiskLens Demo"
        )

        # 旧数据只补归属，不删除。Demo 账号用于承接原先未归属的演示案件。
        migrated_cases = conn.execute(
            "UPDATE cases SET user_id = ? WHERE user_id IS NULL OR user_id = ''",
            (demo_id,),
        ).rowcount
        migrated_analyses = conn.execute(
            """UPDATE analyses
               SET user_id = COALESCE(
                   (SELECT cases.user_id FROM cases WHERE cases.id = analyses.case_id),
                   ?
               )
               WHERE user_id IS NULL OR user_id = ''""",
            (demo_id,),
        ).rowcount
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(json.dumps({
        "admin_username": admin_username,
        "admin_id": admin_id,
        "demo_username": demo_username,
        "demo_id": demo_id,
        "migrated_cases": migrated_cases,
        "migrated_analyses": migrated_analyses,
        "deleted_records": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
