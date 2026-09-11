# Benchmark — Segundos Cerebros (metodologías clásicas + IA-nativas + agent-native)

Resultado de investigación web (sep 2026). Alimenta `knowledge/benchmark.yaml` del proyecto.

## Tabla comparativa

| Sistema | Tipo | Setup | Mantenimiento | Conecta ideas | Gestiona acción | Requiere agente IA | Mejor para |
|---|---|---|---|---|---|---|---|
| PARA / BASB (CODE) | Acción | Bajo | Revisión semanal (~15 min) | Débil | Excelente | No | Gestión de proyectos activos |
| Zettelkasten | Conocimiento | Alto | Continuo (15-30 min/día) | Excelente | Débil | No | Investigación, escritura de largo plazo |
| LYT / MOCs | Conocimiento | Medio | Continuo | Excelente | Moderada | No | Punto medio entre estructura y flexibilidad |
| Evergreen Notes | Conocimiento | Alto | Continuo | Excelente | Débil | No | Construcción de expertise, escritura |
| Johnny Decimal | Administrativo | Bajo | Puntual | Débil | Moderada | No | Archivo/recuperación rápida, no ideación |
| Tana (supertags) | IA-nativa | Alto (curva empinada) | Bajo (IA estructura) | Buena (grafo tipado) | Buena | Sí (agentes nativos) | Power users dispuestos a invertir tiempo |
| Mem 2.0 / Recall / Saner.ai | IA-nativa | Bajo | Muy bajo (auto-organización) | Automática, poco control | Moderada | Sí (caja negra) | Quiere cero fricción, acepta perder trazabilidad |
| Agent-native (AGENTS.md/CLAUDE.md + frontmatter + tiers) | Agente | Medio | Bajo-medio (el agente mantiene) | Buena (vía frontmatter + grep) | Buena | Sí (explícito, transparente) | Knowledge workers técnicos que operan con Claude Code/Cursor |

Fuentes principales: Forte Labs / Building a Second Brain (buildingasecondbrain.com, fortelabs.com), Obsibrain guía Zettelkasten 2026, Taskade/LYT blog sobre Maps of Content, dsebastien.net sobre Johnny Decimal, reviews independientes de Tana (doolpa.com, toolchase.com) y Mem 2.0 (aiagentrank.io, supernormal.com), Atlas Workspace comparativa de 6 métodos (atlasworkspace.ai), y proyectos open source de vaults agent-native (agent-vault, vault-kit, llm-wiki-agent, agent-based-knowledge-management, okhlopkov.com).

## Los 3 arquetipos resultantes (+ 1 híbrido)

**1. Acción-primero** — PARA puro. Estructura: `Projects/ Areas/ Resources/ Archive/`. Sirve cuando el dolor principal es "no sé dónde archivar cosas ni qué hacer con ellas", no "no conecto ideas".

**2. Conocimiento-primero** — Zettelkasten + LYT + Evergreen. Estructura: `Inbox (fleeting) → Notas permanentes (atómicas) → MOCs (hubs temáticos) → Home note`. Sirve cuando el dolor es producir escritura/pensamiento original a partir de lo leído.

**3. Agente-primero** — el patrón emergente en 2026, pensado explícitamente para que un agente de código opere sobre el vault, no solo para que un humano navegue. Estructura: `active/ reference/ archive/` + frontmatter YAML con `estado` y TTL + `INDEX.md` (humano) + `manifest.json` (máquina) + `AGENTS.md`/`CLAUDE.md` en la raíz con las reglas de operación.

**4. Híbrido (el caso más común en usuarios técnicos)** — PARA como capa de acción + Zettelkasten/LYT para conocimiento profundo + capa agent-native encima (frontmatter + CLAUDE.md) para que el agente opere sobre ambas capas. Este es, con evidencia externa, el arquetipo en el que ya cae tu propio Segundo Cerebro (Zettelkasten + YAML) — el campo `estado: activo/dormant/archivado` que ya habías identificado como gap es literalmente el mecanismo de "tiers" del arquetipo 3.

## Dimensiones del diagnóstico (borrador del árbol de decisión)

1. **Propósito primario**: ejecutar proyectos / producir conocimiento y escritura / operar como memoria para un agente de código / estudio y aprendizaje
2. **Tolerancia a mantenimiento manual**: baja (que la IA organice) / media / alta (disfruta vincular notas a mano)
3. **Uso de agentes de código sobre las notas**: ya lo hace / quiere empezar / no le interesa
4. **Volumen de captura**: esporádico / diario-moderado / alto volumen multi-fuente
5. **Perfil técnico**: cómodo con markdown/git / prefiere UI visual, no quiere tocar archivos

## Mapeo arquetipo → estructura → skills iniciales

| Arquetipo | Estructura recomendada | Skills iniciales (v1) |
|---|---|---|
| Acción-primero | PARA (4 carpetas) | `captura-rapida` (inbox processing), `revision-semanal` (checklist PARA), `plantilla-proyecto` |
| Conocimiento-primero | Inbox → Permanentes → MOCs → Home note | `captura-atomica`, `vinculacion-bidireccional`, `moc-builder`, `revision-conexiones` |
| Agente-primero | active/reference/archive + frontmatter + AGENTS.md | `ingest-source`, `lint-vault` (consistencia de frontmatter), `estado-tracker` (mueve active→reference→archive por TTL) |
| Híbrido | PARA + Zettelkasten + capa agent-native | Combinación de los tres sets anteriores, priorizada por la respuesta a la dimensión 1 |

## Preguntas que quedan para Claude Code (no resueltas aquí)

- Formalizar las 5 dimensiones en un árbol de decisión determinístico completo (todas las combinaciones, no solo el caso feliz).
- Definir si los "skills iniciales" se entregan como markdown descriptivo o como SKILL.md ejecutables (dado que ya existe el patrón en el propio Segundo Cerebro de Luigui).
- Diseñar el schema de `knowledge/benchmark.yaml` que este documento debe convertirse en.
