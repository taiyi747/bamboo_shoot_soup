from __future__ import annotations

import app.main as main_module

EXPECTED_ROUTES = {
    ("GET", "/health"),
    ("POST", "/v1/users"),
    ("POST", "/v1/onboarding/sessions"),
    ("POST", "/v1/onboarding/sessions/{session_id}/complete"),
    ("GET", "/v1/onboarding/sessions/{session_id}"),
    ("GET", "/v1/onboarding/sessions/{session_id}/profile"),
    ("GET", "/v1/onboarding/users/{user_id}/profiles"),
    ("POST", "/v1/identity-models/generate"),
    ("GET", "/v1/identity-models/users/{user_id}"),
    ("GET", "/v1/identity-models/{model_id}"),
    ("POST", "/v1/identity-selections"),
    ("GET", "/v1/identity-selections/users/{user_id}"),
    ("POST", "/v1/persona-constitutions/generate"),
    ("GET", "/v1/persona-constitutions/users/{user_id}"),
    ("GET", "/v1/persona-constitutions/users/{user_id}/latest"),
    ("GET", "/v1/persona-constitutions/{constitution_id}"),
    ("POST", "/v1/risk-boundaries"),
    ("GET", "/v1/risk-boundaries/users/{user_id}"),
    ("POST", "/v1/launch-kits/generate"),
    ("GET", "/v1/launch-kits/users/{user_id}"),
    ("GET", "/v1/launch-kits/users/{user_id}/latest"),
    ("GET", "/v1/launch-kits/{kit_id}"),
    ("POST", "/v1/consistency-checks"),
    ("GET", "/v1/consistency-checks/users/{user_id}"),
    ("GET", "/v1/consistency-checks/{check_id}"),
    ("POST", "/v1/events"),
    ("GET", "/v1/events/users/{user_id}"),
    ("GET", "/v1/events/name/{event_name}"),
    ("GET", "/v1/events/recent"),
    ("POST", "/v1/content-matrices/generate"),
    ("GET", "/v1/content-matrices/users/{user_id}"),
    ("GET", "/v1/content-matrices/{matrix_id}"),
    ("POST", "/v1/experiments"),
    ("PATCH", "/v1/experiments/{experiment_id}/result"),
    ("GET", "/v1/experiments/users/{user_id}"),
    ("POST", "/v1/monetization-maps/generate"),
    ("GET", "/v1/monetization-maps/users/{user_id}"),
    ("GET", "/v1/monetization-maps/{map_id}"),
}


def _collect_runtime_routes() -> set[tuple[str, str]]:
    runtime_routes: set[tuple[str, str]] = set()
    for route in main_module.app.routes:
        if route.path != "/health" and not route.path.startswith("/v1/"):
            continue
        methods = getattr(route, "methods", set())
        for method in methods:
            if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                runtime_routes.add((method, route.path))
    return runtime_routes


def test_runtime_routes_match_v1_inventory() -> None:
    runtime_routes = _collect_runtime_routes()
    assert len(runtime_routes) == 38
    assert runtime_routes == EXPECTED_ROUTES
