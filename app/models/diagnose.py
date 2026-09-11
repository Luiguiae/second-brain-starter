"""Modelos de dominio compartidos (Fase 2, T09 — docs/tasks.md).

`DiagnoseRequest` y `DiagnoseResponse` son el **único** lugar donde se
define la forma de entrada/salida del diagnóstico (docs/SPEC.md, "Esquema
de datos"). Tanto el canal REST (Fase 5) como el MCP (Fase 6) importan
estos modelos en vez de redefinirlos — es la garantía estructural de que
ambos validan contra "el mismo JSON Schema" que exige el spec (AGENTS.md,
invariante 2).

Los enums se importan de `app.knowledge.schema` (la fuente canónica fijada
en Fase 1, T05) en vez de redeclararse a mano, para que el benchmark y
estos modelos no puedan divergir sin que un test lo note.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.knowledge.schema import (
    AgentUsage,
    ArchetypeId,
    CaptureVolume,
    MaintenanceTolerance,
    Purpose,
    TechnicalProfile,
)

SkillFormat = "markdown_descriptive"  # único formato soportado en v1 (docs/SPEC.md, Alcance)


class DiagnoseRequest(BaseModel):
    """Entrada de `POST /diagnose` (y de la tool MCP equivalente)."""

    purpose: Purpose = Field(description="Objetivo principal del Segundo Cerebro (Dimensión 1).")
    maintenance_tolerance: MaintenanceTolerance = Field(
        description="Tolerancia a mantenimiento manual (Dimensión 2)."
    )
    agent_usage: AgentUsage = Field(
        description="Uso de agentes de código sobre las notas (Dimensión 3)."
    )
    capture_volume: CaptureVolume = Field(description="Volumen de captura (Dimensión 4).")
    technical_profile: TechnicalProfile = Field(
        description="Comodidad con markdown/git vs. UI visual (Dimensión 5)."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "purpose": "execute_projects",
                    "maintenance_tolerance": "medium",
                    "agent_usage": "want_to_start",
                    "capture_volume": "daily_moderate",
                    "technical_profile": "markdown_git_comfortable",
                }
            ]
        }
    }


class Structure(BaseModel):
    folders: list[str] = Field(description="Carpetas recomendadas, relativas a la raíz del vault.")
    frontmatter_fields: list[str] = Field(
        description="Campos de frontmatter YAML recomendados para las notas."
    )


class SkillOutput(BaseModel):
    name: str
    description: str
    format: str = Field(
        default=SkillFormat,
        description="Formato de la skill. En v1, siempre 'markdown_descriptive' "
        "(docs/SPEC.md, Alcance por iteración).",
    )


class DiagnoseResponse(BaseModel):
    """Salida de `POST /diagnose` (y de la tool MCP equivalente)."""

    archetype: ArchetypeId
    justification: list[str] = Field(
        description="Cada string cita una fuente/sistema de knowledge/benchmark.yaml."
    )
    structure: Structure
    skills: list[SkillOutput] = Field(description="Entre 3 y 5 skills iniciales.")
