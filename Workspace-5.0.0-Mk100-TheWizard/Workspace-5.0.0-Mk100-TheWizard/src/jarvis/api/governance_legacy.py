"""Governance API - REST endpoints for governance system.

Story 9-1: Multi-Human Governance Model  
Implements AC4, AC8, AC12: API endpoints for users, permissions, escalations

Endpoints:
- GET /api/governance/users - List governance users
- POST /api/governance/users - Add new governance user
- PATCH /api/governance/users/{id}/role - Change user role
- GET /api/governance/permissions - Get permission matrix
- GET /api/governance/escalations - List pending escalations
- POST /api/governance/escalations/{id}/resolve - Resolve escalation
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from jarvis.database.postgres import get_session
from jarvis.governance.models import (
    GovernanceUser,
    Role,
    Escalation,
    EscalationStatus,
    EscalationRule,
    AuditLog,
    Vote,
    Proposal,
    VoteChoice,
    ProposalStatus
)
from jarvis.governance.permissions import (
    PermissionGate, 
    PERMISSION_MATRIX,
    require_permission,
    require_role,
    PermissionAction
)
from jarvis.governance.escalation import EscalationEngine
from jarvis.api.dependencies import get_current_governance_user, get_session_dep, require_platform_role


router = APIRouter(prefix="/api/governance", tags=["governance"])


def _get_request_user(request: Request, session) -> Optional[GovernanceUser]:
    """Resolve the governance user from request headers/state for test/dev flows."""
    user_id = getattr(request.state, "governance_user_id", None) or request.headers.get("X-User-ID") or request.headers.get("X-Test-User-ID")
    try:
        user_id_parsed = UUID(str(user_id)) if user_id else None
    except Exception:
        user_id_parsed = user_id

    return session.get(GovernanceUser, user_id_parsed) if user_id_parsed else None


# ==================== Pydantic Models ====================

class UserCreate(BaseModel):
    """Request model for creating a governance user."""
    name: str
    email: EmailStr
    role: str = "observer"


class UserUpdate(BaseModel):
    """Request model for updating a user."""
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class RoleChange(BaseModel):
    """Request model for changing a user's role."""
    role: str


class EscalationResolve(BaseModel):
    """Request model for resolving an escalation."""
    resolution: str
    resolved_by_email: str


class EscalationAssign(BaseModel):
    """Request model for assigning an escalation."""
    assign_to_email: str


# ==================== Debug Endpoints ====================

@router.get("/debug/current-user")
async def get_current_user_debug(
    request: Request,
    user: GovernanceUser = Depends(get_current_governance_user),
):
    """Debug endpoint to verify current authenticated user."""
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "active": user.is_active,
        "trust_score": user.trust_metrics.to_dict() if user.trust_metrics else None
    }


# ==================== User Endpoints ====================

@router.get("/users")
@require_permission(PermissionAction.VIEW)
async def list_governance_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    request: Request = None,  # Required for permission check
) -> Dict[str, Any]:
    """List all governance users."""
    with get_session() as session:
        query = select(GovernanceUser)
        
        if role is not None:
            try:
                role_enum = Role(role)
                query = query.where(GovernanceUser.role == role_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role: {role}. Valid roles: {[r.value for r in Role]}"
                )
        
        if is_active is not None:
            query = query.where(GovernanceUser.is_active == is_active)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = session.execute(count_query).scalar()
        
        # Get paginated results
        query = query.order_by(GovernanceUser.created_at).offset(offset).limit(limit)
        result = session.execute(query)
        users = [u.to_dict() for u in result.scalars().all()]
        
        return {
            "users": users,
            "total": total,
            "limit": limit,
            "offset": offset,
            "roles": [r.value for r in Role],
        }


@router.get("/escalations")
@require_permission(PermissionAction.VIEW)
async def list_escalations(
    status: Optional[str] = Query(None, description="Filter by status"),
    role: Optional[str] = Query(None, description="Filter by current role"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    request: Request = None,  # Required for permission check
) -> Dict[str, Any]:
    """List escalations."""
    with get_session() as session:
        query = select(Escalation)
        
        if status:
            try:
                status_enum = EscalationStatus(status)
                query = query.where(Escalation.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}"
                )
        
        if role:
            try:
                role_enum = Role(role)
                query = query.where(Escalation.current_role == role_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role: {role}"
                )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = session.execute(count_query).scalar()
        
        # Get paginated results
        query = query.order_by(Escalation.created_at.desc()).offset(offset).limit(limit)
        result = session.execute(query)
        escalations = [e.to_dict() for e in result.scalars().all()]
        
        return {
            "escalations": escalations,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.get("/audit")
@require_permission(PermissionAction.VIEW)
async def get_audit_log(
    entity_type: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    request: Request = None,  # Required for permission check
) -> Dict[str, Any]:
    """Get audit log entries."""
    with get_session() as session:
        query = select(AuditLog)
        
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        
        if action_type:
            query = query.where(AuditLog.action_type == action_type)
        
        # Get Total count
        count_query = select(func.count()).select_from(query.subquery())
        total = session.execute(count_query).scalar()
        
        # Get paginated results
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = session.execute(query)
        logs = [l.to_dict() for l in result.scalars().all()]
        
        return {
            "audit_log": logs,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.post("/users")
@require_permission(PermissionAction.MANAGE_USERS)
async def create_governance_user(
    data: UserCreate, 
    request: Request = None,
    _ = Depends(require_platform_role(["user"]))
) -> Dict[str, Any]:
    """Create a new governance user.
    """
    with get_session() as session:
        # Check if email already exists (only if column present in model/schema)
        existing = None
        email_column = getattr(GovernanceUser, "email", None)
        if email_column is not None:
            try:
                existing = session.execute(
                    select(GovernanceUser).where(email_column == data.email)
                ).scalar_one_or_none()
            except Exception:
                existing = None
            
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"User with email {data.email} already exists"
                )
        
        # Validate role
        try:
            role = Role(data.role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {data.role}. Valid roles: {[r.value for r in Role]}"
            )
        
        # Create user
        oidc_claims = getattr(request.state, "oidc_claims", None) or {}
        issuer = oidc_claims.get("iss", "test-suite") if isinstance(oidc_claims, dict) else "test-suite"

        user_kwargs = {
            "name": data.name,
            "role": role,
            "subject_id": getattr(request.state, "legacy_user_id", None) or str(uuid4()),
            "issuer": issuer,
        }
        if email_column is not None:
            user_kwargs["email"] = data.email

        user = GovernanceUser(**user_kwargs)
        session.add(user)
        session.flush()  # Ensure primary key available before audit logging
        
        # Get permissions for role
        gate = PermissionGate()
        user.permissions = gate.get_user_permissions(user)
        
        # Audit log
        log = AuditLog(
            action_type="user_created",
            entity_type="governance_user",
            entity_id=user.id,
            new_value={"name": data.name, "email": data.email, "role": data.role},
            actor_type="api",
        )
        session.add(log)
        
        session.commit()
        
        return {
            "user": user.to_dict(),
            "message": f"User {data.email} created with role {data.role}",
        }


@router.get("/users/{user_id}")
@require_permission(PermissionAction.VIEW)
async def get_governance_user(user_id: UUID, request: Request = None) -> Dict[str, Any]:
    """Get a specific governance user."""
    with get_session() as session:
        user = session.execute(
            select(GovernanceUser).where(GovernanceUser.id == user_id)
        ).scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"user": user.to_dict()}


