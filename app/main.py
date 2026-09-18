"""Second Brain Starter — app FastAPI (Fase 5-6 — docs/tasks.md).

Monta el canal REST (`app/channels/rest.py`, Fase 5) en la raíz y el
canal MCP nativo (`app/channels/mcp_server.py`, Fase 6) en `/mcp`
(docs/SPEC.md, "MCP server nativo (`/mcp`)"). Registra los exception
handlers que traducen los estados de error del engine (Fase 4) a HTTP —
`422`/`400`/`500`, exactamente los de docs/SPEC.md, "Estados de error".

Esta app no contiene lógica de decisión (AGENTS.md, invariante 2): solo
configuración de transporte, metadata de OpenAPI (T22), manejo de
errores (T23), y el montaje de ambos canales.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from mcp.server.transport_security import TransportSecuritySettings

from app.channels.mcp_server import mcp_server
from app.channels.rest import router as rest_router
from app.errors import (
    BenchmarkLoadError,
    InvalidEnumValueError,
    MissingFieldsError,
    classify_validation_errors,
)


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # El canal MCP (streamable-http) necesita su session_manager corriendo
    # dentro de un task group propio; sin esto, cada request a /mcp falla con
    # "Task group is not initialized" (RuntimeError del SDK). FastAPI no
    # arranca el lifespan de una sub-app montada por su cuenta, así que se
    # encadena acá, en el lifespan del app raíz.
    async with mcp_server.session_manager.run():
        yield


# T22: metadata de OpenAPI. `servers` solo se declara si hay una URL pública
# configurada (Render, Fase 9) — GPT Actions requiere un `servers[0].url`
# resoluble; en desarrollo local se omite y FastAPI no lo incluye.
_public_base_url = os.environ.get("PUBLIC_BASE_URL")
_servers = [{"url": _public_base_url}] if _public_base_url else None

# El canal MCP valida el header Host/Origin contra una allowlist (protección
# DNS rebinding del SDK) — sin esto, TODO request a /mcp da 421, incluso en
# desarrollo local. localhost/127.0.0.1 cubren desarrollo local; la URL
# pública (Render, Fase 9) se agrega cuando está configurada. Los tests
# (Fase 6, T27) apuntan su TestClient a http://localhost explícitamente en
# vez de agregar el host sintético de TestClient ("testserver") acá.
_mcp_allowed_hosts = ["localhost", "localhost:*", "127.0.0.1", "127.0.0.1:*"]
_mcp_allowed_origins = [
    "http://localhost",
    "http://localhost:*",
    "http://127.0.0.1",
    "http://127.0.0.1:*",
]
if _public_base_url:
    _parsed_public_url = urlparse(_public_base_url)
    if _parsed_public_url.hostname:
        _mcp_allowed_hosts += [_parsed_public_url.hostname, f"{_parsed_public_url.hostname}:*"]
        _mcp_allowed_origins.append(f"{_parsed_public_url.scheme}://{_parsed_public_url.hostname}")

_mcp_transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=_mcp_allowed_hosts,
    allowed_origins=_mcp_allowed_origins,
)

app = FastAPI(
    title="Second Brain Starter",
    description=(
        "Crea la base de un Segundo Cerebro (PKM) desde cero a partir de 5 "
        "respuestas explícitas y recomienda su estructura + un set inicial de "
        "skills. Motor de reglas determinístico, sin LLM en el core (ver "
        "AGENTS.md)."
    ),
    version="2.0.0",
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    servers=_servers,
    lifespan=_lifespan,
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
    """FastAPI ya validó `payload: CreateSecondBrainPlanRequest` y falló —
    reclasificamos sus errores crudos con la misma lógica que usa el canal
    MCP (T23), para no reimplementar la distinción 422/400 dos veces."""
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


# T25: canal MCP nativo, montado en /mcp (docs/SPEC.md). Debe registrarse
# DESPUÉS de toda ruta directa del app (arriba): un Mount en "/" hace match
# de cualquier path no capturado todavía por una ruta más específica, así
# que si se registrara antes interceptaría /plan, /health, /openapi.json,
# etc. `streamable_http_app()` ya expone su propia ruta interna en /mcp por
# defecto, así que montarlo en la raíz "/" da como resultado exactamente esa
# ruta en la app combinada, sin duplicar el prefijo.
app.mount("/", mcp_server.streamable_http_app(transport_security=_mcp_transport_security))
