"""Schema formal de `knowledge/benchmark.yaml` (Fase 1, T05 — docs/tasks.md).

Este módulo es la fuente canónica de los enums del diagnóstico
(`Purpose`, `MaintenanceTolerance`, `AgentUsage`, `CaptureVolume`,
`TechnicalProfile`) y de los ids de arquetipo (`ArchetypeId`). La Fase 2
(app/models) los importa desde aquí en vez de redefinirlos, para que el
benchmark y los modelos de request/response nunca puedan divergir sin que
un test lo detecte (ver AGENTS.md, invariante 2).

`Benchmark` es el modelo raíz que valida `knowledge/benchmark.yaml` completo,
incluyendo referencias cruzadas (todo `source_ref`/`system_ref` citado en
una regla de decisión debe existir en `sources`/`systems`; cada arquetipo
debe tener entre 3 y 5 skills base; `clasificador-de-fuentes` debe existir
y estar disponible para los 4 arquetipos).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# --- Enums canónicos (ver docs/SPEC.md, sección "Esquema de datos") -------

Purpose = Literal["execute_projects", "produce_knowledge", "agent_memory", "study"]
MaintenanceTolerance = Literal["low", "medium", "high"]
AgentUsage = Literal["already_using", "want_to_start", "not_interested"]
CaptureVolume = Literal["sporadic", "daily_moderate", "high_multi_source"]
TechnicalProfile = Literal["markdown_git_comfortable", "prefers_visual_ui"]
ArchetypeId = Literal["action_first", "knowledge_first", "agent_first", "hybrid"]

DIMENSION_IDS = (
    "purpose",
    "maintenance_tolerance",
    "agent_usage",
    "capture_volume",
    "technical_profile",
)

DIMENSION_VALUES: dict[str, tuple[str, ...]] = {
    "purpose": ("execute_projects", "produce_knowledge", "agent_memory", "study"),
    "maintenance_tolerance": ("low", "medium", "high"),
    "agent_usage": ("already_using", "want_to_start", "not_interested"),
    "capture_volume": ("sporadic", "daily_moderate", "high_multi_source"),
    "technical_profile": ("markdown_git_comfortable", "prefers_visual_ui"),
}

ARCHETYPE_IDS = ("action_first", "knowledge_first", "agent_first", "hybrid")
BASE_ARCHETYPE_IDS = ("action_first", "knowledge_first", "agent_first")


# --- Bloques de datos -------------------------------------------------------


class Source(BaseModel):
    """Una fuente citable, tomada de "Fuentes principales" en docs/BENCHMARK.md."""

    id: str
    description: str
    url: str | None = None


class System(BaseModel):
    """Una fila de la "Tabla comparativa" en docs/BENCHMARK.md."""

    id: str
    name: str
    type: str
    setup: str
    maintenance: str
    connects_ideas: str
    manages_action: str
    requires_ai_agent: bool
    best_for: str
    source_refs: list[str] = Field(default_factory=list)


class Archetype(BaseModel):
    id: ArchetypeId
    name: str
    description: str
    folders: list[str]
    frontmatter_fields: list[str]


class DimensionOption(BaseModel):
    value: str
    label: str


class Dimension(BaseModel):
    """Una de las 5 dimensiones del diagnóstico, copy 1:1 de docs/SPEC.md."""

    id: Literal[
        "purpose",
        "maintenance_tolerance",
        "agent_usage",
        "capture_volume",
        "technical_profile",
    ]
    question: str
    options: list[DimensionOption]

    @model_validator(mode="after")
    def _options_match_canonical_enum(self) -> Dimension:
        expected = set(DIMENSION_VALUES[self.id])
        actual = {opt.value for opt in self.options}
        if actual != expected:
            raise ValueError(
                f"dimension '{self.id}' options {sorted(actual)} no coinciden "
                f"con el enum canónico {sorted(expected)}"
            )
        return self


class SkillCatalogEntry(BaseModel):
    id: str
    name: str
    description: str
    format: Literal["markdown_descriptive"] = "markdown_descriptive"
    archetypes: list[ArchetypeId]
    priority: int = Field(
        description=(
            "Menor = más prioritaria para conservarse. Usada para reemplazar "
            "la skill de menor prioridad de un set ya en 5 elementos cuando "
            "capture_volume == 'high_multi_source' obliga a insertar "
            "clasificador-de-fuentes (ver docs/SPEC.md, modificador de "
            "capture_volume, y tasks.md T14)."
        )
    )


class BaseArchetypeRule(BaseModel):
    """Selección de arquetipo base por Dimensión 1 (purpose)."""

    purpose: Purpose
    archetype: ArchetypeId
    note: str | None = None
    source_refs: list[str]


class HybridModifierRule(BaseModel):
    """Dimensión 3: agent_usage en {already_using, want_to_start} -> hybrid."""

    trigger_agent_usage: list[AgentUsage]
    source_refs: list[str]


class LytModifierRule(BaseModel):
    """Dimensión 2: maintenance_tolerance == low + base knowledge_first -> LYT/MOCs."""

    trigger_maintenance_tolerance: MaintenanceTolerance
    applies_to_base_archetype: ArchetypeId
    note: str
    source_refs: list[str]


class CaptureVolumeModifierRule(BaseModel):
    """Modificador de capture_volume — afecta folders y, en el extremo, skills."""

    value: CaptureVolume
    add_folders: list[str] = Field(default_factory=list)
    add_skill_id: str | None = None
    source_refs: list[str] = Field(default_factory=list)


class TechnicalProfileModifierRule(BaseModel):
    """Modificador de technical_profile — afecta solo justification.

    `default_system_ref` se usa cuando la cita no depende del arquetipo
    (markdown_git_comfortable). `system_ref_by_archetype` se usa cuando sí
    depende del arquetipo resultante (prefers_visual_ui: "Obsidian/Notion/
    Tana según el arquetipo", citando la fila de `systems` correspondiente).
    Ambos citan ids de `systems`, no de `sources` — así lo exige el spec
    ("citando la fila correspondiente de systems en el benchmark").
    """

    value: TechnicalProfile
    justification_template: str
    default_system_ref: str
    system_ref_by_archetype: dict[ArchetypeId, str] | None = None


class DecisionRules(BaseModel):
    base_by_purpose: list[BaseArchetypeRule]
    hybrid_modifier: HybridModifierRule
    lyt_modifier: LytModifierRule
    capture_volume_modifiers: list[CaptureVolumeModifierRule]
    technical_profile_modifiers: list[TechnicalProfileModifierRule]

    @model_validator(mode="after")
    def _covers_all_dimension_values(self) -> DecisionRules:
        purposes = {r.purpose for r in self.base_by_purpose}
        if purposes != set(DIMENSION_VALUES["purpose"]):
            raise ValueError(
                f"base_by_purpose debe cubrir todos los purpose, falta: "
                f"{set(DIMENSION_VALUES['purpose']) - purposes}"
            )
        cv_values = {r.value for r in self.capture_volume_modifiers}
        if cv_values != set(DIMENSION_VALUES["capture_volume"]):
            raise ValueError(
                f"capture_volume_modifiers debe cubrir todos los valores, falta: "
                f"{set(DIMENSION_VALUES['capture_volume']) - cv_values}"
            )
        tp_values = {r.value for r in self.technical_profile_modifiers}
        if tp_values != set(DIMENSION_VALUES["technical_profile"]):
            raise ValueError(
                f"technical_profile_modifiers debe cubrir todos los valores, falta: "
                f"{set(DIMENSION_VALUES['technical_profile']) - tp_values}"
            )
        return self


class Benchmark(BaseModel):
    """Modelo raíz de `knowledge/benchmark.yaml`."""

    version: str
    sources: list[Source]
    systems: list[System]
    archetypes: list[Archetype]
    dimensions: list[Dimension]
    decision_rules: DecisionRules
    skills_catalog: list[SkillCatalogEntry]

    @model_validator(mode="after")
    def _cross_references_resolve(self) -> Benchmark:
        source_ids = {s.id for s in self.sources}
        system_ids = {s.id for s in self.systems}
        archetype_ids = {a.id for a in self.archetypes}
        skill_ids = {s.id for s in self.skills_catalog}

        if archetype_ids != set(ARCHETYPE_IDS):
            raise ValueError(
                f"archetypes debe definir exactamente {ARCHETYPE_IDS}, "
                f"llegó {sorted(archetype_ids)}"
            )
        if {d.id for d in self.dimensions} != set(DIMENSION_IDS):
            raise ValueError("dimensions debe definir exactamente las 5 dimensiones canónicas")

        def _check_source_refs(refs: list[str], where: str) -> None:
            missing = [r for r in refs if r not in source_ids]
            if missing:
                raise ValueError(f"{where} referencia source_ref(s) inexistentes: {missing}")

        def _check_system_ref(ref: str, where: str) -> None:
            if ref not in system_ids:
                raise ValueError(f"{where} referencia un system_ref inexistente: {ref}")

        for system in self.systems:
            _check_source_refs(system.source_refs, f"systems[{system.id}].source_refs")

        for rule in self.decision_rules.base_by_purpose:
            _check_source_refs(
                rule.source_refs, f"decision_rules.base_by_purpose[{rule.purpose}].source_refs"
            )
        _check_source_refs(
            self.decision_rules.hybrid_modifier.source_refs,
            "decision_rules.hybrid_modifier.source_refs",
        )
        _check_source_refs(
            self.decision_rules.lyt_modifier.source_refs, "decision_rules.lyt_modifier.source_refs"
        )
        for cv in self.decision_rules.capture_volume_modifiers:
            _check_source_refs(
                cv.source_refs, f"decision_rules.capture_volume_modifiers[{cv.value}].source_refs"
            )
            if cv.add_skill_id and cv.add_skill_id not in skill_ids:
                raise ValueError(
                    f"capture_volume_modifiers[{cv.value}].add_skill_id "
                    f"'{cv.add_skill_id}' no está en skills_catalog"
                )
        for tp in self.decision_rules.technical_profile_modifiers:
            _check_system_ref(
                tp.default_system_ref,
                f"decision_rules.technical_profile_modifiers[{tp.value}].default_system_ref",
            )
            if tp.system_ref_by_archetype:
                for arch, ref in tp.system_ref_by_archetype.items():
                    _check_system_ref(
                        ref,
                        f"decision_rules.technical_profile_modifiers[{tp.value}]"
                        f".system_ref_by_archetype[{arch}]",
                    )

        for skill in self.skills_catalog:
            for arch in skill.archetypes:
                if arch not in archetype_ids:
                    raise ValueError(
                        f"skills_catalog[{skill.id}] referencia un arquetipo inexistente: {arch}"
                    )

        clasificador = [s for s in self.skills_catalog if s.id == "clasificador-de-fuentes"]
        if not clasificador:
            raise ValueError(
                "skills_catalog debe incluir 'clasificador-de-fuentes' "
                "(ver docs/SPEC.md, modificador de capture_volume)"
            )
        if set(clasificador[0].archetypes) != archetype_ids:
            raise ValueError(
                "'clasificador-de-fuentes' debe estar disponible para los 4 arquetipos"
            )

        # El conteo de 3-5 skills "base" aplica a los 3 arquetipos base;
        # el set de 'hybrid' se compone en tiempo de decisión (Fase 3, T14)
        # combinando los sets base, no se pre-declara aquí.
        for arch_id in BASE_ARCHETYPE_IDS:
            count = sum(
                1
                for s in self.skills_catalog
                if arch_id in s.archetypes and s.id != "clasificador-de-fuentes"
            )
            if not (3 <= count <= 5):
                raise ValueError(
                    f"archetype '{arch_id}' debe tener entre 3 y 5 skills base "
                    f"(sin contar clasificador-de-fuentes), tiene {count}"
                )

        return self
