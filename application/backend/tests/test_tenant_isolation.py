from datetime import datetime

from app.models import CaseInfo
from app.storage.sqlite import SQLiteStore


def _case(case_id: str, user_id: str) -> CaseInfo:
    now = datetime.now()
    return CaseInfo(
        id=case_id,
        user_id=user_id,
        case_no=f"NO-{case_id}",
        title=f"case-{case_id}",
        created_at=now,
        updated_at=now,
    )


def test_cases_and_analyses_are_scoped_by_user(tmp_path):
    store = SQLiteStore(tmp_path / "tenant.db")
    store.upsert_case(_case("case-a", "user-a"))
    store.upsert_case(_case("case-b", "user-b"))
    store.save_analysis("ana-a", "case-a", "user-a", {"ok": True})

    assert store.get_case("case-a", "user-a") is not None
    assert store.get_case("case-a", "user-b") is None
    assert [case.id for case in store.list_cases(user_id="user-a")] == ["case-a"]
    assert store.get_analysis("ana-a", "user-b") is None
    assert store.delete_case("case-a", "user-b") is False
    assert store.get_case("case-a", "user-a") is not None

