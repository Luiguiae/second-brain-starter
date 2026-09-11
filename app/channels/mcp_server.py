"""Canal MCP (Fase 6, T25-T26 — docs/tasks.md).

Expone el mismo engine (AGENTS.md, invariante 2) como una tool MCP
llamada `diagnose`, sobre `MCPServer` del SDK oficial (`mcp==2.2.0`).
Ninguna lógica de decisión vive acá — solo el adaptador de transporte
MCP, análogo a `app/channels/rest.py` (Fase 5). Se monta en `/mcp`
(docs/SPEC.md, "MCP server nativo (`/mcp`)") desde `app/main.py`.

T26 — mapeo de errores: los mismos 3 estados de error de Fase 4
(`MissingFieldsError`, `InvalidEnumValueError`, `BenchmarkLoadError`) se
traducen a `mcp.server.mcpserver.exceptions.ToolError`, que el SDK
convierte en un `CallToolResult(is_error=True, ...)` — el equivalente
nativo de MCP a un error HTTP. El mensaje es el mismo JSON que usa el
canal REST como body de error (`{"error": ..., ...}`), para que la
información sea idéntica en ambos canales (Fase 7, T29), aunque el
transporte la exponga distinto (JSON body + status code vs.
`is_error` + texto).
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app.engine import diagnose as run_diagnose
from app.errors import (
    BenchmarkLoadError,
    InvalidEnumValueError,
    MissingFieldsError,
    get_benchmark,
    validate_diagnose_request,
)

mcp_server = MCPServer(
    name="second-brain-starter",
    title="Second Brain Starter",
    description=(
        "Diagnostica el perfil de conocimiento de una persona y recomienda la "
        "estructura de su Segundo Cerebro (PKM) + un set inicial de skills. "
        "Motor de reglas determinístico, sin LLM en el core."
    ),
    version="1.0.0",
)


@mcp_server.tool(
    name="diagnose",
    description=(
        "Diagnostica el perfil de conocimiento a partir de las 5 dimensiones del "
        "cuestionario (purpose, maintenance_tolerance, agent_usage, "
        "capture_volume, technical_profile) y devuelve, de forma determinística: "
        "archetype, justification (citas al benchmark), structure "
        "(folders/frontmatter_fields) y entre 3 y 5 skills iniciales."
    ),
)
def diagnose_tool(
    purpose: str | None = None,
    maintenance_tolerance: str | None = None,
    agent_usage: str | None = None,
    capture_volume: str | None = None,
    technical_profile: str | None = None,
) -> dict[str, Any]:
    # Los 5 parámetros son `| None = None` a propósito: si el SDK de MCP los
    # declarara `str` (obligatorios), rechazaría un payload incompleto con su
    # propio ToolError genérico *antes* de que este código corra, sin pasar
    # por validate_diagnose_request — perdiendo la clasificación 422 vs 400
    # de Fase 4 (T17-T18) que este canal debe compartir con REST. Filtrando
    # los None acá, un campo ausente llega a validate_diagnose_request como
    # realmente ausente (MissingFieldsError), no como un error de schema del
    # SDK. Casing distinto, string vacío ("") y whitespace SÍ llegan intactos
    # (no son None) y se clasifican igual que en REST — ver
    # test_invalid_enum_edge_cases_are_equivalent_across_channels en
    # tests/parity/test_schema_validity.py.
    #
    # Límite conocido: el SDK liga estos 5 parámetros por firma de Python, así
    # que un campo ausente en `arguments` y un `null` JSON explícito llegan
    # los dos como `None` acá adentro — indistinguibles en este punto. Por
    # eso un `purpose: null` explícito se clasifica como missing_fields en
    # vez de invalid_enum_value (que es lo que REST devuelve para ese mismo
    # input, porque a Pydantic sí le llega la clave presente con valor None).
    # Se prioriza deliberadamente la clasificación correcta del caso común
    # (campo realmente ausente) sobre la paridad exacta en este caso límite —
    # ver test_explicit_null_is_a_known_divergence_of_the_mcp_workaround en
    # el mismo archivo.
    raw_payload = {
        "purpose": purpose,
        "maintenance_tolerance": maintenance_tolerance,
        "agent_usage": agent_usage,
        "capture_volume": capture_volume,
        "technical_profile": technical_profile,
    }
    payload = {k: v for k, v in raw_payload.items() if v is not None}
    try:
        request_ = validate_diagnose_request(payload)
        benchmark = get_benchmark()
        response = run_diagnose(request_, benchmark)
    except MissingFieldsError as exc:
        raise ToolError(
            json.dumps({"error": "missing_fields", "missing_fields": exc.missing_fields})
        ) from exc
    except InvalidEnumValueError as exc:
        raise ToolError(
            json.dumps(
                {
                    "error": "invalid_enum_value",
                    "field": exc.field,
                    "value": exc.value,
                    "valid_values": exc.valid_values,
                }
            )
        ) from exc
    except BenchmarkLoadError as exc:
        raise ToolError(
            json.dumps({"error": "benchmark_unavailable", "message": str(exc)})
        ) from exc

    return response.model_dump(mode="json")
