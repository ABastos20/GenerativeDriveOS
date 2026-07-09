"""Integration tests for Voting Engine (Story 9-2)."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from jarvis.governance.models import (
    ProposalStatus, 
    ProposalType, 
    VoteChoice,
    GovernanceUser,
    Role,
    PlatformRole,
)

def test_voting_lifecycle(client, session, mock_audit_log):
    """Test full proposal lifecycle: Create -> Open -> Vote -> Resolve."""
    
    # 1. Setup Users
    owner = GovernanceUser(name="Owner", subject_id=str(uuid4()), role=Role.OWNER, platform_role=PlatformRole.ADMIN)
    voter1 = GovernanceUser(name="Voter1", subject_id=str(uuid4()), role=Role.CONTRIBUTOR, platform_role=PlatformRole.USER)
    voter2 = GovernanceUser(name="Voter2", subject_id=str(uuid4()), role=Role.CONTRIBUTOR, platform_role=PlatformRole.USER)
    observer = GovernanceUser(name="Obs", subject_id=str(uuid4()), role=Role.OBSERVER, platform_role=PlatformRole.OBSERVER)
    
    session.add_all([owner, voter1, voter2, observer])
    session.commit()
    
    # helper for headers
    def headers(user):
        return {"X-User-ID": str(user.id)}

    # 2. Create Proposal (as Contributor)
    # Observer cannot propose
    resp = client.post(
        "/api/governance/proposals",
        json={
            "title": "Test Proposal",
            "description": "Should we optimize?",
            "proposal_type": "decision"
        },
        headers=headers(observer)
    )
    if resp.status_code != 403:
        print(f"\n[DEBUG] Observer Proposal Status: {resp.status_code}")
        print(f"[DEBUG] Observer Proposal Body: {resp.text}")
    assert resp.status_code == 403

    # Contributor can propose
    resp = client.post(
        "/api/governance/proposals",
        json={
            "title": "Optimization Plan",
            "description": "Optimize db queries",
            "proposal_type": "decision",
            "duration_hours": 24
        },
        headers=headers(voter1)
    )
    if resp.status_code != 200:
        print(f"\n[DEBUG] Contributor Proposal Status: {resp.status_code}")
        print(f"[DEBUG] Contributor Proposal Body: {resp.text}")
    assert resp.status_code == 200
    prop_id = resp.json()["proposal"]["id"]
    assert resp.json()["proposal"]["status"] == "draft"

    # 3. Open Proposal (as Owner/Admin)
    # Contributor cannot open
    resp = client.post(
        f"/api/governance/proposals/{prop_id}/open",
        headers=headers(voter1)
    )
    assert resp.status_code == 403 # Needs MODERATE/MANAGE_USERS

    # Owner can open
    resp = client.post(
        f"/api/governance/proposals/{prop_id}/open",
        headers=headers(owner)
    )
    assert resp.status_code == 200
    assert resp.json()["proposal"]["status"] == "open"
    
    # 4. Cast Votes
    # Voter1 votes FOR
    resp = client.post(
        f"/api/governance/proposals/{prop_id}/vote",
        json={"choice": "for", "justification": "Good idea"},
        headers=headers(voter1)
    )
    assert resp.status_code == 200
    
    # Voter1 tries to duplicate vote
    resp = client.post(
        f"/api/governance/proposals/{prop_id}/vote",
        json={"choice": "against"},
        headers=headers(voter1)
    )
    assert resp.status_code == 400 # Duplicate
    
    # Voter2 votes AGAINST
    resp = client.post(
        f"/api/governance/proposals/{prop_id}/vote",
        json={"choice": "against", "justification": "Too risky"},
        headers=headers(voter2)
    )
    assert resp.status_code == 200
    
    # 5. Check Tally
    resp = client.get(f"/api/governance/proposals/{prop_id}", headers=headers(owner))
    assert resp.status_code == 200
    tally = resp.json()["tally"]
    assert tally["total_for"] == 1.0
    assert tally["total_against"] == 1.0
    assert tally["total_weight"] == 2.0
    
    # 6. Resolve (Tie Scenario)
    # Manually expire the proposal so we can resolve it
    from jarvis.governance.models import Proposal
    p = session.get(Proposal, prop_id)
    p.deadline = datetime.now(timezone.utc) - timedelta(hours=1)
    session.commit()

    # Owner tries to resolve
    resp = client.post(
        f"/api/governance/proposals/{prop_id}/resolve",
        headers=headers(owner)
    )
    assert resp.status_code == 200
    data = resp.json()
    # Should trigger escalation for TIE
    # Or rejected if no tie rule triggers? (Wait, ProposalManager makes an Escalation if rule matches)
    # In integration test, defaults might not be seeded unless we run seed.
    # But escalation logic defaults to REJECTED if no rule.
    # However, EscalationEngine logic creates "Escalated: Tie vote detected" in integration context if rules exist in DB.
    # The DB is empty except users. Escalation rules are NOT seeded in this test.
    # So it should default to REJECTED because no rule found.
    assert data["proposal"]["status"] == "rejected" 

def test_quorum_failure(client, session):
    """Test resolution with insufficient votes."""
    owner = GovernanceUser(name="Owner", subject_id=str(uuid4()), role=Role.OWNER, platform_role=PlatformRole.ADMIN)
    # 10 inactive users to inflate eligible count (if we used that logic, 
    # but current simplified logic uses total_weight / count(Active Users)).
    # Let's add 5 active users who don't vote.
    session.add(owner)
    for i in range(5):
        session.add(GovernanceUser(name=f"Silent{i}", subject_id=str(uuid4()), role=Role.CONTRIBUTOR, platform_role=PlatformRole.USER))
    session.commit()
    
    def headers(u): return {"X-User-ID": str(u.id)}
    
    # Create & Open
    resp = client.post(
        "/api/governance/proposals",
        json={"title": "Quiet Proposal", "description": "...", "proposal_type": "decision"},
        headers=headers(owner)
    )
    prop_id = resp.json()["proposal"]["id"]
    client.post(f"/api/governance/proposals/{prop_id}/open", headers=headers(owner))
    
    # Only Owner votes (1 vote out of 6 eligible) -> < 50%
    client.post(
        f"/api/governance/proposals/{prop_id}/vote",
        json={"choice": "for"},
        headers=headers(owner)
    )
    
    # Resolve
    resp = client.post(f"/api/governance/proposals/{prop_id}/resolve", headers=headers(owner))
    data = resp.json()
    
    # Should be rejected due to quorum failure
    assert data["proposal"]["status"] == "rejected"
    assert "Quorum failed" in data["reason"]

def test_lazy_expiration(client, session):
    """Test preventing votes after deadline."""
    owner = GovernanceUser(name="Owner", subject_id=str(uuid4()), role=Role.OWNER, platform_role=PlatformRole.ADMIN)
    session.add(owner)
    session.commit()
    
    resp = client.post(
        "/api/governance/proposals",
        json={"title": "Fast Proposal", "description": "...", "duration_hours": 1},
        headers={"X-User-ID": str(owner.id)}
    )
    prop_id = resp.json()["proposal"]["id"]
    client.post(f"/api/governance/proposals/{prop_id}/open", headers={"X-Test-User-ID": str(owner.id)})
    
    # Manually hack deadline to be in past
    from jarvis.governance.models import Proposal
    p = session.get(Proposal, prop_id)
    p.deadline = datetime.now(timezone.utc) - timedelta(hours=1)
    session.commit()
    
    # Try vote
    resp = client.post(
        f"/api/governance/proposals/{prop_id}/vote",
        json={"choice": "for"},
        headers={"X-Test-User-ID": str(owner.id)}
    )
    assert resp.status_code == 400
    assert "deadline" in resp.json()["detail"].lower()
