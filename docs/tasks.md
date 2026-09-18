# Tareas — Second Brain Starter

> Desglose ejecutable de [plan.md](./plan.md). Cada tarea es atómica, tiene un criterio de "done" verificable y declara los archivos que toca. Se ejecutan en orden; cada una se implementa, se describe y espera revisión antes de pasar a la siguiente. Los ítems (a)-(f) pedidos explícitamente están marcados junto al ID de tarea correspondiente.

---

## Fase 0 — Fundamentos del repo

### T00 — Inicializar repositorio git
- **Descripción:** `git init` en la raíz del proyecto (actualmente no es un repo git), rama inicial `main`.
- **Archivos:** `.git/` (creado por el comando, no editado a mano).
- **Criterio de done:** `git status` funciona dentro del proyecto; existe un primer commit vacío o con `.gitignore`.

### T01 — Estructura de carpetas base
- **Descripción:** Crear el layout del proyecto: `app/` (código de aplicación), `knowledge/` (base de conocimiento), `tests/`, `docs/` (ya existe).
- **Archivos:** `app/__init__.py`, `knowledge/.gitkeep`, `tests/__init__.py`.
- **Criterio de done:** La estructura de carpetas existe y es importable como paquete Python (`app` es un paquete válido).

### T02 — Licencia y metadatos del repo
- **Descripción:** Añadir `LICENSE` (MIT) y un `README.md` mínimo (nombre, una línea de descripción, badge de licencia) en la raíz.
- **Archivos:** `LICENSE`, `README.md`.
- **Criterio de done:** `LICENSE` contiene el texto estándar MIT con el año y el titular correctos; `README.md` referencia `docs/SPEC.md`.

### T03 — Gestión de dependencias
- **Descripción:** Definir `pyproject.toml` (o `requirements.txt` + `requirements-dev.txt`) fijando Python 3.11 y las dependencias identificadas en `plan.md` (FastAPI, SDK de MCP, Pydantic v2, PyYAML, jsonschema, pytest, httpx, uvicorn). Pinnear versión exacta del SDK de MCP.
- **Archivos:** `pyproject.toml` (o `requirements*.txt`).
- **Criterio de done:** `pip install -e .` (o `pip install -r requirements.txt`) resuelve sin conflictos en un entorno Python 3.11 limpio.

### T04 — Config de linting/formato y `.gitignore`
- **Descripción:** `.gitignore` (venv, `__pycache__`, `.env`, artefactos de build) + config de `ruff`/`black` (o el linter que se decida) con reglas mínimas.
- **Archivos:** `.gitignore`, `pyproject.toml` (sección de tool config) o `.ruff.toml`.
- **Criterio de done:** El linter corre sin configuración adicional y no falla sobre un repo vacío.

### T04.5 — `AGENTS.md` con invariantes de arquitectura
- **Descripción:** Crear `AGENTS.md` en la raíz del repo documentando las invariantes que cualquier cambio futuro (humano o agente) debe respetar, tal como las fija el spec:
  - **Motor sin LLM**: la decisión de arquetipo/estructura/skills es 100% determinística; un LLM puede tocar únicamente el *tono* del texto de salida en iteraciones futuras, nunca la lógica de decisión (Soberanía de Tokens, T1).
  - **Engine único importado por ambos canales**: `app/engine/*` es la única fuente de la lógica de decisión; ni `app/channels/rest.py` ni `app/channels/mcp_server.py` pueden reimplementarla — solo adaptar entrada/salida.
  - **Determinismo**: mismo input → mismo output siempre, sin estado, sin aleatoriedad, sin dependencias de reloj/orden de ejecución en la lógica de decisión.
  - **Sin fallback silencioso**: si `knowledge/benchmark.yaml` falta o no valida, el sistema falla explícito (ver Fase 4) — nunca sirve una recomendación parcial o inventada.
  Estas cuatro invariantes deben quedar redactadas como reglas verificables (no como narrativa), para que sirvan de checklist en revisiones de código posteriores.
