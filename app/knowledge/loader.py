"""Loader y validador de `knowledge/benchmark.yaml` (Fase 1, T07 — docs/tasks.md).

Sin fallback silencioso (AGENTS.md, invariante 4): si el archivo no existe,
no parsea como YAML, o no valida contra el schema `Benchmark`, se lanza
`BenchmarkLoadError` con un mensaje explícito. Nunca se devuelve un
benchmark vacío, parcial o por defecto.

La Fase 4 (T19) atrapa `BenchmarkLoadError` en el borde de cada canal y lo
traduce al estado de error `500` del spec ("knowledge/benchmark.yaml no
disponible o corrupto"). Este módulo no conoce HTTP ni MCP — solo carga y
valida.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from app.knowledge.schema import Benchmark

DEFAULT_BENCHMARK_PATH = Path(__file__).resolve().parents[2] / "knowledge" / "benchmark.yaml"


class BenchmarkLoadError(Exception):
    """knowledge/benchmark.yaml no existe, no parsea, o no valida contra el schema."""


def load_benchmark(path: Path | str = DEFAULT_BENCHMARK_PATH) -> Benchmark:
    """Carga y valida `knowledge/benchmark.yaml`.

    Args:
        path: ruta al YAML. Por defecto, `knowledge/benchmark.yaml` en la
            raíz del repo (resuelta relativa a este archivo, no al cwd).

    Returns:
        Un `Benchmark` validado y tipado.

    Raises:
        BenchmarkLoadError: archivo ausente, ilegible, YAML inválido, vacío,
            o que no valida contra `Benchmark` (incluidas las referencias
            cruzadas: source_ref/system_ref inexistentes, arquetipos sin
            3-5 skills base, falta `clasificador-de-fuentes`, etc.).
    """
    path = Path(path)

    if not path.exists():
        raise BenchmarkLoadError(f"knowledge/benchmark.yaml no encontrado en: {path}")

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BenchmarkLoadError(
            f"No se pudo leer knowledge/benchmark.yaml ({path}): {exc}"
        ) from exc

    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise BenchmarkLoadError(
            f"knowledge/benchmark.yaml no es YAML válido ({path}): {exc}"
        ) from exc

    if data is None:
        raise BenchmarkLoadError(f"knowledge/benchmark.yaml está vacío: {path}")

    try:
        return Benchmark.model_validate(data)
    except ValidationError as exc:
        raise BenchmarkLoadError(
            f"knowledge/benchmark.yaml no valida contra el schema "
            f"(app/knowledge/schema.py:Benchmark): {exc}"
        ) from exc
