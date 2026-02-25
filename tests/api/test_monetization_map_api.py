from __future__ import annotations

import copy

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.services.llm_replay import ReplayGenerationResult
from tests.api.helpers import create_monetization_map


_VALID_PAYLOAD = {
    "primary_path": "咨询服务 -> 小班营",
    "backup_path": "模板产品",
    "weeks": [
        {
            "week_no": i,
            "goal": f"goal-{i}",
            "task": f"task-{i}",
            "deliverable": f"deliverable-{i}",
            "validation_metric": f"metric-{i}",
        }
        for i in range(1, 13)
    ],
}


def test_monetization_map_generate_and_read(
    client: TestClient,
    user_id: str,
    monkeypatch,
) -> None:
    from app.services import monetization_map as monetization_map_service

    def _fake_generate_json_with_replay(*_args, **_kwargs):
        return ReplayGenerationResult(
            payload=copy.deepcopy(_VALID_PAYLOAD),
            degraded=False,
            degrade_reason=None,
        )

    monkeypatch.setattr(
        monetization_map_service,
        "generate_json_with_replay",
        _fake_generate_json_with_replay,
    )

    response = client.post(
        "/v1/monetization-maps/generate",
        json={"user_id": user_id},
    )
    assert response.status_code == 200
    generated = response.json()
    assert generated["id"]

    detail_response = client.get(f"/v1/monetization-maps/{generated['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["user_id"] == user_id

    list_response = client.get(f"/v1/monetization-maps/users/{user_id}")
    assert list_response.status_code == 200
    assert any(item["id"] == generated["id"] for item in list_response.json())

    events_response = client.get(f"/v1/events/users/{user_id}")
    assert events_response.status_code == 200
    assert any(item["event_name"] == "monetization_plan_started" for item in events_response.json())


def test_monetization_map_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/v1/monetization-maps/missing")
    assert response.status_code == 404


def test_monetization_map_read_seeded_data(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        monetization_map = create_monetization_map(db, user_id=user_id)

    response = client.get(f"/v1/monetization-maps/{monetization_map.id}")
    assert response.status_code == 200
    assert response.json()["id"] == monetization_map.id
