"""Estado de error para `knowledge/benchmark.yaml` no disponible/corrupto
(Fase 4, T19 — docs/tasks.md).

`get_benchmark()` es el punto único por el que los canales (Fase 5 REST,
Fase 6 MCP) obtienen el `Benchmark` cargado. Cachea la carga exitosa (no
hay razón para releer el archivo en cada request), pero **nunca** cachea
ni sintetiza un valor por defecto ante un fallo: si `load_benchmark()`
falla una vez, sigue fallando en cada llamada posterior hasta que se pida
`force_reload=True` explícitamente (p. ej. tras arreglar el archivo) o se
reinicie el proceso — nunca un fallback silencioso (AGENTS.md, invariante 4).
"""

from __future__ import annotations

from app.knowledge.loader import BenchmarkLoadError, load_benchmark
from app.knowledge.schema import Benchmark

__all__ = ["BenchmarkLoadError", "get_benchmark"]

_cached_benchmark: Benchmark | None = None
_cached_error: BenchmarkLoadError | None = None


def get_benchmark(*, force_reload: bool = False) -> Benchmark:
    """Devuelve el benchmark cargado y validado.

    Raises:
        BenchmarkLoadError: si `knowledge/benchmark.yaml` no existe, no
            parsea, o no valida contra el schema — se relanza tal cual,
            sin envolver, para que el canal la traduzca a un `500`
            explícito (Fase 5/6).
    """
    global _cached_benchmark, _cached_error

    if force_reload:
        _cached_benchmark = None
        _cached_error = None

    if _cached_benchmark is not None:
        return _cached_benchmark

    if _cached_error is not None:
        raise _cached_error

    try:
        _cached_benchmark = load_benchmark()
    except BenchmarkLoadError as exc:
        _cached_error = exc
        raise
    return _cached_benchmark