- **Archivos:** `AGENTS.md`.
- **Criterio de done:** `AGENTS.md` existe en la raíz, enumera las 4 invariantes de forma explícita y verificable, y cada una referencia la fase/tarea de `tasks.md` donde se implementa y se testea (p. ej. determinismo → T15, sin fallback silencioso → T19).

---

## Fase 1 — `knowledge/benchmark.yaml`

### T05 — Schema de `knowledge/benchmark.yaml` (a)
- **Descripción:** Diseñar el schema formal del archivo (como JSON Schema en `knowledge/benchmark.schema.json` o como modelos Pydantic en `app/knowledge/schema.py`) cubriendo, como mínimo:
  - `systems`: lista de metodologías/herramientas del benchmark (id, tipo, setup, mantenimiento, conecta_ideas, gestiona_accion, requiere_agente_ia, mejor_para, fuentes). Cada fila debe tener un `id`/`source_ref` estable porque ahora también es citada directamente por las líneas de `justification` del modificador `technical_profile` (no solo por `decision_rules`).
  - `archetypes`: los 4 arquetipos (id, nombre, descripción, estructura de carpetas, frontmatter_fields).
  - `dimensions`: las 5 dimensiones del diagnóstico con sus enums válidos (debe poder regenerar los enums de los modelos Pydantic de Fase 2 sin duplicar a mano). Incluye `capture_volume` y `technical_profile`, no solo las 3 dimensiones del árbol de arquetipo base.
  - `decision_rules`: la tabla de "Lógica de decisión" del spec expresada como datos — arquetipo base por dimensión 1, modificador híbrido por dimensión 3, modificador LYT por dimensión 2, **y los dos modificadores nuevos**: `capture_volume` (afecta `structure.folders` — agrega `Inbox/` en `daily_moderate`/`high_multi_source` — y, en `high_multi_source`, agrega la skill `clasificador-de-fuentes` con prioridad de reemplazo si ya hay 5 skills) y `technical_profile` (afecta solo `justification`, nunca `folders`/`skills`). Cada regla con un `source_ref` citable.
  - `skills_catalog`: skills iniciales por arquetipo (name, description, format), 3-5 por arquetipo, **más la nueva entrada `clasificador-de-fuentes`** (disponible para los 4 arquetipos, no ligada a uno solo, con un campo de prioridad/orden que permite reemplazar la skill de menor prioridad del set base cuando `capture_volume == "high_multi_source"` y ya hay 5 seleccionadas).
  - `sources`: lista de fuentes citadas en `docs/BENCHMARK.md` (id, descripción, url) para que `decision_rules` y `systems` referencien un `source_ref` válido — incluye los `source_ref` que sustentan las dos líneas de `justification` de `technical_profile` (`markdown_git_comfortable` y `prefers_visual_ui`, esta última citando la fila de `systems` correspondiente al arquetipo resultante).
- **Archivos:** `knowledge/benchmark.schema.json` (o `app/knowledge/schema.py`), `docs/plan.md` (sin cambios, solo referencia).
- **Criterio de done:** El schema está escrito y documentado (comentarios o descripciones por campo); cada tipo de dato del schema tiene un ejemplo mínimo en la propia definición o en un archivo de ejemplo separado; el schema admite explícitamente la entrada `clasificador-de-fuentes` en `skills_catalog` y los `source_ref` de `technical_profile` sin necesitar una extensión posterior.

