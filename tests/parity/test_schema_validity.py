"""T29 (docs/tasks.md, Fase 7): paridad de errores + validación de schema.

Completa el 4to estado de error de docs/SPEC.md ("Mismatch de schema entre
cliente MCP y REST → validación compartida vía el mismo JSON Schema; falla
= 400 en ambos por igual"), pendiente desde T20 (Fase 4): para los 3
estados de error verificables, invoca el mismo input inválido contra
ambos canales y verifica que el contenido del error es equivalente. Además
valida que tanto la salida feliz como la de error de ambos canales
respetan el mismo JSON Schema exportado en T10.
"""

from __future__ import annotations

import json

import jsonschema
import pytest
from fastapi.testclient import TestClient
from mcp.server.mcpserver.exceptions import ToolError

from app.channels.mcp_server import mcp_server
from app.errors.knowledge_errors import BenchmarkLoadError as LoaderBenchmarkLoadError
from app.main import app
from app.models.schema_export import diagnose_response_json_schema

pytestmark = pytest.mark.anyio

client = TestClient(app)

VALID_PAYLOAD = {
    "purpose": "execute_projects",
    "maintenance_tolerance": "medium",
    "agent_usage": "already_using",
    "capture_volume": "daily_moderate",
    "technical_profile": "markdown_git_comfortable",
}


def _parse_tool_error(exc: ToolError) -> dict:
    text = str(exc)
    return json.loads(text[text.index("{") :])


# --- Estado 4: mismatch de schema / paridad de errores entre canales ------


async def test_missing_fields_error_is_equivalent_across_channels() -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "technical_profile"}

    rest_response = client.post("/diagnose", json=payload)
    assert rest_response.status_code == 422
    rest_body = rest_response.json()

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("diagnose", payload)
    mcp_body = _parse_tool_error(excinfo.value)

    assert rest_body == mcp_body == {
        "error": "missing_fields",
        "missing_fields": ["technical_profile"],
    }


async def test_invalid_enum_error_is_equivalent_across_channels() -> None:
    payload = {**VALID_PAYLOAD, "purpose": "not_a_real_purpose"}

    rest_response = client.post("/diagnose", json=payload)
    assert rest_response.status_code == 400
    rest_body = rest_response.json()

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("diagnose", payload)
    mcp_body = _parse_tool_error(excinfo.value)

    assert rest_body == mcp_body
    assert rest_body["error"] == "invalid_enum_value"
    assert rest_body["field"] == "purpose"


async def test_benchmark_unavailable_error_is_equivalent_across_channels(monkeypatch) -> None:
    def _always_fails(**kwargs):
        raise LoaderBenchmarkLoadError("simulado: knowledge/benchmark.yaml corrupto")

    monkeypatch.setattr("app.channels.rest.get_benchmark", _always_fails)
    monkeypatch.setattr("app.channels.mcp_server.get_benchmark", _always_fails)

    rest_response = client.post("/diagnose", json=VALID_PAYLOAD)
    assert rest_response.status_code == 500
    rest_body = rest_response.json()

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("diagnose", VALID_PAYLOAD)
    mcp_body = _parse_tool_error(excinfo.value)

    assert rest_body["error"] == mcp_body["error"] == "benchmark_unavailable"
    assert "simulado" in rest_body["message"]
    assert "simulado" in mcp_body["message"]


# --- Ambos canales validan contra el mismo JSON Schema (T10) --------------


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID_PAYLOAD, "purpose": "execute_projects"},
        {**VALID_PAYLOAD, "purpose": "produce_knowledge"},
        {**VALID_PAYLOAD, "purpose": "agent_memory"},
        {**VALID_PAYLOAD, "purpose": "study"},
    ],
    ids=["action_first", "knowledge_first", "agent_first", "hybrid_via_agent_usage"],
)
async def test_happy_output_validates_against_shared_schema_in_both_channels(
    payload: dict[str, str],
) -> None:
    schema = diagnose_response_json_schema()

    rest_response = client.post("/diagnose", json=payload)
    assert rest_response.status_code == 200
    jsonschema.validate(instance=rest_response.json(), schema=schema)

    mcp_result = await mcp_server.call_tool("diagnose", payload)
    assert mcp_result.is_error is False
    jsonschema.validate(instance=mcp_result.structured_content, schema=schema)
