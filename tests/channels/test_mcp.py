"""T27 (docs/tasks.md, Fase 6): tests de integración del canal MCP.

Dos niveles, contra el servidor MCP real (`app.channels.mcp_server.mcp_server`,
el mismo objeto que `app.main` monta en `/mcp`), sin mockear el engine:

1. `mcp_server.call_tool("diagnose", ...)` — invoca el mismo código de
   despacho de tool que usa cualquier transporte (stdio/SSE/streamable-http),
   saltándose solo el handshake de sesión JSON-RPC. Es la vía rápida y
   estable para los casos felices y los 3 estados de error.
2. Un smoke test end-to-end real: levanta `app.main.app` completa (con su
   lifespan, que arranca el session_manager de MCP — ver app/main.py) vía
   `TestClient` y hace el handshake `initialize` real por HTTP contra `/mcp`,
   confirmando que el montaje (Fase 5+6 juntas) funciona de punta a punta,
   no solo en el nivel de Python.

Nota sobre el nivel 1: cuando el tool function levanta `ToolError`, el
wrapper interno del SDK (`mcp/server/mcpserver/tools/base.py`) lo vuelve a
envolver anteponiendo `"Error executing tool diagnose: "` al mensaje — por
eso `_parse_tool_error` busca el primer `{` en el texto en vez de asumir que
el mensaje completo es JSON. Sobre el transporte real (JSON-RPC), esa misma
excepción se traduce a `CallToolResult(isError=True, ...)` — el equivalente
MCP nativo a un error, que es lo que T26 pide.
"""

from __future__ import annotations

import json

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from app.channels.mcp_server import mcp_server
from app.errors.knowledge_errors import BenchmarkLoadError as LoaderBenchmarkLoadError

pytestmark = pytest.mark.anyio

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


def _parse_tool_error(exc: ToolError) -> dict:
    text = str(exc)
    return json.loads(text[text.index("{") :])


async def test_diagnose_tool_is_listed() -> None:
    tools = await mcp_server.list_tools()
    assert any(t.name == "diagnose" for t in tools)


@pytest.mark.parametrize("expected_archetype,payload", HAPPY_CASES.items(), ids=HAPPY_CASES.keys())
async def test_diagnose_tool_happy_path_returns_expected_archetype(
    expected_archetype: str, payload: dict[str, str]
) -> None:
    result = await mcp_server.call_tool("diagnose", payload)

    assert result.is_error is False
    assert result.structured_content["archetype"] == expected_archetype
    assert 3 <= len(result.structured_content["skills"]) <= 5
    assert result.structured_content["justification"]


async def test_diagnose_tool_missing_fields_raises_tool_error_with_field_list() -> None:
    payload = {k: v for k, v in HAPPY_CASES["action_first"].items() if k != "technical_profile"}

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("diagnose", payload)

    parsed = _parse_tool_error(excinfo.value)
    assert parsed == {"error": "missing_fields", "missing_fields": ["technical_profile"]}


async def test_diagnose_tool_invalid_enum_raises_tool_error_with_valid_values() -> None:
    payload = {**HAPPY_CASES["action_first"], "purpose": "not_a_real_purpose"}

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("diagnose", payload)

    parsed = _parse_tool_error(excinfo.value)
    assert parsed["error"] == "invalid_enum_value"
    assert parsed["field"] == "purpose"
    assert set(parsed["valid_values"]) == {
        "execute_projects",
        "produce_knowledge",
        "agent_memory",
        "study",
    }


async def test_diagnose_tool_benchmark_unavailable_raises_tool_error(monkeypatch) -> None:
    def _always_fails(**kwargs):
        raise LoaderBenchmarkLoadError("simulado: knowledge/benchmark.yaml corrupto")

    monkeypatch.setattr("app.channels.mcp_server.get_benchmark", _always_fails)

    with pytest.raises(ToolError) as excinfo:
        await mcp_server.call_tool("diagnose", HAPPY_CASES["action_first"])

    parsed = _parse_tool_error(excinfo.value)
    assert parsed["error"] == "benchmark_unavailable"
    assert "simulado" in parsed["message"]


def test_mcp_endpoint_mounted_on_real_app_responds_to_initialize() -> None:
    """Smoke test end-to-end: la app real (con su lifespan) sirve /mcp."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app, base_url="http://localhost") as client:
        response = client.post(
            "/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest-smoke-test", "version": "0.0.1"},
                },
            },
        )

    assert response.status_code == 200
    assert "second-brain-starter" in response.text
