
import sys
import os
sys.path.append(os.getcwd())
from jarvis.governance.models import GovernanceUser, Role

try:
    u = GovernanceUser(
        name="Test",
        subject_id="sub123",
        role=Role.OBSERVER
    )
    print(f"Created: {u}")
    if hasattr(u, "email"):
        print("FAIL: email field still exists")
    else:
        print("SUCCESS: email field removed")
except Exception as e:
    print(f"ERROR: {e}")
