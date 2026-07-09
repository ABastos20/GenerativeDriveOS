"""Synthetic origin tagging utilities (Story 11-7)."""

from __future__ import annotations

import hashlib
import structlog
from dataclasses import dataclass, asdict
from typing import Dict, Optional

from jarvis.simulation.origins import OriginType

logger = structlog.get_logger(__name__)


@dataclass
class SyntheticTag:
    """Metadata applied to any synthetic output."""

    origin: OriginType
    generator_id: str
    model_version: str
    prompt_hash: str

    def as_dict(self) -> Dict[str, str]:
        return {**asdict(self), "origin": self.origin.value}


def hash_prompt(prompt: str) -> str:
    """Stable hash for prompt lineage tracking."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def tag_output(
    content: str,
    generator_id: str,
    model_version: str,
    prompt: str,
) -> SyntheticTag:
    """Create a synthetic tag for generated content."""
    tag = SyntheticTag(
        origin=OriginType.SYNTHETIC,
        generator_id=generator_id,
        model_version=model_version,
        prompt_hash=hash_prompt(prompt),
    )
    logger.info(
        "synthetic_tag_applied",
        generator_id=generator_id,
        model_version=model_version,
        prompt_hash=tag.prompt_hash,
        content_preview=content[:80],
    )
    return tag


def is_synthetic(metadata: Optional[Dict]) -> bool:
    """Detect synthetic origin from metadata."""
    if not metadata:
        return False
    origin = metadata.get("origin") or metadata.get("origin_type")
    return str(origin) == OriginType.SYNTHETIC.value
