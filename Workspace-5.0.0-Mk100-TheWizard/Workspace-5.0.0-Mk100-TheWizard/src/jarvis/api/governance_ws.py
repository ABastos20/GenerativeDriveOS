"""Governance WebSocket - Real-Time Event Stream.

Story 9-5 Phase 4: WebSocket Real-Time Governance Events

Events:
- proposal_opened: New proposal created
- vote_cast: Vote submitted
- quorum_reached: Threshold crossed
- proposal_resolved: Outcome determined
- trust_updated: Trust score changed
- constitution_amended: Law change
- legitimacy_violation: Drift breach
- escalation_triggered: Escalation created
"""

from typing import Dict, Any, Set, Optional
from datetime import datetime, timezone
from uuid import UUID
import json
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter(prefix="/ws/governance", tags=["governance-websocket"])


class GovernanceEventManager:
    """Manages WebSocket connections and event broadcasting.
    
    Singleton pattern for global event distribution.
    """
    
    _instance: Optional["GovernanceEventManager"] = None
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.event_history: list = []  # Last N events for replay
        self.max_history = 100
        
    @classmethod
    def get_instance(cls) -> "GovernanceEventManager":
        if cls._instance is None:
            cls._instance = GovernanceEventManager()
        return cls._instance
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Connected to governance event stream"
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
    
    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients."""
        event = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Broadcast to all connections
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(event)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected
        self.active_connections -= disconnected
    
    def sync_broadcast(self, event_type: str, data: Dict[str, Any]):
        """Synchronous wrapper for broadcasting events.
        
        Used by synchronous code (VotingEngine) to queue events.
        Events are stored and broadcast when async context is available.
        """
        event = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        
        # Always store in history for later retrieval
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Try to broadcast if there's an event loop running
        try:
            loop = asyncio.get_running_loop()
            # Schedule async broadcast
            asyncio.create_task(self._async_broadcast(event))
        except RuntimeError:
            # No event loop - events queued in history for WebSocket clients to retrieve
            pass
    
    async def _async_broadcast(self, event: Dict[str, Any]):
        """Internal async broadcast."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(event)
            except Exception:
                disconnected.add(connection)
        self.active_connections -= disconnected
    
    def get_recent_events(self, limit: int = 20) -> list:
        """Get recent events for replay."""
        return self.event_history[-limit:]


# Global event manager instance
event_manager = GovernanceEventManager.get_instance()


# ==================== WebSocket Endpoint ====================

