import json
import tempfile
import os
from jarvis.security.cids import CognitiveIntrusionDetectionService, CIDSResult

def debug_cids():
    # Create manual config
    config_path = "/tmp/debug_patterns.json"
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
    
    with open(config_path, 'w') as f:
        json.dump(data, f)
        
    print(f"DEBUG: Created config at {config_path}")
    
    cids = CognitiveIntrusionDetectionService(config_path=config_path)
    print(f"DEBUG: Patterns loaded: {len(cids.patterns)}")
    if cids.patterns:
        print(f"DEBUG: Pattern 0: {cids.patterns[0]}")
        
    content = "This is a planned attack on the system."
    print(f"DEBUG: Monitoring content: '{content}'")
    alerts = cids.monitor_content(content)
    
    print(f"DEBUG: Alerts found: {len(alerts)}")
    for a in alerts:
        print(f"  - {a.pattern_id}: {a.severity}")
        
    # Clean up
    if os.path.exists(config_path):
        os.remove(config_path)

if __name__ == "__main__":
    debug_cids()
