from jarvis.governance.trust import TrustCalculator

class MockScore:
    def __init__(self, e, c, h, r):
        self.epistemic_reliability = e
        self.governance_consistency = c
        self.historical_integrity = h
        self.reputation = r

def debug():
    ts2 = MockScore(0.5, 0.0, 1.0, 0.0)
    result = TrustCalculator.calculate_raw_trust(ts2)
    print(f"Result: {result}")
    print(f"Expected: 0.4")
    print(f"Equal? {result == 0.4}")
    
    expected_diff = abs(result - 0.4)
    print(f"Diff: {expected_diff}")

if __name__ == "__main__":
    debug()
