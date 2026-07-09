"""Integration tests for Story 9-1: Governance System.

Verifies:
- User creation and role management
- Permission gating
- Escalation triggers and chain
- Governance Audit Trail
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta, timezone

from jarvis.governance.models import (
    Role, 
    GovernanceUser, 
    Escalation, 
    EscalationStatus, 
    EscalationTriggerType,
    AuditLog,
    PlatformRole,
)
from jarvis.governance.permissions import PermissionGate, PermissionAction
from jarvis.governance.escalation import EscalationEngine, create_default_escalation_rules
from jarvis.memory.governance_node import GovernanceGate, request_human_approval

@pytest.fixture
def governance_session(db_session):
    """Fixture providing a session with default governance rules."""
    create_default_escalation_rules(db_session)
    return db_session

@pytest.fixture
def admin_user(governance_session):
    """Fixture providing an admin user."""
    user = GovernanceUser(
        name="Admin User",
        subject_id=str(uuid4()),
        role=Role.ADMIN,
        platform_role=PlatformRole.ADMIN,
    )
    governance_session.add(user)
    governance_session.commit()
    return user

@pytest.fixture
def contributor_user(governance_session):
    """Fixture providing a contributor user."""
    user = GovernanceUser(
        name="Contributor User",
        subject_id=str(uuid4()),
        role=Role.CONTRIBUTOR,
        platform_role=PlatformRole.USER,
    )
    governance_session.add(user)
    governance_session.commit()
    return user

def test_permission_matrix(admin_user, contributor_user):
    """Test AC3, AC5-8: Permission Logic."""
    gate = PermissionGate()
    
    # Admin checks
    assert gate.can(admin_user, PermissionAction.MANAGE_USERS)
    assert gate.can(admin_user, PermissionAction.VOTE)
    
    # Contributor checks
    assert gate.can(contributor_user, PermissionAction.VOTE)
    assert not gate.can(contributor_user, PermissionAction.MANAGE_USERS)
    
    # Observer role check (implicit)
    observer = GovernanceUser(
        name="Obs",
        subject_id=str(uuid4()),
        role=Role.OBSERVER,
        is_active=True,
    )
    assert gate.can(observer, PermissionAction.VIEW)
    assert not gate.can(observer, PermissionAction.VOTE)

def test_escalation_triggers(governance_session):
    """Test AC10: Escalation Triggers."""
    from jarvis.governance.escalation import should_escalate
    
    # Test Tie Vote trigger
    rule = should_escalate(
        governance_session, 
        EscalationTriggerType.TIE_VOTE, 
        for_votes=0.5, 
        against_votes=0.5
    )
    assert rule is not None
    assert rule.trigger_type == EscalationTriggerType.TIE_VOTE
    
    # Test No Tie
    rule = should_escalate(
        governance_session, 
        EscalationTriggerType.TIE_VOTE, 
        for_votes=0.6, 
        against_votes=0.4
    )
    assert rule is None

def test_manual_escalation_flow(governance_session, contributor_user):
    """Test AC11, AC14: Escalation creation and audit trail."""
    action_details = {"target": "delete_db", "reason": "bad_idea"}
    
    # 1. Request Approval (Manual Escalation)
    result = request_human_approval(
        session=governance_session,
        action_type="critical_action",
        action_details=action_details,
        urgency="normal",
        user_id=str(contributor_user.id)
    )
    
    assert result["status"] == "pending_approval"
    escalation_id = result["request_id"]
    
    # 2. Verify Escalation Record
    escalation = governance_session.query(Escalation).filter_by(id=escalation_id).first()
    assert escalation is not None
    assert escalation.status == EscalationStatus.PENDING
    assert escalation.current_role == Role.ADMIN  # Normal urgency -> Admin
    
    # 3. Verify System State (via GovernanceGate)
    gate = GovernanceGate(governance_session)
    # Just ensure it runs without error and returns valid structure
    state = gate.get_system_state()
    assert "system_csi" in state
    
def test_escalation_resolution(governance_session, admin_user):
    """Test resolving an escalation."""
    engine = EscalationEngine(governance_session)
    
    # Create a dummy escalation
    from jarvis.governance.models import EscalationRule
    rule = governance_session.query(EscalationRule).first()
    
    escalation = engine.create_escalation(
        rule=rule,
        target_type="test",
        target_id=uuid4(),
        trigger_context={"test": True}
    )
    
    assert escalation.status == EscalationStatus.PENDING
    
    # Resolve it
    resolved = engine.resolve_escalation(
        escalation=escalation,
        resolution="Approved",
        resolved_by=admin_user
    )
    
    assert resolved.status == EscalationStatus.RESOLVED
    assert resolved.resolved_by == admin_user.id
    
    # Verify Audit Log
    log = governance_session.query(AuditLog).filter_by(
        entity_id=escalation.id,
        action_type="escalation_resolved"
    ).first()
    assert log is not None
    assert log.actor_id == admin_user.id

def test_governance_user_api(client, governance_session, admin_user):
    """Test API endpoints (AC4)."""
    from unittest.mock import patch
    from contextlib import contextmanager
    from uuid import uuid4

    @contextmanager
    def mock_get_session():
        # Do NOT commit/close test session
        yield governance_session

    headers = {"X-User-ID": str(admin_user.id)}
    
    # Create user via API
    new_email = f"api_{uuid4()}@test.com"
    
    
    # Patch middleware session to use test session - patch globally validation
    # Also patch the endpoint's get_session to ensure it sees the test data
    with patch("jarvis.database.postgres.get_session", side_effect=mock_get_session), \
         patch("jarvis.api.governance.get_session", side_effect=mock_get_session):
        resp = client.post("/api/governance/users", json={
            "name": "API User",
            "email": new_email,
            "role": "admin"
        }, headers=headers)
    
    # Check 400/500 errors
    if resp.status_code != 200:
        print(f"DEBUG: POST Failed: {resp.text}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["name"] == "API User"
    assert data["user"]["role"] == "admin"
    
    # List users
    with patch("jarvis.database.postgres.get_session", side_effect=mock_get_session), \
         patch("jarvis.api.governance.get_session", side_effect=mock_get_session):
        resp = client.get("/api/governance/users", headers=headers)
    
    if resp.status_code != 200:
        print(f"DEBUG: GET Failed: {resp.text}")
        
    assert resp.status_code == 200
    users = resp.json()["users"]
    assert len(users) >= 1
    
    # Verify DB directly using returned id
    db_user = governance_session.get(GovernanceUser, UUID(data["user"]["id"]))
    assert db_user is not None

