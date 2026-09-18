"""T16 (docs/tasks.md, Fase 3): cobertura combinatoria.

Itera el producto cartesiano completo de los enums válidos de los 5
campos de entrada (4x3x3x3x2 = 216 combinaciones) y verifica que el
engine resuelve cada una a un `CreateSecondBrainPlanResponse` válido, sin excepción y
validando contra el JSON Schema de T10. Además asertan explícitamente
(criterio de done actualizado):

- Si capture_volume in {daily_moderate, high_multi_source} -> folders
  contiene "Inbox/".
- Si capture_volume == high_multi_source -> skills contiene
  "clasificador-de-fuentes" y 3 <= len(skills) <= 5.
- Para todo par de inputs idénticos salvo technical_profile -> structure
  y skills son idénticos entre ambos, solo justification difiere.
"""

from __future__ import annotations

import itertools

import jsonschema
import pytest

from app.engine import create_plan
from app.knowledge.schema import DIMENSION_VALUES
from app.models.plan import CreateSecondBrainPlanRequest
from app.models.schema_export import plan_response_json_schema

_DIMENSIONS = (
    "purpose",
    "maintenance_tolerance",
    "agent_usage",
    "capture_volume",
    "technical_profile",
)

ALL_COMBINATIONS = list(itertools.product(*(DIMENSION_VALUES[d] for d in _DIMENSIONS)))


def test_all_216_combinations_exist() -> None:
    assert len(ALL_COMBINATIONS) == 4 * 3 * 3 * 3 * 2 == 216


@pytest.mark.parametrize(
    "combo", ALL_COMBINATIONS, ids=["-".join(c) for c in ALL_COMBINATIONS]
)
def test_every_combination_resolves_without_exception_and_matches_schema(
    combo: tuple[str, str, str, str, str], benchmark
) -> None:
    request_ = CreateSecondBrainPlanRequest(**dict(zip(_DIMENSIONS, combo, strict=True)))

    response = create_plan(request_, benchmark)

    jsonschema.validate(
        instance=response.model_dump(mode="json"), schema=plan_response_json_schema()
    )

    assert 3 <= len(response.skills) <= 5

    _purpose, _maintenance, _agent_usage, capture_volume, _technical_profile = combo

    if capture_volume in ("daily_moderate", "high_multi_source"):
        assert "Inbox/" in response.structure.folders, combo

    if capture_volume == "high_multi_source":
        skill_names = {s.name for s in response.skills}
        assert "clasificador-de-fuentes" in skill_names, combo
        assert 3 <= len(response.skills) <= 5, combo


def _other_four_dimension_combinations() -> list[tuple[str, str, str, str]]:
    other_dims = ("purpose", "maintenance_tolerance", "agent_usage", "capture_volume")
    return list(itertools.product(*(DIMENSION_VALUES[d] for d in other_dims)))


@pytest.mark.parametrize(
    "combo",
    _other_four_dimension_combinations(),
    ids=["-".join(c) for c in _other_four_dimension_combinations()],
)
def test_technical_profile_only_changes_justification(
    combo: tuple[str, str, str, str], benchmark
) -> None:
    purpose, maintenance_tolerance, agent_usage, capture_volume = combo

    response_markdown = create_plan(
        CreateSecondBrainPlanRequest(
            purpose=purpose,
            maintenance_tolerance=maintenance_tolerance,
            agent_usage=agent_usage,
            capture_volume=capture_volume,
            technical_profile="markdown_git_comfortable",
        ),
        benchmark,
    )
    response_visual = create_plan(
        CreateSecondBrainPlanRequest(
            purpose=purpose,
            maintenance_tolerance=maintenance_tolerance,
            agent_usage=agent_usage,
            capture_volume=capture_volume,
            technical_profile="prefers_visual_ui",
        ),
        benchmark,
    )

    assert response_markdown.archetype == response_visual.archetype
    assert response_markdown.structure == response_visual.structure
    assert response_markdown.skills == response_visual.skills
    assert response_markdown.justification != response_visual.justification
