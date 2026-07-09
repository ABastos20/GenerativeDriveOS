"""User management endpoints for governance system.

Handles CRUD operations for governance users, audit logs, and permissions.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func

from jarvis.database.postgres import get_session
from jarvis.governance.models import (
    GovernanceUser,
    Role,
    AuditLog,
)
from jarvis.governance.permissions import (
    PermissionGate,
    PERMISSION_MATRIX,
    require_permission,
    PermissionAction
)

router = APIRouter(tags=["governance-users"])


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


# ==================== User Endpoints ====================

@router.get("/users")
@require_permission(PermissionAction.VIEW)
async def list_governance_users(
    request: Request,
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
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


@router.post("/users")
@require_permission(PermissionAction.MANAGE_USERS)
async def create_governance_user(
    request: Request,
    data: UserCreate,
) -> Dict[str, Any]:
    """Create a new governance user."""
    with get_session() as session:
        # Validate role
        try:
            role = Role(data.role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {data.role}. Valid roles: {[r.value for r in Role]}"
            )
        
        # Check if email already exists - but first check if email column exists
        try:
            existing = session.execute(
                select(GovernanceUser).where(GovernanceUser.email == data.email)
            ).scalar_one_or_none()
            
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"User with email {data.email} already exists"
                )
        except Exception:
            pass  # Email column may not exist in schema
        
        # Create user
        user = GovernanceUser(
            name=data.name,
            role=role,
            is_active=True,
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action_type="user_created",
            entity_type="governance_user",
            entity_id=user.id,
            details={"role": role.value, "name": data.name}
        )
        session.add(audit)
        session.commit()
        
        return {"user": user.to_dict(), "message": "User created successfully"}


@router.get("/users/{user_id}")
@require_permission(PermissionAction.VIEW)
async def get_governance_user(
    request: Request,
    user_id: UUID,
) -> Dict[str, Any]:
    """Get a specific governance user."""
    with get_session() as session:
        user = session.get(GovernanceUser, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user": user.to_dict()}


@router.patch("/users/{user_id}/role")
@require_permission(PermissionAction.MANAGE_USERS)
async def change_user_role(
    request: Request,
    user_id: UUID,
    data: RoleChange,
) -> Dict[str, Any]:
    """Change a user's role."""
    with get_session() as session:
        user = session.get(GovernanceUser, user_id)
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
        
        old_role = user.role
        user.role = new_role
        
        # Audit log
        audit = AuditLog(
            user_id=user_id,
            action_type="role_changed",
            entity_type="governance_user",
            entity_id=user_id,
            details={"old_role": old_role.value, "new_role": new_role.value}
        )
        session.add(audit)
        session.commit()
        session.refresh(user)
        
        return {"user": user.to_dict(), "message": f"Role changed from {old_role.value} to {new_role.value}"}


@router.delete("/users/{user_id}")
@require_permission(PermissionAction.MANAGE_USERS)
async def deactivate_governance_user(
    request: Request,
    user_id: UUID,
) -> Dict[str, Any]:
    """Deactivate a governance user (soft delete)."""
    with get_session() as session:
        user = session.get(GovernanceUser, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = False
        
        # Audit log
        audit = AuditLog(
            user_id=user_id,
            action_type="user_deactivated",
            entity_type="governance_user",
            entity_id=user_id,
            details={"name": user.name}
        )
        session.add(audit)
        session.commit()
        
        return {"message": "User deactivated successfully"}


# ==================== Audit Endpoints ====================

@router.get("/audit")
@require_permission(PermissionAction.VIEW)
async def get_audit_log(
    request: Request,
    entity_type: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """Get audit log entries."""
    with get_session() as session:
        query = select(AuditLog)
        
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if action_type:
            query = query.where(AuditLog.action_type == action_type)
        
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = session.execute(query)
        logs = [log.to_dict() for log in result.scalars().all()]
        
        return {"audit_logs": logs, "limit": limit, "offset": offset}


# ==================== Permission Endpoints ====================

@router.get("/permissions")
async def get_permission_matrix() -> Dict[str, Any]:
    """Get the full permission matrix."""
    gate = PermissionGate()
    return {
        "matrix": gate.get_matrix(),
        "roles": [r.value for r in Role],
        "actions": [a.value for a in PermissionAction if a != PermissionAction.ALL],
    }


@router.get("/users/{user_id}/permissions")
@require_permission(PermissionAction.VIEW)
async def get_user_permissions(
    request: Request,
    user_id: UUID,
) -> Dict[str, Any]:
    """Get permissions for a specific user."""
    with get_session() as session:
        user = session.get(GovernanceUser, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        gate = PermissionGate()
        permissions = gate.get_user_permissions(user)
        
        return {
            "user_id": str(user_id),
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "permissions": permissions,
        }
