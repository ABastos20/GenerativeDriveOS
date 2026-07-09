"""Governance API Plugin Package.

Temporary shim that imports from the original governance.py while refactoring is in progress.
Once all modules are created, this will be updated to import from sub-modules.

Provides `router` and `get_session` for test fixtures that patch DB access.
"""

# Import the router from the original monolithic file
# This preserves backwards compatibility while we migrate to modular structure
from jarvis.api.governance_legacy import router  # noqa: F401
from jarvis.database.postgres import get_session  # noqa: F401

__all__ = ["router", "get_session"]
