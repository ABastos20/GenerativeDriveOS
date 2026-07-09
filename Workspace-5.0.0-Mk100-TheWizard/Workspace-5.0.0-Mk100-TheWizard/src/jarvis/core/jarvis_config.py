"""Helpers for accessing Jarvis core docs within the repo.
This module centralizes paths and simple loaders for:
- Persona definition
- Operating manual
- GD overview
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.jarvis.config.settings import load_settings

_settings = load_settings()
JARVIS_DOCS_DIR = _settings.docs.get_jarvis_docs_dir()


def _read_if_exists(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def get_persona_text() -> Optional[str]:
    """Return the Jarvis persona document contents, if present."""
    return _read_if_exists(JARVIS_DOCS_DIR / "persona.md")


def get_operating_manual_text() -> Optional[str]:
    """Return the Jarvis operating manual contents, if present."""
    return _read_if_exists(JARVIS_DOCS_DIR / "operating-manual.md")


def get_gd_overview_text() -> Optional[str]:
    """Return the GenerativeDrive overview contents, if present."""
    return _read_if_exists(JARVIS_DOCS_DIR / "gd-overview.md")
