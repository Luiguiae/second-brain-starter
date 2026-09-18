"""Canales (Fase 5 REST, Fase 6 MCP) — docs/tasks.md.

`TOOL_DESCRIPTION` es el texto que lee el agente llamador (GPT Action,
Claude Code, u otro cliente MCP) antes de decidir cómo y cuándo invocar
la operación — no un comentario interno. Vive acá, en vez de duplicarse
en `rest.py` y `mcp_server.py`, para que ambos canales muestren
exactamente el mismo contrato (docs/SPEC.md, "Contrato de interacción
con el agente llamador"): si faltan respuestas, preguntarlas con el
texto de "Copy de las preguntas"; nunca leer archivos del usuario para
inferirlas; encuadrar como crear, no como diagnosticar; y (v2.1.0, cambio
aditivo) al materializar los archivos reales, usar `structure.folder_purposes`
para escribir el README.md de cada carpeta y explicarle a la persona el
propósito de cada una, no solo listarlas.
"""

from __future__ import annotations

TOOL_DESCRIPTION = (
    "Crea la base de un Segundo Cerebro (PKM) DESDE CERO: a partir de 5 respuestas "
    "explícitas, devuelve de forma determinística un arquetipo recomendado, "
    "justificación trazable a knowledge/benchmark.yaml, estructura de "
    "carpetas/frontmatter, y 3-5 skills iniciales. Esta NO es una herramienta para "
    "evaluar, auditar o diagnosticar un sistema existente — es para crear uno nuevo. "
    "Encuadrá la conversación con el usuario como 'vamos a crear/armar tu Segundo "
    "Cerebro', nunca como 'voy a diagnosticar/evaluar lo que ya tenés'.\n\n"
    "INSTRUCCIONES PARA EL AGENTE LLAMADOR — leer antes de invocar:\n"
    "1. Si falta alguna de las 5 respuestas, preguntale al usuario cada una en "
    "lenguaje natural, una a la vez si hace falta, usando este texto exacto:\n"
    "   1. ¿Cuál es el objetivo principal de tu Segundo Cerebro? → Ejecutar y dar "
    "seguimiento a proyectos activos (execute_projects) / Producir conocimiento "
    "propio: escribir, investigar (produce_knowledge) / Que un agente de IA opere "
    "sobre mis notas como memoria de trabajo (agent_memory) / Estudiar y retener "
    "contenido (study)\n"
    "   2. ¿Cuánto tiempo quieres invertir manteniendo el sistema? → Poco, quiero "
    "organización automática (low) / Algo, una revisión periódica está bien "
    "(medium) / Mucho, disfruto estructurar y conectar notas a mano (high)\n"
    "   3. ¿Usas o planeas usar agentes de código (Claude Code, Cursor) sobre tus "
    "notas? → Ya lo hago (already_using) / No todavía, pero quiero empezar "
    "(want_to_start) / No me interesa por ahora (not_interested)\n"
    "   4. ¿Con qué frecuencia capturas información nueva? → Esporádicamente "
    "(sporadic) / A diario, de una o dos fuentes (daily_moderate) / A diario, de "
    "muchas fuentes distintas (high_multi_source)\n"
    "   5. ¿Qué tan cómodo estás trabajando con archivos markdown y git? → Muy "
    "cómodo, prefiero texto plano (markdown_git_comfortable) / Prefiero una "
    "interfaz visual (prefers_visual_ui)\n"
    "   Nunca asumas valores por defecto ni los infieras de otra fuente.\n"
    "2. Nunca leas archivos, explores el sistema de archivos del usuario, ni "
    "asumas que existe un Segundo Cerebro previo para completar respuestas "
    "faltantes. Esta tool no lee nada del usuario — todo el input viaja explícito "
    "en esta llamada.\n"
    "3. Encuadrá siempre como crear/armar, nunca como diagnosticar/evaluar.\n"
    "4. Al crear los archivos reales de la estructura (paso separado y explícito, "
    "después de mostrar el plan), usá el texto de structure.folder_purposes para "
    "escribir el README.md de cada carpeta en lenguaje humano (qué va ahí y para "
    "qué sirve), y para explicarle a la persona, en el resumen de lo que hiciste, "
    "el propósito de cada carpeta — no te limites a listarlas por nombre ni a "
    "reglas para el agente (frontmatter, convenciones)."
)
