# Changelog

## v2.0.0 — Renombrado breaking: diagnose → plan

**Breaking change de la API pública.** Motivo (docs/SPEC.md, "Historial de renombres"): "diagnóstico" implica evaluar algo existente, y esta herramienta es para crear un Segundo Cerebro desde cero, no para auditar uno que ya existe. El encuadre equivocado podía llevar al agente llamador a explorar el sistema de archivos del usuario buscando "algo que diagnosticar" — exactamente lo que esta tool nunca hace (todo el input viaja explícito en la llamada). La lógica de decisión, el motor de reglas y `knowledge/benchmark.yaml` **no cambiaron de comportamiento** — solo de nombre.

### Cambios

- **REST**: `POST /diagnose` → `POST /plan`. `operationId` de OpenAPI: `diagnoseSecondBrain` → `createSecondBrainPlan`.
- **MCP**: tool `diagnose` → `create_second_brain_plan`.
- **Modelos**: `DiagnoseRequest`/`DiagnoseResponse` → `CreateSecondBrainPlanRequest`/`CreateSecondBrainPlanResponse` (`app/models/diagnose.py` → `app/models/plan.py`).
- **Engine**: `app.engine.diagnose()` → `app.engine.create_plan()`.
- **Validación**: `validate_diagnose_request()` → `validate_create_plan_request()`.
- **Contrato de interacción con el agente llamador** (nuevo, docs/SPEC.md): la descripción del tool (MCP y OpenAPI) — el texto que lee el agente llamador, no un comentario interno — ahora instruye explícitamente:
  1. Si faltan respuestas, preguntarlas en lenguaje natural usando el texto exacto de "Copy de las preguntas", nunca inferirlas ni asumir defaults.
  2. Nunca leer archivos ni explorar el sistema de archivos del usuario para completarlas — todo el input viaja explícito en la llamada.
  3. Encuadrar la conversación como "crear/armar" el Segundo Cerebro, nunca como "diagnosticar/evaluar" uno existente.

  `TOOL_DESCRIPTION` vive en `app/channels/__init__.py`, compartido por ambos canales — no hay dos copias del texto que puedan divergir.

### Verificado

- Suite completa (407 tests) y `ruff check .` en verde tras el renombrado.
- Probado en vivo contra un servidor local real: `POST /plan` responde, `POST /diagnose` da 404, y la tool MCP `create_second_brain_plan` lista con la descripción completa (incluidas las 5 preguntas).

### No cambia

- La lógica de decisión, `knowledge/benchmark.yaml`, los estados de error, y la paridad MCP/REST — mismo comportamiento, verificado por la misma suite de tests (renombrada, no reescrita).

## v1.0.1 — Deploy final en Render (patch, sin cambios de código)

Patch release: solo se resuelve dónde y cómo se despliega la app. Ningún archivo de `app/`, `tests/`, ni la lógica del motor de reglas cambió respecto a v1.0.0 — mismo `Dockerfile` de T31 en los tres intentos de plataforma.

### Secuencia real de plataforma de deploy

La plataforma de deploy cambió tres veces antes de asentarse; se documenta acá tal cual pasó, no como si siempre hubiese sido Render:

1. **Railway** (spec original, docs/SPEC.md inicial) — descartada antes de deployar: costo, requiere plan pago para uso sostenido.
2. **Koyeb** (adoptada para v1.0.0) — descartada en feb 2026: eliminó su plan gratuito al ser adquirida por Mistral AI, dejó de ser viable.
3. **Render** (final) — confirmado en producción: **https://second-brain-starter.onrender.com**. Free tier con tarjeta solo para verificación de $1 (reembolsado) y sleep tras inactividad (cold start de ~40-60s en el primer request tras un período inactivo).

### Verificado

- Smoke test real (`scripts/smoke_test.sh`) contra el deploy de Render: los 3 checks (`GET /health`, `POST /diagnose`, `POST /mcp`) pasan.
- `README.md`, `.env.example` y los comentarios de `app/main.py` actualizados al flujo real de Render (dashboard **New → Web Service** → conectar GitHub → Docker autodetectado → `PUBLIC_BASE_URL` → health check en `/health`).
- Resuelve el punto "Pendiente de verificación manual" de v1.0.0 — el deploy real ya se ejecutó y se verificó, en Render en vez de en Koyeb.

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
- **Deploy**: `Dockerfile` para Koyeb, `scripts/smoke_test.sh` para verificar un deploy arriba.
- 403 tests, `ruff check .` limpio.

### Pendiente de verificación manual

- El deploy real en Koyeb no se ejecutó desde este entorno (requiere una cuenta/proyecto Koyeb) — la configuración de arranque se verificó con un `docker build` + `docker run` real del `Dockerfile` del repo (mismo comando de arranque que usaría Koyeb: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).

### Fuera de esta iteración (ver docs/SPEC.md, "Alcance por iteración" e "Iteración 2")

- Skills iniciales como `SKILL.md` ejecutables (v1 las entrega como markdown descriptivo).
- Modo "audita mi vault existente" (v1 es standalone, no lee archivos reales).
- Personalización de tono de salida vía LLM opcional (v1 no usa LLM en absoluto).
- Arquetipos de estudio dedicados (Cornell/Outline) — `purpose == study` mapea a Conocimiento-primero con una nota textual, sin arquetipo propio.
- Cuentas de usuario, persistencia del diagnóstico, sync/almacenamiento de notas.
