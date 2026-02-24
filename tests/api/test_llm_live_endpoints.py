from __future__ import annotations

import json
import os
from pathlib import Path
import time

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.services.llm_client import reset_llm_client_cache
from tests.api.helpers import create_identity_model, create_persona_constitution

pytestmark = [
    pytest.mark.live_llm,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_LLM_TESTS") != "1",
        reason="set RUN_LIVE_LLM_TESTS=1 to run real LLM endpoint tests",
    ),
]


def _load_dotenv_values(dotenv_path: Path) -> dict[str, str]:
    if not dotenv_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def _retryable_provider_status(provider_status: object) -> bool:
    return provider_status == 429 or (
        isinstance(provider_status, int) and provider_status >= 500
    )


def _post_with_transient_retry(client: TestClient, path: str, payload: dict) -> object:
    max_retries = int(os.getenv("LIVE_LLM_MAX_RETRIES", "2"))
    base_backoff = float(os.getenv("LIVE_LLM_RETRY_BACKOFF_SECONDS", "1"))

    response = None
    for attempt in range(max_retries + 1):
        response = client.post(path, json=payload)
        if response.status_code == 200:
            return response

        if response.status_code != 502:
            return response

        detail = response.json().get("detail", {})
        provider_status = detail.get("provider_status")
        if attempt < max_retries and _retryable_provider_status(provider_status):
            time.sleep(base_backoff * (2**attempt))
            continue
        return response
    return response


def _assert_live_success(response: object, endpoint: str, scenario: str) -> None:
    assert response is not None
    if response.status_code != 200:
        pytest.fail(
            f"{endpoint} scenario={scenario} failed with status={response.status_code}, "
            f"body={response.text}"
        )


def _count_user_events(client: TestClient, user_id: str, event_name: str) -> int:
    response = client.get(f"/v1/events/users/{user_id}", params={"limit": 200})
    assert response.status_code == 200
    events = response.json()
    return sum(1 for event in events if event["event_name"] == event_name)


def _create_completed_onboarding_session(client: TestClient, user_id: str) -> str:
    create_response = client.post("/v1/onboarding/sessions", json={"user_id": user_id})
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]

    complete_response = client.post(
        f"/v1/onboarding/sessions/{session_id}/complete",
        json={
            "session_id": session_id,
            "questionnaire_responses": {"goal": "Find a profitable creator niche"},
            "skill_stack": ["python", "analytics", "writing"],
            "interest_energy_curve": [{"topic": "growth", "score": 5}],
            "cognitive_style": "systematic",
            "value_boundaries": ["No fake metrics", "No impersonation"],
            "risk_tolerance": 3,
            "time_investment_hours": 10,
        },
    )
    assert complete_response.status_code == 200
    return session_id


@pytest.fixture()
def live_env_ready(monkeypatch) -> None:
    project_root = Path(__file__).resolve().parents[2]
    dotenv_values = _load_dotenv_values(project_root / ".env")

    for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "MODEL_NAME"):
        if key in dotenv_values and dotenv_values[key]:
            monkeypatch.setenv(key, dotenv_values[key])

    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "")
    model_name = os.getenv("MODEL_NAME", "")
    if not api_key or api_key == "test-openai-key":
        pytest.fail("RUN_LIVE_LLM_TESTS=1 but OPENAI_API_KEY is missing or still test placeholder.")
    if not base_url:
        pytest.fail("RUN_LIVE_LLM_TESTS=1 but OPENAI_BASE_URL is missing.")
    if not model_name or model_name == "test-model":
        pytest.fail("RUN_LIVE_LLM_TESTS=1 but MODEL_NAME is missing or still test placeholder.")

    get_settings.cache_clear()
    reset_llm_client_cache()
    yield
    get_settings.cache_clear()
    reset_llm_client_cache()


def test_identity_generate_live_multi_scenarios(
    live_env_ready,
    client: TestClient,
    user_id: str,
) -> None:
    del live_env_ready
    session_id = _create_completed_onboarding_session(client, user_id)

    scenarios = [
        (
            "A_minimal",
            {
                "user_id": user_id,
                "count": 3,
            },
        ),
        (
            "B_rich",
            {
                "user_id": user_id,
                "count": 5,
                "capability_profile": {
                    "skill_stack": ["Python", "SQL", "Product", "Narrative writing"],
                    "cognitive_style": "Data-driven and first-principles",
                    "risk_tolerance": 3,
                    "constraints": "Need repeatable system, avoid hype.",
                    "language": "zh-CN + en-US",
                },
            },
        ),
        (
            "C_related_session",
            {
                "user_id": user_id,
                "session_id": session_id,
                "count": 3,
                "capability_profile": {"ignored_when_session_exists": True},
            },
        ),
    ]

    for scenario_name, payload in scenarios:
        response = _post_with_transient_retry(client, "/v1/identity-models/generate", payload)
        _assert_live_success(response, "/v1/identity-models/generate", scenario_name)
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == payload["count"]
        for item in body:
            assert item["id"]
            assert item["title"].strip()
            assert item["target_audience_pain"].strip()
            assert item["differentiation"].strip()

    assert _count_user_events(client, user_id, "identity_models_generated") >= 3


