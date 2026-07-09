import pytest
import os
import json
import tempfile
from jarvis.security.cids import CognitiveIntrusionDetectionService

class TestCIDS:
    
    @pytest.fixture
    def patterns_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            data = {
                "patterns": [
                    {
                        "id": "test_attack",
                        "name": "Test Attack",
                        "regex": "\\battack\\b",
                        "category": "test",
                        "severity": "high",
                        "action": "block"
                    }
                ]
            }
            json.dump(data, f)
            path = f.name
        yield path
        os.unlink(path)

    def test_load_patterns(self, patterns_file):
        cids = CognitiveIntrusionDetectionService(config_path=patterns_file)
        assert len(cids.patterns) == 1
        assert cids.patterns[0].id == "test_attack"

    def test_detect_abuse(self, patterns_file):
        cids = CognitiveIntrusionDetectionService(config_path=patterns_file)
        alerts = cids.monitor_content("This is a planned attack on the system.")
        assert len(alerts) == 1
        assert alerts[0].pattern_id == "test_attack"
        assert alerts[0].severity == "high"

    def test_clean_content(self, patterns_file):
        cids = CognitiveIntrusionDetectionService(config_path=patterns_file)
        alerts = cids.monitor_content("This is a safe string.")
        assert len(alerts) == 0

    def test_probing_detection(self, patterns_file):
        cids = CognitiveIntrusionDetectionService(config_path=patterns_file)
        # Simulate 3 attacks
        cids.monitor_content("attack 1")
        cids.monitor_content("attack 2")
        cids.monitor_content("attack 3")
        
        assert cids.detect_probing(threshold=3) is True
        assert cids.get_risk_score() >= 0.3
