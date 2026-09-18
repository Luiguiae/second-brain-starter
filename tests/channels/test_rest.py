"""T24 (docs/tasks.md, Fase 5): tests de integración del canal REST.

Contra la app real (`app.main.app`, sin mockear el engine): casos felices
(uno por arquetipo) + los 3 estados de error verificables a nivel HTTP.
El 4to estado (mismatch de schema MCP/REST) se completa en T29.

Renombrado en v2.0.0 (docs/SPEC.md, "Historial de renombres"):
`POST /diagnose` → `POST /plan`.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.errors.knowledge_errors import BenchmarkLoadError
from app.main import app

client = TestClient(app)

HAPPY_CASES: dict[str, dict[str, str]] = {
    "action_first": {
        "purpose": "execute_projects",
        "maintenance_tolerance": "medium",
        "agent_usage": "not_interested",
        "capture_volume": "sporadic",
        "technical_profile": "markdown_git_comfortable",
    },
    "knowledge_first": {
        "purpose": "produce_knowledge",
        "maintenance_tolerance": "high",
        "agent_usage": "not_interested",
        "capture_volume": "daily_moderate",
        "technical_profile": "prefers_visual_ui",
    },
    "agent_first": {
        "purpose": "agent_memory",
        "maintenance_tolerance": "low",
        "agent_usage": "not_interested",
        "capture_volume": "high_multi_source",
        "technical_profile": "markdown_git_comfortable",
    },
    "hybrid": {
        "purpose": "execute_projects",
        "maintenance_tolerance": "medium",
        "agent_usage": "already_using",
        "capture_volume": "daily_moderate",
        "technical_profile": "prefers_visual_ui",
    },
}


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("expected_archetype,payload", HAPPY_CASES.items(), ids=HAPPY_CASES.keys())
def test_plan_happy_path_returns_expected_archetype(
    expected_archetype: str, payload: dict[str, str]
) -> None:
    response = client.post("/plan", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["archetype"] == expected_archetype
    assert 3 <= len(body["skills"]) <= 5
    assert body["justification"]
    assert body["structure"]["folders"]


def test_plan_missing_fields_returns_422_with_field_list() -> None:
    response = client.post("/plan", json={"purpose": "execute_projects"})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "missing_fields"
    assert set(body["missing_fields"]) == {
        "maintenance_tolerance",
        "agent_usage",
        "capture_volume",
        "technical_profile",
    }


def test_plan_invalid_enum_returns_400_with_valid_values() -> None:
    payload = {**HAPPY_CASES["action_first"], "purpose": "not_a_real_purpose"}
    response = client.post("/plan", json=payload)

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "invalid_enum_value"
    assert body["field"] == "purpose"
    assert set(body["valid_values"]) == {
        "execute_projects",
        "produce_knowledge",
        "agent_memory",
        "study",
    }


def test_plan_benchmark_unavailable_returns_500(monkeypatch) -> None:
    def _always_fails(**kwargs):
        raise BenchmarkLoadError("simulado: knowledge/benchmark.yaml corrupto")

    monkeypatch.setattr("app.channels.rest.get_benchmark", _always_fails)

    response = client.post("/plan", json=HAPPY_CASES["action_first"])

    assert response.status_code == 500
    body = response.json()
    assert body["error"] == "benchmark_unavailable"
    assert "simulado" in body["message"]


def test_openapi_json_is_openapi_3x_with_plan_operation() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert "/plan" in schema["paths"]
    operation_ids = {
        op.get("operationId") for path in schema["paths"].values() for op in path.values()
    }
    assert "createSecondBrainPlan" in operation_ids
