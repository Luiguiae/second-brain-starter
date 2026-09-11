"""T20 (docs/tasks.md, Fase 4): los 4 estados de error de docs/SPEC.md.

Cubre los 3 estados de error verificables a este nivel (validación de
entrada y carga del benchmark). El 4to estado — "mismatch de schema entre
cliente MCP y REST" — se completa en Fase 7 (T29), una vez existen ambos
canales, verificando que ambos fallan igual (400) ante el mismo input
inválido.
"""

from __future__ import annotations

import pytest

from app.errors.knowledge_errors import BenchmarkLoadError, get_benchmark
from app.errors.validation import (
    InvalidEnumValueError,
    MissingFieldsError,
    validate_diagnose_request,
)
from app.knowledge.loader import BenchmarkLoadError as LoaderBenchmarkLoadError

VALID_PAYLOAD = {
    "purpose": "execute_projects",
    "maintenance_tolerance": "medium",
    "agent_usage": "already_using",
    "capture_volume": "daily_moderate",
    "technical_profile": "markdown_git_comfortable",
}


# --- Estado 1: campos obligatorios faltantes -> 422 -----------------------


def test_valid_payload_does_not_raise() -> None:
    request_ = validate_diagnose_request(VALID_PAYLOAD)
    assert request_.purpose == "execute_projects"


def test_missing_fields_error_lists_exactly_the_missing_fields() -> None:
    payload = dict(VALID_PAYLOAD)
    del payload["capture_volume"]
    del payload["technical_profile"]

    with pytest.raises(MissingFieldsError) as excinfo:
        validate_diagnose_request(payload)

    assert set(excinfo.value.missing_fields) == {"capture_volume", "technical_profile"}


def test_missing_single_field_reports_only_that_field() -> None:
    payload = dict(VALID_PAYLOAD)
    del payload["purpose"]

    with pytest.raises(MissingFieldsError) as excinfo:
        validate_diagnose_request(payload)

    assert excinfo.value.missing_fields == ["purpose"]


def test_empty_payload_lists_all_five_fields_missing() -> None:
    with pytest.raises(MissingFieldsError) as excinfo:
        validate_diagnose_request({})

    assert set(excinfo.value.missing_fields) == {
        "purpose",
        "maintenance_tolerance",
        "agent_usage",
        "capture_volume",
        "technical_profile",
    }


# --- Estado 2: valor fuera del enum permitido -> 400 -----------------------


def test_invalid_enum_value_error_reports_field_and_valid_values() -> None:
    payload = {**VALID_PAYLOAD, "purpose": "not_a_real_purpose"}

    with pytest.raises(InvalidEnumValueError) as excinfo:
        validate_diagnose_request(payload)

    assert excinfo.value.field == "purpose"
    assert excinfo.value.value == "not_a_real_purpose"
    assert set(excinfo.value.valid_values) == {
        "execute_projects",
        "produce_knowledge",
        "agent_memory",
        "study",
    }


def test_missing_fields_take_priority_over_invalid_enum_values() -> None:
    payload = {"purpose": "not_a_real_purpose"}  # falta + inválido a la vez

    with pytest.raises(MissingFieldsError):
        validate_diagnose_request(payload)


# --- Estado 3: knowledge/benchmark.yaml no disponible/corrupto -> 500 -----


def test_get_benchmark_returns_the_real_benchmark() -> None:
    benchmark = get_benchmark(force_reload=True)
    assert benchmark.version == "1.0.0"


def test_get_benchmark_propagates_load_error_without_silent_fallback(monkeypatch) -> None:
    def _always_fails(*args, **kwargs):
        raise LoaderBenchmarkLoadError("simulado: archivo corrupto")

    monkeypatch.setattr("app.errors.knowledge_errors.load_benchmark", _always_fails)

    with pytest.raises(BenchmarkLoadError, match="simulado"):
        get_benchmark(force_reload=True)

    # Segunda llamada: sigue fallando explícito, no cachea un benchmark vacío.
    with pytest.raises(BenchmarkLoadError, match="simulado"):
        get_benchmark()


def test_get_benchmark_recovers_after_force_reload_once_fixed(monkeypatch) -> None:
    def _always_fails(*args, **kwargs):
        raise LoaderBenchmarkLoadError("simulado: archivo corrupto")

    monkeypatch.setattr("app.errors.knowledge_errors.load_benchmark", _always_fails)
    with pytest.raises(BenchmarkLoadError):
        get_benchmark(force_reload=True)

    monkeypatch.undo()
    benchmark = get_benchmark(force_reload=True)
    assert benchmark.version == "1.0.0"
