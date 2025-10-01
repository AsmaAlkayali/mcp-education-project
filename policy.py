import datetime
from typing import Dict

ROLES = ["student", "researcher", "instructor", "admin"]

POLICIES = {
    "student": {"can_search": True, "can_summarize": True, "can_share": False},
    "researcher": {"can_search": True, "can_summarize": True, "can_share": True},
    "instructor": {"can_search": True, "can_summarize": True, "can_share": True},
    "admin": {"can_search": True, "can_summarize": True, "can_share": True, "can_audit": True},
}

def apply_privacy_filter(data: Dict, role: str):
    filtered = data.copy()
    if role == "student":
        filtered.pop("audit_trail", None)
    return filtered

def check_permission(role: str, action: str) -> bool:
    perms = POLICIES.get(role, {})
    return perms.get(action, False)
