"""
Minimal MCP server for agentic workflows (no API keys required).

Exposes:
- /mcp/ping     – liveness
- /mcp/health   – DB / pgcrypto status
- /mcp/agents   – static agent list for discovery
- /mcp/log_message – append a message to Jarvis conversation store
"""
from __future__ import annotations

import importlib.util
import logging
import os
from typing import Any, Optional
from uuid import UUID

from fastapi import FastAPI
from pydantic import BaseModel

from jarvis.database.models import Conversation, Message
from jarvis.database.postgres import get_session

LOGGER = logging.getLogger(__name__)
logging.basicConfig()


def _load_is_pgcrypto_available():
    """Attempt to import `is_pgcrypto_available` from the DB helper.

    Tries several strategies so the module works when run as a script or
    under a package import.
    """
    # First, try normal package import
    try:
        from jarvis.database.postgres import is_pgcrypto_available  # type: ignore

        return is_pgcrypto_available
    except Exception:
        LOGGER.debug("package import of jarvis.database.postgres failed, trying file import")

    # Fallback: load module by path relative to this file
    try:
        this_dir = os.path.dirname(__file__)
        postgres_path = os.path.join(this_dir, "database", "postgres.py")
        spec = importlib.util.spec_from_file_location("jarvis.database.postgres", postgres_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return getattr(mod, "is_pgcrypto_available")
    except Exception:
        LOGGER.exception("Failed to import is_pgcrypto_available from postgres.py")

    # Last resort: return a noop that reports False
    def _fallback():
        return False

    return _fallback


is_pgcrypto_available = _load_is_pgcrypto_available()
app = FastAPI()


class MCPLogMessage(BaseModel):
    """Payload for logging a message via MCP into Jarvis conversation store."""

    agent: str
    role: str
    content: str
    conversation_id: Optional[UUID] = None
    citation_provenance: Optional[Any] = None


@app.on_event("startup")
def _startup_checks():
    """Run quick startup checks and log DB UUID strategy."""
    try:
        pgcrypto = bool(is_pgcrypto_available())
    except Exception:
        pgcrypto = False

    if pgcrypto:
        LOGGER.info("DB-side UUID generation enabled: using gen_random_uuid() (pgcrypto)")
    else:
        LOGGER.info("DB-side UUID unavailable: falling back to Python uuid.uuid4() for UUID defaults")

@app.get("/mcp/ping")
def ping():
    return {"status": "ok"}

@app.get("/mcp/agents")
def list_agents():
    # TODO: Load agent list from .bmad/core/agents
    return {"agents": ["jarvis-agent", "bmad-master", "bmad-web-orchestrator", "bmad-greenfield"]}

@app.get("/mcp/health")
def health():
    """Health endpoint for MCP server including DB extension availability."""
    try:
        pgcrypto = bool(is_pgcrypto_available())
    except Exception:
        LOGGER.exception("Error while checking pgcrypto availability")
        pgcrypto = False

    return {"status": "ok", "pgcrypto": pgcrypto}


@app.post("/mcp/log_message")
def log_message(payload: MCPLogMessage):
    """Append a message to the Jarvis conversation store.

    This endpoint allows external MCP clients (Codex, Claude, Gemini, BMAD agents)
    to persist their interactions into Jarvis's Postgres-backed conversation schema.

    - If ``conversation_id`` is omitted, a new conversation is created.
    - If ``conversation_id`` is provided but does not exist, a new conversation with
      that ID is created.
    """
    with get_session() as session:
        conversation: Optional[Conversation]
        if payload.conversation_id is not None:
            conversation = session.get(Conversation, payload.conversation_id)
            if conversation is None:
                conversation = Conversation(id=payload.conversation_id)
                session.add(conversation)
        else:
            conversation = Conversation()
            session.add(conversation)
            session.flush()

        message = Message(
            conversation_id=conversation.id,
            role=payload.role,
            content=payload.content,
            agent_persona=payload.agent,
            citation_provenance=payload.citation_provenance,
        )
        session.add(message)
        session.flush()

        LOGGER.info(
            "mcp_message_logged",
            extra={
                "conversation_id": str(conversation.id),
                "message_id": str(message.id),
                "agent": payload.agent,
                "role": payload.role,
            },
        )

        return {
            "conversation_id": str(conversation.id),
            "message_id": str(message.id),
        }


if __name__ == "__main__":
    # Allow running directly for quick local tests: `python src/jarvis/mcp_server.py`
    try:
        import uvicorn

        uvicorn.run("src.jarvis.mcp_server:app", host="127.0.0.1", port=8001, log_level="info")
    except Exception:
        # If uvicorn isn't available, provide a helpful message
        print("Install requirements-mcp.txt and run with uvicorn, e.g.:")
        print("python -m uvicorn src.jarvis.mcp_server:app --host 127.0.0.1 --port 8001")
# Next: Add endpoints for workflows, memory, and tool execution
