"""T30 (docs/tasks.md, Fase 8): catálogo de skills por arquetipo.

Para cada uno de los 4 arquetipos de salida (incluido híbrido), las
`skills` devueltas están entre 3 y 5, todas presentes en `skills_catalog`
de `knowledge/benchmark.yaml`, y el caso híbrido efectivamente combina
skills de más de un arquetipo base.
"""

from __future__ import annotations

import pytest

from app.engine import diagnose
from app.models.diagnose import DiagnoseRequest

CASES: dict[str, DiagnoseRequest] = {
    "action_first": DiagnoseRequest(
        purpose="execute_projects",
        maintenance_tolerance="medium",
        agent_usage="not_interested",
        capture_volume="sporadic",
        technical_profile="markdown_git_comfortable",
    ),
    "knowledge_first": DiagnoseRequest(
        purpose="produce_knowledge",
        maintenance_tolerance="high",
        agent_usage="not_interested",
        capture_volume="sporadic",
        technical_profile="markdown_git_comfortable",
    ),
    "agent_first": DiagnoseRequest(
        purpose="agent_memory",
        maintenance_tolerance="medium",
        agent_usage="not_interested",
        capture_volume="sporadic",
        technical_profile="markdown_git_comfortable",
    ),
    "hybrid": DiagnoseRequest(
        purpose="execute_projects",
        maintenance_tolerance="medium",
        agent_usage="already_using",
        capture_volume="sporadic",
        technical_profile="markdown_git_comfortable",
    ),
}

# Mapa skill -> arquetipo base "dueño" en knowledge/benchmark.yaml, para
# poder verificar que el set del híbrido combina más de uno.
SKILL_OWNER_ARCHETYPE = {
    "captura-rapida": "action_first",
    "revision-semanal": "action_first",
    "plantilla-proyecto": "action_first",
    "captura-atomica": "knowledge_first",
    "vinculacion-bidireccional": "knowledge_first",
    "moc-builder": "knowledge_first",
    "revision-conexiones": "knowledge_first",
    "ingest-source": "agent_first",
    "lint-vault": "agent_first",
    "estado-tracker": "agent_first",
    "clasificador-de-fuentes": None,  # disponible para los 4, no "dueño" único
}


@pytest.mark.parametrize("archetype,request_", CASES.items(), ids=CASES.keys())
def test_skills_count_is_between_3_and_5(
    archetype: str, request_: DiagnoseRequest, benchmark
) -> None:
    response = diagnose(request_, benchmark)
    assert response.archetype == archetype
    assert 3 <= len(response.skills) <= 5


@pytest.mark.parametrize("archetype,request_", CASES.items(), ids=CASES.keys())
def test_all_skills_exist_in_the_catalog(
    archetype: str, request_: DiagnoseRequest, benchmark
) -> None:
    response = diagnose(request_, benchmark)
    catalog_names = {s.name for s in benchmark.skills_catalog}
    for skill in response.skills:
        assert skill.name in catalog_names
        assert skill.format == "markdown_descriptive"


def test_hybrid_combines_skills_from_more_than_one_base_archetype(benchmark) -> None:
    response = diagnose(CASES["hybrid"], benchmark)
    owner_archetypes = {SKILL_OWNER_ARCHETYPE[s.name] for s in response.skills}
    owner_archetypes.discard(None)
    assert len(owner_archetypes) > 1, (
        f"el set del híbrido no combina múltiples arquetipos base: {owner_archetypes}"
    )