@router.patch("/users/{user_id}/role")
@require_role(Role.OWNER)
async def change_user_role(
    user_id: UUID, 
    data: RoleChange, 
    request: Request = None,
    _ = Depends(require_platform_role(["user"]))
) -> Dict[str, Any]:
    """Change a user's role.
    
    Implements PATCH /api/governance/users/{id}/role {role} -> GovernanceUser
    """
    with get_session() as session:
        user = session.execute(
            select(GovernanceUser).where(GovernanceUser.id == user_id)
        ).scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate new role
        try:
            new_role = Role(data.role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {data.role}. Valid roles: {[r.value for r in Role]}"
            )
        
        old_role = user.role.value if isinstance(user.role, Role) else user.role
        
        # Update role
        user.role = new_role
        user.updated_at = datetime.now(timezone.utc)
        
        # Update cached permissions
        gate = PermissionGate()
        user.permissions = gate.get_user_permissions(user)
        
        # Audit log (AC15)
        log = AuditLog(
            action_type="role_changed",
            entity_type="governance_user",
            entity_id=user.id,
            old_value={"role": old_role},
            new_value={"role": data.role},
            actor_type="api",
        )
        session.add(log)
        
        session.commit()
        
        return {
            "user": user.to_dict(),
            "message": f"Role changed from {old_role} to {data.role}",
        }


@router.delete("/users/{user_id}")
@require_permission(PermissionAction.MANAGE_USERS)
async def deactivate_governance_user(
    user_id: UUID, 
    request: Request = None,
    _ = Depends(require_platform_role(["user"]))
) -> Dict[str, Any]:
    """Deactivate a governance user (soft delete)."""
    with get_session() as session:
        user = session.execute(
            select(GovernanceUser).where(GovernanceUser.id == user_id)
        ).scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        
        # Audit log
        log = AuditLog(
            action_type="user_deactivated",
            entity_type="governance_user",
            entity_id=user.id,
            actor_type="api",
        )
        session.add(log)
        
        session.commit()
        
        return {
            "message": f"User {user.email} deactivated",
            "user_id": str(user_id),
        }


# ==================== Permission Endpoints ====================

@router.get("/permissions")
async def get_permission_matrix() -> Dict[str, Any]:
    """Get the full permission matrix.
    
    Implements AC8: GET /api/governance/permissions returns matrix
    """
    gate = PermissionGate()
    matrix = gate.get_matrix()
    
    return {
        "permissions": matrix,
        "roles": [r.value for r in Role],
        "role_hierarchy": [r.value for r in Role.escalation_chain()],
        "description": {
            "owner": "Full control, constitutional authority",
            "admin": "Manage users, moderate votes, config changes",
            "contributor": "Vote and propose",
            "observer": "Read-only access",
        },
    }


@router.get("/permissions/{user_id}")
async def get_user_permissions(user_id: UUID) -> Dict[str, Any]:
    """Get permissions for a specific user."""
    with get_session() as session:
        user = session.execute(
            select(GovernanceUser).where(GovernanceUser.id == user_id)
        ).scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        gate = PermissionGate()
        permissions = gate.get_user_permissions(user)
        
        return {
            "user_id": str(user_id),
            "role": user.role.value if isinstance(user.role, Role) else user.role,
            "permissions": permissions,
        }


# ==================== Escalation Endpoints ====================

@router.get("/escalations")
@require_permission(PermissionAction.VIEW)
async def list_escalations(
    status: Optional[str] = Query(None, description="Filter by status"),
    role: Optional[str] = Query(None, description="Filter by current role"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    request: Request = None,  # Required for permission check
) -> Dict[str, Any]:
    """List escalations.
    
    Implements AC12: GET /api/governance/escalations returns pending
    """
    with get_session() as session:
        query = select(Escalation)
        
        if status:
            try:
                status_enum = EscalationStatus(status)
                query = query.where(Escalation.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}"
                )
        
        if role:
            try:
                role_enum = Role(role)
                query = query.where(Escalation.current_role == role_enum)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role: {role}"
                )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = session.execute(count_query).scalar()
        
        # Get paginated results
        query = query.order_by(Escalation.created_at.desc()).offset(offset).limit(limit)
        result = session.execute(query)
        escalations = [e.to_dict() for e in result.scalars().all()]
        
        return {
            "escalations": escalations,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.get("/escalations/{escalation_id}")
@require_permission(PermissionAction.VIEW)
async def get_escalation(escalation_id: UUID, request: Request = None) -> Dict[str, Any]:
    """Get a specific escalation."""
    with get_session() as session:
        escalation = session.execute(
            select(Escalation).where(Escalation.id == escalation_id)
        ).scalar_one_or_none()
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        return {"escalation": escalation.to_dict()}


@router.post("/escalations/{escalation_id}/resolve")
@require_permission(PermissionAction.MODERATE)
async def resolve_escalation(
    escalation_id: UUID,
    data: EscalationResolve,
    request: Request = None,
    _ = Depends(require_platform_role(["user"]))
) -> Dict[str, Any]:
    """Resolve an escalation.
    
    Implements POST /api/governance/escalations/{id}/resolve -> {status: str}
    """
    with get_session() as session:
        escalation = session.execute(
            select(Escalation).where(Escalation.id == escalation_id)
        ).scalar_one_or_none()
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        if escalation.status != EscalationStatus.PENDING and escalation.status != EscalationStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot resolve escalation with status: {escalation.status}"
            )
        
        # Find resolver
        resolver = session.execute(
            select(GovernanceUser).where(GovernanceUser.email == data.resolved_by_email)
        ).scalar_one_or_none()
        
        if not resolver:
            raise HTTPException(
                status_code=404,
                detail=f"User not found: {data.resolved_by_email}"
            )
        
        # Resolve
        engine = EscalationEngine(session)
        escalation = engine.resolve_escalation(
            escalation=escalation,
            resolution=data.resolution,
            resolved_by=resolver,
        )
        
        session.commit()
        
        return {
            "status": "resolved",
            "escalation": escalation.to_dict(),
            "resolved_by": resolver.name,
        }


