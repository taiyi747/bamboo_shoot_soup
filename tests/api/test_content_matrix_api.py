from __future__ import annotations

import copy

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.services.llm_replay import ReplayGenerationResult
from tests.api.helpers import create_content_matrix


_VALID_PAYLOAD = {
    "pillars": [
        {
            "pillar": f"pillar-{idx}",
            "topics": [f"topic-{idx}-{i}" for i in range(1, 21)],
            "platform_rewrites": {
                "xiaohongshu": [f"xhs-{idx}"],
                "wechat": [f"wechat-{idx}"],
                "video_channel": [f"video-{idx}"],
            },
        }
        for idx in range(1, 4)
    ]
}


def test_content_matrix_generate_and_read(
    client: TestClient,
    user_id: str,
    monkeypatch,
) -> None:
    from app.services import content_matrix as content_matrix_service

    def _fake_generate_json_with_replay(*_args, **_kwargs):
        return ReplayGenerationResult(
            payload=copy.deepcopy(_VALID_PAYLOAD),
            degraded=False,
            degrade_reason=None,
        )

    monkeypatch.setattr(
        content_matrix_service,
        "generate_json_with_replay",
        _fake_generate_json_with_replay,
    )

    response = client.post(
        "/v1/content-matrices/generate",
        json={"user_id": user_id},
    )
    assert response.status_code == 200
    generated = response.json()
    assert generated["id"]
    assert generated["degraded"] is False

    detail_response = client.get(f"/v1/content-matrices/{generated['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["user_id"] == user_id

    list_response = client.get(f"/v1/content-matrices/users/{user_id}")
    assert list_response.status_code == 200
    assert any(item["id"] == generated["id"] for item in list_response.json())


def test_content_matrix_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/v1/content-matrices/missing")
    assert response.status_code == 404


def test_content_matrix_read_seeded_data(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        matrix = create_content_matrix(db, user_id=user_id)

    response = client.get(f"/v1/content-matrices/{matrix.id}")
    assert response.status_code == 200
    assert response.json()["id"] == matrix.id