### T06 — Conversión de `docs/BENCHMARK.md` a `knowledge/benchmark.yaml`
- **Descripción:** Transcribir el contenido de `docs/BENCHMARK.md` (tabla comparativa, los 3 arquetipos + híbrido, las 5 dimensiones, el mapeo arquetipo→estructura→skills) al formato definido en T05. Ningún dato nuevo se inventa; todo lo que no está en el BENCHMARK explícitamente (p. ej. ids técnicos) se deriva de forma mecánica (slugify de nombres). Además, siguiendo la sección "Lógica de decisión" actualizada del spec:
  - Agregar la skill `clasificador-de-fuentes` a `skills_catalog`, disponible para los 4 arquetipos, con la metadata de prioridad que T14 necesita para el reemplazo en `high_multi_source`.
  - Agregar en `sources`/`decision_rules` los `source_ref` de las dos líneas de `justification` del modificador `technical_profile`: uno para la recomendación de archivos planos + git (`markdown_git_comfortable`), y uno por cada fila de `systems` que pueda citarse como herramienta visual por arquetipo (`prefers_visual_ui` — p. ej. Obsidian/Notion/Tana según corresponda).
- **Archivos:** `knowledge/benchmark.yaml`.
- **Criterio de done:** El archivo existe, es YAML válido, valida contra el schema de T05, y cada arquetipo/regla/skill —incluida `clasificador-de-fuentes` y los `source_ref` nuevos de `technical_profile`— es rastreable línea a línea a una fila o sección de `docs/BENCHMARK.md` o del propio spec actualizado.

### T07 — Loader y validador de `knowledge/benchmark.yaml`
- **Descripción:** Función/módulo que carga el YAML al arrancar la app, lo valida contra el schema de T05, y falla de forma explícita y temprana (excepción clara, sin fallback) si el archivo no existe, no parsea, o no valida contra el schema. Esta función es la que luego usa el estado de error 500 del spec (Fase 4), pero aquí solo se implementa el loader puro.
- **Archivos:** `app/knowledge/loader.py`.
- **Criterio de done:** Cargar un YAML válido devuelve un objeto Python tipado; cargar un YAML corrupto o que no valida contra el schema lanza una excepción con mensaje explícito (no un error genérico de parseo).

### T08 — Test: `knowledge/benchmark.yaml` válido
- **Descripción:** Test que carga el `knowledge/benchmark.yaml` real del repo (no un fixture) con el loader de T07 y verifica que valida sin errores.
- **Archivos:** `tests/knowledge/test_benchmark_yaml.py`.
- **Criterio de done:** `pytest tests/knowledge/test_benchmark_yaml.py` pasa contra el archivo real del repo.

---

## Fase 2 — Modelos de dominio compartidos

### T09 — Modelos Pydantic de entrada y salida
- **Descripción:** `DiagnoseRequest` (los 5 campos con sus enums, según "Esquema de datos" del spec) y `DiagnoseResponse` (`archetype`, `justification`, `structure`, `skills`), como modelos Pydantic v2. Los enums de `DiagnoseRequest` deben coincidir exactamente con los valores listados en el spec (`execute_projects`, `produce_knowledge`, `agent_memory`, `study`, etc.).
- **Archivos:** `app/models/diagnose.py`.
- **Criterio de done:** Instanciar `DiagnoseRequest` y `DiagnoseResponse` con los ejemplos JSON del spec (sección "Esquema de datos") no lanza errores de validación; instanciar con un valor fuera de enum sí lanza `ValidationError`.

### T10 — JSON Schema exportado de los modelos
- **Descripción:** Función que exporta el `model_json_schema()` de `DiagnoseRequest` y `DiagnoseResponse` a un artefacto reutilizable (archivo o función pública) — este es "el mismo JSON Schema" que el spec exige que valide tanto al cliente MCP como al REST.
- **Archivos:** `app/models/schema_export.py` (o función expuesta en `app/models/diagnose.py`).
- **Criterio de done:** El JSON Schema exportado es válido (parsea como JSON Schema draft usado por Pydantic v2) y contiene los mismos campos/enums que T09.

### T11 — Test de modelos de dominio
- **Descripción:** Tests que instancian los modelos con los ejemplos exactos del spec y verifican round-trip de serialización (`model_dump_json` → `model_validate_json`).
- **Archivos:** `tests/models/test_diagnose_models.py`.
- **Criterio de done:** Tests pasan; incluyen al menos un caso por cada enum inválido esperando `ValidationError`.

