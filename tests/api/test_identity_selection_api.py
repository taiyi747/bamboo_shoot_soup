from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.models.identity_model import IdentityModel
from tests.api.helpers import create_identity_model


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
