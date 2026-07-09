"""Intent index and behavioral signatures (Story 11-4)."""

from __future__ import annotations

import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class IntentRecord:
    timestamp: float
    intent_class: str
    prompt: str


@dataclass
class IntentSignature:
    agent_id: str
    window_size: int
    total_events: int
    vector: Dict[str, float]
    last_intent: Optional[str]
    last_prompt: Optional[str]
    anomaly: Optional[str] = None


class IntentIndex:
    """Tracks rolling intent windows and detects behavior shifts."""

    def __init__(self, window_size: int = 25, rate_limit: int = 5, rate_window_seconds: int = 300) -> None:
        self.window_size = window_size
        self.rate_limit = rate_limit
        self.rate_window_seconds = rate_window_seconds
        self._records: Dict[str, Deque[IntentRecord]] = defaultdict(deque)

    # ---- Public API -----------------------------------------------------

    def track(self, agent_id: str, prompt: str, intent_class: str, timestamp: Optional[float] = None) -> None:
        ts = timestamp or time.time()
        records = self._records[agent_id]
        records.append(IntentRecord(timestamp=ts, intent_class=intent_class, prompt=prompt))

        while len(records) > self.window_size:
            records.popleft()

    def get_signature(self, agent_id: str) -> IntentSignature:
        records = self._records.get(agent_id, deque())
        vector = self._build_vector(records)
        last = records[-1] if records else None
        anomaly = self.detect_shift(agent_id)
        return IntentSignature(
            agent_id=agent_id,
            window_size=self.window_size,
            total_events=len(records),
            vector=vector,
            last_intent=last.intent_class if last else None,
            last_prompt=last.prompt if last else None,
            anomaly=anomaly.get("kind") if isinstance(anomaly, dict) else None,
        )

    def detect_shift(self, agent_id: str) -> Optional[Dict[str, str]]:
        records = list(self._records.get(agent_id, deque()))
        if len(records) < 4:
            return None

        mid = len(records) // 2
        first, second = records[:mid], records[mid:]
        dom_first = Counter(r.intent_class for r in first).most_common(1)[0][0]
        dom_second = Counter(r.intent_class for r in second).most_common(1)[0][0]

        if dom_first != dom_second:
            logger.warning(
                "intent_shift_detected",
                agent_id=agent_id,
                from_intent=dom_first,
                to_intent=dom_second,
            )
            return {"kind": "intent_shift", "from": dom_first, "to": dom_second}
        return None

    def check_rate_limit(self, agent_id: str, intent_class: str, timestamp: Optional[float] = None) -> bool:
        ts = timestamp or time.time()
        records = self._records.get(agent_id, deque())
        recent = [r for r in records if r.intent_class == intent_class and r.timestamp >= ts - self.rate_window_seconds]
        return len(recent) >= self.rate_limit

    # ---- Internal helpers -----------------------------------------------

    def _build_vector(self, records: List[IntentRecord] | Deque[IntentRecord]) -> Dict[str, float]:
        total = len(records)
        if total == 0:
            return {}
        counts = Counter(r.intent_class for r in records)
        return {intent: round(count / total, 3) for intent, count in counts.items()}
