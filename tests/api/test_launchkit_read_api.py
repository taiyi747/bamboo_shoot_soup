from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from tests.api.helpers import create_launch_kit


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
