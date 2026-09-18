# Plan de implementación — Second Brain Starter

> Basado en [SPEC.md](./SPEC.md) y [BENCHMARK.md](./BENCHMARK.md). Este documento no contiene código, solo la secuencia de fases, dependencias y riesgos. El desglose ejecutable está en [tasks.md](./tasks.md).

## Overview del objetivo

Construir una herramienta open source (MIT, repo público) que:

1. Recibe respuestas a un diagnóstico de 5 dimensiones (ver Esquema de datos del spec).
2. Aplica un **motor de reglas determinístico, sin LLM**, sobre una base de conocimiento versionada (`knowledge/benchmark.yaml`) para decidir un arquetipo de Segundo Cerebro (Acción-primero, Conocimiento-primero, Agente-primero o Híbrido).
3. Devuelve arquetipo + justificación trazable al benchmark + estructura de carpetas/frontmatter + 3-5 skills iniciales.
4. Expone esa misma lógica por **dos canales equivalentes**: MCP server nativo (`/mcp`) y API REST con OpenAPI 3.x (compatible con Custom GPT Actions) — mismo input, misma salida, mismo JSON Schema de validación.
5. Se despliega en Render.

El criterio de éxito técnico no es solo "que responda", sino que:
- La decisión sea **100% reproducible** (mismo input → mismo output, siempre).
- Cada afirmación de la recomendación sea **citable** a una fila/sección de `knowledge/benchmark.yaml`, nunca a una heurística implícita en el código.
- MCP y REST sean **dos vistas del mismo engine**, no dos implementaciones paralelas que puedan divergir.
- Los 4 estados de error del spec estén cubiertos explícitamente, sin fallback silencioso.

## Fases de implementación (orden)

El orden respeta una regla explícita: **la base de conocimiento se congela en formato versionado antes de escribir el motor de reglas**, porque el motor consume ese archivo como fuente de verdad y cualquier cambio de forma después de escrito el engine obliga a retrabajo.

### Fase 0 — Fundamentos del repo
Estructura de carpetas, gestión de dependencias (Python 3.11), licencia MIT, control de versiones. Sin esto no hay dónde poner nada de lo que sigue. El directorio de trabajo actual no es un repo git — se inicializa aquí.

### Fase 1 — `knowledge/benchmark.yaml` (fuente de verdad versionada)
Diseño del schema del YAML (qué campos, qué relaciones entre sistemas/arquetipos/dimensiones/skills) y conversión de `docs/BENCHMARK.md` a ese formato. Incluye el loader que valida el archivo al arrancar la app. **Esta fase se completa y se congela antes de tocar el motor de reglas** — es el requisito explícito del encargo. El catálogo de skills iniciales (3-5 por arquetipo, formato `markdown_descriptive`) vive aquí como datos, no como código.

### Fase 2 — Modelos de dominio compartidos
Los modelos Pydantic de entrada/salida (el "mismo JSON Schema" que el spec exige que validen tanto MCP como REST) se definen antes del engine y antes de los dos canales, para que ambos canales los importen del mismo sitio en vez de redefinirlos.

### Fase 3 — Motor de reglas determinístico
Implementación del árbol de decisión completo de la sección "Lógica de decisión" del spec: arquetipo base por Dimensión 1, modificador agent-native por Dimensión 3, modificador LYT-vs-Zettelkasten por Dimensión 2 + arquetipo base Conocimiento-primero. Cubre todas las combinaciones relevantes, no solo el caso feliz. Depende de Fase 1 (lee `knowledge/benchmark.yaml`) y Fase 2 (habla en los modelos compartidos).

### Fase 4 — Validación y estados de error
Los 4 estados de error listados en el spec (422 campos faltantes, 400 enum inválido, 500 benchmark no disponible/corrupto, 400 mismatch de schema) implementados como capa explícita, reutilizable por ambos canales.

### Fase 5 — API REST + OpenAPI
Canal REST sobre el engine de Fase 3, con manejo de errores de Fase 4 y OpenAPI 3.x autogenerado. Sigue el patrón arquitectónico de Rikra (separación engine/canal, sin reutilizar su código).

### Fase 6 — MCP server nativo
Segundo canal (`/mcp`) sobre el **mismo** engine y los **mismos** modelos — no una reimplementación. Reutiliza el manejo de errores de Fase 4.

### Fase 7 — Paridad MCP/REST
Tests dedicados que prueban, para el mismo conjunto de inputs, que ambos canales devuelven salidas idénticas (incluyendo los mismos errores en los mismos casos). Requiere que Fase 5 y Fase 6 existan.

### Fase 8 — Verificación del catálogo de skills
Validación de que el motor selecciona entre 3 y 5 skills del catálogo de `knowledge/benchmark.yaml` para cada arquetipo, incluida la combinación del híbrido.

### Fase 9 — Deploy en Render
Configuración de arranque (Dockerfile + variables de entorno) y smoke test post-deploy. Render, no Koyeb: Koyeb eliminó su plan gratuito al ser adquirida por Mistral AI (feb 2026), dejó de ser viable (decisión de Luigui) — segundo cambio de plataforma después de Railway → Koyeb. Render free tier: tarjeta solo para verificación de $1 reembolsado, sleep tras inactividad. El Dockerfile explícito de T31 no cambia con este swap — es precisamente la portabilidad que justificó no depender del auto-detect de buildpacks de una plataforma específica.

### Fase 10 — Documentación y cierre
README de uso (quickstart REST + MCP), instrucciones de edición de `knowledge/benchmark.yaml` sin tocar código, y tag de versión inicial.

## Dependencias y riesgos identificados

