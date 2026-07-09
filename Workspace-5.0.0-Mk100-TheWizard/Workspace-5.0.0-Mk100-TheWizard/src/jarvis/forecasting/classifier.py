"""Forecast vs fact classifier (Story 11-7)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Tuple
import structlog

logger = structlog.get_logger(__name__)

FUTURE_TERMS = [
    r"\bwill\b",
    r"\bforecast\b",
    r"\bexpected\b",
    r"\bproject(ed)?\b",
    r"\bnext quarter\b",
    r"\bin \d+ (days|weeks|months|years)\b",
]


@dataclass
class ForecastClassification:
    is_forecast: bool
    confidence: float
    knowledge_class: str
    confidence_interval: Tuple[float, float] | None = None


class ForecastClassifier:
    """Heuristic forecast detector with confidence labeling."""

    def __init__(self, min_confidence: float = 0.15) -> None:
        self.min_confidence = min_confidence
        self.patterns = [re.compile(pat, re.IGNORECASE) for pat in FUTURE_TERMS]

    def classify(self, content: str, metadata: Dict | None = None) -> ForecastClassification:
        hits = sum(1 for pat in self.patterns if pat.search(content or ""))
        confidence = min(1.0, hits / max(1, len(self.patterns)))
        is_forecast = confidence >= self.min_confidence
        ci = metadata.get("confidence_interval") if isinstance(metadata, dict) else None
        result = ForecastClassification(
            is_forecast=is_forecast,
            confidence=round(confidence, 3),
            knowledge_class="forecast" if is_forecast else metadata.get("knowledge_class", "unknown") if isinstance(metadata, dict) else "unknown",
            confidence_interval=ci if is_forecast else None,
        )
        logger.info(
            "forecast_classified",
            is_forecast=is_forecast,
            confidence=result.confidence,
            knowledge_class=result.knowledge_class,
        )
        return result
