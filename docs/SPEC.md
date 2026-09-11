# Second Brain Starter

## Resumen
Herramienta open source que diagnostica el perfil de conocimiento de una persona mediante un cuestionario corto y recomienda la estructura de su Segundo Cerebro (PKM) + un set inicial de skills/plantillas, expuesta simultáneamente como MCP server y API REST/OpenAPI para que Claude Code, GPT u otros agentes la invoquen directamente.

## Problema
Construir un Segundo Cerebro obliga a elegir entre metodologías (PARA, Zettelkasten, LYT, Johnny Decimal) y herramientas (Obsidian, Notion, Tana, Reflect, Mem) sin criterio objetivo. La mayoría abandona por sobre-estructuración o parálisis de elección. No existe un diagnóstico que traduzca el perfil real de la persona en una estructura concreta, trazable a evidencia, y accionable el mismo día.

## Usuarios objetivo
Knowledge workers y builders técnicos, cómodos usando Claude Code o un GPT personalizado, que quieren iniciar o reestructurar su sistema de notas sin pagar el costo de investigar metodologías desde cero.

## Casos de uso principales
1. Como usuario nuevo, quiero responder un diagnóstico corto (8-12 preguntas) y recibir una estructura de Segundo Cerebro ajustada a mi perfil.
2. Como usuario, quiero recibir junto a la estructura 3-5 skills/plantillas iniciales para empezar a usar el sistema el mismo día.
3. Como desarrollador en Claude Code, quiero invocar el diagnóstico vía MCP sin salir de mi flujo de trabajo.
4. Como usuario de un GPT personalizado, quiero invocar la misma lógica vía Action (OpenAPI).
5. Como mantenedor, quiero que cada recomendación sea trazable a una fuente del benchmark, no a una heurística arbitraria.

## Lógica de decisión (MVP, determinística)
La Dimensión 1 (propósito primario) elige el arquetipo base:
- "Ejecutar proyectos" → Acción-primero (PARA)
- "Producir conocimiento/escritura" → Conocimiento-primero (Zettelkasten/LYT)
- "Operar como memoria para un agente de código" → Agente-primero
- "Estudio y aprendizaje" → Conocimiento-primero, variante ligera (Cornell/Outline en notas de recomendación, fuera de alcance implementar esos arquetipos en v1)

Modificadores (no cambian el arquetipo base, ajustan la recomendación):
- Dimensión 3 = "ya uso agentes de código" o "quiero empezar" → se agrega la capa agent-native (frontmatter + AGENTS.md/CLAUDE.md) sobre cualquier arquetipo base → resultado: Híbrido
- Dimensión 2 = "baja tolerancia a mantenimiento manual" + arquetipo base Conocimiento-primero → se recomienda LYT (MOCs) en vez de Zettelkasten puro (menor fricción)

Esto cubre las 4x2x2 combinaciones principales sin necesitar una matriz exhaustiva de 3^5 casos.

**Modificador de `capture_volume`** (afecta `structure.folders` y, en el caso extremo, `skills` — no cambia el arquetipo):
- `sporadic` → sin cambios sobre la estructura base del arquetipo.
- `daily_moderate` → se agrega una carpeta `Inbox/` a `structure.folders` (captura sin triage inmediato), consistente con el paso "Capture" de BASB y las "fleeting notes" de Zettelkasten/LYT documentados en el benchmark.
- `high_multi_source` → además de `Inbox/`, se incluye la skill `clasificador-de-fuentes` (nueva entrada en `skills_catalog`, disponible para los 4 arquetipos) en el set de `skills`, reemplazando la de menor prioridad si ya hay 5 seleccionadas (para mantenerse en el rango 3-5).

**Modificador de `technical_profile`** (afecta solo `justification`, nunca `folders`/`skills` — mantiene la recomendación agnóstica de herramienta):
- `markdown_git_comfortable` → se agrega una línea a `justification` recomendando implementación en archivos planos + git.
- `prefers_visual_ui` → se agrega una línea a `justification` recomendando implementar la misma estructura en una herramienta visual (Obsidian/Notion/Tana según el arquetipo), citando la fila correspondiente de `systems` en el benchmark.

Ninguno de los dos modificadores cambia el Esquema de datos de salida (`folders` y `skills` ya son arrays, `justification` ya es array de strings) — solo afecta `knowledge/benchmark.yaml` (agregar 1 skill + los `source_ref` de las líneas de justificación) y la lógica de ensamblado (T13/T14 en tasks.md).

## Criterios de aceptación
- DADO un set de respuestas a las 5 dimensiones, CUANDO se envían al endpoint/tool, ENTONCES la respuesta aplica la lógica de decisión de arriba y devuelve: arquetipo, justificación con cita al benchmark, estructura de carpetas/frontmatter, y 3-5 skills iniciales — verificable comparando contra la tabla de la lógica de decisión.
- DADO que el mismo input se envía dos veces, ENTONCES la recomendación es idéntica (determinístico, sin LLM en el core).
- DADO un cliente MCP (Claude Code) y un cliente REST (GPT Action), ENTONCES ambos reciben una respuesta que valida contra el mismo JSON Schema de salida (ver sección Esquema de datos).
- DADO un diagnóstico incompleto o con valores fuera de las opciones válidas, ENTONCES el sistema responde con un error estructurado (ver Estados de error), nunca con una recomendación parcial o inventada.

