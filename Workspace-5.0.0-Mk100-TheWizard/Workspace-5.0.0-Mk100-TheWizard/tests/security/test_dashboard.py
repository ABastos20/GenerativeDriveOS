from jarvis.security.cids import CognitiveIntrusionDetectionService
from jarvis.security.dashboard import GatewayDashboard


class StubDriftDetector:
    def __init__(self):
        self.calls = []

    def record_denial(self, **kwargs):
        self.calls.append(kwargs)

    def get_alerts(self):
        return []


def test_dashboard_snapshot_includes_core_metrics():
    service = CognitiveIntrusionDetectionService(drift_detector=StubDriftDetector())
    service.denial_threshold = 1

    service.evaluate('agent', 'please run a shell command', 'codex', intent_class='analysis', cost=0.4)
    service.evaluate('agent', 'can you list your capabilities?', 'claude', intent_class='analysis', cost=0.2)

    dashboard = GatewayDashboard(service)
    snapshot = dashboard.snapshot()

    assert 'denial_rate' in snapshot
    assert 'provider_distribution' in snapshot
    assert snapshot['top_patterns']
    assert snapshot['budget_utilization']