### Dependencias técnicas
- **Python 3.11 + FastAPI**: define el canal REST y sirve OpenAPI 3.x nativo.
- **SDK de MCP en Python** (oficial, `modelcontextprotocol/python-sdk` o equivalente): a confirmar versión exacta en Fase 0/6 — es la pieza menos madura del stack y la que más probablemente tenga cambios de API entre versiones.
- **Pydantic v2**: modelos compartidos + generación de JSON Schema (Fase 2), base para validación compartida entre canales (spec: "Mismatch de schema... validación compartida vía el mismo JSON Schema").
- **PyYAML** (o `ruamel.yaml` si se necesita preservar comentarios/orden al editar el benchmark) + una librería de validación de schema (`jsonschema` o el propio Pydantic) para `knowledge/benchmark.yaml`.
- **pytest + httpx** (TestClient de FastAPI) para toda la capa de tests, incluida la paridad MCP/REST.
- **Render**: deploy (free tier, tarjeta solo para verificación de $1 reembolsado, sleep tras inactividad); variables de entorno y comando de arranque a definir en Fase 9. La configuración de arranque debe ser portable (Dockerfile explícito, sin variables auto-inyectadas específicas de una plataforma) para no acoplar el proyecto a Render más de lo necesario — ya evitó retrabajo en el swap Railway → Koyeb → Render, el mismo Dockerfile sirvió para los tres.

### Riesgos
1. **Duplicación de lógica entre MCP y REST.** Es el riesgo central del encargo (de ahí la Fase 7 explícita). Mitigación: Fases 3-6 obligan a que el engine sea un módulo único importado por ambos canales — ningún canal debe reimplementar la lógica de decisión ni el armado de la respuesta.
2. **El schema de `knowledge/benchmark.yaml` se diseña una sola vez "a ciegas".** Si el schema de Fase 1 no anticipa lo que el motor de reglas de Fase 3 necesita citar (ids de fuente, ids de sistema, etc.), hay que romper el schema después de escrito el engine. Mitigación: la Fase 1 debe leer el spec y el BENCHMARK completos antes de fijar el schema (ids explícitos para systems, archetypes, decision_rules y skills_catalog), y la conversión de contenido (T06) se revisa antes de aprobar la fase.
3. **Combinatoria de la lógica de decisión.** El spec dice "esto cubre las 4x2x2 combinaciones principales sin necesitar una matriz exhaustiva de 3^5 casos", pero la entrada real tiene 4×3×3×3×2 = 216 combinaciones posibles de enums. Sigue siendo el mismo total tras la actualización del spec — `capture_volume` y `technical_profile` no agregan dimensiones nuevas, formalizan modificadores sobre dimensiones que ya estaban en el Esquema de datos original. Lo que cambia es que ahora **las 5 dimensiones participan en la lógica de decisión** (antes solo 3 de las 5 afectaban el resultado; `capture_volume` y `technical_profile` viajaban en el input pero no se usaban), así que cada una de las 216 combinaciones debe producir una salida visiblemente distinta según al menos un modificador — ya no alcanza con verificar que el engine no lance excepción. Riesgo de que el árbol de decisión, escrito como reglas condicionales, (a) deje combinaciones sin arquetipo asignado, o (b) resuelva sin excepción pero ignorando silenciosamente `capture_volume`/`technical_profile` para algún subconjunto de casos (el modificador "no hace nada" en `sporadic`/caso base es válido, pero debe ser una decisión explícita de la regla, no una omisión). Mitigación: el test de cobertura (T16) no solo verifica que las 216 combinaciones resuelven a un arquetipo válido sin excepción, sino que valida el comportamiento esperado de cada modificador (T13 para `technical_profile` sobre `justification`, T14 para `capture_volume` sobre `folders`/`skills`) en cada combinación relevante.
4. **Madurez del SDK de MCP en Python.** Cambios de API entre versiones del SDK son más probables que en FastAPI. Mitigación: pinnear versión exacta en Fase 0, aislar el código específico del SDK en la capa de canal (Fase 6), nunca en el engine.
5. **OpenAPI compatible con Custom GPT Actions** tiene restricciones propias (sin `oneOf` complejos en algunos casos, límites de tamaño de schema, `operationId` únicos). Riesgo de que el schema autogenerado por FastAPI no sea válido tal cual para un GPT Action. Mitigación: verificación manual en Fase 5 (T22) contra los requisitos conocidos de GPT Actions, no solo contra el validador de OpenAPI genérico.
6. **Nombre del repo/dominio.** El spec marca como pregunta abierta no bloqueante verificar disponibilidad de "Second Brain Starter". No bloquea ninguna fase técnica; se deja como pendiente informativo antes de publicar.
7. **Alcance de las Métricas de éxito.** El spec lista métricas (% de sesiones completas, cobertura del benchmark, adopción MCP vs REST) que requieren telemetría o logging, pero v1 es explícitamente stateless y sin persistencia. No hay fase de instrumentación en este plan porque no está pedida como tarea de código en el spec — se deja anotado como gap conocido, no como riesgo de bloqueo.
8. **Variante de estudio (Cornell/Outline) fuera de alcance.** El spec es explícito en que Dimensión 1 = `study` mapea a Conocimiento-primero variante ligera *solo como nota textual*, sin arquetipo propio. Riesgo de ambigüedad al implementar el engine si no se trata `study` como alias de `produce_knowledge` con un texto adicional en la justificación. Se deja resuelto en el diseño del árbol de decisión de Fase 3, no como pregunta abierta.

## Aprobación requerida

Este plan y `tasks.md` deben ser aprobados por el humano antes de ejecutar ninguna tarea. Ninguna fase implica código escrito todavía.
