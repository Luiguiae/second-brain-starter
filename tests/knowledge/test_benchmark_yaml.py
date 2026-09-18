"""T08 (docs/tasks.md, Fase 1): knowledge/benchmark.yaml real valida.

Carga el archivo real del repo (no un fixture) con el loader de T07 y
verifica que valida sin errores contra el schema de T05, más algunas
propiedades que las fases siguientes dan por sentadas.
"""

from __future__ import annotations

import pytest

from app.knowledge.loader import DEFAULT_BENCHMARK_PATH, BenchmarkLoadError, load_benchmark
from app.knowledge.schema import ARCHETYPE_IDS, BASE_ARCHETYPE_IDS, DIMENSION_IDS, Benchmark


def test_real_benchmark_yaml_loads_and_validates() -> None:
    benchmark = load_benchmark()
    assert isinstance(benchmark, Benchmark)


def test_real_benchmark_yaml_path_is_the_repo_file() -> None:
    assert DEFAULT_BENCHMARK_PATH.name == "benchmark.yaml"
    assert DEFAULT_BENCHMARK_PATH.exists()


def test_covers_all_archetypes_and_dimensions() -> None:
    benchmark = load_benchmark()
    assert {a.id for a in benchmark.archetypes} == set(ARCHETYPE_IDS)
    assert {d.id for d in benchmark.dimensions} == set(DIMENSION_IDS)


def test_base_archetypes_have_3_to_5_skills() -> None:
    benchmark = load_benchmark()
    for archetype_id in BASE_ARCHETYPE_IDS:
        skills = [
            s
            for s in benchmark.skills_catalog
            if archetype_id in s.archetypes and s.id != "clasificador-de-fuentes"
        ]
        assert 3 <= len(skills) <= 5, f"{archetype_id} tiene {len(skills)} skills base"


def test_clasificador_de_fuentes_available_for_all_archetypes() -> None:
    benchmark = load_benchmark()
    clasificador = next(s for s in benchmark.skills_catalog if s.id == "clasificador-de-fuentes")
    assert set(clasificador.archetypes) == set(ARCHETYPE_IDS)


def test_capture_volume_modifiers_cover_all_three_values() -> None:
    benchmark = load_benchmark()
    values = {r.value for r in benchmark.decision_rules.capture_volume_modifiers}
    assert values == {"sporadic", "daily_moderate", "high_multi_source"}

    high_multi_source = next(
        r
        for r in benchmark.decision_rules.capture_volume_modifiers
        if r.value == "high_multi_source"
    )
    assert "Inbox/" in high_multi_source.add_folders
    assert high_multi_source.add_skill_id == "clasificador-de-fuentes"


def test_technical_profile_modifiers_cover_both_values() -> None:
    benchmark = load_benchmark()
    values = {r.value for r in benchmark.decision_rules.technical_profile_modifiers}
    assert values == {"markdown_git_comfortable", "prefers_visual_ui"}

    prefers_visual_ui = next(
        r
        for r in benchmark.decision_rules.technical_profile_modifiers
        if r.value == "prefers_visual_ui"
    )
    assert prefers_visual_ui.system_ref_by_archetype is not None
    assert set(prefers_visual_ui.system_ref_by_archetype) == set(ARCHETYPE_IDS)


def test_folder_purposes_covers_every_folder_used_by_any_archetype_or_modifier() -> None:
    benchmark = load_benchmark()

    used_folders: set[str] = set()
    for archetype in benchmark.archetypes:
        used_folders.update(archetype.folders)
    for cv in benchmark.decision_rules.capture_volume_modifiers:
        used_folders.update(cv.add_folders)

    assert used_folders  # sanity: hay al menos una carpeta usada
    assert used_folders <= set(benchmark.folder_purposes)


def test_missing_file_raises_explicit_error(tmp_path) -> None:
    missing_path = tmp_path / "does-not-exist.yaml"
    with pytest.raises(BenchmarkLoadError, match="no encontrado"):
        load_benchmark(missing_path)


def test_corrupt_yaml_raises_explicit_error(tmp_path) -> None:
    corrupt_path = tmp_path / "corrupt.yaml"
    corrupt_path.write_text("archetypes: [unclosed", encoding="utf-8")
    with pytest.raises(BenchmarkLoadError, match="no es YAML válido"):
        load_benchmark(corrupt_path)


def test_yaml_not_matching_schema_raises_explicit_error(tmp_path) -> None:
    invalid_path = tmp_path / "invalid.yaml"
    invalid_path.write_text("version: '1.0.0'\n", encoding="utf-8")
    with pytest.raises(BenchmarkLoadError, match="no valida contra el schema"):
        load_benchmark(invalid_path)