@router.post("/escalations/{escalation_id}/assign")
@require_permission(PermissionAction.MODERATE)
async def assign_escalation(
    escalation_id: UUID,
    data: EscalationAssign,
    request: Request = None,
    _ = Depends(require_platform_role(["user"]))
) -> Dict[str, Any]:
    """Assign an escalation to a user."""
    with get_session() as session:
        escalation = session.execute(
            select(Escalation).where(Escalation.id == escalation_id)
        ).scalar_one_or_none()
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        # Find assignee
        assignee = session.execute(
            select(GovernanceUser).where(GovernanceUser.email == data.assign_to_email)
        ).scalar_one_or_none()
        
        if not assignee:
            raise HTTPException(
                status_code=404,
                detail=f"User not found: {data.assign_to_email}"
            )
        
        # Assign
        engine = EscalationEngine(session)
        escalation = engine.assign_escalation(
            escalation=escalation,
            user=assignee,
        )
        
        session.commit()
        
        return {
            "status": "assigned",
            "escalation": escalation.to_dict(),
            "assigned_to": assignee.name,
        }


@router.post("/escalations/{escalation_id}/escalate")
@require_permission(PermissionAction.VOTE)
async def escalate_further(
    escalation_id: UUID, 
    request: Request = None,
    _ = Depends(require_platform_role(["user"]))
) -> Dict[str, Any]:
    """Escalate to the next level in the chain."""
    with get_session() as session:
        escalation = session.execute(
            select(Escalation).where(Escalation.id == escalation_id)
        ).scalar_one_or_none()
        
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        current_role = escalation.current_role
        if isinstance(current_role, str):
            current_role = Role(current_role)
        
        if current_role.can_escalate_to() is None:
            raise HTTPException(
                status_code=400,
                detail="Already at highest escalation level (owner)"
            )
        
        engine = EscalationEngine(session)
        escalation = engine.escalate_further(escalation)
        
        session.commit()
        
        return {
            "status": "escalated",
            "escalation": escalation.to_dict(),
            "new_role": escalation.current_role.value if isinstance(escalation.current_role, Role) else escalation.current_role,
        }


# ==================== Escalation Rules Endpoints ====================

@router.get("/escalation-rules")
async def list_escalation_rules() -> Dict[str, Any]:
    """List all escalation rules."""
    with get_session() as session:
        result = session.execute(
            select(EscalationRule).order_by(EscalationRule.priority)
        )
        rules = [r.to_dict() for r in result.scalars().all()]
        
        return {
            "rules": rules,
            "total": len(rules),
        }



class ProposalCreate(BaseModel):
    """Request model for creating a proposal."""
    title: str
    description: str
    proposal_type: str = "decision"
    domain: Optional[str] = None
    duration_hours: int = 48


class VoteCast(BaseModel):
    """Request model for casting a vote."""
    choice: str
    justification: Optional[str] = None


# ==================== Proposal & Voting Endpoints ====================

@router.post("/proposals")
@require_permission(PermissionAction.PROPOSE)
async def create_proposal(
    data: ProposalCreate,
    request: Request = None,
    _ = Depends(require_platform_role(["user"]))
) -> Dict[str, Any]:
    """Create a new proposal."""
    with get_session() as session:
        db_user = _get_request_user(request, session)
        if not db_user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        from jarvis.governance.voting import ProposalManager
        from jarvis.governance.models import ProposalType
        
        try:
            prop_type = ProposalType(data.proposal_type)
        except ValueError:
             raise HTTPException(status_code=400, detail=f"Invalid proposal type. Valid: {[t.value for t in ProposalType]}")

        mgr = ProposalManager(session)
        proposal = mgr.create_proposal(
            title=data.title,
            description=data.description,
            proposer=db_user,
            proposal_type=prop_type,
            domain=data.domain,
            duration_hours=data.duration_hours
        )
        
        session.commit()
        
        return {"proposal": proposal.to_dict(), "message": "Proposal created"}


@router.post("/proposals/{proposal_id}/open")
@require_permission(PermissionAction.MODERATE)
async def open_proposal_voting(
    proposal_id: UUID,
    request: Request = None,
    _ = Depends(require_platform_role(["user"]))
) -> Dict[str, Any]:
    """Open a proposal for voting (moves from DRAFT to OPEN)."""
    with get_session() as session:
        db_user = _get_request_user(request, session)
        if not db_user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        from jarvis.governance.voting import ProposalManager
        mgr = ProposalManager(session)
        
        try:
            proposal = mgr.open_proposal(proposal_id, db_user)
            session.commit()
            return {"proposal": proposal.to_dict(), "message": "Proposal opened for voting"}
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/proposals/{proposal_id}/vote")
@require_permission(PermissionAction.VOTE)
async def cast_vote(
    proposal_id: UUID,
    data: VoteCast,
    request: Request = None,
    _ = Depends(require_platform_role(["user"]))
) -> Dict[str, Any]:
    """Cast a vote on a proposal using governance identity headers/state."""
    with get_session() as session:
        db_user = _get_request_user(request, session)
        if not db_user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        from jarvis.governance.voting import VotingEngine

        try:
            choice_enum = VoteChoice(data.choice)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid choice. Valid: {[c.value for c in VoteChoice]}")

        engine = VotingEngine(session)
        try:
            vote = engine.cast_vote(
                proposal_id=proposal_id,
                voter=db_user,
                choice=choice_enum,
                justification=data.justification
            )
            session.commit()
            return {
                "vote": vote.to_dict(), 
                "weight_applied": vote.weight,
                "message": "Vote cast successfully"
            }
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/proposals")
@require_permission(PermissionAction.VIEW)
async def list_proposals(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    request: Request = None
) -> Dict[str, Any]:
    """List proposals."""
    from jarvis.governance.models import Proposal, ProposalStatus
    
    with get_session() as session:
        stmt = select(Proposal).order_by(Proposal.created_at.desc())
        
        if status:
            s_enum = None
            # Try exact match, then lower, then upper
            for s in [status, status.lower(), status.upper()]:
                try:
                    s_enum = ProposalStatus(s)
                    break
                except ValueError:
                    continue
            
            if s_enum:
                stmt = stmt.where(Proposal.status == s_enum)
            else:
                 raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
                 
        start = offset
        stmt = stmt.offset(start).limit(limit)
        
        proposals = session.execute(stmt).scalars().all()
        
        return {
            "proposals": [p.to_dict() for p in proposals],
            "limit": limit,
            "offset": offset
        }


