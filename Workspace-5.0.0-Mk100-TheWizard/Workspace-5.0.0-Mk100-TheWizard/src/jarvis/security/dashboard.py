"""Gateway dashboard aggregations for the Cognitive Security Control Plane."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

import structlog

from jarvis.security.cids import CognitiveIntrusionDetectionService

logger = structlog.get_logger(__name__)


class GatewayDashboard:
    """Computes dashboard-ready metrics from C-IDS events."""

    def __init__(self, cids: CognitiveIntrusionDetectionService) -> None:
        self.cids = cids

    def snapshot(self) -> Dict[str, Any]:
        events = self.cids.events
        data = {
            "denial_rate": self._denial_rate(events),
            "top_patterns": self._top_patterns(events),
            "provider_distribution": self.cids.correlation_tracker.provider_distribution(),
            "budget_utilization": self.cids.correlation_tracker.budget_utilization(),
            "intent_alerts": self._intent_alerts(events),
            "governance_events": self._governance_events(),
        }
        return data

    def _denial_rate(self, events) -> Dict[str, Dict[str, float]]:
        by_agent: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for event in events:
            by_agent[event.agent_id]["total"] += 1
            if event.action == "deny" or event.alert:
                by_agent[event.agent_id]["denied"] += 1
        return {
            agent: {
                "denied": counts.get("denied", 0),
                "total": counts.get("total", 0),
                "rate": round(counts.get("denied", 0) / counts.get("total", 1), 3),
            }
            for agent, counts in by_agent.items()
        }

    def _top_patterns(self, events) -> List[tuple]:
        counter: Counter[str] = Counter()
        for event in events:
            counter.update(event.patterns)
        return counter.most_common(5)

    def _intent_alerts(self, events) -> List[Dict[str, Any]]:
        alerts = []
        for event in events:
            if any(p.startswith("intent_") for p in event.patterns):
                alerts.append({
                    "agent_id": event.agent_id,
                    "intent_class": event.intent_class,
                    "severity": event.severity,
                    "patterns": event.patterns,
                    "timestamp": event.timestamp,
                })
        return alerts

    def _governance_events(self) -> List[Dict[str, Any]]:
        getter = getattr(self.cids.drift_detector, "get_alerts", None)
        if callable(getter):
            try:
                return list(getter())
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("dashboard_governance_events_failed", error=str(exc))
        return []
