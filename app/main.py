"""Second Brain Starter — app FastAPI (Fase 5, T21-T23 — docs/tasks.md).

Monta el canal REST (`app/channels/rest.py`) y registra los exception
handlers que traducen los estados de error del engine (Fase 4) a HTTP —
`422`/`400`/`500`, exactamente los de docs/SPEC.md, "Estados de error".
El canal MCP (Fase 6) se monta aparte, en `/mcp`.

Esta app no contiene lógica de decisión (AGENTS.md, invariante 2): solo
configuración de transporte, metadata de OpenAPI (T22), y manejo de
errores (T23).
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.channels.rest import router as rest_router
from app.errors import (
    BenchmarkLoadError,
    InvalidEnumValueError,
    MissingFieldsError,
    classify_validation_errors,
)

# T22: metadata de OpenAPI. `servers` solo se declara si hay una URL pública
# configurada (Railway, Fase 9) — GPT Actions requiere un `servers[0].url`
# resoluble; en desarrollo local se omite y FastAPI no lo incluye.
_public_base_url = os.environ.get("PUBLIC_BASE_URL")
_servers = [{"url": _public_base_url}] if _public_base_url else None

app = FastAPI(
    title="Second Brain Starter",
    description=(
        "Diagnostica el perfil de conocimiento de una persona y recomienda la "
        "estructura de su Segundo Cerebro (PKM) + un set inicial de skills. "
        "Motor de reglas determinístico, sin LLM en el core (ver AGENTS.md)."
    ),
    version="1.0.0",
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    servers=_servers,
)

app.include_router(rest_router)


def _validation_error_response(exc: MissingFieldsError | InvalidEnumValueError) -> JSONResponse:
    if isinstance(exc, MissingFieldsError):
        return JSONResponse(
            status_code=422,
            content={"error": "missing_fields", "missing_fields": exc.missing_fields},
        )
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_enum_value",
            "field": exc.field,
            "value": exc.value,
            "valid_values": exc.valid_values,
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """FastAPI ya validó `payload: DiagnoseRequest` y falló — reclasificamos
    sus errores crudos con la misma lógica que usa el canal MCP (T23),
    para no reimplementar la distinción 422/400 dos veces."""
    classified = classify_validation_errors(exc.errors())
    return _validation_error_response(classified)


@app.exception_handler(MissingFieldsError)
async def handle_missing_fields_error(request: Request, exc: MissingFieldsError) -> JSONResponse:
    return _validation_error_response(exc)


@app.exception_handler(InvalidEnumValueError)
async def handle_invalid_enum_value_error(
    request: Request, exc: InvalidEnumValueError
) -> JSONResponse:
    return _validation_error_response(exc)


@app.exception_handler(BenchmarkLoadError)
async def handle_benchmark_load_error(request: Request, exc: BenchmarkLoadError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "benchmark_unavailable", "message": str(exc)},
    )


@app.get("/health", tags=["meta"], summary="Healthcheck", operation_id="health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