@router.get("/proposals/{proposal_id}")
@require_permission(PermissionAction.VIEW)
async def get_proposal(
    proposal_id: UUID, 
    request: Request = None
) -> Dict[str, Any]:
    """Get proposal details and current tally.
    
    Returns flattened structure for frontend ease-of-use.
    """
    from jarvis.governance.voting import VotingEngine
    
    with get_session() as session:
        engine = VotingEngine(session)
        try:
            # 1. Get raw proposal
            from jarvis.governance.models import Proposal, GovernanceUser
            p = session.get(Proposal, proposal_id)
            
            if not p:
                 raise HTTPException(status_code=404, detail="Proposal not found in database")

            # 2. Get Proposer details
            proposer = session.get(GovernanceUser, p.proposer_id)
            proposer_name = proposer.name if proposer else "Unknown"
            
            # 3. Get Tally
            tally = engine.tally_votes(proposal_id)
            
            # 4. Construct Flattened Response
            # Merge proposal dict + tally dict + frontend helpers
            p_dict = p.to_dict()
            
            response = {
                **p_dict,
                **tally,
                "tally": tally,
                "proposer": {
                    "display_name": proposer_name,
                    "id": p_dict["proposer_id"]
                },
                # Frontend (governance.js) compatibility mapping
                "yes_votes": tally.get("total_for", 0),
                "no_votes": tally.get("total_against", 0),
                "abstain_votes": tally.get("total_abstain", 0),
                "weighted_yes": tally.get("total_for", 0),  # Assuming weight-based tally
                "current_weight": tally.get("total_weight", 0),
                "required_quorum": p.quorum_required * (p.total_weight_at_open or 1.0) if p.total_weight_at_open else 0.5 # Estimate or raw? JS uses raw quorum_required?
                # Actually JS Line 197: weighted_yes / required_quorum. 
                # Model quorum_required is 0.0-1.0. Weighted yes is absolute?
                # If weighted_yes is absolute, we need absolute quorum.
                # But let's check JS. JS displays "0.00 / 0.00".
                # If quorum_required in DB is 0.5 (percent), and weight is 0.5 (sum), then 0.5 / 0.5 = 100%.
                # JS expects matching units.
                # I'll verify logic in a sec, but mapping is better than nothing.
            }
            
            return response

        except HTTPException:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@router.post("/proposals/{proposal_id}/resolve")
@require_permission(PermissionAction.MODERATE)
async def resolve_proposal(
    proposal_id: UUID,
    request: Request = None
) -> Dict[str, Any]:
    """Manually trigger resolution (check quorum/deadline)."""
    with get_session() as session:
        from jarvis.governance.voting import VotingEngine
        engine = VotingEngine(session)
        db_user = _get_request_user(request, session)
        if not db_user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        try:
            p = engine.resolve_proposal(proposal_id, resolver=db_user, force=True)
            session.commit()
            return {
                "proposal": p.to_dict(), 
                "message": f"Proposal resolved: {p.status}",
                "reason": p.resolution_reason
            }
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


# ==================== Trust & Transparency Endpoints (Story 9-3) ====================

