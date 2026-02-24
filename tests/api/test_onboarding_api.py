from __future__ import annotations

from fastapi.testclient import TestClient


def _valid_complete_payload(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "questionnaire_responses": {"goal": "Build creator identity"},
        "skill_stack": ["python", "writing"],
        "interest_energy_curve": [{"topic": "growth", "score": 4}],
        "cognitive_style": "structured",
        "value_boundaries": ["no fake claims"],
        "risk_tolerance": 3,
        "time_investment_hours": 8,
    }


def test_onboarding_endpoints_full_flow_with_events(client: TestClient, user_id: str) -> None:
    create_response = client.post("/v1/onboarding/sessions", json={"user_id": user_id})
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]

    complete_response = client.post(
        f"/v1/onboarding/sessions/{session_id}/complete",
        json=_valid_complete_payload(session_id),
    )
    assert complete_response.status_code == 200
    complete_body = complete_response.json()
    assert complete_body["session_id"] == session_id
    assert complete_body["status"] == "completed"

    session_response = client.get(f"/v1/onboarding/sessions/{session_id}")
    assert session_response.status_code == 200
    assert session_response.json()["status"] == "completed"

    profile_response = client.get(f"/v1/onboarding/sessions/{session_id}/profile")
    assert profile_response.status_code == 200
    profile_body = profile_response.json()
    assert profile_body["session_id"] == session_id
    assert profile_body["risk_tolerance"] == 3

    user_profiles_response = client.get(f"/v1/onboarding/users/{user_id}/profiles")
    assert user_profiles_response.status_code == 200
    profiles = user_profiles_response.json()
    assert len(profiles) == 1
    assert profiles[0]["id"] == complete_body["profile_id"]

    events_response = client.get(f"/v1/events/users/{user_id}", params={"limit": 20})
    assert events_response.status_code == 200
    event_names = {event["event_name"] for event in events_response.json()}
    assert "onboarding_started" in event_names
    assert "onboarding_completed" in event_names


def test_create_session_validation_error_returns_422(client: TestClient) -> None:
    response = client.post("/v1/onboarding/sessions", json={})
    assert response.status_code == 422


def test_complete_session_validation_error_returns_422(client: TestClient, user_id: str) -> None:
    create_response = client.post("/v1/onboarding/sessions", json={"user_id": user_id})
    session_id = create_response.json()["id"]

    response = client.post(
        f"/v1/onboarding/sessions/{session_id}/complete",
        json={
            "session_id": session_id,
            "risk_tolerance": 7,
        },
    )
    assert response.status_code == 422


def test_complete_session_not_found_returns_404(client: TestClient) -> None:
    response = client.post(
        "/v1/onboarding/sessions/not-found/complete",
        json=_valid_complete_payload("not-found"),
    )
    assert response.status_code == 404


def test_get_missing_onboarding_session_and_profile_return_404(client: TestClient) -> None:
    session_response = client.get("/v1/onboarding/sessions/missing-session")
    profile_response = client.get("/v1/onboarding/sessions/missing-session/profile")

    assert session_response.status_code == 404
    assert profile_response.status_code == 404