---

## Fase 3 — Motor de reglas determinístico

### T12 — Árbol de decisión completo (b)
- **Descripción:** Implementar la función `decide_archetype(request: DiagnoseRequest, benchmark) -> ArchetypeDecision` que aplica exactamente la lógica de la sección "Lógica de decisión" del spec:
  - Arquetipo base por Dimensión 1 (`purpose`): `execute_projects` → `action_first`; `produce_knowledge` o `study` → `knowledge_first` (con nota textual distinta para `study`, sin arquetipo propio); `agent_memory` → `agent_first`.
  - Modificador agent-native: si `agent_usage` ∈ {`already_using`, `want_to_start`}, el resultado final es `hybrid` sobre cualquier arquetipo base.
  - Modificador LYT-vs-Zettelkasten: si arquetipo base es `knowledge_first` y `maintenance_tolerance == "low"`, se anota preferencia por LYT/MOCs en vez de Zettelkasten puro (esto afecta la estructura devuelta, no el `archetype` de salida).
  - Debe resolver sin excepción **todas** las combinaciones del producto cartesiano de los 5 enums de entrada, no solo el "caso feliz" de la tabla.
- **Archivos:** `app/engine/decision.py`.
- **Criterio de done:** Función pura, sin I/O ni dependencia de FastAPI/MCP; cubre los 4 casos base + el modificador híbrido + el modificador LYT, verificable con los ejemplos manuales de la sección "Criterios de aceptación" del spec.

### T13 — Justificación trazable al benchmark (incluye modificador `technical_profile`)
- **Descripción:** Función que, dada la decisión de T12, arma la lista `justification: string[]` citando el `source_ref`/id de `knowledge/benchmark.yaml` que sustenta cada afirmación (no texto libre inventado). Además de las líneas propias del arquetipo/modificadores híbrido/LYT, aplica el modificador de `technical_profile` de las 5 dimensiones (el spec ahora usa las 5, no solo 3):
  - `markdown_git_comfortable` → agrega una línea citando el `source_ref` de recomendación de archivos planos + git.
  - `prefers_visual_ui` → agrega una línea citando el `source_ref` de la fila de `systems` correspondiente a una herramienta visual para el arquetipo resultante (p. ej. Obsidian/Notion/Tana según arquetipo, no una herramienta fija para todos).
  Este modificador **nunca** toca `structure.folders` ni `skills` — solo agrega texto a `justification`, manteniendo la recomendación agnóstica de herramienta tal como exige el spec.
- **Archivos:** `app/engine/justification.py`.
- **Criterio de done:** Cada string de `justification` para cada arquetipo posible contiene una referencia verificable a un id existente en `knowledge/benchmark.yaml`; para cada uno de los dos valores de `technical_profile`, la línea correspondiente aparece exactamente una vez y cita un `source_ref` distinto según el arquetipo (verificado en T15/T16); cambiar `technical_profile` entre los dos valores válidos, con el resto del input fijo, no cambia `structure` ni `skills`, solo `justification`.

### T14 — Armado de `structure` y `skills` (incluye modificador `capture_volume`)
- **Descripción:** Función que, dado el arquetipo final (incluido el caso híbrido y el modificador LYT), arma `structure.folders`, `structure.frontmatter_fields` y selecciona entre 3 y 5 `skills` del `skills_catalog` de `knowledge/benchmark.yaml` (combinando los sets de los arquetipos base cuando el resultado es híbrido, según el spec: "Combinación de los tres sets anteriores, priorizada por la respuesta a la dimensión 1"). Sobre ese resultado base, aplica el modificador de `capture_volume`:
  - `sporadic` → sin cambios sobre `structure.folders` ni `skills`.
  - `daily_moderate` → agrega `Inbox/` a `structure.folders` (si el arquetipo no la tiene ya).
  - `high_multi_source` → agrega `Inbox/` a `structure.folders` (igual que `daily_moderate`) **y además** incluye la skill `clasificador-de-fuentes` en `skills`; si el set ya tiene 5 skills, reemplaza la de menor prioridad del `skills_catalog` para mantenerse en el rango 3-5, sin superar 5 ni bajar de 3.
