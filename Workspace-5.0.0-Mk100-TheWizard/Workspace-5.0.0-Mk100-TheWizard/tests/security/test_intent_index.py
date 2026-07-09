from jarvis.security.intent_index import IntentIndex


def test_intent_index_tracks_and_evicts():
    index = IntentIndex(window_size=3, rate_limit=2, rate_window_seconds=60)
    index.track('agent', 'first', 'narrative', timestamp=0)
    index.track('agent', 'second', 'narrative', timestamp=1)
    index.track('agent', 'third', 'forbidden', timestamp=2)
    index.track('agent', 'fourth', 'forbidden', timestamp=3)

    signature = index.get_signature('agent')
    assert signature.total_events == 3
    assert signature.last_intent == 'forbidden'
    assert signature.vector.get('forbidden') is not None


def test_intent_index_detects_shift():
    index = IntentIndex(window_size=6)
    index.track('agent', 'alpha', 'narrative', timestamp=0)
    index.track('agent', 'beta', 'narrative', timestamp=1)
    index.track('agent', 'gamma', 'analysis', timestamp=2)
    index.track('agent', 'delta', 'forbidden', timestamp=3)
    index.track('agent', 'epsilon', 'forbidden', timestamp=4)

    shift = index.detect_shift('agent')
    assert shift is not None
    assert shift['from'] != shift['to']


def test_rate_limit_checks_intent_class():
    index = IntentIndex(window_size=5, rate_limit=2, rate_window_seconds=10)
    index.track('agent', 'one', 'analysis', timestamp=0)
    index.track('agent', 'two', 'analysis', timestamp=1)
    assert index.check_rate_limit('agent', 'analysis', timestamp=2)
    assert not index.check_rate_limit('agent', 'forbidden', timestamp=2)
