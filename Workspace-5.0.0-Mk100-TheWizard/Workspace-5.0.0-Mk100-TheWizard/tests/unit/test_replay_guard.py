from jarvis.simulation.replay_guard import ReplayGuard, _hash_payload


def test_replay_guard_detects_deterministic_match():
    guard = ReplayGuard()
    result_payload = {"a": 1}
    expected_hash = _hash_payload(result_payload)
    result = guard.validate_replay("sim", seed=1, expected_hash=expected_hash, actual_result=result_payload)
    assert result.deterministic
    assert result.valid


def test_replay_guard_detects_drift():
    guard = ReplayGuard()
    res = guard.validate_replay("sim", seed=1, expected_hash="abc", actual_result={"b": 2})
    assert not res.deterministic
