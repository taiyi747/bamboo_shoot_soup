from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from tests.api.helpers import create_consistency_check


def test_consistency_read_endpoints(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    now = datetime.now(timezone.utc)
    with session_local() as db:
        first = create_consistency_check(
            db,
            user_id=user_id,
            created_at=now - timedelta(minutes=3),
        )
        second = create_consistency_check(
            db,
            user_id=user_id,
            created_at=now,
        )

    list_response = client.get(f"/v1/consistency-checks/users/{user_id}")
    assert list_response.status_code == 200
    checks = list_response.json()
    assert [checks[0]["id"], checks[1]["id"]] == [second.id, first.id]

    detail_response = client.get(f"/v1/consistency-checks/{first.id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == first.id


def test_consistency_detail_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/v1/consistency-checks/missing")
    assert response.status_code == 404