def test_persona_generate_live_multi_scenarios(
    live_env_ready,
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    del live_env_ready
    with session_local() as db:
        related_identity = create_identity_model(db, user_id=user_id, title="Related Identity")

    scenarios = [
        ("A_minimal", {"user_id": user_id}),
        (
            "B_rich",
            {
                "user_id": user_id,
                "common_words": ["evidence", "system", "clarity", "迭代"],
                "forbidden_words": ["guarantee", "overnight", "绝对化"],
            },
        ),
        (
            "C_related_identity",
            {
                "user_id": user_id,
                "identity_model_id": related_identity.id,
                "common_words": ["framework", "consistency", "sustainable"],
                "forbidden_words": ["fake", "spam", "抄袭"],
            },
        ),
    ]

    versions: list[int] = []
    for scenario_name, payload in scenarios:
        response = _post_with_transient_retry(
            client,
            "/v1/persona-constitutions/generate",
            payload,
        )
        _assert_live_success(response, "/v1/persona-constitutions/generate", scenario_name)
        body = response.json()
        assert body["id"]
        assert body["user_id"] == user_id
        assert body["narrative_mainline"].strip()
        versions.append(body["version"])

    assert versions == [1, 2, 3]


def test_launch_kit_generate_live_multi_scenarios(
    live_env_ready,
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    del live_env_ready
    with session_local() as db:
        related_identity = create_identity_model(db, user_id=user_id, title="Launch Identity")
        related_constitution = create_persona_constitution(
            db,
            user_id=user_id,
            identity_model_id=related_identity.id,
            version=1,
        )

    scenarios = [
        ("A_minimal", {"user_id": user_id}),
        (
            "B_rich",
            {
                "user_id": user_id,
                "sustainable_columns": ["案例拆解", "system teardown", "weekly reflection"],
                "growth_experiment_suggestion": [
                        {
                            "name": "标题钩子 A/B",
                            "hypothesis": "具体收益型标题提高收藏率",
                            "variables": "title, opening",
                            "duration": "7d",
                            "success_metric": "save_rate",
                        }
                    ],
                },
        ),
        (
            "C_related_resources",
            {
                "user_id": user_id,
                "identity_model_id": related_identity.id,
                "constitution_id": related_constitution.id,
                "sustainable_columns": ["deep dive", "myth busting", "playbook"],
                "growth_experiment_suggestion": [{"name": "format test"}],
            },
        ),
    ]

    for scenario_name, payload in scenarios:
        response = _post_with_transient_retry(client, "/v1/launch-kits/generate", payload)
        _assert_live_success(response, "/v1/launch-kits/generate", scenario_name)
        body = response.json()
        assert body["id"]
        assert body["user_id"] == user_id
        day_numbers = [day["day_no"] for day in body["days"]]
        assert sorted(day_numbers) == [1, 2, 3, 4, 5, 6, 7]
        assert all(day["theme"].strip() for day in body["days"])
        assert all(day["opening_text"].strip() for day in body["days"])

    assert _count_user_events(client, user_id, "launch_kit_generated") >= 3


def test_consistency_check_live_multi_scenarios(
    live_env_ready,
    client: TestClient,
    user_id: str,
    session_local: sessionmaker,
) -> None:
    del live_env_ready
    with session_local() as db:
        related_identity = create_identity_model(db, user_id=user_id, title="Consistency Identity")
        related_constitution = create_persona_constitution(
            db,
            user_id=user_id,
            identity_model_id=related_identity.id,
            version=1,
        )

    scenarios = [
        (
            "A_minimal",
            {
                "user_id": user_id,
                "draft_text": "我想稳定输出，但经常断更。请给我可执行建议。",
            },
        ),
        (
            "B_rich",
            {
                "user_id": user_id,
                "draft_text": (
                    "This post promises guaranteed revenue in 7 days and implies secret insider methods. "
                    "我还想用夸大案例来吸引点击，请帮我检查风险。"
                ),
            },
        ),
        (
            "C_related_resources",
            {
                "user_id": user_id,
                "identity_model_id": related_identity.id,
                "constitution_id": related_constitution.id,
                "draft_text": "今天分享一个方法论草稿，想保持理性语气并避免过度承诺。",
            },
        ),
    ]

    for scenario_name, payload in scenarios:
        response = _post_with_transient_retry(client, "/v1/consistency-checks", payload)
        _assert_live_success(response, "/v1/consistency-checks", scenario_name)
        body = response.json()
        assert body["id"]

        deviation_items = json.loads(body["deviation_items"])
        deviation_reasons = json.loads(body["deviation_reasons"])
        suggestions = json.loads(body["suggestions"])

        assert deviation_items
        assert deviation_reasons
        assert suggestions
        assert isinstance(body["degraded"], bool)
        assert isinstance(body["schema_repair_attempts"], int)
        assert 0 <= body["schema_repair_attempts"] <= 2
        if body["degraded"]:
            assert body["degrade_reason"] == "llm_schema_retry_exhausted"
            assert body["schema_repair_attempts"] == 2
        else:
            assert body["degrade_reason"] is None

        if body["risk_triggered"]:
            assert body["risk_warning"].strip()

    assert _count_user_events(client, user_id, "consistency_check_triggered") >= 3
