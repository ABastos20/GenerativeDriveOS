"""Debug endpoints for governance system.

Provides development and debugging utilities.
"""

from fastapi import APIRouter, Depends, Request

from jarvis.governance.models import GovernanceUser
from jarvis.api.dependencies import get_current_governance_user

router = APIRouter(tags=["governance-debug"])


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
