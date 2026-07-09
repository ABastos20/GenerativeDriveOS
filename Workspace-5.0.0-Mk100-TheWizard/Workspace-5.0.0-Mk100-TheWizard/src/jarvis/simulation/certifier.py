"""Simulation certificate generation (Story 11-7)."""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple
import structlog

from jarvis.simulation.certificates import SimulationCertificate
from jarvis.simulation.origins import OriginType

logger = structlog.get_logger(__name__)


class SimulationCertifier:
    """Generates certificates for simulation outputs."""

    def __init__(self, default_hazards: Iterable[str] | None = None) -> None:
        self.default_hazards: List[str] = list(default_hazards or [])

    def certify(
        self,
        sim_id: str,
        model_id: str,
        assumptions: List[str],
        boundary_conditions: Dict,
        confidence_interval: Tuple[float, float],
        hazards: Iterable[str] | None = None,
    ) -> SimulationCertificate:
        hazard_list = list(self.default_hazards) + list(hazards or [])
        cert = SimulationCertificate(
            sim_id=sim_id,
            model_id=model_id,
            assumptions=list(assumptions),
            boundary_conditions=dict(boundary_conditions),
            confidence_interval=confidence_interval,
            hazard_flags=hazard_list,
        )
        logger.info(
            "simulation_certified",
            sim_id=sim_id,
            model_id=model_id,
            hazards=hazard_list,
            origin=OriginType.SYNTHETIC.value,
        )
        return cert
