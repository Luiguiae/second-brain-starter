"""Validación de entrada — estados de error 422/400 (Fase 4, T17-T18 — docs/tasks.md).

Envuelve la validación de Pydantic de `CreateSecondBrainPlanRequest`,
distinguiendo dos estados de error explícitos y distintos (docs/SPEC.md,
"Estados de error"):

- Campos obligatorios faltantes → `MissingFieldsError` (422), con la
  lista exacta de campos faltantes.
- Valor fuera del enum permitido → `InvalidEnumValueError` (400), con el
  campo y sus valores válidos.

Si un payload tiene ambos problemas a la vez, se reporta como campos
faltantes primero (422) — es el error más "estructural"; una vez
resueltos los campos faltantes, un segundo request expondría el/los
valores inválidos.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.knowledge.schema import DIMENSION_VALUES
from app.models.plan import CreateSecondBrainPlanRequest


class MissingFieldsError(Exception):
    """422: uno o más campos obligatorios faltan en el payload."""

    def __init__(self, missing_fields: list[str]) -> None:
        self.missing_fields = missing_fields
        super().__init__(f"Campos obligatorios faltantes: {missing_fields}")


class InvalidEnumValueError(Exception):
    """400: un campo tiene un valor fuera del enum permitido."""

    def __init__(self, field: str, value: Any, valid_values: list[str]) -> None:
        self.field = field
        self.value = value
        self.valid_values = valid_values
        super().__init__(
            f"Valor inválido para '{field}': {value!r}. Válidos: {valid_values}"
        )


def classify_validation_errors(
    errors: list[dict[str, Any]],
) -> MissingFieldsError | InvalidEnumValueError:
    """Clasifica los errores crudos de un `pydantic.ValidationError`.

    Se usa tanto desde `validate_create_plan_request` (abajo, para MCP y
    para cualquier validación manual) como desde el exception handler de
    `RequestValidationError` del canal REST (Fase 5, T23) — una sola
    implementación de la clasificación, dos puntos de entrada, para que
    ambos canales clasifiquen exactamente igual (Fase 7, T29).

    `loc[-1]` en vez de `loc[0]`: FastAPI antepone `"body"` al `loc` de
    los errores del body (`("body", "purpose")`), mientras que una
    validación directa contra `CreateSecondBrainPlanRequest.model_validate`
    produce `("purpose",)` — `loc[-1]` funciona igual en ambos casos.
    """
    missing = sorted({str(e["loc"][-1]) for e in errors if e["type"] == "missing"})
    if missing:
        return MissingFieldsError(missing_fields=missing)

    first = errors[0]
    field_name = str(first["loc"][-1]) if first["loc"] else "unknown"
    return InvalidEnumValueError(
        field=field_name,
        value=first.get("input"),
        valid_values=list(DIMENSION_VALUES.get(field_name, [])),
    )


def validate_create_plan_request(payload: dict[str, Any]) -> CreateSecondBrainPlanRequest:
    """Valida un payload crudo (p. ej. el JSON de un request HTTP o de una tool MCP).

    Raises:
        MissingFieldsError: si falta algún campo obligatorio.
        InvalidEnumValueError: si no falta ningún campo pero alguno tiene
            un valor fuera de enum (o, más en general, no pasa la
            validación de tipo/formato de Pydantic).
    """
    try:
        return CreateSecondBrainPlanRequest.model_validate(payload)
    except ValidationError as exc:
        raise classify_validation_errors(exc.errors()) from exc
