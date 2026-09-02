from unittest.mock import Mock

import pytest

from app.services.retrieval import RetrievalService
import app.services.retrieval as retrieval_module


class EmptyEmbedding:
    def embed(self, _queries):
        return []


@pytest.mark.asyncio
async def test_retrieval_log_never_contains_query_or_filter_values(monkeypatch):
    logger = Mock()
    monkeypatch.setattr(retrieval_module, "log", logger)
    service = RetrievalService()
    service.embedding = EmptyEmbedding()

    query = "张三身份证110101199001011234的离婚案情"
    await service.search(query=query, filters={"_access_user_id": "user-987"})

    message = logger.info.call_args.args[0]
    assert query not in message
    assert "user-987" not in message
    assert "query_chars=" in message
    assert "filters_present=True" in message
