# Changelog

## v1.0.0 — Iteración 1 (MVP)

Implementación completa de [docs/SPEC.md](docs/SPEC.md), Iteración 1, siguiendo el plan de [docs/plan.md](docs/plan.md) y el desglose de [docs/tasks.md](docs/tasks.md) (T00→T34).

### Incluido

- **`knowledge/benchmark.yaml`**: base de conocimiento versionada — 8 fuentes, 8 sistemas/metodologías, 4 arquetipos, las 5 dimensiones del diagnóstico, la tabla completa de reglas de decisión (arquetipo base + modificadores híbrido, LYT, `capture_volume` y `technical_profile`) y 11 skills iniciales. Schema formal en `app/knowledge/schema.py`, con validación de referencias cruzadas.
- **Motor de reglas determinístico** (`app/engine/`): árbol de decisión que cubre las 216 combinaciones posibles de las 5 dimensiones sin excepción, sin LLM en el core. Mismo input → mismo output siempre (verificado por test).
- **Los 4 estados de error** del spec: campos faltantes (422), valor fuera de enum (400), benchmark no disponible/corrupto (500, sin fallback silencioso), y mismatch de schema entre canales (400 en ambos por igual).
- **API REST + OpenAPI** (`app/channels/rest.py`, `app/main.py`): `POST /diagnose`, OpenAPI 3.1.0 verificado compatible con Custom GPT Actions.
- **MCP server nativo** (`app/channels/mcp_server.py`), montado en `/mcp`: tool `diagnose` sobre el SDK oficial (`mcp==2.2.0`), mismo engine que REST.
- **Paridad MCP/REST verificada por test**: mismo input → salida estructuralmente idéntica en ambos canales, en casos felices y en los 3 estados de error verificables a este nivel.
- **`AGENTS.md`**: invariantes de arquitectura (motor sin LLM, engine único, determinismo, sin fallback silencioso).
- **Deploy**: `Procfile` + `railway.json` para Railway, `scripts/smoke_test.sh` para verificar un deploy arriba.
- 403 tests, `ruff check .` limpio.

### Pendiente de verificación manual

- El deploy real en Railway no se ejecutó desde este entorno (requiere una cuenta/proyecto Railway) — la configuración de arranque se verificó localmente con el comando exacto que usaría Railway (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`).

### Fuera de esta iteración (ver docs/SPEC.md, "Alcance por iteración" e "Iteración 2")

- Skills iniciales como `SKILL.md` ejecutables (v1 las entrega como markdown descriptivo).
- Modo "audita mi vault existente" (v1 es standalone, no lee archivos reales).
- Personalización de tono de salida vía LLM opcional (v1 no usa LLM en absoluto).
- Arquetipos de estudio dedicados (Cornell/Outline) — `purpose == study` mapea a Conocimiento-primero con una nota textual, sin arquetipo propio.
- Cuentas de usuario, persistencia del diagnóstico, sync/almacenamiento de notas.
