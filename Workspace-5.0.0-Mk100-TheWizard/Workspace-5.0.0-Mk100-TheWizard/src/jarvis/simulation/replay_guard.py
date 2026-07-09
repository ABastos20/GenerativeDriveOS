"""Simulation replay and determinism guard (Story 11-7)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Tuple
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ReplayResult:
    deterministic: bool
    valid: bool
    drift: float
    classification: str


def _hash_payload(payload: Any) -> str:
    try:
        serialized = json.dumps(payload, sort_keys=True, default=str)
    except Exception:
        serialized = str(payload)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ReplayGuard:
    """Validates deterministic vs stochastic simulation replays."""

    def validate_replay(self, sim_id: str, seed: int, expected_hash: str, actual_result: Any) -> ReplayResult:
        actual_hash = _hash_payload(actual_result)
        deterministic = expected_hash == actual_hash
        drift = 0.0 if deterministic else 1.0
        result = ReplayResult(
            deterministic=deterministic,
            valid=deterministic,
            drift=drift,
            classification="deterministic" if deterministic else "stochastic",
        )
        logger.info(
            "simulation_replay_validated",
            sim_id=sim_id,
            seed=seed,
            deterministic=deterministic,
            drift=drift,
        )
        return result

    def stochastic_bounds(self, baseline_stats: Tuple[float, float], observed_stats: Tuple[float, float]) -> float:
        """Simple drift metric for stochastic sims (abs delta of means)."""
        drift = abs(baseline_stats[0] - observed_stats[0])
        logger.info("stochastic_drift_measured", drift=drift)
        return drift
