"""Canal REST (Fase 5, T21-T23 — docs/tasks.md).

Adaptador HTTP puro sobre el engine (AGENTS.md, invariante 2): parsea el
request (FastAPI, vía `DiagnoseRequest`), llama a `get_benchmark()` +
`engine.diagnose()`, y devuelve el resultado. Ninguna lógica de decisión
vive acá — solo transporte. El manejo de errores (T23) está en
`app/main.py`, como exception handlers a nivel de app, para que aplique
igual sin importar qué router los dispare.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.engine import diagnose as run_diagnose
from app.errors import get_benchmark
from app.models.diagnose import DiagnoseRequest, DiagnoseResponse

router = APIRouter()


@router.post(
    "/diagnose",
    response_model=DiagnoseResponse,
    operation_id="diagnoseSecondBrain",
    summary="Diagnostica el perfil de conocimiento y recomienda una estructura de Segundo Cerebro",
    description=(
        "Recibe las 5 dimensiones del diagnóstico (docs/SPEC.md, 'Esquema de "
        "datos') y devuelve, de forma determinística: el arquetipo recomendado, "
        "justificación trazable a knowledge/benchmark.yaml, la estructura de "
        "carpetas/frontmatter, y entre 3 y 5 skills iniciales."
    ),
    responses={
        422: {"description": "Campos obligatorios faltantes en el payload."},
        400: {"description": "Un campo tiene un valor fuera del enum permitido."},
        500: {"description": "knowledge/benchmark.yaml no disponible o corrupto."},
    },
)
async def post_diagnose(payload: DiagnoseRequest) -> DiagnoseResponse:
    benchmark = get_benchmark()
    return run_diagnose(payload, benchmark)