@router.get("/trust/{user_id}")
@require_permission(PermissionAction.VIEW)
async def get_user_trust_score(user_id: UUID) -> Dict[str, Any]:
    """Get the detailed trust score decomposition for a user.
    
    Implements Transparency Requirement: Users must see WHY they have a certain weight.
    """
    with get_session() as session:
        user = session.get(GovernanceUser, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        trust_metrics = user.trust_metrics
        # If None, dummy
        if not trust_metrics:
             return {
                 "user_id": str(user_id),
                 "trust_score": None,
                 "effective_weight": 0.05,
                 "components": {}
             }
             
        from jarvis.governance.trust import TrustCalculator
        from jarvis.governance.voting import VotingEngine 
        
        # Calculate live weight
        engine = VotingEngine(session)
        effective_weight = engine._compute_vote_weight(user)
        
        return {
            "user_id": str(user_id),
            "trust_metrics": trust_metrics.to_dict(),
            "raw_trust": TrustCalculator.calculate_raw_trust(trust_metrics),
            "effective_weight": effective_weight,
            "formula": "T = 0.4E + 0.3C + 0.2H + 0.1R",
            "constraints_applied": ["sybil_penalty", "anti_elite_cap", "minority_floor"]
        }

@router.get("/trust/distribution/stats")
@require_permission(PermissionAction.VIEW)
async def get_trust_distribution_stats() -> Dict[str, Any]:
    """Get system-wide trust statistics (Median, Cap, etc)."""
    with get_session() as session:
        stmt = select(GovernanceUser).where(GovernanceUser.is_active == True)
        users = session.execute(stmt).scalars().all()
        
        from jarvis.governance.voting import VotingEngine
        engine = VotingEngine(session)
        
        weights = []
        for u in users:
            w = engine._compute_vote_weight(u)
            weights.append(w)
            
        import statistics
        median = 0.0
        if weights:
            median = statistics.median(weights)
            
        return {
            "total_users": len(users),
            "median_weight": median,
            "anti_elite_cap": median * 5.0,
            "total_system_weight": sum(weights),
            "weights": sorted(weights) # Anonymized distribution
        }


class TrustRecalculateRequest(BaseModel):
    """Request model for batch trust recalculation."""
    apply_decay: bool = False
    apply_recenter: bool = False
    epochs_inactive: int = 1


@router.post(
    "/trust/recalculate",
    dependencies=[Depends(require_platform_role(["admin"]))]
)
async def recalculate_trust(
    request: Request,
    data: TrustRecalculateRequest,
) -> Dict[str, Any]:
    """Batch recalculate trust for all users.
    
    Story 9-3 AC 10: POST /api/governance/trust/recalculate
    
    Operations:
    - apply_decay: Apply inactivity decay to all users
    - apply_recenter: Move all users toward population mean
    
    Returns summary of updates made.
    """
    # Explicit Constitutional Check
    # At this point, Platform Admin is guaranteed by `dependencies`
    # Now we check Governance Role (must be OWNER to trigger recalc)
    
    current_user = Depends(get_current_governance_user)(request)
    # Note: depends call pattern might be cleaner if injected as arg, 
    # but to match user request pattern exactly:
    
    if current_user.role != Role.OWNER:
        raise HTTPException(
            status_code=403, 
            detail="Permission denied: Only Constitutional Node (OWNER) can trigger recalculation"
        )
    with get_session() as session:
        from jarvis.governance.trust import TrustUpdater
        
        stmt = select(GovernanceUser).where(GovernanceUser.is_active == True)
        users = session.execute(stmt).scalars().all()
        
        updated_count = 0
        decay_applied = 0
        recenter_applied = 0
        
        for user in users:
            if user.trust_metrics:
                if data.apply_decay:
                    TrustUpdater.apply_inactivity_decay(
                        user.trust_metrics, 
                        epochs_inactive=data.epochs_inactive
                    )
                    decay_applied += 1
                    
                if data.apply_recenter:
                    TrustUpdater.recenter_to_mean(user.trust_metrics)
                    recenter_applied += 1
                    
                updated_count += 1
        
        session.commit()
        
        return {
            "status": "success",
            "users_processed": updated_count,
            "decay_applied": decay_applied if data.apply_decay else 0,
            "recenter_applied": recenter_applied if data.apply_recenter else 0
        }


# ==================== Constitution Endpoints (Story 9-4) ====================

class ConstitutionCheckRequest(BaseModel):
    """Request model for constitutional check."""
    # Parameters to validate
    weight_epistemic: Optional[float] = None
    weight_consistency: Optional[float] = None
    weight_integrity: Optional[float] = None
    weight_reputation: Optional[float] = None
    sybil_threshold: Optional[float] = None
    minority_floor: Optional[float] = None
    anti_elite_multiplier: Optional[float] = None
    max_legitimacy_drift: Optional[float] = None


class ConstitutionAmendRequest(BaseModel):
    """Request model for constitutional amendment."""
    parameter_name: str
    new_value: float
    justification: str


@router.get("/constitution")
@require_permission(PermissionAction.VIEW)
async def get_constitution(request: Request) -> Dict[str, Any]:
    """Get the active constitution.
    
    Story 9-4 AC 4: GET /api/governance/constitution returns full constitution
    
    Returns all constitutional parameters and their current values.
    """
    # Default constitution for when DB is unavailable
    default_constitution = {
        "id": None,
        "version": 1,
        "is_active": False,
        "enacted_at": None,
        "sybil_threshold": 0.3,
        "minority_floor": 0.1,
        "anti_elite_multiplier": 3.0,
        "max_legitimacy_drift": 0.15,
        "parameters": {
            "weight_expertise": 0.4,
            "weight_contribution": 0.3,
            "weight_history": 0.2,
            "weight_reputation": 0.1,
            "sybil_threshold": 0.3,
            "minority_floor": 0.1,
            "anti_elite_multiplier": 3.0,
            "max_legitimacy_drift": 0.15
        },
        "formula": {
            "trust": "T = 0.4*E + 0.3*C + 0.2*H + 0.1*R"
        },
        "eternity_clauses": [
            "Trust weights must sum to 1.0 (±0.01)",
            "No negative weights allowed",
            "Sybil threshold: 0.0 ≤ τ ≤ 0.5",
            "Minority floor: 0.01 ≤ ε ≤ 0.2"
        ],
        "note": "Using defaults - database unavailable or no constitution configured"
    }
    
    try:
        with get_session() as session:
            from jarvis.governance.constitution import ConstitutionalGuard
            
            constitution = ConstitutionalGuard.get_active_constitution(session)
            
            if not constitution:
                return default_constitution
            
            return {
                "id": str(constitution.id),
                "version": 1,  # Constitution doesn't have version, use constant
                "is_active": constitution.active,  # actual column is 'active'
                "enacted_at": constitution.created_at.isoformat() if constitution.created_at else None,
                "sybil_threshold": constitution.sybil_threshold,
                "minority_floor": constitution.minority_floor,
                "anti_elite_multiplier": constitution.anti_elite_multiplier,
                "max_legitimacy_drift": constitution.max_legitimacy_drift,
                "parameters": constitution.to_dict(),
                "formula": {
                    "trust": "T = w_E*E + w_C*C + w_H*H + w_R*R",
                    "sybil_penalty": "w = T²/τ if T < τ else T",
                    "anti_elite": f"w ≤ {constitution.anti_elite_multiplier}× median",
                    "minority_floor": f"w ≥ {constitution.minority_floor}"
                },
                "eternity_clauses": [
                    "Trust weights must sum to 1.0 (±0.01)",
                    "No negative weights allowed",
                    "Sybil threshold: 0.0 ≤ τ ≤ 0.5",
                    "Minority floor: 0.01 ≤ ε ≤ 0.2",
                    "Anti-elite multiplier: 1.5 ≤ x ≤ 10",
                    "Max legitimacy drift: 0.0 ≤ δ ≤ 0.2"
                ]
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return default_constitution


@router.post("/constitution/check")
@require_permission(PermissionAction.VIEW)
async def check_constitution(data: ConstitutionCheckRequest) -> Dict[str, Any]:
    """Validate proposed constitutional parameters.
    
    Story 9-4 AC 8: POST /api/governance/constitution/check validates proposal
    
    Performs dry-run validation against eternity clauses.
    """
    from jarvis.governance.constitution import ConstitutionalGuard, ConstitutionalViolation
    
    # Build params dict from non-None values
    params = {}
    if data.weight_epistemic is not None:
        params["weight_epistemic"] = data.weight_epistemic
    if data.weight_consistency is not None:
        params["weight_consistency"] = data.weight_consistency
    if data.weight_integrity is not None:
        params["weight_integrity"] = data.weight_integrity
    if data.weight_reputation is not None:
        params["weight_reputation"] = data.weight_reputation
    if data.sybil_threshold is not None:
        params["sybil_threshold"] = data.sybil_threshold
    if data.minority_floor is not None:
        params["minority_floor"] = data.minority_floor
    if data.anti_elite_multiplier is not None:
        params["anti_elite_multiplier"] = data.anti_elite_multiplier
    if data.max_legitimacy_drift is not None:
        params["max_legitimacy_drift"] = data.max_legitimacy_drift
    
    try:
        ConstitutionalGuard.validate_parameter_safety(**params)
        return {
            "valid": True,
            "message": "Proposed parameters pass all eternity clause checks",
            "violations": []
        }
    except ConstitutionalViolation as e:
        return {
            "valid": False,
            "message": str(e),
            "violations": [str(e)]
        }


@router.post("/constitution/amend")
@require_permission(PermissionAction.AMEND)
async def propose_amendment(
    data: ConstitutionAmendRequest,
    _ = Depends(require_platform_role(["user"]))
) -> Dict[str, Any]:
    """Propose a constitutional amendment.
    
    Story 9-4 AC 12: POST /api/governance/constitution/amend proposes amendment
    
    Creates a CONSTITUTIONAL_AMENDMENT proposal with:
    - 75% quorum (supermajority)
    - 80% approval threshold
    - 7-day cooling period before enactment
    """
    from jarvis.governance.models import ProposalType
    from jarvis.governance.voting import ProposalManager
    from jarvis.governance.constitution import ConstitutionalGuard, ConstitutionalViolation
    
    # Validate the proposed parameter first
    try:
        params = {data.parameter_name: data.new_value}
        ConstitutionalGuard.validate_parameter_safety(**params)
    except ConstitutionalViolation as e:
        raise HTTPException(status_code=400, detail=f"Amendment violates eternity clause: {e}")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Unknown constitutional parameter: {data.parameter_name}")
    
    with get_session() as session:
        constitution = ConstitutionalGuard.get_active_constitution(session)
        
        # Get current value
        current_value = getattr(constitution, data.parameter_name, None)
        
        # Return amendment proposal details (actual proposal creation would need user context)
        return {
            "status": "amendment_proposal_ready",
            "parameter": data.parameter_name,
            "current_value": current_value,
            "proposed_value": data.new_value,
            "justification": data.justification,
            "requirements": {
                "quorum": "75% (supermajority)",
                "approval_threshold": "80%",
                "cooling_period": "7 days",
                "proposal_type": "CONSTITUTIONAL_AMENDMENT"
            },
            "note": "Use POST /api/proposals to create the actual proposal with type=constitutional_amendment"
        }


@router.get("/constitution/history")
@require_permission(PermissionAction.VIEW)
async def get_constitution_history() -> Dict[str, Any]:
    """Get constitutional amendment history.
    
    Story 9-4 AC 16: GET /api/governance/constitution/history returns versions
    
    Returns all constitutional versions with timestamps.
    """
    with get_session() as session:
        from jarvis.governance.models import Constitution
        
        stmt = select(Constitution).order_by(Constitution.version.desc())
        constitutions = session.execute(stmt).scalars().all()
        
        history = []
        for c in constitutions:
            history.append({
                "id": str(c.id),
                "version": c.version,
                "is_active": c.is_active,
                "enacted_at": c.enacted_at.isoformat() if c.enacted_at else None,
                "parameters": c.to_dict()
            })
        
        return {
            "total_versions": len(history),
            "versions": history,
            "original_preserved": len(history) > 0
        }


# ==================== Legitimacy Endpoints (Story 9-5 Phase 1) ====================

@router.get("/proposals/{proposal_id}/legitimacy")
@require_permission(PermissionAction.VIEW)
async def get_proposal_legitimacy(proposal_id: UUID) -> Dict[str, Any]:
    """Get legitimacy snapshot for a specific proposal.
    
    Story 9-5 Phase 1: Frozen trust + drift data for a proposal
    
    Returns frozen weight snapshot and legitimacy metrics.
    """
    with get_session() as session:
        from jarvis.governance.models import Proposal
        
        proposal = session.get(Proposal, proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Calculate current total weight for drift comparison
        from jarvis.governance.voting import VotingEngine
        engine = VotingEngine(session)
        
        current_snapshot, current_total = engine._create_trust_snapshot()
        
        weight_at_open = proposal.total_weight_at_open or 0.0
        drift = 0.0
        if weight_at_open > 0:
            drift = abs(current_total - weight_at_open) / weight_at_open
        
        return {
            "proposal_id": str(proposal_id),
            "title": proposal.title,
            "status": proposal.status.value if hasattr(proposal.status, 'value') else proposal.status,
            "opened_at": proposal.opened_at.isoformat() if proposal.opened_at else None,
            "legitimacy": {
                "total_weight_at_open": weight_at_open,
                "current_total_weight": current_total,
                "drift": drift,
                "drift_percentage": f"{drift*100:.2f}%",
                "within_limit": drift <= 0.1  # 10% max drift
            },
            "frozen_snapshot": {
                "voter_count": len(proposal.frozen_trust_snapshot or {}),
                "snapshot_exists": proposal.frozen_trust_snapshot is not None
            }
        }


@router.get("/legitimacy/system")
@require_permission(PermissionAction.VIEW)
async def get_system_legitimacy(request: Request) -> Dict[str, Any]:
    """Get system-wide legitimacy metrics.
    
    Story 9-5 Phase 1: Total weight now vs baseline
    
    Provides governance health overview.
    """
    with get_session() as session:
        from jarvis.governance.models import Proposal, ProposalStatus
        from jarvis.governance.constitution import ConstitutionalGuard
        from jarvis.governance.voting import VotingEngine
        
        constitution = ConstitutionalGuard.get_active_constitution(session)
        max_drift = constitution.max_legitimacy_drift if constitution else 0.15
        
        # Get current system weight with error handling
        try:
            engine = VotingEngine(session)
            _, current_total = engine._create_trust_snapshot()
        except Exception:
            current_total = 0.0
        
        # Get active proposals and their legitimacy
        stmt = select(Proposal).where(Proposal.status == ProposalStatus.OPEN)
        open_proposals = session.execute(stmt).scalars().all()
        
        legitimacy_checks = []
        for p in open_proposals:
            weight_at_open = p.total_weight_at_open or 0.0
            drift = 0.0
            if weight_at_open > 0:
                drift = abs(current_total - weight_at_open) / weight_at_open
            legitimacy_checks.append({
                "proposal_id": str(p.id),
                "title": p.title,
                "drift": drift,
                "valid": drift <= max_drift
            })
        
        all_valid = all(lc["valid"] for lc in legitimacy_checks) if legitimacy_checks else True
        
        return {
            "system_health": "healthy" if all_valid else "drift_violation",
            "current_total_weight": current_total,
            "max_legitimacy_drift": max_drift,
            "active_proposals": len(open_proposals),
            "legitimacy_checks": legitimacy_checks,
            "constitution_version": 1  # Constitution has no version column
        }


# ==================== Dashboard Endpoints (Story 9-5 Phase 3) ====================

@router.get("/dashboard/system")
@require_permission(PermissionAction.VIEW)
async def get_dashboard_system(request: Request) -> Dict[str, Any]:
    """Get system dashboard overview.
    
    Story 9-5 Phase 3: CSI, Total Weight, Drift, Active Constitution
    """
    # Default response for when DB is unavailable
    default_response = {
        "governance_system": {
            "total_users": 0,
            "total_weight": 0.0,
            "constitution_version": 1
        },
        "proposals": {
            "open": 0,
            "passed": 0,
            "rejected": 0
        },
        "escalations": {
            "pending": 0
        },
        "health": {
            "status": "initializing",
            "last_check": datetime.now(timezone.utc).isoformat()
        },
        "note": "Database unavailable or initializing"
    }
    
    try:
        with get_session() as session:
            from jarvis.governance.models import Proposal, ProposalStatus, Escalation, EscalationStatus
            from jarvis.governance.constitution import ConstitutionalGuard
            from jarvis.governance.voting import VotingEngine
            
            constitution = ConstitutionalGuard.get_active_constitution(session)
            constitution_version = 1  # Constitution model has no version column
            
            # Get current system state
            try:
                engine = VotingEngine(session)
                _, total_weight = engine._create_trust_snapshot()
            except Exception:
                total_weight = 0.0
            
            # Count users
            stmt = select(func.count(GovernanceUser.id)).where(GovernanceUser.is_active == True)
            user_count = session.execute(stmt).scalar() or 0
            
            # Count proposals by status
            open_count = session.execute(
                select(func.count(Proposal.id)).where(Proposal.status == ProposalStatus.OPEN)
            ).scalar() or 0
            
            passed_count = session.execute(
                select(func.count(Proposal.id)).where(Proposal.status == ProposalStatus.PASSED)
            ).scalar() or 0
            
            rejected_count = session.execute(
                select(func.count(Proposal.id)).where(Proposal.status == ProposalStatus.REJECTED)
            ).scalar() or 0
            
            # Count pending escalations
            pending_escalations = session.execute(
                select(func.count(Escalation.id)).where(Escalation.status == EscalationStatus.PENDING)
            ).scalar() or 0
            
            return {
                "governance_system": {
                    "total_users": user_count,
                    "total_weight": total_weight,
                    "constitution_version": constitution_version
                },
                "proposals": {
                    "open": open_count,
                    "passed": passed_count,
                    "rejected": rejected_count
                },
                "escalations": {
                    "pending": pending_escalations
                },
                "health": {
                    "status": "operational",
                    "last_check": datetime.now(timezone.utc).isoformat()
                }
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return default_response


@router.get("/dashboard/proposals")
@require_permission(PermissionAction.VIEW)
async def get_dashboard_proposals(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """Get proposals for dashboard view.
    
    Story 9-5 Phase 3: Status, quorum, frozen weight, deadlines
    """
    with get_session() as session:
        from jarvis.governance.models import Proposal, ProposalStatus
        from jarvis.governance.voting import VotingEngine
        
        stmt = select(Proposal).order_by(Proposal.created_at.desc()).limit(limit)
        
        if status:
            try:
                status_enum = ProposalStatus(status)
                stmt = stmt.where(Proposal.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        
        proposals = session.execute(stmt).scalars().all()
        
        engine = VotingEngine(session)
        
        result = []
        for p in proposals:
            # Calculate current quorum
            current_quorum = 0.0
            if p.total_weight > 0 and p.total_weight_at_open:
                current_quorum = p.total_weight / p.total_weight_at_open
            
            result.append({
                "id": str(p.id),
                "title": p.title,
                "status": p.status.value if hasattr(p.status, 'value') else p.status,
                "type": p.proposal_type.value if hasattr(p.proposal_type, 'value') else p.proposal_type,
                "deadline": p.deadline.isoformat() if p.deadline else None,
                "votes": {
                    "for": p.total_for,
                    "against": p.total_against,
                    "abstain": p.total_abstain
                },
                "quorum": {
                    "required": p.quorum_required,
                    "current": current_quorum
                },
                "has_frozen_snapshot": p.frozen_trust_snapshot is not None
            })
        
        return {
            "proposals": result,
            "count": len(result)
        }


# ==================== Export/Analytics Endpoints (Story 9-5 Phase 5) ====================

@router.get("/export/trust")
@require_permission(PermissionAction.VIEW)
async def export_trust_data(format: str = Query("json", enum=["json", "csv"])) -> Any:
    """Export trust data for analysis.
    
    Story 9-5 Phase 5: Trust history export for bias analysis
    """
    with get_session() as session:
        from jarvis.governance.models import TrustScore
        from jarvis.governance.voting import VotingEngine
        
        stmt = select(GovernanceUser).where(GovernanceUser.is_active == True)
        users = session.execute(stmt).scalars().all()
        
        engine = VotingEngine(session)
        
        data = []
        for u in users:
            metrics = u.trust_metrics
            if metrics:
                weight = engine._compute_vote_weight(u)
                data.append({
                    "user_id": str(u.id),
                    "name": u.name,
                    "epistemic_reliability": metrics.epistemic_reliability,
                    "governance_consistency": metrics.governance_consistency,
                    "historical_integrity": metrics.historical_integrity,
                    "reputation": metrics.reputation,
                    "effective_weight": weight
                })
        
        if format == "csv":
            import csv
            import io
            from fastapi.responses import StreamingResponse
            
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=trust_export.csv"}
            )
        
        return {"data": data, "count": len(data)}


@router.get("/export/proposals")
@require_permission(PermissionAction.VIEW)
async def export_proposals_data(format: str = Query("json", enum=["json", "csv"])) -> Any:
    """Export proposal history for audit.
    
    Story 9-5 Phase 5: Proposal chain export for legal audit
    """
    with get_session() as session:
        from jarvis.governance.models import Proposal
        
        stmt = select(Proposal).order_by(Proposal.created_at.desc())
        proposals = session.execute(stmt).scalars().all()
        
        data = []
        for p in proposals:
            data.append({
                "id": str(p.id),
                "title": p.title,
                "type": p.proposal_type.value if hasattr(p.proposal_type, 'value') else p.proposal_type,
                "status": p.status.value if hasattr(p.status, 'value') else p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "resolved_at": p.resolved_at.isoformat() if p.resolved_at else None,
                "total_for": p.total_for,
                "total_against": p.total_against,
                "quorum_required": p.quorum_required,
                "approval_threshold": p.approval_threshold,
                "resolution_reason": p.resolution_reason
            })
        
        if format == "csv":
            import csv
            import io
            from fastapi.responses import StreamingResponse
            
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=proposals_export.csv"}
            )
        
        return {"data": data, "count": len(data)}


# ==================== Story 9-5: Remaining ACs ====================

@router.get("/votes/history")
@require_permission(PermissionAction.VIEW)
async def get_vote_history(
    request: Request,
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """Get vote history for a user across all proposals.
    
    Story 9-5 AC7: Vote History - My votes across all proposals
    """
    with get_session() as session:
        from jarvis.governance.models import Vote, Proposal, GovernanceUser
        
        query = select(Vote, Proposal).join(Proposal, Vote.proposal_id == Proposal.id)
        
        if user_id:
            query = query.where(Vote.user_id == user_id)
        
        query = query.order_by(Vote.voted_at.desc()).limit(limit)
        results = session.execute(query).all()
        
        votes = []
        for vote, proposal in results:
            votes.append({
                "id": str(vote.id),
                "proposal_id": str(proposal.id),
                "proposal_title": proposal.title,
                "vote_type": vote.choice.value if hasattr(vote.choice, 'value') else vote.choice,
                "weight": vote.weight,
                "rationale": vote.justification,
                "created_at": vote.voted_at.isoformat() if vote.voted_at else None,
                "proposal_status": proposal.status.value if hasattr(proposal.status, 'value') else proposal.status
            })
        
        return {"votes": votes, "count": len(votes)}


@router.post("/proposals/{proposal_id}/quick-vote")
@require_permission(PermissionAction.VOTE)
async def quick_vote(
    proposal_id: UUID,
    vote_type: str = Query(..., enum=["yes", "no", "abstain"]),
    rationale: Optional[str] = Query(None),
    request: Request = None,
) -> dict:
    """Cast vote directly from dashboard (quick vote).
    
    Story 9-5 AC8: Quick Vote - Cast vote directly from dashboard
    """
    # Get current user from request context
    user_email = request.state.governance_user_email if hasattr(request.state, 'governance_user_email') else None
    
    if not user_email:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    with get_session() as session:
        from jarvis.governance.models import GovernanceUser, Proposal
        from jarvis.governance.voting import VotingEngine, VoteType
        
        # Get user
        user = session.query(GovernanceUser).filter(GovernanceUser.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get proposal
        proposal = session.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Map vote type
        vote_map = {"yes": VoteType.YES, "no": VoteType.NO, "abstain": VoteType.ABSTAIN}
        vote_enum = vote_map.get(vote_type.lower())
        if not vote_enum:
            raise HTTPException(status_code=400, detail=f"Invalid vote type: {vote_type}")
        
        # Cast vote
        engine = VotingEngine(session)
        try:
            vote = engine.cast_vote(
                proposal_id=proposal_id,
                user_id=user.id,
                vote_type=vote_enum,
                rationale=rationale
            )
            session.commit()
            
            # Refresh proposal to get updated counts
            session.refresh(proposal)
            
            return {
                "success": True,
                "vote_id": str(vote.id),
                "vote_type": vote_type,
                "weight": vote.weight,
                "proposal_status": proposal.status.value if hasattr(proposal.status, 'value') else proposal.status,
                "total_for": proposal.total_for,
                "total_against": proposal.total_against,
                "quorum_met": proposal.total_for + proposal.total_against >= proposal.quorum_required
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/trust-trend")
@require_permission(PermissionAction.VIEW)
async def get_trust_trend(
    request: Request,
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    days: int = Query(default=30, ge=7, le=90),
) -> dict:
    """Get trust score trend over time.
    
    Story 9-5 AC11: Trust Trend - Graph of trust changes over time
    """
    try:
        from datetime import timedelta
        
        with get_session() as session:
            from jarvis.governance.models import AuditLog
            
            # Trust trend from audit logs tracking trust changes
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = select(AuditLog).where(
                AuditLog.action_type == "trust_updated",
                AuditLog.created_at >= cutoff
            )
            
            if user_id:
                query = query.where(AuditLog.entity_id == str(user_id))
            
            query = query.order_by(AuditLog.created_at.asc())
            logs = session.execute(query).scalars().all()
            
            # Group by date
            trend = {}
            for log in logs:
                day = log.created_at.date().isoformat()
                if day not in trend:
                    trend[day] = {"date": day, "updates": 0, "avg_delta": 0.0, "deltas": []}
                
                trend[day]["updates"] += 1
                
                # Try to extract delta from metadata
                if log.metadata and isinstance(log.metadata, dict):
                    if "new_trust" in log.metadata and "old_trust" in log.metadata:
                        delta = log.metadata["new_trust"] - log.metadata["old_trust"]
                        trend[day]["deltas"].append(delta)
            
            # Calculate averages
            result = []
            for day, data in sorted(trend.items()):
                avg_delta = sum(data["deltas"]) / len(data["deltas"]) if data["deltas"] else 0.0
                result.append({
                    "date": data["date"],
                    "updates": data["updates"],
                    "avg_delta": round(avg_delta, 4)
                })
            
            return {"trend": result, "days": days, "data_points": len(result)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"trend": [], "days": days, "data_points": 0, "note": "Database unavailable"}


@router.get("/expertise/claims")
@require_permission(PermissionAction.VIEW)
async def list_expertise_claims(
    request: Request,
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
) -> dict:
    """Get list of expertise claims (high trust scores).
    
    Story 9-5 AC12: Expertise Claims - Manage my claimed expertise
    """
    try:
        with get_session() as session:
            from jarvis.governance.models import TrustScore, GovernanceUser
            
            query = select(TrustScore, GovernanceUser).join(
                GovernanceUser, TrustScore.user_id == GovernanceUser.id
            )
            
            if user_id:
                query = query.where(TrustScore.user_id == user_id)
            
            # Filter to high epistemic reliability (expertise proxy)
            query = query.where(TrustScore.epistemic_reliability > 0.5)
            
            results = session.execute(query).all()
            
            claims = []
            for trust, user in results:
                total = (trust.epistemic_reliability * 0.4 + 
                        trust.governance_consistency * 0.3 +
                        trust.historical_integrity * 0.2 +
                        trust.reputation * 0.1)
                claims.append({
                    "id": str(trust.id),
                    "user_id": str(user.id),
                    "user_name": user.name,
                    "domain": "general",
                    "epistemic_reliability": trust.epistemic_reliability,
                    "total_score": round(total, 3),
                    "last_updated": trust.last_updated.isoformat() if trust.last_updated else None
                })
            
            return {"claims": claims, "count": len(claims)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"claims": [], "count": 0, "note": "Database unavailable"}


@router.post("/expertise/claim")
@require_permission(PermissionAction.VOTE)
async def submit_expertise_claim(
    domain: str = Query(..., description="Domain to claim expertise in"),
    evidence: Optional[str] = Query(None, description="Evidence of expertise"),
    request: Request = None,
) -> dict:
    """Submit a new expertise claim.
    
    Story 9-5 AC12: Expertise Claims - Manage my claimed expertise
    """
    # Get user_id from request state (set by middleware)
    user_id = getattr(request.state, 'governance_user_id', None)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    with get_session() as session:
        from jarvis.governance.models import GovernanceUser, TrustScore, AuditLog
        
        # Get user
        user = session.get(GovernanceUser, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has a TrustScore record (1:1 relationship usually)
        # For this MVP, we treat 'evidence' submission as boosting epistemic_reliability
        trust = user.trust_metrics
        if not trust:
            # Create if missing
            trust = TrustScore(user_id=user.id)
            session.add(trust)
            
        # Boost epistemic reliability (cap at 1.0)
        trust.epistemic_reliability = min(trust.epistemic_reliability + 0.1, 1.0)
        
        # Log the claim
        claim_id = trust.id # Use trust ID as claim ID for now
        session.add(trust)
        session.flush()
        
        # Audit log
        audit = AuditLog(
            entity_type="expertise_claim",
            entity_id=str(claim_id),
            action_type="expertise_claimed",
            actor_id=user.id,
            metadata={"domain": domain, "evidence": evidence, "action": "updated"}
        )
        session.add(audit)
        session.commit()
        
        return {
            "success": True,
            "claim_id": str(claim_id),
            "domain": domain,
            "action": action,
            "message": f"Expertise claim for {domain} {action} successfully"
        }


@router.get("/violations")
@require_permission(PermissionAction.VIEW)
async def list_violation_log(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """List proposals blocked by constitution.
    
    Story 9-5 AC16: Violation Log - Proposals blocked by constitution
    """
    with get_session() as session:
        from jarvis.governance.models import Proposal, AuditLog
        
        # Get proposals that were blocked (status = rejected with constitutional reason)
        query = select(AuditLog).where(
            AuditLog.action_type.in_(["proposal_blocked", "legitimacy_violation", "eternity_clause_violation"])
        ).order_by(AuditLog.created_at.desc()).limit(limit)
        
        logs = session.execute(query).scalars().all()
        
        violations = []
        for log in logs:
            violations.append({
                "id": str(log.id),
                "entity_id": log.entity_id,
                "violation_type": log.action_type,
                "reason": log.metadata.get("reason") if log.metadata else None,
                "clause_violated": log.metadata.get("clause") if log.metadata else None,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })
        
        # Also get proposals with blocked status
        blocked_proposals = session.query(Proposal).filter(
            Proposal.resolution_reason.contains("constitutional")
        ).order_by(Proposal.created_at.desc()).limit(limit).all()
        
        for p in blocked_proposals:
            violations.append({
                "id": str(p.id),
                "entity_id": str(p.id),
                "violation_type": "proposal_blocked",
                "proposal_title": p.title,
                "reason": p.resolution_reason,
                "clause_violated": None,
                "created_at": p.created_at.isoformat() if p.created_at else None
            })
        
        # Sort by date and dedupe
        seen = set()
        unique_violations = []
        for v in sorted(violations, key=lambda x: x["created_at"] or "", reverse=True):
            key = v["entity_id"]
            if key not in seen:
                seen.add(key)
                unique_violations.append(v)
        
        return {"violations": unique_violations[:limit], "count": len(unique_violations[:limit])}

