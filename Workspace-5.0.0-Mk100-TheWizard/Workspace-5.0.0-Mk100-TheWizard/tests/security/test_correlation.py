import time

from jarvis.security.correlation import ProviderCorrelationTracker


def test_provider_hopping_and_escalation():
    tracker = ProviderCorrelationTracker(window_seconds=120)
    now = time.time()
    tracker.record_interaction('agent', 'codex', 'narrative', action='allow', severity='low', timestamp=now, cost=0.1)
    tracker.record_interaction('agent', 'claude', 'analysis', action='deny', severity='high', timestamp=now + 1, cost=0.2)

    assert tracker.detect_provider_hopping('agent')
    assert tracker.detect_escalation('agent')

    timeline = tracker.get_timeline('agent')
    assert timeline[0].provider == 'codex'
    assert timeline[-1].provider == 'claude'

    distribution = tracker.provider_distribution()
    assert distribution.get('codex') == 1 and distribution.get('claude') == 1

    budget = tracker.budget_utilization()
    assert budget.get('codex') == 0.1
    assert budget.get('claude') == 0.2
