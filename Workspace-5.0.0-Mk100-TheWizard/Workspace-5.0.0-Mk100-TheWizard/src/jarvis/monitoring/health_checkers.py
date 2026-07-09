"""Health check implementations - Separated for complexity compliance.

Each check method is isolated to reduce HealthMonitor class complexity.
"""
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime
import structlog

from qdrant_client import QdrantClient
from jarvis.database import qdrant as qdrant_db
from jarvis.api.dashboard import get_enrichment_coverage, get_heuristic_hit_rate

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


class QdrantHealthChecker:
    """Qdrant-specific health checks."""

    def __init__(self, min_expected_points: int, deviation_threshold_pct: float):
        self.min_expected_points = min_expected_points
        self.deviation_threshold = deviation_threshold_pct
        self.last_point_count: Optional[int] = None

    def check(self, collection_name: str) -> HealthCheckResult:
        """Check Qdrant collection health."""
        try:
            client: QdrantClient = qdrant_db.get_qdrant_client()
            collection_info = client.get_collection(collection_name)
            current_count = collection_info.points_count
            
            result = self._evaluate_count(current_count)
            self.last_point_count = current_count
            return result
            
        except Exception as e:
            return HealthCheckResult(
                check_name="qdrant_point_count",
                status="critical",
                message=f"Qdrant error: {str(e)}",
            )

    def _evaluate_count(self, current_count: int) -> HealthCheckResult:
        """Evaluate point count against thresholds."""
        # Below minimum check
        if current_count < self.min_expected_points:
            return HealthCheckResult(
                check_name="qdrant_point_count",
                status="critical",
                message=f"Point count ({current_count}) below minimum ({self.min_expected_points})",
                value=current_count,
                threshold=self.min_expected_points,
            )

        # Deviation check
        if self.last_point_count is not None:
            deviation_pct = abs(current_count - self.last_point_count) / self.last_point_count * 100
            if deviation_pct > self.deviation_threshold:
                status = "critical" if current_count < self.last_point_count else "warning"
                return HealthCheckResult(
                    check_name="qdrant_point_count",
                    status=status,
                    message=f"Point count changed by {deviation_pct:.1f}%",
                    value=current_count,
                    threshold=self.last_point_count,
                )

        return HealthCheckResult(
            check_name="qdrant_point_count",
            status="ok",
            message=f"Qdrant healthy: {current_count:,} points",
            value=current_count,
        )


class HeuristicHealthChecker:
    """Heuristic hit rate health checks."""

    def __init__(self, min_hit_rate: float):
        self.min_hit_rate = min_hit_rate

    def check(self, collection_name: str) -> HealthCheckResult:
        """Check heuristic classification hit rate."""
        try:
            stats = get_heuristic_hit_rate(collection_name)
            hit_rate = stats.get("heuristic_rate_percent", 0.0)

            if hit_rate < self.min_hit_rate:
                return HealthCheckResult(
                    check_name="heuristic_hit_rate",
                    status="warning",
                    message=f"Hit rate ({hit_rate:.1f}%) below threshold ({self.min_hit_rate}%)",
                    value=hit_rate,
                    threshold=self.min_hit_rate,
                )

            return HealthCheckResult(
                check_name="heuristic_hit_rate",
                status="ok",
                message=f"Heuristic hit rate: {hit_rate:.1f}%",
                value=hit_rate,
            )

        except Exception as e:
            return HealthCheckResult(
                check_name="heuristic_hit_rate",
                status="warning",
                message=f"Error checking heuristic rate: {str(e)}",
            )


class EnrichmentHealthChecker:
    """Enrichment coverage health checks."""

    def __init__(self, min_coverage: float, max_coverage: float):
        self.min_coverage = min_coverage
        self.max_coverage = max_coverage

    def check(self, collection_name: str) -> HealthCheckResult:
        """Check enrichment coverage."""
        try:
            stats = get_enrichment_coverage(collection_name)
            coverage = stats.get("coverage_percent", 0.0)

            if coverage < self.min_coverage:
                return HealthCheckResult(
                    check_name="enrichment_coverage",
                    status="warning",
                    message=f"Coverage ({coverage:.1f}%) below minimum ({self.min_coverage}%)",
                    value=coverage,
                    threshold=self.min_coverage,
                )

            if coverage > self.max_coverage:
                return HealthCheckResult(
                    check_name="enrichment_coverage",
                    status="warning",
                    message=f"Coverage ({coverage:.1f}%) above maximum ({self.max_coverage}%)",
                    value=coverage,
                    threshold=self.max_coverage,
                )

            return HealthCheckResult(
                check_name="enrichment_coverage",
                status="ok",
                message=f"Enrichment coverage: {coverage:.1f}%",
                value=coverage,
            )

        except Exception as e:
            return HealthCheckResult(
                check_name="enrichment_coverage",
                status="warning",
                message=f"Error checking enrichment coverage: {str(e)}",
            )
