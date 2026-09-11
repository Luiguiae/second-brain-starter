"""T11 (docs/tasks.md, Fase 2): modelos de dominio compartidos.

Instancia los modelos con los ejemplos exactos de docs/SPEC.md (sección
"Esquema de datos"), verifica round-trip de serialización, y que cada
enum inválido lanza ValidationError.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.diagnose import DiagnoseRequest, DiagnoseResponse, SkillOutput, Structure
from app.models.schema_export import diagnose_request_json_schema, diagnose_response_json_schema

# Ejemplo exacto de docs/SPEC.md, "Esquema de datos" -> Entrada.
SPEC_REQUEST_EXAMPLE = {
    "purpose": "execute_projects",
    "maintenance_tolerance": "medium",
    "agent_usage": "already_using",
    "capture_volume": "daily_moderate",
    "technical_profile": "markdown_git_comfortable",
}

# Ejemplo exacto de docs/SPEC.md, "Esquema de datos" -> Salida.
SPEC_RESPONSE_EXAMPLE = {
    "archetype": "hybrid",
    "justification": ["string (con referencia a la fuente del benchmark)"],
    "structure": {"folders": ["string"], "frontmatter_fields": ["string"]},
    "skills": [{"name": "string", "description": "string", "format": "markdown_descriptive"}],
}


def test_request_example_from_spec_validates() -> None:
    request = DiagnoseRequest.model_validate(SPEC_REQUEST_EXAMPLE)
    assert request.purpose == "execute_projects"
    assert request.capture_volume == "daily_moderate"
    assert request.technical_profile == "markdown_git_comfortable"


def test_response_example_from_spec_validates() -> None:
    response = DiagnoseResponse.model_validate(SPEC_RESPONSE_EXAMPLE)
    assert response.archetype == "hybrid"
    assert response.structure == Structure(folders=["string"], frontmatter_fields=["string"])
    assert response.skills == [
        SkillOutput(name="string", description="string", format="markdown_descriptive")
    ]


def test_request_round_trip_serialization() -> None:
    request = DiagnoseRequest.model_validate(SPEC_REQUEST_EXAMPLE)
    round_tripped = DiagnoseRequest.model_validate_json(request.model_dump_json())
    assert round_tripped == request


def test_response_round_trip_serialization() -> None:
    response = DiagnoseResponse.model_validate(SPEC_RESPONSE_EXAMPLE)
    round_tripped = DiagnoseResponse.model_validate_json(response.model_dump_json())
    assert round_tripped == response


@pytest.mark.parametrize(
    "field,invalid_value",
    [
        ("purpose", "invalid_purpose"),
        ("maintenance_tolerance", "extreme"),
        ("agent_usage", "maybe"),
        ("capture_volume", "constant"),
        ("technical_profile", "no_preference"),
    ],
)
def test_request_rejects_out_of_enum_values(field: str, invalid_value: str) -> None:
    payload = {**SPEC_REQUEST_EXAMPLE, field: invalid_value}
    with pytest.raises(ValidationError):
        DiagnoseRequest.model_validate(payload)


def test_request_rejects_missing_fields() -> None:
    with pytest.raises(ValidationError):
        DiagnoseRequest.model_validate({"purpose": "execute_projects"})


def test_response_rejects_invalid_archetype() -> None:
    payload = {**SPEC_RESPONSE_EXAMPLE, "archetype": "not_a_real_archetype"}
    with pytest.raises(ValidationError):
        DiagnoseResponse.model_validate(payload)


def test_exported_json_schema_has_the_five_dimensions() -> None:
    schema = diagnose_request_json_schema()
    assert set(schema["properties"]) == {
        "purpose",
        "maintenance_tolerance",
        "agent_usage",
        "capture_volume",
        "technical_profile",
    }


def test_exported_response_json_schema_has_the_four_output_fields() -> None:
    schema = diagnose_response_json_schema()
    assert set(schema["properties"]) == {"archetype", "justification", "structure", "skills"}
