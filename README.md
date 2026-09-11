# Second Brain Starter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Diagnostica tu perfil de conocimiento con un cuestionario corto (5 dimensiones) y recomienda la estructura de tu Segundo Cerebro (PKM) + un set inicial de skills/plantillas — expuesto simultáneamente como **MCP server nativo** (`/mcp`) y **API REST/OpenAPI** (`/diagnose`), para que Claude Code, un GPT personalizado, u otro agente lo invoquen directamente.

Motor de reglas **determinístico, sin LLM en el core** (ver [AGENTS.md](AGENTS.md)): mismo input, siempre la misma recomendación, trazable a [`knowledge/benchmark.yaml`](knowledge/benchmark.yaml).

Ver [docs/SPEC.md](docs/SPEC.md) para la especificación completa, [docs/BENCHMARK.md](docs/BENCHMARK.md) para la investigación que sustenta las recomendaciones, y [docs/plan.md](docs/plan.md) / [docs/tasks.md](docs/tasks.md) para el plan de implementación.

## Quickstart local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

uvicorn app.main:app --reload
```

La app queda arriba en `http://127.0.0.1:8000`:
- `GET /health` — healthcheck.
- `POST /diagnose` — el endpoint REST.
- `GET /docs` — documentación interactiva (Swagger UI).
- `GET /openapi.json` — el schema OpenAPI 3.x (compatible con Custom GPT Actions).
- `POST /mcp` — el servidor MCP nativo (streamable HTTP).

Corré los tests con:

```bash
pytest
ruff check .
```

## Ejemplo — REST

```bash
curl -X POST http://127.0.0.1:8000/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "purpose": "execute_projects",
    "maintenance_tolerance": "medium",
    "agent_usage": "already_using",
    "capture_volume": "daily_moderate",
    "technical_profile": "markdown_git_comfortable"
  }'
```

Devuelve `archetype`, `justification` (citando `knowledge/benchmark.yaml`), `structure` (folders + frontmatter_fields) y entre 3 y 5 `skills` — ver el schema completo en [docs/SPEC.md](docs/SPEC.md#esquema-de-datos).

## Ejemplo — MCP

El servidor MCP expone una única tool, `diagnose`, con los mismos 5 parámetros que el body de `/diagnose` (`purpose`, `maintenance_tolerance`, `agent_usage`, `capture_volume`, `technical_profile`) y devuelve exactamente la misma forma de respuesta — ambos canales comparten el mismo motor de reglas y el mismo JSON Schema (ver [AGENTS.md](AGENTS.md), invariante 2).

Para conectarlo desde Claude Code (o cualquier cliente MCP que hable streamable-http), agregá el servidor apuntando a `http://127.0.0.1:8000/mcp` en local, o a `https://tu-deploy.up.railway.app/mcp` en producción.

## Editar `knowledge/benchmark.yaml` sin tocar código

Toda la base de conocimiento — metodologías (`systems`), arquetipos, las 5 dimensiones del diagnóstico, la tabla de reglas de decisión (`decision_rules`) y el catálogo de skills iniciales (`skills_catalog`) — vive en [`knowledge/benchmark.yaml`](knowledge/benchmark.yaml), versionado en el repo.

Para agregar o ajustar una recomendación:

1. Editá `knowledge/benchmark.yaml` directamente (es YAML plano, sin necesidad de tocar `app/`).
2. Si agregás una fuente nueva, sumala a la sección `sources:` primero — cualquier `source_refs`/`system_ref` que no exista en `sources`/`systems` hace fallar la validación del archivo (ver `app/knowledge/schema.py`).
3. Corré `pytest tests/knowledge/` — valida el archivo completo (schema + referencias cruzadas + cobertura de las 5 dimensiones y los 4 arquetipos) contra el `knowledge/benchmark.yaml` real, no contra un fixture.
4. Si el cambio afecta cómo se combinan las skills o los folders (no solo qué dice cada uno), revisá también `pytest tests/engine/` — cubre las 216 combinaciones posibles de las 5 dimensiones.

Si el archivo no valida, la app **no arranca en silencio con datos parciales** — falla explícito (`BenchmarkLoadError`, ver `app/knowledge/loader.py` y `app/errors/knowledge_errors.py`), tal como exige [AGENTS.md](AGENTS.md).

## Deploy

Ver [Procfile](Procfile) / [railway.json](railway.json) para el deploy en Railway, y [`scripts/smoke_test.sh`](scripts/smoke_test.sh) para verificar un deploy ya arriba (`./scripts/smoke_test.sh https://tu-app.up.railway.app`).

## Licencia

MIT — ver [LICENSE](LICENSE).