- **Archivos:** `app/engine/structure.py`.
- **Criterio de done:** Para cada uno de los 4 arquetipos de salida, la función devuelve `folders` no vacío, `frontmatter_fields` no vacío, y entre 3 y 5 `skills`; para `capture_volume in {daily_moderate, high_multi_source}`, `folders` contiene `Inbox/`; para `capture_volume == "high_multi_source"`, `skills` contiene `clasificador-de-fuentes` y la lista sigue teniendo entre 3 y 5 elementos.

### T15 — Test: determinismo
- **Descripción:** Test que llama al engine completo (T12+T13+T14 encadenados, o una función `diagnose()` que las orquesta) dos veces con el mismo input y verifica igualdad exacta (`==`) del resultado completo, para varios inputs distintos.
- **Archivos:** `tests/engine/test_determinism.py`.
- **Criterio de done:** Test pasa para al menos un caso por cada arquetipo de salida (`action_first`, `knowledge_first`, `agent_first`, `hybrid`).

### T16 — Test: cobertura combinatoria
- **Descripción:** Test que itera el producto cartesiano completo de los enums válidos de los 5 campos de entrada (4×3×3×3×2 = 216 combinaciones) y verifica que el engine resuelve cada una a un `DiagnoseResponse` válido, sin excepción y validando contra el JSON Schema de T10.
- **Archivos:** `tests/engine/test_coverage.py`.
- **Criterio de done:** Test pasa sobre las 216 combinaciones sin excepciones ni fallos de validación de schema, y además asertan explícitamente:
  - Si `capture_volume ∈ {daily_moderate, high_multi_source}` → `structure.folders` contiene `"Inbox/"`.
  - Si `capture_volume == "high_multi_source"` → `skills` contiene `"clasificador-de-fuentes"` y `3 ≤ len(skills) ≤ 5`.
  - Para todo par de inputs idénticos salvo `technical_profile` → `structure` y `skills` son idénticos entre ambos, solo `justification` difiere.

---

## Fase 4 — Validación y estados de error

### T17 — Error: campos obligatorios faltantes (c)
- **Descripción:** Capa de validación de request cruda (antes de Pydantic o capturando su `ValidationError`) que, ante campos faltantes, produce un error estructurado equivalente a `422` con la lista exacta de campos faltantes.
- **Archivos:** `app/errors/validation.py`.
- **Criterio de done:** Dado un payload con 1-2 campos faltantes, el error estructurado lista exactamente esos campos, ni más ni menos.

### T18 — Error: valor fuera de enum (c)
- **Descripción:** Sobre la misma capa de T17, distinguir el caso de campo presente pero con valor inválido, devolviendo un error equivalente a `400` con el nombre del campo y la lista de valores válidos para ese campo.
- **Archivos:** `app/errors/validation.py` (mismo módulo que T17).
- **Criterio de done:** Dado un payload con un valor fuera de enum en un campo, el error indica el campo y enumera exactamente los valores válidos de ese campo (tomados del modelo de Fase 2, no hardcodeados).

### T19 — Error: benchmark no disponible o corrupto (c)
- **Descripción:** Envolver el loader de T07 en el arranque de la app (y opcionalmente en un endpoint de salud) de forma que, si `knowledge/benchmark.yaml` falta o no valida, la app responde con un error equivalente a `500` con mensaje explícito, y **nunca** sirve una recomendación con datos parciales o de fallback.
- **Archivos:** `app/errors/knowledge_errors.py`, integración en `app/main.py` (definido en Fase 5).
- **Criterio de done:** Con el archivo movido/renombrado o con YAML corrupto, cualquier intento de diagnóstico falla explícitamente en vez de responder 200 con datos incompletos.

