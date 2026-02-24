from fastapi.testclient import TestClient

import app.main as main_module


def test_health_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "ensure_llm_ready", lambda: None)
    client = TestClient(main_module.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db_ok": True}
