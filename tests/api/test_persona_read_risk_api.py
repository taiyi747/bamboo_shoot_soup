from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from tests.api.helpers import create_persona_constitution, create_risk_boundary_item


def test_persona_read_endpoints_return_expected_resources(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        first = create_persona_constitution(db, user_id=user_id, version=1)
        second = create_persona_constitution(
            db,
            user_id=user_id,
            version=2,
            previous_version_id=first.id,
        )

    list_response = client.get(f"/v1/persona-constitutions/users/{user_id}")
    assert list_response.status_code == 200
    versions = [item["version"] for item in list_response.json()]
    assert versions == [2, 1]

    latest_response = client.get(f"/v1/persona-constitutions/users/{user_id}/latest")
    assert latest_response.status_code == 200
    assert latest_response.json()["id"] == second.id

    detail_response = client.get(f"/v1/persona-constitutions/{first.id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["version"] == 1


def test_persona_latest_and_detail_not_found_return_404(client: TestClient, user_id: str) -> None:
    latest_response = client.get(f"/v1/persona-constitutions/users/{user_id}/latest")
    detail_response = client.get("/v1/persona-constitutions/missing")

    assert latest_response.status_code == 404
    assert detail_response.status_code == 404


def test_risk_boundary_create_and_list_endpoints(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        constitution = create_persona_constitution(db, user_id=user_id, version=1)
        create_risk_boundary_item(
            db,
            user_id=user_id,
            constitution_id=constitution.id,
            risk_level=2,
        )

    create_response = client.post(
        "/v1/risk-boundaries",
        json={
            "user_id": user_id,
            "constitution_id": constitution.id,
            "risk_level": 3,
            "boundary_type": "legal",
            "statement": "Do not impersonate people.",
            "source": "user_input",
        },
    )
    assert create_response.status_code == 200
    created_item = create_response.json()
    assert created_item["risk_level"] == 3
    assert created_item["boundary_type"] == "legal"

    list_response = client.get(f"/v1/risk-boundaries/users/{user_id}")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2


def test_risk_boundary_validation_error_returns_422(client: TestClient, user_id: str) -> None:
    response = client.post(
        "/v1/risk-boundaries",
        json={
            "user_id": user_id,
            "risk_level": 7,
        },
    )
    assert response.status_code == 422
