"""Cross-provider correlation for Cognitive IDS (Story 11-4)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ProviderEvent:
    timestamp: float
    agent_id: str
    provider: str
    intent_class: str
    action: str
    severity: str
    pattern: Optional[str] = None
    cost: float = 0.0


class ProviderCorrelationTracker:
    """Tracks LLM interactions across providers for evasion detection."""

    def __init__(self, window_seconds: int = 900) -> None:
        self.window_seconds = window_seconds
        self._events: Dict[str, Deque[ProviderEvent]] = defaultdict(deque)

    # ---- Public API -----------------------------------------------------

    def record_interaction(
        self,
        agent_id: str,
        provider: str,
        intent_class: str,
        action: str,
        severity: str,
        pattern: Optional[str] = None,
        cost: float = 0.0,
        timestamp: Optional[float] = None,
    ) -> None:
        ts = timestamp or time.time()
        events = self._events[agent_id]
        events.append(
            ProviderEvent(
                timestamp=ts,
                agent_id=agent_id,
                provider=provider,
                intent_class=intent_class,
                action=action,
                severity=severity,
                pattern=pattern,
                cost=cost,
            )
        )
        self._prune(events, ts)

    def detect_provider_hopping(self, agent_id: str) -> bool:
        events = self._recent_events(agent_id)
        providers = {event.provider for event in events}
        return len(providers) > 1

    def detect_escalation(self, agent_id: str) -> bool:
        events = self._recent_events(agent_id)
        if len(events) < 2:
            return False
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        for first, second in zip(events, events[1:]):
            if first.provider != second.provider and order.get(first.severity, 0) < order.get(second.severity, 0):
                return True
        return False

    def get_timeline(self, agent_id: str) -> List[ProviderEvent]:
        return sorted(list(self._events.get(agent_id, deque())), key=lambda e: e.timestamp)

    def provider_distribution(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for events in self._events.values():
            for event in events:
                counts[event.provider] += 1
        return dict(counts)

    def budget_utilization(self) -> Dict[str, float]:
        usage: Dict[str, float] = defaultdict(float)
        for events in self._events.values():
            for event in events:
                usage[event.provider] += event.cost
        return dict(usage)

    # ---- Internal helpers -----------------------------------------------

    def _prune(self, events: Deque[ProviderEvent], now_ts: float) -> None:
        while events and events[0].timestamp < now_ts - self.window_seconds:
            events.popleft()

    def _recent_events(self, agent_id: str) -> List[ProviderEvent]:
        now_ts = time.time()
        events = self._events.get(agent_id, deque())
        return [e for e in events if e.timestamp >= now_ts - self.window_seconds]
