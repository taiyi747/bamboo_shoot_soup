from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.services import launch_kit as launch_kit_service
from tests.api.helpers import (
    create_capability_profile,
    create_identity_model,
    create_launch_kit,
    create_onboarding_session,
    create_persona_constitution,
)


class _FakeLaunchKitLLMClient:
    def __init__(self, payload: dict) -> None:
        self.payload = copy.deepcopy(payload)
        self.calls: list[dict] = []

    def generate_json(self, *, operation: str, system_prompt: str, user_payload: dict) -> dict:
        self.calls.append(
            {
                "operation": operation,
                "system_prompt": system_prompt,
                "user_payload": copy.deepcopy(user_payload),
            }
        )
        return copy.deepcopy(self.payload)


def _valid_launch_kit_payload() -> dict:
    return {
        "sustainable_columns": ["col1", "col2", "col3"],
        "growth_experiment_suggestion": [
            {
                "name": "exp",
                "hypothesis": "hyp",
                "variables": ["v1"],
                "duration": "7d",
                "success_metric": "metric",
            }
        ],
        "days": [
            {
                "day_no": i,
                "theme": f"theme-{i}",
                "draft_or_outline": f"draft-{i}",
                "opening_text": f"opening-{i}",
            }
            for i in range(1, 8)
        ],
    }


def test_launchkit_read_endpoints(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    now = datetime.now(timezone.utc)
    with session_local() as db:
        first = create_launch_kit(
            db,
            user_id=user_id,
            created_at=now - timedelta(minutes=5),
        )
        second = create_launch_kit(
            db,
            user_id=user_id,
            created_at=now,
        )

    list_response = client.get(f"/v1/launch-kits/users/{user_id}")
    assert list_response.status_code == 200
    listed_ids = {item["id"] for item in list_response.json()}
    assert listed_ids == {first.id, second.id}

    latest_response = client.get(f"/v1/launch-kits/users/{user_id}/latest")
    assert latest_response.status_code == 200
    latest = latest_response.json()
    assert latest["id"] == second.id
    assert len(latest["days"]) == 7

    detail_response = client.get(f"/v1/launch-kits/{first.id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == first.id
    assert [day["day_no"] for day in detail["days"]] == [1, 2, 3, 4, 5, 6, 7]


def test_launchkit_latest_not_found_returns_404(client: TestClient, user_id: str) -> None:
    response = client.get(f"/v1/launch-kits/users/{user_id}/latest")
    assert response.status_code == 404


def test_launchkit_detail_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/v1/launch-kits/missing")
    assert response.status_code == 404


def test_launchkit_generate_backfills_resolved_identity_and_constitution(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
    monkeypatch,
) -> None:
    fake_client = _FakeLaunchKitLLMClient(_valid_launch_kit_payload())
    monkeypatch.setattr(launch_kit_service, "get_llm_client", lambda: fake_client)

    with session_local() as db:
        session = create_onboarding_session(db, user_id=user_id, status="completed")
        create_capability_profile(db, session_id=session.id, user_id=user_id, skill_stack=["python"])
        identity = create_identity_model(
            db,
            user_id=user_id,
            title="Launch Identity",
            session_id=session.id,
        )
        constitution = create_persona_constitution(
            db,
            user_id=user_id,
            identity_model_id=identity.id,
            version=1,
        )

    generate_response = client.post(
        "/v1/launch-kits/generate",
        json={"user_id": user_id},
    )
    assert generate_response.status_code == 200
    kit_id = generate_response.json()["id"]

    detail_response = client.get(f"/v1/launch-kits/{kit_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["identity_model_id"] == identity.id
    assert detail["constitution_id"] == constitution.id

    resolution_meta = fake_client.calls[0]["user_payload"]["context_bundle"]["resolution_meta"]
    assert resolution_meta["identity_model_source"] == "latest"
    assert resolution_meta["persona_constitution_source"] == "identity"
