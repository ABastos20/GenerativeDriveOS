"""Simulation certificate models (Story 11-7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class SimulationCertificate:
    """Certification payload attached to every simulation result."""

    sim_id: str
    model_id: str
    assumptions: List[str]
    boundary_conditions: Dict
    confidence_interval: Tuple[float, float]
    hazard_flags: List[str] = field(default_factory=list)
    classification: str = "synthetic_certified"
