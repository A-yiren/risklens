from app.models import DocumentInfo, SourceType
from app.storage.qdrant_client import QdrantVectorStore
from app.storage.sqlite import SQLiteStore


def test_shared_and_private_documents_are_scoped_without_deleting_existing(tmp_path):
    store = SQLiteStore(tmp_path / "visibility.db")
    store.upsert_document(DocumentInfo(id="shared", name="法规.md", source=SourceType.SEED))
    store.upsert_document(DocumentInfo(
        id="private-a",
        name="甲的材料.md",
        source=SourceType.UPLOAD,
        owner_user_id="user-a",
        visibility="private",
    ))
    store.upsert_document(DocumentInfo(
        id="private-b",
        name="乙的材料.md",
        source=SourceType.UPLOAD,
        owner_user_id="user-b",
        visibility="private",
    ))

    assert {doc.id for doc in store.list_documents(user_id="user-a")} == {"shared", "private-a"}
    assert {doc.id for doc in store.list_documents(user_id="user-b")} == {"shared", "private-b"}
    assert store.get_document("private-a", user_id="user-b") is None
    assert store.delete_document("shared", user_id="user-a") is False
    assert store.delete_document("private-a", user_id="user-a") is True
    assert store.get_document("shared", user_id="user-a") is not None


def test_qdrant_access_filter_contains_shared_legacy_and_owner_paths():
    store = QdrantVectorStore()
    query_filter = store._build_filter({"law_name": "民法典", "_access_user_id": "user-a"})

    assert len(query_filter.must) == 1
    assert len(query_filter.should) == 3
    rendered = query_filter.model_dump()
    assert "user-a" in str(rendered)
    assert "shared" in str(rendered)
    assert "visibility" in str(rendered)
