"""Abuse pattern library for Cognitive IDS (Story 11-4)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class AbusePattern:
    """Immutable abuse pattern definition."""

    id: str
    name: str
    category: str
    regex: str
    severity: str
    response: str


@dataclass
class AbuseMatch:
    """Match result for a pattern."""

    pattern_id: str
    name: str
    category: str
    severity: str
    response: str
    matched_text: str


class AbusePatternLibrary:
    """Loads and evaluates regex-based abuse patterns."""

    def __init__(self, config_path: Path | str = Path("config/abuse_patterns.json")) -> None:
        self.config_path = Path(config_path)
        self.patterns: List[AbusePattern] = []
        self.categories: List[str] = []
        self.default_policy: str = "suspicious"
        self.version: str = "0.0.0"
        self._compiled: List[tuple[AbusePattern, re.Pattern[str]]] = []

        self._load()

    # ---- Public API -----------------------------------------------------

    @property
    def immutable(self) -> bool:
        """Patterns are immutable at runtime."""
        return True

    def add_pattern(self, *_: object, **__: object) -> None:  # pragma: no cover - defensive
        """Explicitly block runtime mutation."""
        raise RuntimeError("Abuse patterns are immutable at runtime")

    def match(self, text: str) -> List[AbuseMatch]:
        """Return all pattern matches for the given text."""
        matches: List[AbuseMatch] = []
        for pattern, compiled in self._compiled:
            m = compiled.search(text)
            if m:
                matches.append(
                    AbuseMatch(
                        pattern_id=pattern.id,
                        name=pattern.name,
                        category=pattern.category,
                        severity=pattern.severity,
                        response=pattern.response,
                        matched_text=m.group(0),
                    )
                )
        return matches

    def evaluate(self, text: str) -> Dict[str, object]:
        """Evaluate text and return matches plus default policy if none."""
        matches = self.match(text)
        alert = bool(matches)
        top_severity = self._highest_severity([m.severity for m in matches]) if matches else "low"
        action = matches[0].response if matches else self.default_policy
        return {
            "alert": alert,
            "severity": top_severity,
            "action": action,
            "matches": matches,
            "policy": self.default_policy if not matches else "explicit",
        }

    # ---- Internal helpers -----------------------------------------------

    def _load(self) -> None:
        if not self.config_path.exists():
            logger.error("abuse_patterns_missing", path=str(self.config_path))
            return

        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("abuse_patterns_load_failed", path=str(self.config_path), error=str(exc))
            return

        self.version = raw.get("version", "0.0.0")
        self.default_policy = raw.get("default_policy", "suspicious")
        self.categories = raw.get("categories", [])

        patterns: List[AbusePattern] = []
        for item in raw.get("patterns", []):
            try:
                patterns.append(
                    AbusePattern(
                        id=item["id"],
                        name=item["name"],
                        category=item["category"],
                        regex=item["regex"],
                        severity=item.get("severity", "medium"),
                        response=item.get("response", "alert"),
                    )
                )
            except KeyError as exc:  # pragma: no cover - defensive
                logger.warning("abuse_pattern_invalid", missing=str(exc), pattern=item)

        self.patterns = patterns
        self._compiled = [
            (pattern, re.compile(pattern.regex, re.IGNORECASE | re.MULTILINE))
            for pattern in self.patterns
        ]

        logger.info(
            "abuse_patterns_loaded",
            count=len(self.patterns),
            categories=self.categories,
            version=self.version,
        )

    def _highest_severity(self, severities: List[str]) -> str:
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        best = max(severities, key=lambda s: order.get(s, 0))
        return best
