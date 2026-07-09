"""Domain evolution tracking - monitor how knowledge grows over time.

Tracks domain distribution changes, enrichment progress, and knowledge
growth patterns to visualize JARVIS brain evolution.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import structlog
from sqlalchemy import Column, String, Integer, Float, Date, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session

from jarvis.database.postgres import get_session, get_engine
from jarvis.api.dashboard import (
    get_domain_distribution,
    get_enrichment_coverage,
    get_heuristic_hit_rate,
)

logger = structlog.get_logger(__name__)

Base = declarative_base()


class DomainSnapshot(Base):
    """Periodic snapshot of domain distribution."""

    __tablename__ = "domain_snapshots"

    snapshot_date = Column(Date, primary_key=True)
    collection_name = Column(String(100), primary_key=True)
    domain = Column(String(200), primary_key=True)
    point_count = Column(Integer, nullable=False)
    enrichment_pct = Column(Float, nullable=True)


class SystemSnapshot(Base):
    """Periodic snapshot of system-wide metrics."""

    __tablename__ = "system_snapshots"

    snapshot_date = Column(Date, primary_key=True)
    collection_name = Column(String(100), primary_key=True)
    total_points = Column(Integer, nullable=False)
    total_domains = Column(Integer, nullable=False)
    heuristic_hit_rate = Column(Float, nullable=True)
    enrichment_coverage = Column(Float, nullable=True)
    llm_fallback_rate = Column(Float, nullable=True)
    extra_metadata = Column(JSON, nullable=True)


@dataclass
class DomainGrowth:
    """Growth statistics for a domain."""

    domain: str
    current_count: int
    previous_count: int
    change_count: int
    change_percent: float
    is_growing: bool


def create_snapshot_tables():
    """Create snapshot tables if they don't exist."""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("snapshot_tables_created")
    except Exception as e:
        logger.error("snapshot_tables_creation_error", error=str(e))


def capture_domain_snapshot(
    collection_name: str = "jarvis-core",
    snapshot_date: Optional[date] = None,
):
    """Capture current domain distribution as a snapshot."""
    if snapshot_date is None:
        snapshot_date = date.today()

    logger.info("capturing_domain_snapshot", collection=collection_name, date=snapshot_date)

    try:
        # Get current domain distribution
        distribution = get_domain_distribution(collection_name)

        with get_session() as session:
            # Delete existing snapshots for this date/collection
            session.query(DomainSnapshot).filter_by(
                snapshot_date=snapshot_date,
                collection_name=collection_name,
            ).delete()

            # Insert new snapshots
            for domain, count in distribution.items():
                snapshot = DomainSnapshot(
                    snapshot_date=snapshot_date,
                    collection_name=collection_name,
                    domain=domain,
                    point_count=count,
                    enrichment_pct=None,  # Can be enhanced later
                )
                session.add(snapshot)

            session.commit()

            logger.info(
                "domain_snapshot_captured",
                domains=len(distribution),
                total_points=sum(distribution.values()),
            )

    except Exception as e:
        logger.error("domain_snapshot_error", error=str(e))
        raise


def capture_system_snapshot(
    collection_name: str = "jarvis-core",
    snapshot_date: Optional[date] = None,
):
    """Capture system-wide metrics snapshot."""
    if snapshot_date is None:
        snapshot_date = date.today()

    logger.info("capturing_system_snapshot", collection=collection_name, date=snapshot_date)

    try:
        # Gather metrics
        domain_dist = get_domain_distribution(collection_name)
        enrichment = get_enrichment_coverage(collection_name)
        heuristic = get_heuristic_hit_rate(collection_name)

        with get_session() as session:
            # Delete existing snapshot
            session.query(SystemSnapshot).filter_by(
                snapshot_date=snapshot_date,
                collection_name=collection_name,
            ).delete()

            # Create new snapshot
            snapshot = SystemSnapshot(
                snapshot_date=snapshot_date,
                collection_name=collection_name,
                total_points=enrichment.get("total_points", 0),
                total_domains=len(domain_dist),
                heuristic_hit_rate=heuristic.get("heuristic_rate_percent"),
                enrichment_coverage=enrichment.get("coverage_percent"),
                llm_fallback_rate=heuristic.get("llm_rate_percent"),
                extra_metadata={
                    "top_domains": dict(list(domain_dist.items())[:10]),
                    "enrichment_fields": enrichment.get("field_coverage", {}),
                },
            )
            session.add(snapshot)
            session.commit()

            logger.info(
                "system_snapshot_captured",
                points=snapshot.total_points,
                domains=snapshot.total_domains,
            )

    except Exception as e:
        logger.error("system_snapshot_error", error=str(e))
        raise


