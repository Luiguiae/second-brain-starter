"""T28 (docs/tasks.md, Fase 7): paridad de salidas entre REST y MCP.

Para un set representativo de inputs — uno por arquetipo, más los casos
límite de los modificadores híbrido y LYT que docs/SPEC.md describe —
invoca el mismo input contra el canal REST (`TestClient`) y el canal MCP
(`mcp_server.call_tool`), y compara ambos resultados por igualdad
estructural exacta. Cualquier divergencia hace fallar el test
explícitamente (docs/tasks.md, T28: "no comparación parcial").
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.channels.mcp_server import mcp_server
from app.main import app

pytestmark = pytest.mark.anyio

client = TestClient(app)

# Un caso por arquetipo + los casos límite de los modificadores explícitos
# del spec (híbrido vía already_using/want_to_start, LYT, capture_volume en
# sus 3 valores, technical_profile en sus 2 valores, purpose == study).
REPRESENTATIVE_CASES: dict[str, dict[str, str]] = {
    "action_first-sporadic": {
        "purpose": "execute_projects",
        "maintenance_tolerance": "medium",
        "agent_usage": "not_interested",
        "capture_volume": "sporadic",
        "technical_profile": "markdown_git_comfortable",
    },
    "knowledge_first-no_lyt": {
        "purpose": "produce_knowledge",
        "maintenance_tolerance": "high",
        "agent_usage": "not_interested",
        "capture_volume": "daily_moderate",
        "technical_profile": "prefers_visual_ui",
    },
    "knowledge_first-lyt_modifier": {
        # maintenance_tolerance == low + base knowledge_first -> LYT (caso límite)
        "purpose": "produce_knowledge",
        "maintenance_tolerance": "low",
        "agent_usage": "not_interested",
        "capture_volume": "sporadic",
        "technical_profile": "markdown_git_comfortable",
    },
    "agent_first-high_multi_source": {
        "purpose": "agent_memory",
        "maintenance_tolerance": "medium",
        "agent_usage": "already_using",
        "capture_volume": "high_multi_source",
        "technical_profile": "markdown_git_comfortable",
    },
    "hybrid-already_using": {
        # caso límite del modificador híbrido: agent_usage == already_using
        "purpose": "execute_projects",
        "maintenance_tolerance": "medium",
        "agent_usage": "already_using",
        "capture_volume": "daily_moderate",
        "technical_profile": "prefers_visual_ui",
    },
    "hybrid-want_to_start": {
        # caso límite del modificador híbrido: agent_usage == want_to_start
        "purpose": "produce_knowledge",
        "maintenance_tolerance": "low",
        "agent_usage": "want_to_start",
        "capture_volume": "high_multi_source",
        "technical_profile": "prefers_visual_ui",
    },
    "study-purpose": {
        # purpose == study -> knowledge_first, variante ligera (caso límite)
        "purpose": "study",
        "maintenance_tolerance": "medium",
        "agent_usage": "not_interested",
        "capture_volume": "sporadic",
        "technical_profile": "markdown_git_comfortable",
    },
}


@pytest.mark.parametrize("payload", REPRESENTATIVE_CASES.values(), ids=REPRESENTATIVE_CASES.keys())
async def test_rest_and_mcp_return_structurally_identical_output(payload: dict[str, str]) -> None:
    rest_response = client.post("/diagnose", json=payload)
    assert rest_response.status_code == 200
    rest_body = rest_response.json()

    mcp_result = await mcp_server.call_tool("diagnose", payload)
    assert mcp_result.is_error is False
    mcp_body = mcp_result.structured_content

    assert rest_body == mcp_body, f"REST y MCP divergen para {payload}"