### T20 — Test: los 4 estados de error (c)
- **Descripción:** Suite de tests que fuerza cada uno de los 4 estados de error del spec de forma aislada (campos faltantes, enum inválido, benchmark corrupto/ausente, mismatch de schema — este último se completa junto con T29 de Fase 7) y verifica el código/forma exacta del error.
- **Archivos:** `tests/errors/test_error_states.py`.
- **Criterio de done:** 4 tests, uno por estado de error, todos pasando; cada uno verifica tanto el "código" del error como el contenido explicado en el spec (lista de campos / campo+enums válidos / mensaje explícito).

---

## Fase 5 — API REST + OpenAPI

### T21 — App FastAPI + endpoint `POST /diagnose` (d)
- **Descripción:** `app/main.py` con la instancia de FastAPI, y `app/channels/rest.py` (patrón de abstracción de canal, análogo a `app/channel.py` de Rikra pero sin código compartido) que expone `POST /diagnose`, delegando toda la lógica al engine de Fase 3 y a los modelos de Fase 2. El canal REST no debe contener lógica de decisión, solo adaptación HTTP.
- **Archivos:** `app/main.py`, `app/channels/rest.py`.
- **Criterio de done:** `uvicorn app.main:app` arranca; `POST /diagnose` con el payload de ejemplo del spec devuelve el JSON de ejemplo del spec (mismos campos, arquetipo correcto).

### T22 — OpenAPI 3.x compatible con GPT Actions (d)
- **Descripción:** Verificar y, si hace falta, ajustar el schema autogenerado por FastAPI en `/openapi.json` (metadata, `operationId` único y descriptivo, descripciones de cada campo) contra los requisitos conocidos de Custom GPT Actions.
- **Archivos:** `app/main.py` (metadata), posible `app/openapi_overrides.py`.
- **Criterio de done:** `/openapi.json` es servido, es OpenAPI 3.x válido, y no usa construcciones no soportadas por GPT Actions (verificación manual documentada en el mensaje de descripción de cambios de esta tarea).

### T23 — Mapeo de errores del engine a HTTP (d)
- **Descripción:** Exception handlers de FastAPI que traducen los errores estructurados de Fase 4 a las respuestas HTTP exactas del spec (422/400/500) con el body estructurado correspondiente.
- **Archivos:** `app/channels/rest.py` o `app/main.py` (exception handlers).
- **Criterio de done:** Los 4 tests de error de T20, ejecutados vía `TestClient` contra el endpoint REST, devuelven el código HTTP y el body esperados.

### T24 — Test de integración REST (d)
- **Descripción:** Tests de integración end-to-end sobre el endpoint REST: casos felices (uno por arquetipo) + los 4 estados de error, usando `httpx`/`TestClient`.
- **Archivos:** `tests/channels/test_rest.py`.
- **Criterio de done:** Suite pasa completa contra la app real (no mocks del engine).

---

## Fase 6 — MCP server nativo

### T25 — MCP server sobre el mismo engine (e)
- **Descripción:** `app/channels/mcp_server.py` que expone `/mcp` con una tool `diagnose` (nombre a definir) que recibe los mismos 5 campos, invoca el **mismo** engine de Fase 3 con los **mismos** modelos de Fase 2 (sin reimplementar la lógica de decisión), y devuelve la misma forma de `DiagnoseResponse`.
- **Archivos:** `app/channels/mcp_server.py`, montaje en `app/main.py`.
- **Criterio de done:** Un cliente MCP de prueba puede listar la tool `diagnose`, invocarla con el payload de ejemplo del spec, y recibir de vuelta un resultado estructuralmente idéntico al de T21.

