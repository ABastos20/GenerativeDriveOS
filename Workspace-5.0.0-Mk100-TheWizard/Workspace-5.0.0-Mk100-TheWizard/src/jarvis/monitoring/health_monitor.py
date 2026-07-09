"""Automated memory health monitoring with alerts.

Monitors JARVIS memory system health and sends alerts when issues detected:
- Qdrant point count anomalies
- Heuristic hit rate degradation
- Query latency spikes
- Enrichment coverage drops
- Cost overruns
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

import structlog
from qdrant_client import QdrantClient

from jarvis.database import qdrant as qdrant_db
from jarvis.api.dashboard import (
    get_domain_distribution,
    get_enrichment_coverage,
    get_heuristic_hit_rate,
)

logger = structlog.get_logger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    check_name: str
    status: str  # "ok", "warning", "critical"
    message: str
    value: Optional[Any] = None
    threshold: Optional[Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class AlertConfig:
    """Configuration for health monitoring alerts."""

    # Qdrant thresholds
    qdrant_point_count_deviation_pct: float = 10.0  # Alert if ±10% change
    qdrant_min_expected_points: int = 40000

    # Heuristic hit rate
    heuristic_hit_rate_min: float = 65.0  # Alert if <65%

    # Query latency (not implemented yet, placeholder)
    query_latency_p95_max_ms: float = 2000.0  # Alert if >2s

    # Enrichment coverage
    enrichment_coverage_min: float = 30.0  # Alert if <30%
    enrichment_coverage_max: float = 60.0  # Alert if >60% (over-enriching)

    # Cost limits (per day)
    daily_cost_limit_usd: float = 5.0

    # Webhook URLs
    discord_webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    email_recipient: Optional[str] = None


class HealthMonitor:
    """Automated health monitoring system."""

    def __init__(self, config: AlertConfig = None):
        self.config = config or AlertConfig()
        self.last_point_count: Optional[int] = None
        self.check_history: List[HealthCheckResult] = []

    def _create_check_result(
        self,
        check_name: str,
        status: str,
        message: str,
        value: Any = None,
        threshold: Any = None,
    ) -> HealthCheckResult:
        """Helper to create HealthCheckResult."""
        return HealthCheckResult(
            check_name=check_name,
            status=status,
            message=message,
            value=value,
            threshold=threshold,
        )

    def _init_checkers(self):
        """Initialize delegated health checkers (class split for complexity)."""
        from jarvis.monitoring.health_checkers import (
            QdrantHealthChecker,
            HeuristicHealthChecker,
            EnrichmentHealthChecker,
        )
        self._qdrant_checker = QdrantHealthChecker(
            self.config.qdrant_min_expected_points,
            self.config.qdrant_point_count_deviation_pct,
        )
        self._heuristic_checker = HeuristicHealthChecker(self.config.heuristic_hit_rate_min)
        self._enrichment_checker = EnrichmentHealthChecker(
            self.config.enrichment_coverage_min,
            self.config.enrichment_coverage_max,
        )

    def run_all_checks(
        self,
        collection_name: str = "knowledge",
    ) -> List[HealthCheckResult]:
        """Run all health checks and return results."""
        if not hasattr(self, '_qdrant_checker'):
            self._init_checkers()

        results = [
            self._qdrant_checker.check(collection_name),
            self._heuristic_checker.check(collection_name),
            self._enrichment_checker.check(collection_name),
        ]

        self.check_history.extend(results)
        if len(self.check_history) > 1000:
            self.check_history = self.check_history[-1000:]

        return results



    def send_alerts(self, results: List[HealthCheckResult]):
        """Send alerts for failed health checks."""
        failures = [r for r in results if r.status in ["warning", "critical"]]

        if not failures:
            logger.info("health_check_passed", checks=len(results))
            return

        alert_message = self.format_alert_message(failures)

        logger.warning(
            "health_check_failures",
            failures=len(failures),
            total_checks=len(results),
        )

        # Send to configured channels
        if self.config.discord_webhook_url:
            self._send_discord_alert(alert_message)

        if self.config.slack_webhook_url:
            self._send_slack_alert(alert_message)

        if self.config.email_recipient:
            self._send_email_alert(alert_message)

    def format_alert_message(self, failures: List[HealthCheckResult]) -> str:
        """Format alert message for webhook/email."""
        lines = [
            "🚨 JARVIS Memory Health Alert",
            "=" * 60,
            f"Timestamp: {datetime.utcnow().isoformat()}",
            f"Failures: {len(failures)}",
            "",
        ]

        for result in failures:
            emoji = "⚠️" if result.status == "warning" else "🔴"
            lines.append(f"{emoji} {result.check_name.upper()}")
            lines.append(f"   Status: {result.status}")
            lines.append(f"   Message: {result.message}")

            if result.value is not None:
                lines.append(f"   Current Value: {result.value}")
            if result.threshold is not None:
                lines.append(f"   Threshold: {result.threshold}")

            lines.append("")

        lines.append("=" * 60)
        lines.append("Run 'jarvis health check' for details")

        return "\n".join(lines)

    def _send_discord_alert(self, message: str):
        """Send alert to Discord webhook."""
        try:
            import requests

            payload = {"content": f"```\n{message}\n```"}
            requests.post(self.config.discord_webhook_url, json=payload, timeout=10)

            logger.info("discord_alert_sent")

        except Exception as e:
            logger.error("discord_alert_failed", error=str(e))

    def _send_slack_alert(self, message: str):
        """Send alert to Slack webhook."""
        try:
            import requests

            payload = {"text": f"```\n{message}\n```"}
            requests.post(self.config.slack_webhook_url, json=payload, timeout=10)

            logger.info("slack_alert_sent")

        except Exception as e:
            logger.error("slack_alert_failed", error=str(e))

    def _send_email_alert(self, message: str):
        """Send alert via email (placeholder)."""
        # Implement email sending if needed
        logger.info("email_alert_placeholder", recipient=self.config.email_recipient)

    def run_daemon(
        self,
        collection_name: str = "jarvis-core",
        check_interval_minutes: int = 15,
    ):
        """Run health monitor as daemon (continuous loop)."""
        logger.info(
            "health_monitor_started",
            interval_minutes=check_interval_minutes,
            collection=collection_name,
        )

        while True:
            try:
                results = self.run_all_checks(collection_name)
                self.send_alerts(results)

                logger.info(
                    "health_check_complete",
                    total=len(results),
                    ok=sum(1 for r in results if r.status == "ok"),
                    warnings=sum(1 for r in results if r.status == "warning"),
                    critical=sum(1 for r in results if r.status == "critical"),
                )

            except Exception as e:
                logger.error("health_check_error", error=str(e))

            # Sleep until next check
            time.sleep(check_interval_minutes * 60)


def format_health_report(results: List[HealthCheckResult]) -> str:
    """Format health check results for CLI output."""
    lines = ["JARVIS Memory Health Report", "=" * 60, ""]

    for result in results:
        emoji = "✅" if result.status == "ok" else ("⚠️" if result.status == "warning" else "❌")

        lines.append(f"{emoji} {result.check_name}")
        lines.append(f"   Status: {result.status.upper()}")
        lines.append(f"   {result.message}")

        if result.value is not None:
            lines.append(f"   Value: {result.value}")

        lines.append(f"   Checked: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

    summary = {
        "ok": sum(1 for r in results if r.status == "ok"),
        "warning": sum(1 for r in results if r.status == "warning"),
        "critical": sum(1 for r in results if r.status == "critical"),
    }

    lines.append("=" * 60)
    lines.append(f"Summary: {summary['ok']} OK, {summary['warning']} warnings, {summary['critical']} critical")

    return "\n".join(lines)
