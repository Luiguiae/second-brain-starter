from __future__ import annotations

import pytest

from app.knowledge.loader import load_benchmark
from app.knowledge.schema import Benchmark


@pytest.fixture(scope="session")
def benchmark() -> Benchmark:
    return load_benchmark()
