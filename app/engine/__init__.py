"""Motor de reglas determinístico (Fase 3 — docs/tasks.md).

Único lugar del repo con lógica de decisión (AGENTS.md, invariante 2).
`diagnose()` es la función pública que ambos canales (REST, Fase 5; MCP,
Fase 6) deben llamar — ninguno debe reimplementar nada de lo que hay aquí.
"""

from app.engine.core import diagnose

__all__ = ["diagnose"]