@router.websocket("/events")
async def governance_events_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time governance events.
    
    Story 9-5 Phase 4: Real-time governance stream
    
    Events:
    - proposal_opened
    - vote_cast
    - quorum_reached
    - proposal_resolved
    - trust_updated
    - constitution_amended
    - legitimacy_violation
    - escalation_triggered
    """
    await event_manager.connect(websocket)
    
    try:
        # Send recent events on connect
        recent = event_manager.get_recent_events()
        if recent:
            await websocket.send_json({
                "type": "replay",
                "events": recent
            })
        
        # Keep connection alive and listen for pings
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second heartbeat
                )
                
                # Handle ping
                if message == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
    except WebSocketDisconnect:
        event_manager.disconnect(websocket)


# ==================== Event Emission Functions ====================

async def emit_proposal_opened(proposal_id: UUID, title: str, proposer: str, deadline: datetime):
    """Emit proposal_opened event."""
    await event_manager.broadcast("proposal_opened", {
        "proposal_id": str(proposal_id),
        "title": title,
        "proposer": proposer,
        "deadline": deadline.isoformat() if deadline else None
    })


async def emit_vote_cast(proposal_id: UUID, user_id: UUID, choice: str, weight: float):
    """Emit vote_cast event."""
    await event_manager.broadcast("vote_cast", {
        "proposal_id": str(proposal_id),
        "user_id": str(user_id),
        "choice": choice,
        "weight": weight
    })


async def emit_quorum_reached(proposal_id: UUID, quorum_percentage: float):
    """Emit quorum_reached event."""
    await event_manager.broadcast("quorum_reached", {
        "proposal_id": str(proposal_id),
        "quorum_percentage": quorum_percentage
    })


async def emit_proposal_resolved(proposal_id: UUID, status: str, reason: str):
    """Emit proposal_resolved event."""
    await event_manager.broadcast("proposal_resolved", {
        "proposal_id": str(proposal_id),
        "status": status,
        "reason": reason
    })


async def emit_trust_updated(user_id: UUID, old_value: float, new_value: float, reason: str):
    """Emit trust_updated event."""
    await event_manager.broadcast("trust_updated", {
        "user_id": str(user_id),
        "old_value": old_value,
        "new_value": new_value,
        "reason": reason
    })


async def emit_constitution_amended(version: int, parameter: str, old_value: Any, new_value: Any):
    """Emit constitution_amended event."""
    await event_manager.broadcast("constitution_amended", {
        "version": version,
        "parameter": parameter,
        "old_value": old_value,
        "new_value": new_value
    })


async def emit_legitimacy_violation(proposal_id: UUID, drift: float, threshold: float):
    """Emit legitimacy_violation event."""
    await event_manager.broadcast("legitimacy_violation", {
        "proposal_id": str(proposal_id),
        "drift": drift,
        "threshold": threshold,
        "severity": "critical" if drift > threshold * 2 else "warning"
    })


async def emit_escalation_triggered(escalation_id: UUID, target_type: str, target_id: UUID, reason: str):
    """Emit escalation_triggered event."""
    await event_manager.broadcast("escalation_triggered", {
        "escalation_id": str(escalation_id),
        "target_type": target_type,
        "target_id": str(target_id),
        "reason": reason
    })


# ==================== Synchronous Emit Functions (for VotingEngine) ====================

def sync_emit_proposal_opened(proposal_id: UUID, title: str, proposer: str, deadline: datetime):
    """Sync emit proposal_opened event - for VotingEngine.open_proposal."""
    event_manager.sync_broadcast("proposal_opened", {
        "proposal_id": str(proposal_id),
        "title": title,
        "proposer": proposer,
        "deadline": deadline.isoformat() if deadline else None
    })


def sync_emit_vote_cast(proposal_id: UUID, user_id: UUID, choice: str, weight: float):
    """Sync emit vote_cast event - for VotingEngine.cast_vote."""
    event_manager.sync_broadcast("vote_cast", {
        "proposal_id": str(proposal_id),
        "user_id": str(user_id),
        "choice": choice,
        "weight": weight
    })


def sync_emit_quorum_reached(proposal_id: UUID, quorum_percentage: float):
    """Sync emit quorum_reached event."""
    event_manager.sync_broadcast("quorum_reached", {
        "proposal_id": str(proposal_id),
        "quorum_percentage": quorum_percentage
    })


def sync_emit_proposal_resolved(proposal_id: UUID, status: str, reason: str):
    """Sync emit proposal_resolved event - for VotingEngine.resolve_proposal."""
    event_manager.sync_broadcast("proposal_resolved", {
        "proposal_id": str(proposal_id),
        "status": status,
        "reason": reason
    })


def sync_emit_trust_updated(user_id: UUID, old_value: float, new_value: float, reason: str):
    """Sync emit trust_updated event - for TrustUpdater."""
    event_manager.sync_broadcast("trust_updated", {
        "user_id": str(user_id),
        "old_value": old_value,
        "new_value": new_value,
        "reason": reason
    })


def sync_emit_legitimacy_violation(proposal_id: UUID, drift: float, threshold: float):
    """Sync emit legitimacy_violation event."""
    event_manager.sync_broadcast("legitimacy_violation", {
        "proposal_id": str(proposal_id),
        "drift": drift,
        "threshold": threshold,
        "severity": "critical" if drift > threshold * 2 else "warning"
    })


def sync_emit_escalation_triggered(escalation_id: UUID, target_type: str, target_id: UUID, reason: str):
    """Sync emit escalation_triggered event - for EscalationEngine."""
    event_manager.sync_broadcast("escalation_triggered", {
        "escalation_id": str(escalation_id),
        "target_type": target_type,
        "target_id": str(target_id),
        "reason": reason
    })
