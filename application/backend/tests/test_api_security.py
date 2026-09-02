from fastapi.testclient import TestClient

from app.main import app


def test_business_routes_require_authentication():
    with TestClient(app) as client:
        assert client.get("/api/cases").status_code == 401
        assert client.post("/api/analyze", json={"case_description": "测试"}).status_code == 401
        assert client.post("/api/knowledge/reindex").status_code == 401
        assert client.post("/api/obsidian/sync").status_code == 401
        assert client.post("/api/contracts/requirements-preview", json={"requirements": "租房"}).status_code == 401


def test_health_is_not_false_ok_without_llm_key():
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["llm_configured"] is False
    assert body["status"] == "degraded"
