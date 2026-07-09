"""
Ingestion Firewall (Story 11-6).
Blocks poisoning attempts, malformed data, and malicious intent.
"""
from typing import Dict, Optional, List
import structlog

logger = structlog.get_logger(__name__)

class IngestionViolation(Exception):
    pass

class IngestionFirewall:
    def __init__(self, cids_service=None):
        self.cids = cids_service

    def validate(self, content: str, metadata: Dict) -> bool:
        """
        Validates content integrity and safety.
        Raises IngestionViolation on failure.
        """
        # 1. Structural Validation
        if not content:
            raise IngestionViolation("Empty content")
            
        if len(content) > 10_000_000: # 10MB limit
            raise IngestionViolation("Content exceeds size limit")

        # 2. Metadata Schema
        required_meta = ["source_type", "source_uri"]
        for key in required_meta:
            if key not in metadata:
                raise IngestionViolation(f"Missing required metadata: {key}")

        # 3. Intent/Abuse Scanning (via C-IDS if available)
        if self.cids:
            alerts = self.cids.monitor_content(content[:1000], context={"source": "ingestion"})
            critical_alerts = [a for a in alerts if a.severity in ("critical", "high")]
            if critical_alerts:
                logger.warning("ingestion_firewall_block", alerts=critical_alerts)
                raise IngestionViolation(f"Security Alert: {critical_alerts[0].pattern_id}")

        return True
