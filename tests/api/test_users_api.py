from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient


def test_create_user_for_api_testing(client: TestClient) -> None:
    create_user_response = client.post("/v1/users")
    assert create_user_response.status_code == 200

    create_user_body = create_user_response.json()
    UUID(create_user_body["id"])
    assert "created_at" in create_user_body

    create_session_response = client.post(
        "/v1/onboarding/sessions",
        json={"user_id": create_user_body["id"]},
    )
    assert create_session_response.status_code == 200
