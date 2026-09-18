"""Modelos de dominio compartidos (Fase 2, T09 — docs/tasks.md).

`CreateSecondBrainPlanRequest` y `CreateSecondBrainPlanResponse` son el
**único** lugar donde se define la forma de entrada/salida del plan
(docs/SPEC.md, "Esquema de datos"). Tanto el canal REST (Fase 5) como el
MCP (Fase 6) importan estos modelos en vez de redefinirlos — es la
garantía estructural de que ambos validan contra "el mismo JSON Schema"
que exige el spec (AGENTS.md, invariante 2).

Los enums se importan de `app.knowledge.schema` (la fuente canónica fijada
en Fase 1, T05) en vez de redeclararse a mano, para que el benchmark y
estos modelos no puedan divergir sin que un test lo note.

Historial de renombres (docs/SPEC.md, "Historial de renombres"): hasta
v1.0.x este módulo se llamaba `diagnose.py` y estos modelos
`DiagnoseRequest`/`DiagnoseResponse`. Renombrado en v2.0.0 porque
"diagnóstico" implica evaluar algo existente, y esta herramienta crea un
Segundo Cerebro desde cero — cambio de nombre únicamente, el
comportamiento (validación, campos, enums) no cambió.
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


class CreateSecondBrainPlanRequest(BaseModel):
    """Entrada de `POST /plan` (y de la tool MCP `create_second_brain_plan`)."""

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
    folder_purposes: dict[str, str] = Field(
        description=(
            "Propósito de cada carpeta de `folders`, en 1-2 frases en lenguaje "
            "humano (docs/SPEC.md, 'Catálogo de propósito por carpeta'). Cubre "
            "cada carpeta de `folders` sin excepciones — nunca solo un "
            "subconjunto. Pensado para que el agente llamador escriba el "
            "README.md de cada carpeta y le explique el propósito a la "
            "persona, no solo liste nombres (ver 'Contrato de interacción con "
            "el agente llamador')."
        )
    )
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


class CreateSecondBrainPlanResponse(BaseModel):
    """Salida de `POST /plan` (y de la tool MCP `create_second_brain_plan`)."""

    archetype: ArchetypeId
    justification: list[str] = Field(
        description="Cada string cita una fuente/sistema de knowledge/benchmark.yaml."
    )
    structure: Structure
    skills: list[SkillOutput] = Field(description="Entre 3 y 5 skills iniciales.")
