import pytest

from jarvis.simulation.self_training_guard import SelfTrainingGuard, SelfTrainingViolation, Waiver


def test_self_training_guard_blocks_recursive_without_waiver():
    guard = SelfTrainingGuard()
    with pytest.raises(SelfTrainingViolation):
        guard.validate("k1", ingestion_lineage=["k1"], origin="synthetic", waiver=None)


def test_self_training_guard_allows_with_waiver():
    guard = SelfTrainingGuard()
    waiver = Waiver(granted_by="governance", reason="approved experiment", signature="sig")
    guard.validate("k1", ingestion_lineage=["k1"], origin="synthetic", waiver=waiver)
