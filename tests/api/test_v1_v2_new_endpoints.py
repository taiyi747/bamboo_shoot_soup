from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from tests.api.helpers import create_identity_model


def test_content_matrix_generate_and_query(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        identity = create_identity_model(db, user_id=user_id, title="Matrix Identity")

    create_response = client.post(
        "/v1/content-matrixes/generate",
        json={
            "user_id": user_id,
            "identity_model_id": identity.id,
            "pillars": ["方法论"],
            "platforms": ["xiaohongshu"],
            "formats": ["post"],
            "count_per_pillar": 20,
        },
    )
    assert create_response.status_code == 200
    body = create_response.json()
    assert body["count"] == 1
    assert body["matrixes"][0]["topics_count"] == 20

    list_response = client.get("/v1/content-matrixes", params={"user_id": user_id})
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    detail_response = client.get(f"/v1/content-matrixes/{body['matrixes'][0]['id']}")
    assert detail_response.status_code == 200
    assert len(detail_response.json()["topics"]) == 20
    first_topic = detail_response.json()["topics"][0]

    publish_response = client.post(
        f"/v1/content-matrixes/{body['matrixes'][0]['id']}/topics/{first_topic['id']}/publish",
        json={"user_id": user_id},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"

    events_response = client.get(f"/v1/events/users/{user_id}", params={"limit": 30})
    assert events_response.status_code == 200
    assert any(event["event_name"] == "content_published" for event in events_response.json())


def test_content_matrix_generate_rejects_invalid_count(
    client: TestClient,
    user_id: str,
) -> None:
    response = client.post(
        "/v1/content-matrixes/generate",
        json={
            "user_id": user_id,
            "pillars": ["方法论"],
            "platforms": ["xiaohongshu"],
            "formats": ["post"],
            "count_per_pillar": 10,
        },
    )
    assert response.status_code == 422


def test_experiment_create_patch_and_gate(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        identity = create_identity_model(db, user_id=user_id, title="Exp Identity")

    create_response = client.post(
        "/v1/experiments",
        json={
            "user_id": user_id,
            "identity_model_id": identity.id,
            "hypothesis": "A 标题提高点击",
            "variables": ["标题", "封面"],
            "duration": "7d",
        },
    )
    assert create_response.status_code == 200
    experiment_id = create_response.json()["id"]

    invalid_patch = client.patch(
        f"/v1/experiments/{experiment_id}",
        json={"next_iteration": "下一轮实验"},
    )
    assert invalid_patch.status_code == 400

    valid_patch = client.patch(
        f"/v1/experiments/{experiment_id}",
        json={"conclusion": "结论成立", "next_iteration": "放大变量"},
    )
    assert valid_patch.status_code == 200
    assert valid_patch.json()["next_iteration"] == "放大变量"

    list_response = client.get("/v1/experiments", params={"user_id": user_id})
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    events_response = client.get(f"/v1/events/users/{user_id}", params={"limit": 30})
    assert events_response.status_code == 200
    assert any(event["event_name"] == "experiment_created" for event in events_response.json())


def test_monetization_map_generate_and_query(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        identity = create_identity_model(db, user_id=user_id, title="Monetization Identity")

    create_response = client.post(
        "/v1/monetization-maps/generate",
        json={
            "user_id": user_id,
            "identity_model_id": identity.id,
            "title": "12 周验证路线",
        },
    )
    assert create_response.status_code == 200
    body = create_response.json()
    assert len(body["weeks"]) == 12

    list_response = client.get("/v1/monetization-maps", params={"user_id": user_id})
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    detail_response = client.get(f"/v1/monetization-maps/{body['id']}")
    assert detail_response.status_code == 200
    assert len(detail_response.json()["weeks"]) == 12

    events_response = client.get(f"/v1/events/users/{user_id}", params={"limit": 30})
    assert events_response.status_code == 200
    assert any(event["event_name"] == "monetization_plan_started" for event in events_response.json())


def test_identity_portfolio_generate_and_list(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        primary = create_identity_model(db, user_id=user_id, title="Primary")
        backup = create_identity_model(db, user_id=user_id, title="Backup")

    create_response = client.post(
        "/v1/identity-portfolios/generate",
        json={
            "user_id": user_id,
            "primary_identity_id": primary.id,
            "backup_identity_id": backup.id,
            "anonymous_identity": "匿名观察者",
            "tool_identity": "工具教程号",
        },
    )
    assert create_response.status_code == 200

    list_response = client.get("/v1/identity-portfolios", params={"user_id": user_id})
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    invalid_response = client.post(
        "/v1/identity-portfolios/generate",
        json={
            "user_id": user_id,
            "primary_identity_id": primary.id,
            "backup_identity_id": primary.id,
            "anonymous_identity": "匿名观察者",
            "tool_identity": "工具教程号",
        },
    )
    assert invalid_response.status_code == 400


def test_metrics_simulator_and_viewpoint_assets(
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    with session_local() as db:
        identity = create_identity_model(db, user_id=user_id, title="V2 Identity")

    simulator_response = client.post(
        "/v1/simulator/prepublish-evaluations",
        json={
            "user_id": user_id,
            "identity_model_id": identity.id,
            "draft_text": "这条内容保证你七天爆发，内幕技巧全部公开。",
            "platform": "xiaohongshu",
            "stage_goal": "增长",
        },
    )
    assert simulator_response.status_code == 200
    sim_body = simulator_response.json()
    assert sim_body["recommendation"] in {"发", "改后发", "暂缓"}
    assert "growth_prediction_range" in sim_body

    extract_response = client.post(
        "/v1/viewpoint-assets/extract",
        json={
            "user_id": user_id,
            "identity_model_id": identity.id,
            "topic": "AI 提效",
            "platform": "all",
            "source_contents": ["内容样本 1", "内容样本 2"],
        },
    )
    assert extract_response.status_code == 200
    assert extract_response.json()["count"] == 2

    search_response = client.get(
        "/v1/viewpoint-assets/search",
        params={"user_id": user_id, "query": "AI"},
    )
    assert search_response.status_code == 200
    assert len(search_response.json()) >= 1

    metrics_response = client.get("/v1/metrics/dashboard")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert "funnel" in metrics
    assert "weekly_retention" in metrics
    assert "publish_rate" in metrics
