from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from tests.api.helpers import create_experiment


def test_experiment_create_update_and_list(
    client: TestClient,
    user_id: str,
) -> None:
    create_response = client.post(
        "/v1/experiments",
        json={
            "user_id": user_id,
            "hypothesis": "更具体的标题提升收藏率",
            "variables": ["title", "opening"],
            "execution_cycle": "7d",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    experiment_id = created["id"]

    update_response = client.patch(
        f"/v1/experiments/{experiment_id}/result",
        json={
            "result": "收藏率提升 18%",
            "conclusion": "保留具体收益型标题",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "completed"

    list_response = client.get(f"/v1/experiments/users/{user_id}")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert any(item["id"] == experiment_id for item in listed)

    events_response = client.get(f"/v1/events/users/{user_id}")
    assert events_response.status_code == 200
    assert any(item["event_name"] == "experiment_created" for item in events_response.json())


def test_experiment_update_requires_non_empty_conclusion(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        experiment = create_experiment(db, user_id=user_id)

    response = client.patch(
        f"/v1/experiments/{experiment.id}/result",
        json={"result": "有结果", "conclusion": ""},
    )
    assert response.status_code == 422


def test_experiment_update_missing_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/v1/experiments/missing/result",
        json={"result": "r", "conclusion": "c"},
    )
    assert response.status_code == 404
