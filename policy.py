import datetime

ROLES = ["student", "researcher", "instructor", "admin"]

POLICIES = {
    "student": {"can_search": True, "can_summarize": True, "can_share": False},
    "researcher": {"can_search": True, "can_summarize": True, "can_share": True},
    "instructor": {"can_search": True, "can_summarize": True, "can_share": True},
    "admin": {"can_search": True, "can_summarize": True, "can_share": True, "can_audit": True},
}

AUDIT_LOG = []

def apply_privacy_filter(data: dict, role: str):
    filtered = data.copy()
    if role == "student":
        filtered.pop("audit_trail", None)
    return filtered

def check_permission(role: str, action: str) -> bool:
    return POLICIES.get(role, {}).get(action, False)

def log_audit(user: str, role: str, action: str, status: str):
    entry = {"user": user, "role": role, "action": action, "status": status, "timestamp": datetime.datetime.utcnow().isoformat()}
    AUDIT_LOG.append(entry)
    print(f"[AUDIT] {entry}")
    return entry

def get_audit_log():
    return AUDIT_LOG
