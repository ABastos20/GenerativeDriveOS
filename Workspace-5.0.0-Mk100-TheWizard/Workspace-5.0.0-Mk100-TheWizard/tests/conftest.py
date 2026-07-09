"""Test configuration shared across the suite.

Adds the repository ``src`` directory to ``sys.path`` so imports using
``src.jarvis`` work without requiring PYTHONPATH tweaks in every test run.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"

# Allow imports like `src.jarvis.*` (namespace package) and `jarvis.*`.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import structlog

# Configure structlog to write to stderr during tests to avoid polluting stdout
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

import pytest
from jarvis.database.qdrant import close_qdrant_client

@pytest.fixture(autouse=True)
def reset_qdrant_state():
    """Ensure clean Qdrant client state for every test."""
    close_qdrant_client()
    yield
    close_qdrant_client()

@pytest.fixture(autouse=True)
def reset_arches_state():
    """Reset ARCHES controller singleton state."""
    import jarvis.arches.controller as arches_mod
    arches_mod._global_controller = None
    yield
    arches_mod._global_controller = None
