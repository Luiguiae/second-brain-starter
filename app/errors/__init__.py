"""Estados de error explícitos (Fase 4 — docs/tasks.md).

Sin fallback silencioso (AGENTS.md, invariante 4): cada estado de error
de docs/SPEC.md ("Estados de error") tiene una excepción propia que los
canales (Fase 5 REST, Fase 6 MCP) traducen a su formato de transporte,
sin nunca atraparla para devolver una recomendación parcial o inventada.
"""

from app.errors.knowledge_errors import BenchmarkLoadError, get_benchmark
from app.errors.validation import (
    InvalidEnumValueError,
    MissingFieldsError,
    validate_diagnose_request,
)

__all__ = [
    "BenchmarkLoadError",
    "get_benchmark",
    "InvalidEnumValueError",
    "MissingFieldsError",
    "validate_diagnose_request",
]
