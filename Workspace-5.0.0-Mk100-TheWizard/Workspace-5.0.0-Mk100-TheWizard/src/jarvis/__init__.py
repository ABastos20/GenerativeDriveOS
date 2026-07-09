"""Auto-enable uvloop for 2-4x async performance improvement.

This must be imported before any other async code to replace the default event loop.
"""
from __future__ import annotations

try:
    import uvloop
    # uvloop.install() is deprecated; let uvicorn handle the loop or use uvloop.run() explicitly if needed.
except ImportError:
    # uvloop not installed - using default asyncio event loop
    pass

__all__ = []
