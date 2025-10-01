# app.py
from fastapi import FastAPI, Depends, HTTPException, Header
from db import init_db, SessionLocal, AuditLog
from policy import check_permission

app = FastAPI(title="MCP Project PoC")

# تهيئة قاعدة البيانات عند بدء التطبيق
init_db()

def get_current_user(authorization: str = Header(...)):
    # مثال: تحليل token
    user_id, role = authorization.split(":")
    return {"id": user_id, "role": role}

@app.post("/api/v1/search")
def search(q: str, user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], "can_search"):
        raise HTTPException(status_code=403, detail="Policy denied")
    
    # مثال: إضافة سجل Audit
    session = SessionLocal()
    entry = AuditLog(
        user_id=user["id"],
        action="search",
        resource="papers",
        details={"query": q}
    )
    session.add(entry)
    session.commit()
    session.close()

    # هنا تضيفين عملية البحث الفعلية، حالياً مثال:
    results = [{"title": "Example Paper", "doi": "10.1234/example"}]
    return {"results": results}