### T26 — Mapeo de errores del engine a MCP (e)
- **Descripción:** Traducir los mismos errores estructurados de Fase 4 al formato de error nativo del SDK de MCP, preservando la misma información (campos faltantes / campo+enums válidos / mensaje explícito de benchmark corrupto).
- **Archivos:** `app/channels/mcp_server.py`.
- **Criterio de done:** Los 4 casos de error de T20, invocados vía la tool MCP, devuelven un error MCP con el mismo contenido semántico que su contraparte REST (verificado en Fase 7).

### T27 — Test de integración MCP (e)
- **Descripción:** Tests de integración sobre el servidor MCP: casos felices (uno por arquetipo) + los 4 estados de error, usando el cliente de test del SDK de MCP.
- **Archivos:** `tests/channels/test_mcp.py`.
- **Criterio de done:** Suite pasa completa contra el servidor MCP real (no mocks del engine).

---

## Fase 7 — Paridad MCP/REST

### T28 — Test de paridad de salidas (f)
- **Descripción:** Test parametrizado que, para un conjunto representativo de inputs (al menos uno por arquetipo + casos límite de los modificadores híbrido/LYT), invoca **el mismo input** contra el canal REST (T21) y contra el canal MCP (T25), y compara ambos resultados por igualdad estructural exacta (mismo `archetype`, misma `justification`, misma `structure`, mismos `skills`, mismo orden).
- **Archivos:** `tests/parity/test_rest_mcp_parity.py`.
- **Criterio de done:** Test pasa para todos los casos del set representativo; cualquier divergencia entre canales lo hace fallar explícitamente (no comparación parcial).

### T29 — Test de paridad de errores y de schema (f)
- **Descripción:** Extensión de T28 (o archivo hermano) que, para los 4 estados de error, invoca el mismo input inválido contra ambos canales y verifica que el contenido del error es equivalente en ambos, y que tanto la salida feliz como la de error de ambos canales validan contra el JSON Schema exportado en T10. Esto completa el estado de error "mismatch de schema" pendiente de T20.
- **Archivos:** `tests/parity/test_rest_mcp_parity.py` (o `tests/parity/test_schema_validity.py`).
- **Criterio de done:** Test pasa; cubre los 4 estados de error en ambos canales y valida contra schema en ambos canales para al menos un caso feliz por arquetipo.

---

## Fase 8 — Catálogo de skills

### T30 — Test: catálogo de skills por arquetipo
- **Descripción:** Test que, para cada uno de los 4 arquetipos de salida (incluido híbrido), verifica que las `skills` devueltas están entre 3 y 5, todas presentes en `skills_catalog` de `knowledge/benchmark.yaml`, y que el caso híbrido efectivamente combina skills de más de un arquetipo base.
- **Archivos:** `tests/engine/test_skills_catalog.py`.
- **Criterio de done:** Test pasa para los 4 arquetipos.

---

## Fase 9 — Deploy en Render

> Segundo cambio de plataforma (decisión de Luigui): Render en vez de Koyeb — Koyeb eliminó su plan gratuito al ser adquirida por Mistral AI (feb 2026), dejó de ser viable. Historial: Railway → Koyeb → Render. El `Dockerfile` de T31 (ya construido y verificado con Docker real) **no cambia** — Render lo despliega directo, detectándolo automáticamente en la raíz del repo, sin reescribir nada de la imagen. La configuración de red del canal MCP (`TransportSecuritySettings` en `app/main.py`) sigue leyendo `PUBLIC_BASE_URL`, una variable de entorno genérica configurada a mano — no depende de nada auto-inyectado por ninguna plataforma, así que este segundo swap tampoco toca código.

