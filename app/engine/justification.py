"""Justificación trazable al benchmark (Fase 3, T13 — docs/tasks.md).

Arma `justification: list[str]`, citando siempre un `source_ref`/
`system_ref` que existe en `knowledge/benchmark.yaml` (nunca texto libre
inventado). Aplica el modificador de `technical_profile` (Dimensión 5):
agrega exactamente una línea, citando la fila de `systems` correspondiente
al arquetipo final cuando el valor es `prefers_visual_ui` (docs/SPEC.md:
"Obsidian/Notion/Tana según el arquetipo... citando la fila
correspondiente de systems").

Este módulo **nunca** toca `structure` ni `skills` — ver app/engine/structure.py
y AGENTS.md, invariante 2 (separación de responsabilidades dentro del
propio engine, para que cambiar `technical_profile` con el resto del
input fijo solo cambie esta lista).
"""

from __future__ import annotations

from app.engine.decision import ArchetypeDecision
from app.knowledge.schema import Benchmark
from app.models.plan import CreateSecondBrainPlanRequest


def _source_description(benchmark: Benchmark, source_id: str) -> str:
    source = next(s for s in benchmark.sources if s.id == source_id)
    return source.description


def _system_name(benchmark: Benchmark, system_id: str) -> str:
    system = next(s for s in benchmark.systems if s.id == system_id)
    return system.name


def build_justification(
    request: CreateSecondBrainPlanRequest, decision: ArchetypeDecision, benchmark: Benchmark
) -> list[str]:
    lines: list[str] = []

    base_rule = next(
        r for r in benchmark.decision_rules.base_by_purpose if r.purpose == request.purpose
    )
    base_archetype = next(a for a in benchmark.archetypes if a.id == decision.base_archetype)
    base_refs = "; ".join(_source_description(benchmark, r) for r in base_rule.source_refs)
    base_line = (
        f"Tu objetivo principal ('{request.purpose}') mapea a {base_archetype.name} "
        f"— fuente: {base_refs}."
    )
    if base_rule.note:
        base_line += f" {base_rule.note}"
    lines.append(base_line)

    if decision.applies_lyt_modifier:
        lyt = benchmark.decision_rules.lyt_modifier
        lyt_refs = "; ".join(_source_description(benchmark, r) for r in lyt.source_refs)
        lines.append(f"{lyt.note} — fuente: {lyt_refs}.")

    if decision.is_hybrid:
        hybrid = benchmark.decision_rules.hybrid_modifier
        hybrid_refs = "; ".join(_source_description(benchmark, r) for r in hybrid.source_refs)
        lines.append(
            "Ya usas o quieres empezar a usar agentes de código sobre tus notas: "
            "se agrega la capa agent-native (frontmatter + AGENTS.md/CLAUDE.md) sobre "
            f"el arquetipo base → resultado Híbrido — fuente: {hybrid_refs}."
        )

    tp_rule = next(
        r
        for r in benchmark.decision_rules.technical_profile_modifiers
        if r.value == request.technical_profile
    )
    if tp_rule.system_ref_by_archetype:
        system_id = tp_rule.system_ref_by_archetype[decision.final_archetype]
    else:
        system_id = tp_rule.default_system_ref
    system_name = _system_name(benchmark, system_id)
    lines.append(f"{tp_rule.justification_template} — fuente: {system_name}.")

    return lines
