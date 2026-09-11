"""Validación de entrada — estados de error 422/400 (Fase 4, T17-T18 — docs/tasks.md).

Envuelve la validación de Pydantic de `DiagnoseRequest`, distinguiendo dos
estados de error explícitos y distintos (docs/SPEC.md, "Estados de error"):

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
from app.models.diagnose import DiagnoseRequest


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


def validate_diagnose_request(payload: dict[str, Any]) -> DiagnoseRequest:
    """Valida un payload crudo (p. ej. el JSON de un request HTTP o de una tool MCP).

    Raises:
        MissingFieldsError: si falta algún campo obligatorio.
        InvalidEnumValueError: si no falta ningún campo pero alguno tiene
            un valor fuera de enum (o, más en general, no pasa la
            validación de tipo/formato de Pydantic).
    """
    try:
        return DiagnoseRequest.model_validate(payload)
    except ValidationError as exc:
        errors = exc.errors()

        missing = sorted({str(e["loc"][0]) for e in errors if e["type"] == "missing"})
        if missing:
            raise MissingFieldsError(missing_fields=missing) from exc

        first = errors[0]
        field_name = str(first["loc"][0]) if first["loc"] else "unknown"
        raise InvalidEnumValueError(
            field=field_name,
            value=first.get("input"),
            valid_values=list(DIMENSION_VALUES.get(field_name, [])),
        ) from exc
