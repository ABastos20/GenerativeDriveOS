import pytest

from jarvis.knowledge.tiers import KnowledgeTier
from jarvis.simulation.firewall import SyntheticFirewall, PromotionBlocked
from jarvis.simulation.origins import OriginType


def test_firewall_blocks_synthetic_to_primary():
    firewall = SyntheticFirewall()
    with pytest.raises(PromotionBlocked):
        firewall.enforce("k1", KnowledgeTier.K4, KnowledgeTier.K2, OriginType.SYNTHETIC)


def test_firewall_allows_provisional_label():
    firewall = SyntheticFirewall()
    decision = firewall.validate_promotion("k1", KnowledgeTier.K4, KnowledgeTier.K3, OriginType.SYNTHETIC)
    assert decision.allowed
