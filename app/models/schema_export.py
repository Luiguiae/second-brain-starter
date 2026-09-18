"""JSON Schema exportado de los modelos de dominio (Fase 2, T10 — docs/tasks.md).

Este es "el mismo JSON Schema" que docs/SPEC.md exige que valide tanto al
cliente MCP como al REST (criterio de aceptación: "ambos reciben una
respuesta que valida contra el mismo JSON Schema de salida"). Ambos
canales (Fase 5, Fase 6) deben llamar a estas funciones en vez de generar
su propio schema — así la paridad de Fase 7 (T28-T29) es estructural, no
un acuerdo de caballeros entre dos implementaciones separadas.
"""

from __future__ import annotations

from typing import Any

from app.models.plan import CreateSecondBrainPlanRequest, CreateSecondBrainPlanResponse


def plan_request_json_schema() -> dict[str, Any]:
    """JSON Schema (draft usado por Pydantic v2) de `CreateSecondBrainPlanRequest`."""
    return CreateSecondBrainPlanRequest.model_json_schema()


def plan_response_json_schema() -> dict[str, Any]:
    """JSON Schema (draft usado por Pydantic v2) de `CreateSecondBrainPlanResponse`."""
    return CreateSecondBrainPlanResponse.model_json_schema()
