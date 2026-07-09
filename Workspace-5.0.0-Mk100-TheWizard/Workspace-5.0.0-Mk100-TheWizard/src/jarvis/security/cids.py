"""Cognitive Intrusion Detection Service (Story 11-4) with legacy compatibility."""

from __future__ import annotations

import difflib
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Dict, List, Optional

import structlog

from jarvis.governance.capabilities import PromptDriftDetector, get_drift_detector
from jarvis.security.abuse_patterns import AbuseMatch, AbusePatternLibrary
from jarvis.security.correlation import ProviderCorrelationTracker
from jarvis.security.intent_index import IntentIndex

logger = structlog.get_logger(__name__)


@dataclass
class PatternAlert:
    """Alert emitted by monitor_content (legacy API)."""

    timestamp: str
    pattern_id: str
    prompt_snippet: str
    severity: str
    context: Dict = field(default_factory=dict)


@dataclass
class CIDSResult:
    """Structured result from an evaluation."""

    alert: bool
    severity: str
    patterns: List[str]
    action: str
    reasons: List[str] = field(default_factory=list)
    agent_id: str = "unknown"
    provider: str = "unknown"
    intent_class: str = "unknown"
    capability: str = "unknown"
    timestamp: float = field(default_factory=lambda: time.time())
    cost: float = 0.0


SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class CognitiveIntrusionDetectionService:
    """Detects abuse patterns, probing behavior, and intent drift across providers."""

    denial_threshold = 3
    denial_window_seconds = 600
    morph_similarity = 0.82

    def __init__(
        self,
        config_path: str | Path = "config/abuse_patterns.json",
        pattern_library: Optional[AbusePatternLibrary] = None,
        intent_index: Optional[IntentIndex] = None,
        correlation_tracker: Optional[ProviderCorrelationTracker] = None,
        drift_detector: Optional[PromptDriftDetector] = None,
    ) -> None:
        if pattern_library:
            self.pattern_library = pattern_library
        else:
            self.pattern_library = AbusePatternLibrary(Path(config_path))
        self.intent_index = intent_index or IntentIndex()
        self.correlation_tracker = correlation_tracker or ProviderCorrelationTracker()
        self.drift_detector = drift_detector or get_drift_detector()

        self._denials: Dict[str, Deque[float]] = defaultdict(deque)
        self._prompt_history: Dict[str, Deque[str]] = defaultdict(deque)
        self.events: List[CIDSResult] = []
        self.event_window: Deque[Dict] = deque()
        self.window_size: int = 50

    @property
    def patterns(self):
        """Expose loaded patterns for legacy callers."""
        return self.pattern_library.patterns

    # ---- Public API -----------------------------------------------------

    def monitor_content(self, content: str, context: Optional[Dict] = None) -> List[PatternAlert]:
        """Legacy content scan returning pattern alerts."""
        context = context or {}
        matches: List[AbuseMatch] = self.pattern_library.match(content)
        now = datetime.now(timezone.utc).isoformat()
        alerts: List[PatternAlert] = []
        for match in matches:
            alert = PatternAlert(
                timestamp=now,
                pattern_id=match.pattern_id,
                prompt_snippet=content[:100],
                severity=match.severity,
                context=context,
            )
            alerts.append(alert)
            self._record_alert(alert)

        self._update_intent_profile(has_alert=bool(alerts))
        return alerts

    def evaluate(
        self,
        agent_id: str,
        prompt: str,
        provider: str,
        intent_class: str = "unknown",
        agent_role: str = "unknown",
        capability: str = "llm_call",
        cost: float = 0.0,
    ) -> CIDSResult:
        """Main detection entry point used by runtime and new tests."""
        ts = time.time()
        matches: List[AbuseMatch] = self.pattern_library.match(prompt)
        patterns = [m.pattern_id for m in matches]
        reasons = [f"matched:{m.pattern_id}" for m in matches]
        severity = self._highest([m.severity for m in matches]) if matches else "low"
        action = matches[0].response if matches else "allow"
        alert = bool(matches)

        # Heuristic signals
        if self._is_capability_probe(prompt):
            patterns.append("capability_probe")
            reasons.append("Detected capability probing language")
            severity = self._bump(severity, "medium")
            alert = True

        if self._is_role_probe(prompt):
            patterns.append("role_probe")
            reasons.append("Detected role or identity probing")
            severity = self._bump(severity, "high")
            alert = True
            action = "deny"

        morph = self._detect_morphology(agent_id, prompt)
        if morph:
            patterns.append("jailbreak_morphology")
            reasons.append(morph)
            severity = self._bump(severity, "high")
            alert = True
            action = "deny"

        if self.intent_index.check_rate_limit(agent_id, intent_class, timestamp=ts):
            patterns.append("intent_rate_limit")
            reasons.append("Intent-based rate limit hit")
            severity = self._bump(severity, "high")
            alert = True
            action = "deny"

        # Repeated denial / probing detection
        deny_count = self._register_denial(agent_id, alert, ts)
        if deny_count >= self.denial_threshold:
            patterns.append("probing_behavior")
            reasons.append(f"{deny_count} suspicious prompts in window")
            severity = self._bump(severity, "high")
            alert = True
            action = "deny"

        # Provider correlation tracking (best-effort)
        try:
            self.correlation_tracker.record_interaction(
                agent_id=agent_id,
                provider=provider,
                intent_class=intent_class,
                action=action,
                severity=severity,
                pattern=patterns[0] if patterns else None,
                cost=cost,
                timestamp=ts,
            )
        except Exception:
            pass  # correlation is opportunistic

        # Intent tracking
        self.intent_index.track(agent_id, prompt, intent_class, timestamp=ts)
        self._store_prompt(agent_id, prompt)
        self._update_intent_profile(has_alert=alert)

        event = CIDSResult(
            alert=alert,
            severity=severity,
            patterns=patterns or ["unknown"],
            action=action if alert else "allow",
            reasons=reasons,
            agent_id=agent_id,
            provider=provider,
            intent_class=intent_class,
            capability=capability,
            timestamp=ts,
            cost=cost,
        )
        self.events.append(event)

        if alert:
            try:
                self.drift_detector.record_denial(
                    agent_id=agent_id,
                    agent_role=agent_role,
                    capability=capability,
                    action_type=capability,
                    matched_rules=patterns or ["cids_alert"],
                    prompt=prompt,
                )
            except Exception:
                logger.warning("cids_drift_record_failed")

        return event

    # ---- Detection helpers ----------------------------------------------

    def _record_alert(self, alert: PatternAlert) -> None:
        logger.warning(
            "cids_alert",
            pattern=alert.pattern_id,
            severity=alert.severity,
            role=alert.context.get("agent_role", "unknown"),
        )

    def _update_intent_profile(self, has_alert: bool) -> None:
        event = {"timestamp": time.time(), "has_alert": has_alert}
        self.event_window.append(event)
        if len(self.event_window) > self.window_size:
            self.event_window.popleft()

    def _register_denial(self, agent_id: str, alert: bool, timestamp: float) -> int:
        window = self._denials[agent_id]
        if alert:
            window.append(timestamp)
        while window and window[0] < timestamp - self.denial_window_seconds:
            window.popleft()
        return len(window)

    def _detect_morphology(self, agent_id: str, prompt: str) -> Optional[str]:
        history = list(self._prompt_history.get(agent_id, []))
        for prev in reversed(history[-5:]):
            similarity = difflib.SequenceMatcher(None, prev, prompt).ratio()
            if similarity >= self.morph_similarity and prev != prompt:
                return f"Morphing detected (similarity {similarity:.2f})"
        return None

    def _store_prompt(self, agent_id: str, prompt: str) -> None:
        history = self._prompt_history[agent_id]
        history.append(prompt)
        while len(history) > 10:
            history.popleft()

    def _is_capability_probe(self, prompt: str) -> bool:
        lowered = prompt.lower()
        probes = [
            "what are you allowed",
            "list your capabilities",
            "can you execute",
            "what tools do you have",
            "bypass capability",
        ]
        if any(term in lowered for term in probes):
            return True
        if "command" in lowered and any(term in lowered for term in ["run", "execute", "shell", "bash"]):
            return True
        return False

    def _is_role_probe(self, prompt: str) -> bool:
        lowered = prompt.lower()
        return any(
            phrase in lowered
            for phrase in [
                "you are now root",
                "act as admin",
                "ignore your safety rules",
                "system override",
            ]
        )

    def detect_probing(self, window_seconds: int = 600, threshold: int = 3) -> bool:
        """Legacy probing detection based on recent alert history."""
        now = time.time()
        cutoff = now - window_seconds
        recent = [e for e in self.event_window if e["has_alert"] and e["timestamp"] > cutoff]
        return len(recent) >= threshold

    def get_risk_score(self) -> float:
        """Calculate probabilistic risk score (0.0 - 1.0)."""
        if not self.event_window:
            return 0.0
        recent_alerts = len([e for e in self.event_window if e["has_alert"]])
        return min(1.0, recent_alerts / 10.0)

    def _highest(self, severities: List[str]) -> str:
        return max(severities, key=lambda s: SEVERITY_ORDER.get(s, 0))

    def _bump(self, current: str, candidate: str) -> str:
        return candidate if SEVERITY_ORDER.get(candidate, 0) > SEVERITY_ORDER.get(current, 0) else current
