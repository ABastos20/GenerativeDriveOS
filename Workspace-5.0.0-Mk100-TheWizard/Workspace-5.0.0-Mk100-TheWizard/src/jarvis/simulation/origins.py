"""Origin types for synthetic sovereignty (Story 11-7)."""

from __future__ import annotations

from enum import Enum


class OriginType(str, Enum):
    """Canonical origin classification for knowledge artifacts."""

    OBSERVED = "observed"
    REPORTED = "reported"
    SYNTHETIC = "synthetic"

