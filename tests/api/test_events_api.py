from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from tests.api.helpers import create_event_log


def test_events_create_and_query_endpoints(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        create_event_log(db, user_id=user_id, event_name="onboarding_started", stage="MVP")

    create_response = client.post(
        "/v1/events",
        json={
            "user_id": user_id,
            "event_name": "experiment_created",
            "stage": "V1",
            "payload": {"hypothesis": "new CTA works"},
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["event_name"] == "experiment_created"

    user_events_response = client.get(f"/v1/events/users/{user_id}", params={"limit": 10})
    assert user_events_response.status_code == 200
    user_events = user_events_response.json()
    assert len(user_events) >= 2
    assert any(event["event_name"] == "experiment_created" for event in user_events)

    named_response = client.get("/v1/events/name/experiment_created", params={"limit": 10})
    assert named_response.status_code == 200
    named_events = named_response.json()
    assert named_events
    assert all(item["event_name"] == "experiment_created" for item in named_events)
    assert json.loads(named_events[0]["payload_json"])["hypothesis"] == "new CTA works"

    recent_response = client.get("/v1/events/recent", params={"limit": 10})
    assert recent_response.status_code == 200
    recent_events = recent_response.json()
    assert any(event["id"] == created["id"] for event in recent_events)


def test_create_event_invalid_event_name_returns_400(client: TestClient, user_id: str) -> None:
    response = client.post(
        "/v1/events",
        json={
            "user_id": user_id,
            "event_name": "invalid_event",
            "stage": "MVP",
            "payload": {},
        },
    )
    assert response.status_code == 400


def test_create_event_invalid_stage_returns_422(client: TestClient, user_id: str) -> None:
    response = client.post(
        "/v1/events",
        json={
            "user_id": user_id,
            "event_name": "content_published",
            "stage": "INVALID",
            "payload": {},
        },
    )
    assert response.status_code == 422


def test_events_limit_query_validation_returns_422(client: TestClient, user_id: str) -> None:
    user_response = client.get(f"/v1/events/users/{user_id}", params={"limit": "not-an-int"})
    name_response = client.get("/v1/events/name/content_published", params={"limit": "bad"})
    recent_response = client.get("/v1/events/recent", params={"limit": "oops"})

    assert user_response.status_code == 422
    assert name_response.status_code == 422
    assert recent_response.status_code == 422
