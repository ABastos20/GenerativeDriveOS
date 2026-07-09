"""Jarvis Governance Package.

Political governance for multi-human decision making.
Epic 9: Political Governance & Multi-Human Consensus

This package provides:
- GovernanceUser model with roles and permissions
- Permission matrix for role-based access control
- Escalation rules and engine
- Integration with epistemic governance gate

Motto: "Many voices. Weighted wisdom. Constitutional limits."
"""

from jarvis.governance.models import (
    GovernanceUser,
    Role,
    Permission,
    EscalationRule,
    Escalation,
)
from jarvis.governance.permissions import (
    PermissionGate,
    PERMISSION_MATRIX,
    require_permission,
)
from jarvis.governance.escalation import (
    EscalationEngine,
    EscalationTrigger,
)

__all__ = [
    # Models
    "GovernanceUser",
    "Role",
    "Permission",
    "EscalationRule",
    "Escalation",
    # Permissions
    "PermissionGate",
    "PERMISSION_MATRIX",
    "require_permission",
    # Escalation
    "EscalationEngine",
    "EscalationTrigger",
]
