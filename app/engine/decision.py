"""Árbol de decisión de arquetipo (Fase 3, T12 — docs/tasks.md).

Implementa exactamente docs/SPEC.md, sección "Lógica de decisión":

- Arquetipo base por Dimensión 1 (`purpose`).
- Modificador híbrido: Dimensión 3 (`agent_usage`) en
  {already_using, want_to_start} → resultado final `hybrid`, sobre
  cualquier arquetipo base.
- Modificador LYT: Dimensión 2 (`maintenance_tolerance`) == "low" +
  arquetipo base `knowledge_first` → se anota preferencia por LYT/MOCs
  (afecta la nota de justificación, no el `archetype` de salida).

`decide_archetype` es una función pura (AGENTS.md, invariante 3): sin
aleatoriedad, sin estado, sin I/O propio. `benchmark.decision_rules`
cubre los 4 valores de `purpose` (validado en Fase 1, T05), así que esta
función resuelve sin excepción cualquiera de las 216 combinaciones de
entrada válidas (Fase 3, T16).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.knowledge.schema import ArchetypeId, Benchmark
from app.models.diagnose import DiagnoseRequest


@dataclass(frozen=True)
class ArchetypeDecision:
    """Resultado del árbol de decisión, antes de armar justification/structure/skills."""

    base_archetype: ArchetypeId
    final_archetype: ArchetypeId
    is_hybrid: bool
    applies_lyt_modifier: bool
    study_note: str | None


def decide_archetype(request: DiagnoseRequest, benchmark: Benchmark) -> ArchetypeDecision:
    base_rule = next(
        r for r in benchmark.decision_rules.base_by_purpose if r.purpose == request.purpose
    )
    base_archetype = base_rule.archetype

    hybrid_rule = benchmark.decision_rules.hybrid_modifier
    is_hybrid = request.agent_usage in hybrid_rule.trigger_agent_usage
    final_archetype: ArchetypeId = "hybrid" if is_hybrid else base_archetype

    lyt_rule = benchmark.decision_rules.lyt_modifier
    applies_lyt_modifier = (
        request.maintenance_tolerance == lyt_rule.trigger_maintenance_tolerance
        and base_archetype == lyt_rule.applies_to_base_archetype
    )

    return ArchetypeDecision(
        base_archetype=base_archetype,
        final_archetype=final_archetype,
        is_hybrid=is_hybrid,
        applies_lyt_modifier=applies_lyt_modifier,
        study_note=base_rule.note if request.purpose == "study" else None,
    )
