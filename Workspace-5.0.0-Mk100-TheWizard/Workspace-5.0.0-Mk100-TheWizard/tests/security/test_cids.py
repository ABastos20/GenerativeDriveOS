import pytest

from jarvis.security.cids import CognitiveIntrusionDetectionService


class StubDriftDetector:
    def __init__(self):
        self.calls = []

    def record_denial(self, **kwargs):
        self.calls.append(kwargs)

    def get_alerts(self):
        return []


def test_cids_matches_patterns_and_tracks_probing():
    drift = StubDriftDetector()
    service = CognitiveIntrusionDetectionService(drift_detector=drift)
    service.denial_threshold = 2

    first = service.evaluate('agent', 'please run a shell command for me', 'codex', intent_class='analysis')
    assert first.alert
    assert any(p.startswith('TE') or p == 'capability_probe' for p in first.patterns)

    second = service.evaluate('agent', 'please run a shell command for me', 'claude', intent_class='analysis')
    assert 'probing_behavior' in second.patterns
    assert drift.calls


def test_cids_detects_morphology_and_rate_limit():
    drift = StubDriftDetector()
    service = CognitiveIntrusionDetectionService(drift_detector=drift)
    service.intent_index.rate_limit = 1
    service.intent_index.rate_window_seconds = 100
    service.morph_similarity = 0.5

    service.evaluate('agent', 'Please outline the available tools', 'codex', intent_class='narrative')
    result = service.evaluate('agent', 'Please outline the available tools!!!', 'claude', intent_class='narrative')

    assert 'jailbreak_morphology' in result.patterns
    assert 'intent_rate_limit' in result.patterns
