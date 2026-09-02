import builtins

import pytest

from app.config import settings
from app.services.embedding import EmbeddingService
from app.storage.qdrant_client import QdrantVectorStore


def test_embedding_dependency_failure_does_not_return_fake_vectors(monkeypatch):
    service = EmbeddingService()
    service.model = None
    service._last_error = None
    monkeypatch.setattr(settings, "testing", False)
    original_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise ImportError("blocked by test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    with pytest.raises(RuntimeError, match="拒绝生成伪向量"):
        service.embed(["测试"])


def test_qdrant_memory_mode_is_test_only(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_mode", "memory")
    monkeypatch.setattr(settings, "testing", False)
    store = QdrantVectorStore()
    with pytest.raises(RuntimeError, match="拒绝降级"):
        _ = store.client

