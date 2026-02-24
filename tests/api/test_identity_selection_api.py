from __future__ import annotations

import copy
import threading

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.models.identity_model import IdentityModel
from app.services import identity_model as identity_service
from tests.api.helpers import create_identity_model


class _FakeLLMClient:
    def __init__(self, payload_by_operation: dict[str, list[dict]]) -> None:
        self._payload_by_operation = copy.deepcopy(payload_by_operation)
        self._lock = threading.Lock()

    def generate_json(self, *, operation: str, system_prompt: str, user_payload: dict) -> dict:
        with self._lock:
            operation_payload = self._payload_by_operation[operation]
            if not operation_payload:
                raise AssertionError(f"no payload left for operation={operation}")
            return copy.deepcopy(operation_payload.pop(0))


def _identity_model_payload(prefix: str, label: str) -> dict:
    return {
        "models": [
            {
                "title": f"{prefix} {label}",
                "target_audience_pain": f"Pain {label}",
                "content_pillars": ["P1", "P2", "P3"],
                "tone_keywords": ["k1", "k2"],
                "tone_examples": ["e1", "e2", "e3", "e4", "e5"],
                "long_term_views": ["v1", "v2", "v3", "v4", "v5"],
                "differentiation": f"{prefix} Diff {label}",
                "growth_path_0_3m": f"Plan {label}1",
                "growth_path_3_12m": f"Plan {label}2",
                "monetization_validation_order": ["m1"],
                "risk_boundary": ["r1"],
            }
        ]
    }


def test_identity_read_endpoints_return_seeded_models(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        first = create_identity_model(db, user_id=user_id, title="Identity A")
        second = create_identity_model(db, user_id=user_id, title="Identity B")

    list_response = client.get(f"/v1/identity-models/users/{user_id}")
    assert list_response.status_code == 200
    returned_ids = {item["id"] for item in list_response.json()}
    assert returned_ids == {first.id, second.id}

    detail_response = client.get(f"/v1/identity-models/{first.id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Identity A"


def test_get_identity_model_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/v1/identity-models/missing-model")
    assert response.status_code == 404


def test_get_user_identity_models_returns_latest_generated_batch_only(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
    monkeypatch,
) -> None:
    fake_client = _FakeLLMClient(
        {
            "generate_identity_models": [
                _identity_model_payload("Batch1", "A"),
                _identity_model_payload("Batch1", "B"),
                _identity_model_payload("Batch1", "C"),
                _identity_model_payload("Batch2", "A"),
                _identity_model_payload("Batch2", "B"),
                _identity_model_payload("Batch2", "C"),
            ]
        }
    )
    monkeypatch.setattr(identity_service, "get_llm_client", lambda: fake_client)

    first_generate = client.post(
        "/v1/identity-models/generate",
        json={
            "user_id": user_id,
            "session_id": None,
            "capability_profile": {"skill_stack": ["python"]},
            "count": 3,
        },
    )
    assert first_generate.status_code == 200
    first_ids = {item["id"] for item in first_generate.json()}

    second_generate = client.post(
        "/v1/identity-models/generate",
        json={
            "user_id": user_id,
            "session_id": None,
            "capability_profile": {"skill_stack": ["python"]},
            "count": 3,
        },
    )
    assert second_generate.status_code == 200
    second_ids = {item["id"] for item in second_generate.json()}

    list_response = client.get(f"/v1/identity-models/users/{user_id}")
    assert list_response.status_code == 200
    listed_ids = {item["id"] for item in list_response.json()}
    assert listed_ids == second_ids
    assert listed_ids.isdisjoint(first_ids)

    with session_local() as db:
        db_models = db.query(IdentityModel).filter(IdentityModel.user_id == user_id).all()
    assert {model.id for model in db_models} == second_ids


def test_select_identity_updates_flags_and_logs_event(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        primary = create_identity_model(db, user_id=user_id, title="Primary")
        backup = create_identity_model(db, user_id=user_id, title="Backup")

    select_response = client.post(
        "/v1/identity-selections",
        json={
            "user_id": user_id,
            "primary_identity_id": primary.id,
            "backup_identity_id": backup.id,
        },
    )
    assert select_response.status_code == 200

    current_response = client.get(f"/v1/identity-selections/users/{user_id}")
    assert current_response.status_code == 200
    current = current_response.json()
    assert current["primary_identity_id"] == primary.id
    assert current["backup_identity_id"] == backup.id

    with session_local() as db:
        refreshed_primary = db.query(IdentityModel).filter(IdentityModel.id == primary.id).first()
        refreshed_backup = db.query(IdentityModel).filter(IdentityModel.id == backup.id).first()
        assert refreshed_primary is not None
        assert refreshed_backup is not None
        assert refreshed_primary.is_primary is True
        assert refreshed_backup.is_backup is True

    events_response = client.get(f"/v1/events/users/{user_id}", params={"limit": 20})
    assert events_response.status_code == 200
    identity_selected_events = [
        event for event in events_response.json() if event["event_name"] == "identity_selected"
    ]
    assert identity_selected_events
    assert identity_selected_events[0]["identity_model_id"] == primary.id


def test_select_identity_returns_400_when_identity_missing(client: TestClient, user_id: str) -> None:
    response = client.post(
        "/v1/identity-selections",
        json={
            "user_id": user_id,
            "primary_identity_id": "missing",
            "backup_identity_id": None,
        },
    )
    assert response.status_code == 400


def test_select_identity_returns_422_for_invalid_payload(
    client: TestClient,
    user_id: str,
) -> None:
    same_ids_response = client.post(
        "/v1/identity-selections",
        json={
            "user_id": user_id,
            "primary_identity_id": "same-id",
            "backup_identity_id": "same-id",
        },
    )
    assert same_ids_response.status_code == 422

    missing_field_response = client.post("/v1/identity-selections", json={"user_id": user_id})
    assert missing_field_response.status_code == 422


def test_get_identity_selection_not_found_returns_404(client: TestClient, user_id: str) -> None:
    response = client.get(f"/v1/identity-selections/users/{user_id}")
    assert response.status_code == 404