def get_domain_growth(
    domain: str,
    collection_name: str = "jarvis-core",
    days: int = 7,
) -> Optional[DomainGrowth]:
    """Get growth statistics for a specific domain."""
    try:
        with get_session() as session:
            today = date.today()
            past_date = today - timedelta(days=days)

            # Get current snapshot
            current = session.query(DomainSnapshot).filter_by(
                collection_name=collection_name,
                domain=domain,
                snapshot_date=today,
            ).first()

            # Get past snapshot
            past = session.query(DomainSnapshot).filter_by(
                collection_name=collection_name,
                domain=domain,
                snapshot_date=past_date,
            ).first()

            if not current:
                return None

            previous_count = past.point_count if past else 0
            current_count = current.point_count
            change_count = current_count - previous_count
            change_percent = (change_count / previous_count * 100) if previous_count > 0 else 100.0

            return DomainGrowth(
                domain=domain,
                current_count=current_count,
                previous_count=previous_count,
                change_count=change_count,
                change_percent=change_percent,
                is_growing=change_count > 0,
            )

    except Exception as e:
        logger.error("domain_growth_error", error=str(e))
        return None


def get_top_growing_domains(
    collection_name: str = "jarvis-core",
    days: int = 7,
    limit: int = 10,
) -> List[DomainGrowth]:
    """Get top growing domains by absolute count increase."""
    from datetime import timedelta

    try:
        with get_session() as session:
            today = date.today()
            past_date = today - timedelta(days=days)

            # Get all domains from current snapshot
            current_snapshots = session.query(DomainSnapshot).filter_by(
                collection_name=collection_name,
                snapshot_date=today,
            ).all()

            growth_stats = []

            for current in current_snapshots:
                past = session.query(DomainSnapshot).filter_by(
                    collection_name=collection_name,
                    domain=current.domain,
                    snapshot_date=past_date,
                ).first()

                previous_count = past.point_count if past else 0
                change_count = current.point_count - previous_count
                change_percent = (change_count / previous_count * 100) if previous_count > 0 else 100.0

                growth_stats.append(
                    DomainGrowth(
                        domain=current.domain,
                        current_count=current.point_count,
                        previous_count=previous_count,
                        change_count=change_count,
                        change_percent=change_percent,
                        is_growing=change_count > 0,
                    )
                )

            # Sort by absolute change, descending
            growth_stats.sort(key=lambda x: x.change_count, reverse=True)

            return growth_stats[:limit]

    except Exception as e:
        logger.error("top_growing_domains_error", error=str(e))
        return []


def get_evolution_timeline(
    collection_name: str = "jarvis-core",
    days: int = 30,
) -> Dict[str, List[Dict[str, Any]]]:
    """Get evolution timeline showing domain growth over time."""
    from datetime import timedelta

    try:
        with get_session() as session:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            snapshots = session.query(SystemSnapshot).filter(
                SystemSnapshot.collection_name == collection_name,
                SystemSnapshot.snapshot_date >= start_date,
                SystemSnapshot.snapshot_date <= end_date,
            ).order_by(SystemSnapshot.snapshot_date).all()

            timeline = {
                "dates": [],
                "total_points": [],
                "total_domains": [],
                "heuristic_hit_rate": [],
                "enrichment_coverage": [],
            }

            for snapshot in snapshots:
                timeline["dates"].append(snapshot.snapshot_date.isoformat())
                timeline["total_points"].append(snapshot.total_points)
                timeline["total_domains"].append(snapshot.total_domains)
                timeline["heuristic_hit_rate"].append(snapshot.heuristic_hit_rate or 0)
                timeline["enrichment_coverage"].append(snapshot.enrichment_coverage or 0)

            return timeline

    except Exception as e:
        logger.error("evolution_timeline_error", error=str(e))
        return {}


def format_domain_growth_report(
    growth_stats: List[DomainGrowth],
    title: str = "Domain Growth Report",
) -> str:
    """Format domain growth statistics for CLI output."""
    lines = [title, "=" * 70, ""]

    for i, growth in enumerate(growth_stats, 1):
        arrow = "📈" if growth.is_growing else "📉"
        sign = "+" if growth.change_count >= 0 else ""

        lines.append(f"{i}. {arrow} {growth.domain}")
        lines.append(f"   Current: {growth.current_count:,} points")
        lines.append(f"   Previous: {growth.previous_count:,} points")
        lines.append(f"   Change: {sign}{growth.change_count:,} ({sign}{growth.change_percent:+.1f}%)")
        lines.append("")

    return "\n".join(lines)