### T31 — Configuración de arranque para Render (Dockerfile, sin cambios)
- **Descripción:** El `Dockerfile` existente no se modifica — Render lo detecta automáticamente en la raíz del repo y lo usa como build method sin selección manual de builder. Solo cambia el flujo documentado: Render dashboard → **New** → **Web Service** → conectar el repo de GitHub → Render detecta el `Dockerfile` automáticamente → configurar `PUBLIC_BASE_URL` con el dominio que Render asigna (`https://<app>.onrender.com`, o dominio custom) → health check en `/health`. Actualizar `README.md` con este flujo (reemplazando el de Koyeb).
- **Archivos:** `Dockerfile` (sin cambios), `.env.example` (sin cambios, sigue siendo genérico), `README.md` (sección de deploy).
- **Criterio de done:** `docker build` + `docker run` local levanta la app y responde en `/health` y `/docs` con el mismo comando que usaría Render (ya verificado con Docker real en la ejecución anterior de T31, sigue vigente sin cambios); deploy manual en un servicio Render de prueba levanta la app y responde en `/` o `/docs`; `app/main.py` sigue sin referenciar ninguna variable de entorno auto-inyectada específica de una plataforma — solo `PUBLIC_BASE_URL`, configurada a mano.

### T32 — Smoke test post-deploy (contra Render)
- **Descripción:** Mismo smoke test de siempre — sin cambios de contenido ni de lógica, solo de destino: `GET /health`, `POST /diagnose` con un caso feliz, y una conexión de prueba (`initialize`) a `/mcp`. Se ejecuta contra la URL pública que asigna Render (`https://<app>.onrender.com` o el dominio custom configurado), no contra Koyeb. Tener en cuenta el sleep tras inactividad del free tier de Render: el primer request post-sleep puede tardar más (cold start) — no es una falla del smoke test si el primer intento tarda y uno posterior no.
- **Archivos:** `scripts/smoke_test.sh` (sin cambios de lógica; revisar que los ejemplos de uso en sus comentarios y en `README.md` citen una URL de Render, no de Koyeb).
- **Criterio de done:** Los 3 checks pasan contra el deploy real en Render.

---

## Fase 10 — Documentación y cierre

### T33 — README de uso
- **Descripción:** Ampliar `README.md` con: quickstart local, ejemplo `curl` de `POST /diagnose`, ejemplo de invocación MCP, instrucciones para editar `knowledge/benchmark.yaml` sin tocar código, y nota de licencia MIT.
- **Archivos:** `README.md`.
- **Criterio de done:** Siguiendo el README desde cero (clonar + instalar + correr), un tercero puede invocar ambos canales sin leer el código.

### T34 — Tag de versión inicial
- **Descripción:** Commit final de cierre de la iteración 1 y tag `v1.0.0` (o el que se acuerde), con un `CHANGELOG.md` mínimo resumiendo el alcance de esta iteración.
- **Archivos:** `CHANGELOG.md`, tag de git.
- **Criterio de done:** `git tag` lista la versión; `CHANGELOG.md` referencia las fases 0-9 como completadas y menciona explícitamente lo que queda para Iteración 2 (según "Fuera de alcance" del spec).

---

## Resumen de cobertura de los requisitos explícitos

| Requisito del encargo | Tareas |
|---|---|
| (a) Schema de `knowledge/benchmark.yaml` | T05, T06 |
| (b) Motor de reglas determinístico según "Lógica de decisión" (5 dimensiones, incluidos los modificadores `capture_volume` y `technical_profile`) | T12, T13, T14, T15, T16 |
| (c) Validación de los 4 estados de error | T17, T18, T19, T20 |
| (d) Endpoint REST + OpenAPI | T21, T22, T23, T24 |
| (e) MCP server | T25, T26, T27 |
| (f) Tests de paridad MCP/REST | T28, T29 |
| Invariantes de arquitectura (`AGENTS.md`): sin LLM, engine único, determinismo, sin fallback silencioso | T04.5 |

## Aprobación requerida

Ninguna tarea se ejecuta hasta que `plan.md` y este archivo sean aprobados. Una vez aprobados, se ejecutan en el orden T00→T34, y cada una se implementa, se describe y espera revisión antes de continuar con la siguiente.
