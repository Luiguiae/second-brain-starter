"""Orquestador del motor de reglas (Fase 3 — docs/tasks.md).

`diagnose()` es la única función pública que los canales (REST, Fase 5;
MCP, Fase 6) deben llamar (AGENTS.md, invariante 2). No hace I/O propio
más allá de leer el `Benchmark` ya cargado — determinista y puro
(AGENTS.md, invariante 3).
"""

from __future__ import annotations

from app.engine.decision import decide_archetype
from app.engine.justification import build_justification
from app.engine.structure import build_structure_and_skills
from app.knowledge.schema import Benchmark
from app.models.diagnose import DiagnoseRequest, DiagnoseResponse


def diagnose(request: DiagnoseRequest, benchmark: Benchmark) -> DiagnoseResponse:
    decision = decide_archetype(request, benchmark)
    justification = build_justification(request, decision, benchmark)
    structure, skills = build_structure_and_skills(decision, request.capture_volume, benchmark)
    return DiagnoseResponse(
        archetype=decision.final_archetype,
        justification=justification,
        structure=structure,
        skills=skills,
    )