## Esquema de datos
**Entrada** (`POST /diagnose`):
```json
{
  "purpose": "execute_projects | produce_knowledge | agent_memory | study",
  "maintenance_tolerance": "low | medium | high",
  "agent_usage": "already_using | want_to_start | not_interested",
  "capture_volume": "sporadic | daily_moderate | high_multi_source",
  "technical_profile": "markdown_git_comfortable | prefers_visual_ui"
}
```
**Salida**:
```json
{
  "archetype": "action_first | knowledge_first | agent_first | hybrid",
  "justification": ["string (con referencia a la fuente del benchmark)"],
  "structure": {"folders": ["string"], "frontmatter_fields": ["string"]},
  "skills": [{"name": "string", "description": "string", "format": "markdown_descriptive"}]
}
```

## Estados de error
- Campos obligatorios faltantes → `422` con lista de campos faltantes.
- Valor fuera del enum permitido en algún campo → `400` con el campo y los valores válidos.
- `knowledge/benchmark.yaml` no disponible o corrupto → `500`, mensaje explícito, sin fallback silencioso (nunca inventar una recomendación).
- Mismatch de schema entre cliente MCP y REST → validación compartida vía el mismo JSON Schema; falla = `400` en ambos por igual.

## Integraciones
- v1 es standalone: no lee el vault real de Luigui ni ningún vault de terceros, solo recibe respuestas al diagnóstico.
- Reutiliza el patrón arquitectónico de Rikra (FastAPI + MCP server, abstracción de canal) pero sin dependencias de código compartidas.
- Fuera de esta iteración: un modo "audita mi vault existente" que sí lea archivos reales (ver Fuera de alcance).

## Alcance por iteración
- **Iteración 1 (MVP, esta spec):** motor de reglas + `knowledge/benchmark.yaml` con las combinaciones de la Lógica de decisión + API REST/OpenAPI + MCP server + skills iniciales como markdown descriptivo.
- **Iteración 2 (no incluida aquí):** skills iniciales como SKILL.md ejecutables, modo auditoría de vault existente, personalización de tono de salida vía LLM opcional.

## Fuera de alcance (v1)
- No migra ni importa notas existentes, ni audita un vault real (queda para Iteración 2).
- No es una app de toma de notas (no reemplaza Obsidian/Notion/Tana).
- No incluye sync ni almacenamiento de las notas del usuario.
- No genera contenido de las notas, solo estructura + skills.
- No hay cuentas de usuario ni persistencia del diagnóstico en v1 (stateless por sesión).
- Los arquetipos de estudio (Cornell/Outline) no se implementan en v1, solo se mencionan como nota de recomendación textual.

## Stack / restricciones técnicas
- Python 3.11 + FastAPI (mismo patrón arquitectónico que Rikra)
- MCP server nativo (`/mcp`) + API REST documentada con OpenAPI 3.x (compatible con Custom GPT Actions)
- Motor de recomendación: árbol de decisión determinístico sobre las dimensiones del benchmark — sin LLM en el core (transparencia + costo cero por request; alineado a Soberanía de Tokens, T1). LLM opcional solo para personalizar el *tono* del texto de salida, nunca la decisión.
- Base de conocimiento: `knowledge/benchmark.yaml` versionado en el repo, resultado documentado de la fase de investigación (fuente de verdad, editable sin tocar código)
- Deploy: Railway
- Licencia: MIT, repo público

## Métricas de éxito
- % de sesiones que completan el diagnóstico completo
- Cobertura del benchmark: nº de metodologías/herramientas documentadas y trazables por recomendación
- Adopción: nº de invocaciones vía MCP vs. vía REST (valida si el acceso dual realmente se usa)

## Copy del diagnóstico (lenguaje natural, mapea 1:1 a los enums del Esquema de datos)
1. **¿Cuál es el objetivo principal de tu Segundo Cerebro?** → Ejecutar y dar seguimiento a proyectos activos (`execute_projects`) / Producir conocimiento propio: escribir, investigar (`produce_knowledge`) / Que un agente de IA opere sobre mis notas como memoria de trabajo (`agent_memory`) / Estudiar y retener contenido (`study`)
2. **¿Cuánto tiempo quieres invertir manteniendo el sistema?** → Poco, quiero organización automática (`low`) / Algo, una revisión periódica está bien (`medium`) / Mucho, disfruto estructurar y conectar notas a mano (`high`)
3. **¿Usas o planeas usar agentes de código (Claude Code, Cursor) sobre tus notas?** → Ya lo hago (`already_using`) / No todavía, pero quiero empezar (`want_to_start`) / No me interesa por ahora (`not_interested`)
4. **¿Con qué frecuencia capturas información nueva?** → Esporádicamente (`sporadic`) / A diario, de una o dos fuentes (`daily_moderate`) / A diario, de muchas fuentes distintas (`high_multi_source`)
5. **¿Qué tan cómodo estás trabajando con archivos markdown y git?** → Muy cómodo, prefiero texto plano (`markdown_git_comfortable`) / Prefiero una interfaz visual (`prefers_visual_ui`)

## Preguntas abiertas
- Ninguna bloqueante. Pendiente menor: verificar disponibilidad de "Second Brain Starter" como nombre de repo/dominio antes de publicar.
