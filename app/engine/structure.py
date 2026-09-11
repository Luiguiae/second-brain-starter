"""Armado de `structure` y `skills` (Fase 3, T14 — docs/tasks.md).

Arma `structure.folders`/`structure.frontmatter_fields` del arquetipo
final y selecciona entre 3 y 5 `skills` de `skills_catalog`. Para
`hybrid`, combina los sets base de los 3 arquetipos, priorizando el que
coincide con la Dimensión 1 (`purpose`) — "Combinación de los tres sets
anteriores, priorizada por la respuesta a la dimensión 1" (docs/BENCHMARK.md).

Aplica el modificador de `capture_volume` (Dimensión 4):
- `sporadic` → sin cambios.
- `daily_moderate` → agrega `Inbox/` a `folders`.
- `high_multi_source` → agrega `Inbox/` y además `clasificador-de-fuentes`
  a `skills`, reemplazando la skill de menor prioridad si el set ya tiene
  5 (manteniéndose en el rango 3-5).

Este módulo **nunca** lee `technical_profile` — ver app/engine/justification.py
y AGENTS.md, invariante 2.
"""

from __future__ import annotations

from app.engine.decision import ArchetypeDecision
from app.knowledge.schema import BASE_ARCHETYPE_IDS, ArchetypeId, Benchmark, SkillCatalogEntry
from app.models.diagnose import SkillOutput, Structure

_MAX_SKILLS = 5
_MIN_SKILLS = 3


def _base_skills_for(benchmark: Benchmark, archetype_id: ArchetypeId) -> list[SkillCatalogEntry]:
    """Skills de un arquetipo base, sin `clasificador-de-fuentes`, priority ascendente."""
    return sorted(
        (
            s
            for s in benchmark.skills_catalog
            if archetype_id in s.archetypes and s.id != "clasificador-de-fuentes"
        ),
        key=lambda s: s.priority,
    )


def _hybrid_skills(benchmark: Benchmark, purpose_archetype: ArchetypeId) -> list[SkillCatalogEntry]:
    """Combina los 3 sets base, priorizando el que coincide con purpose, tope 5.

    El arquetipo del que viene `purpose` va primero (ya priority-ordenado);
    los otros dos se agregan después, en el orden canónico de
    BASE_ARCHETYPE_IDS. Se trunca a 5: los últimos elementos de la lista
    combinada son, por construcción, los de menor prioridad relativa.
    """
    ordered_archetypes = [purpose_archetype] + [
        a for a in BASE_ARCHETYPE_IDS if a != purpose_archetype
    ]
    combined: list[SkillCatalogEntry] = []
    seen_ids: set[str] = set()
    for archetype_id in ordered_archetypes:
        for skill in _base_skills_for(benchmark, archetype_id):
            if skill.id not in seen_ids:
                combined.append(skill)
                seen_ids.add(skill.id)
    return combined[:_MAX_SKILLS]


def build_structure_and_skills(
    decision: ArchetypeDecision,
    capture_volume: str,
    benchmark: Benchmark,
) -> tuple[Structure, list[SkillOutput]]:
    archetype = next(a for a in benchmark.archetypes if a.id == decision.final_archetype)
    folders = list(archetype.folders)
    frontmatter_fields = list(archetype.frontmatter_fields)

    if decision.is_hybrid:
        skills = _hybrid_skills(benchmark, decision.base_archetype)
    else:
        skills = _base_skills_for(benchmark, decision.final_archetype)

    cv_rule = next(
        r for r in benchmark.decision_rules.capture_volume_modifiers if r.value == capture_volume
    )
    for folder in cv_rule.add_folders:
        if folder not in folders:
            folders.append(folder)

    if cv_rule.add_skill_id:
        clasificador = next(s for s in benchmark.skills_catalog if s.id == cv_rule.add_skill_id)
        if clasificador.id not in {s.id for s in skills}:
            if len(skills) >= _MAX_SKILLS:
                # El último elemento es, por construcción de _base_skills_for /
                # _hybrid_skills, el de menor prioridad relativa dentro del set.
                skills = skills[: _MAX_SKILLS - 1] + [clasificador]
            else:
                skills = skills + [clasificador]

    assert _MIN_SKILLS <= len(skills) <= _MAX_SKILLS, (
        f"invariante de rango de skills violada: {len(skills)} para {decision.final_archetype}"
    )

    skill_outputs = [
        SkillOutput(name=s.name, description=s.description, format=s.format) for s in skills
    ]
    return Structure(folders=folders, frontmatter_fields=frontmatter_fields), skill_outputs
