"""T15 (docs/tasks.md, Fase 3): determinismo del engine.

Mismo input -> mismo output, siempre (AGENTS.md, invariante 3;
docs/SPEC.md, criterio de aceptación). Un caso por cada uno de los 4
arquetipos de salida.
"""

from __future__ import annotations

import pytest

from app.engine import diagnose
from app.knowledge.schema import Benchmark
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
        capture_volume="daily_moderate",
        technical_profile="prefers_visual_ui",
    ),
    "agent_first": DiagnoseRequest(
        purpose="agent_memory",
        maintenance_tolerance="low",
        agent_usage="not_interested",
        capture_volume="high_multi_source",
        technical_profile="markdown_git_comfortable",
    ),
    "hybrid": DiagnoseRequest(
        purpose="produce_knowledge",
        maintenance_tolerance="low",
        agent_usage="already_using",
        capture_volume="high_multi_source",
        technical_profile="prefers_visual_ui",
    ),
}


@pytest.mark.parametrize("expected_archetype,request_", CASES.items(), ids=CASES.keys())
def test_same_input_twice_yields_identical_output(
    expected_archetype: str, request_: DiagnoseRequest, benchmark: Benchmark
) -> None:
    first = diagnose(request_, benchmark)
    second = diagnose(request_, benchmark)

    assert first.archetype == expected_archetype
    assert first == second


def test_repeated_calls_are_stable_across_many_runs(benchmark: Benchmark) -> None:
    request_ = CASES["hybrid"]
    results = [diagnose(request_, benchmark) for _ in range(20)]
    assert all(r == results[0] for r in results)
