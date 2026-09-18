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
from app.models.schema_export import plan_response_json_schema

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

    rest_response = client.post("/plan", json=payload)
    assert rest_response.status_code == 422
    rest_body = rest_response.json()

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("create_second_brain_plan", payload)
    mcp_body = _parse_tool_error(excinfo.value)

    assert rest_body == mcp_body == {
        "error": "missing_fields",
        "missing_fields": ["technical_profile"],
    }


async def test_invalid_enum_error_is_equivalent_across_channels() -> None:
    payload = {**VALID_PAYLOAD, "purpose": "not_a_real_purpose"}

    rest_response = client.post("/plan", json=payload)
    assert rest_response.status_code == 400
    rest_body = rest_response.json()

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("create_second_brain_plan", payload)
    mcp_body = _parse_tool_error(excinfo.value)

    assert rest_body == mcp_body
    assert rest_body["error"] == "invalid_enum_value"
    assert rest_body["field"] == "purpose"


@pytest.mark.parametrize(
    "invalid_purpose",
    ["Execute_Projects", "", " execute_projects "],
    ids=["different_casing", "empty_string", "whitespace"],
)
async def test_invalid_enum_edge_cases_are_equivalent_across_channels(invalid_purpose: str) -> None:
    """Ejercita específicamente la validación manual de MCP en mcp_server.py
    (el workaround `str | None` — ver su docstring) contra la de Pydantic en
    REST: casing distinto, string vacío, y whitespace no son `None`, así que
    ninguno de los dos activa el filtrado de `None` del canal MCP — ambos
    deben llegar a `validate_create_plan_request` intactos y clasificarse
    exactamente igual en los dos canales."""
    payload = {**VALID_PAYLOAD, "purpose": invalid_purpose}

    rest_response = client.post("/plan", json=payload)
    assert rest_response.status_code == 400
    rest_body = rest_response.json()

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("create_second_brain_plan", payload)
    mcp_body = _parse_tool_error(excinfo.value)

    assert rest_body == mcp_body
    assert rest_body == {
        "error": "invalid_enum_value",
        "field": "purpose",
        "value": invalid_purpose,
        "valid_values": ["execute_projects", "produce_knowledge", "agent_memory", "study"],
    }


async def test_explicit_null_is_a_known_divergence_of_the_mcp_workaround() -> None:
    """Documenta, en vez de esconder, el único caso en el que el workaround
    `str | None = None` de mcp_server.py (ver su docstring) SÍ diverge de
    REST: un `null` JSON explícito.

    En REST, `{"purpose": null, ...}` llega intacto al body — Pydantic ve
    la clave presente con valor `None` contra un `Literal[str, ...]` y lo
    clasifica como valor inválido (400). En MCP, el SDK liga los 5
    parámetros de la tool function por firma de Python: un `purpose`
    ausente en `arguments` y un `purpose: null` explícito producen, los
    dos, `purpose=None` dentro de la función — indistinguibles en ese
    punto sin acceder a los argumentos crudos pre-binding del SDK (fuera
    de alcance de este workaround). Por diseño, `create_second_brain_plan_tool` filtra
    todo `None` para preservar la clasificación correcta del caso común
    (un campo realmente ausente -> missing_fields, ver
    test_missing_fields_error_is_equivalent_across_channels), a costa de
    que un `null` explícito se clasifique como missing_fields en vez de
    invalid_enum_value. Ambos canales siguen devolviendo un error de
    cliente explícito — ninguno cae en 200 ni en una excepción sin
    clasificar — solo difiere cuál de los dos estados de error eligen.
    """
    payload = {**VALID_PAYLOAD, "purpose": None}

    rest_response = client.post("/plan", json=payload)
    assert rest_response.status_code == 400
    rest_body = rest_response.json()
    assert rest_body == {
        "error": "invalid_enum_value",
        "field": "purpose",
        "value": None,
        "valid_values": ["execute_projects", "produce_knowledge", "agent_memory", "study"],
    }

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("create_second_brain_plan", payload)
    mcp_body = _parse_tool_error(excinfo.value)
    assert mcp_body == {"error": "missing_fields", "missing_fields": ["purpose"]}


async def test_benchmark_unavailable_error_is_equivalent_across_channels(monkeypatch) -> None:
    def _always_fails(**kwargs):
        raise LoaderBenchmarkLoadError("simulado: knowledge/benchmark.yaml corrupto")

    monkeypatch.setattr("app.channels.rest.get_benchmark", _always_fails)
    monkeypatch.setattr("app.channels.mcp_server.get_benchmark", _always_fails)

    rest_response = client.post("/plan", json=VALID_PAYLOAD)
    assert rest_response.status_code == 500
    rest_body = rest_response.json()

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("create_second_brain_plan", VALID_PAYLOAD)
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
    schema = plan_response_json_schema()

    rest_response = client.post("/plan", json=payload)
    assert rest_response.status_code == 200
    jsonschema.validate(instance=rest_response.json(), schema=schema)

    mcp_result = await mcp_server.call_tool("create_second_brain_plan", payload)
    assert mcp_result.is_error is False
    jsonschema.validate(instance=mcp_result.structured_content, schema=schema)
