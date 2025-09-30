import datetime
from typing import Dict

# -------------------------
# أدوار النظام
# -------------------------
ROLES = ["student", "researcher", "instructor", "admin"]

# -------------------------
# قاعدة سياسات بسيطة
# -------------------------
POLICIES = {
    "student": {"can_search": True, "can_summarize": True, "can_share": False},
    "researcher": {"can_search": True, "can_summarize": True, "can_share": True},
    "instructor": {"can_search": True, "can_summarize": True, "can_share": True},
    "admin": {"can_search": True, "can_summarize": True, "can_share": True, "can_audit": True},
}

# -------------------------
# Privacy Filter
# -------------------------
def apply_privacy_filter(data: Dict, role: str):
    """
    يخفي الحقول الحساسة حسب الدور
    """
    filtered = data.copy()
    if role == "student":
        # مثال: الطالب ما يشوف بيانات حساسة عن الآخرين
        filtered.pop("audit_trail", None)
    return filtered

# -------------------------
# RBAC/ABAC Evaluator
# -------------------------
def check_permission(role: str, action: str) -> bool:
    perms = POLICIES.get(role, {})
    return perms.get(action, False)

# -------------------------
# Audit Logger (بسيط)
# -------------------------
AUDIT_LOG = []

def log_audit(user: str, role: str, action: str, status: str):
    entry = {
        "user": user,
        "role": role,
        "action": action,
        "status": status,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    AUDIT_LOG.append(entry)
    print(f"[AUDIT] {entry}")
    return entry

def get_audit_log():
    return AUDIT_LOG
