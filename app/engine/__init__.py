"""Motor de reglas determinístico (Fase 3 — docs/tasks.md).

Único lugar del repo con lógica de decisión (AGENTS.md, invariante 2).
`create_plan()` es la función pública que ambos canales (REST, Fase 5; MCP,
Fase 6) deben llamar — ninguno debe reimplementar nada de lo que hay aquí.
"""

from app.engine.core import create_plan

__all__ = ["create_plan"]
