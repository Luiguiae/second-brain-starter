# AGENTS.md — Invariantes de arquitectura

Este archivo documenta las reglas que **cualquier cambio** a este repo — humano o agente — debe respetar. No son preferencias de estilo: son invariantes verificables. Si un cambio las rompe, el cambio está mal, no la regla.

Ver [docs/SPEC.md](docs/SPEC.md) para la especificación funcional completa y [docs/tasks.md](docs/tasks.md) para el desglose de tareas que implementa y testea cada invariante.

## 1. Motor sin LLM

La decisión de `archetype`, `structure` y `skills` es un árbol de reglas 100% determinístico sobre `knowledge/benchmark.yaml`. **Ningún LLM participa en la decisión del core**, en ninguna fase de esta iteración. Un LLM puede tocar, en una iteración futura fuera de este alcance, únicamente el *tono* del texto de salida — nunca qué arquetipo, estructura o skills se devuelven.

- **Motivo:** transparencia, costo cero por request, alineado a Soberanía de Tokens (T1) — ver spec, sección "Stack / restricciones técnicas".
- **Verificable en:** `app/engine/` no importa ningún SDK de LLM ni hace llamadas de red para decidir. Implementado en Fase 3 (T12-T14), testeado en T15-T16.
- **Regla de revisión:** cualquier PR que agregue una dependencia de LLM (Anthropic, OpenAI, etc.) dentro de `app/engine/` se rechaza, sin excepción, aunque el caso de uso parezca justificado.

## 2. Engine único importado por ambos canales

Toda la lógica de decisión vive en `app/engine/` y es el **único** lugar donde existe. `app/channels/rest.py` (Fase 5) y `app/channels/mcp_server.py` (Fase 6) son adaptadores de entrada/salida — parsean el transporte (HTTP o MCP), llaman al engine, y traducen la respuesta y los errores al formato del canal. Ninguno de los dos canales puede reimplementar, ni siquiera parcialmente, una regla de decisión, un armado de `structure`/`skills`, o una validación que ya existe en el engine.

- **Motivo:** es la garantía estructural de que MCP y REST no pueden divergir — el requisito explícito de paridad del spec ("DADO un cliente MCP... y un cliente REST... ambos reciben una respuesta que valida contra el mismo JSON Schema").
- **Verificable en:** ningún archivo bajo `app/channels/` contiene lógica condicional sobre los valores de `purpose`, `maintenance_tolerance`, `agent_usage`, `capture_volume` o `technical_profile` — esa lógica solo existe bajo `app/engine/`. Implementado en Fases 3, 5 y 6; testeado explícitamente en Fase 7 (T28-T29, tests de paridad MCP/REST).
- **Regla de revisión:** si un fix parece requerir tocar `app/channels/rest.py` y `app/channels/mcp_server.py` a la vez para el mismo bug de decisión, el fix está en el lugar equivocado — debe ir en `app/engine/`.

## 3. Determinismo

Mismo input → mismo output, siempre. El engine no tiene estado entre requests, no usa aleatoriedad, no depende del orden de ejecución ni del reloj del sistema para decidir.

- **Motivo:** criterio de aceptación explícito del spec ("DADO que el mismo input se envía dos veces, ENTONCES la recomendación es idéntica").
- **Verificable en:** `app/engine/` es puro — funciones que reciben `CreateSecondBrainPlanRequest` + el `benchmark` cargado y devuelven `CreateSecondBrainPlanResponse`, sin I/O propio más allá de la carga (ya resuelta) de `knowledge/benchmark.yaml`. Implementado en Fase 3, testeado en T15 (test de determinismo) y T16 (cobertura combinatoria de las 216 combinaciones).
- **Regla de revisión:** cualquier uso de `random`, `datetime.now()`, orden de iteración no determinístico (p. ej. iterar un `set` sin ordenar) o estado mutable compartido entre requests dentro de `app/engine/` se rechaza.

## 4. Sin fallback silencioso

Si `knowledge/benchmark.yaml` no existe, no parsea, o no valida contra su schema, el sistema **falla explícito** — nunca sirve una recomendación parcial, con datos default, o inventada para cubrir el hueco.

- **Motivo:** estado de error explícito del spec ("`knowledge/benchmark.yaml` no disponible o corrupto → `500`, mensaje explícito, sin fallback silencioso (nunca inventar una recomendación)").
- **Verificable en:** el loader de `knowledge/benchmark.yaml` (Fase 1, T07) lanza excepción en carga inválida; esa excepción se propaga hasta un error explícito en ambos canales (Fase 4, T19), nunca se atrapa para devolver un valor por defecto. Testeado en T20 (los 4 estados de error) y T29 (paridad de errores entre canales).
- **Regla de revisión:** ningún `except` alrededor de la carga del benchmark puede devolver un valor por defecto, un benchmark vacío, o continuar la ejecución — solo puede loggear y re-lanzar (o dejar propagar) el error.
