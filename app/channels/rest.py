"""Canal REST (Fase 5, T21-T23 — docs/tasks.md).

Adaptador HTTP puro sobre el engine (AGENTS.md, invariante 2): parsea el
request (FastAPI, vía `CreateSecondBrainPlanRequest`), llama a
`get_benchmark()` + `engine.create_plan()`, y devuelve el resultado.
Ninguna lógica de decisión vive acá — solo transporte. El manejo de
errores (T23) está en `app/main.py`, como exception handlers a nivel de
app, para que aplique igual sin importar qué router los dispare.

Renombrado en v2.0.0 (docs/SPEC.md, "Historial de renombres"):
`POST /diagnose` → `POST /plan`. El `description` de abajo es el texto
que lee el agente llamador (GPT Action, Claude Code) al decidir cómo y
cuándo invocar esta operación — implementa en sustancia las 3
instrucciones de "Contrato de interacción con el agente llamador" del
spec. Ver app/channels/mcp_server.py para el texto equivalente del lado
MCP (mismo contenido, pensado para el mismo propósito).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.channels import TOOL_DESCRIPTION
from app.engine import create_plan as run_create_plan
from app.errors import get_benchmark
from app.models.plan import CreateSecondBrainPlanRequest, CreateSecondBrainPlanResponse

router = APIRouter()


@router.post(
    "/plan",
    response_model=CreateSecondBrainPlanResponse,
    operation_id="createSecondBrainPlan",
    summary="Crea la base de un Segundo Cerebro (PKM) desde cero a partir de 5 respuestas",
    description=TOOL_DESCRIPTION,
    responses={
        422: {"description": "Campos obligatorios faltantes en el payload."},
        400: {"description": "Un campo tiene un valor fuera del enum permitido."},
        500: {"description": "knowledge/benchmark.yaml no disponible o corrupto."},
    },
)
async def post_plan(payload: CreateSecondBrainPlanRequest) -> CreateSecondBrainPlanResponse:
    benchmark = get_benchmark()
    return run_create_plan(payload, benchmark)
