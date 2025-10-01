import uvicorn
import json
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from db import init_db, SessionLocal, AuditLog
from policy import check_permission, apply_privacy_filter

# Init DB
init_db()
app = FastAPI(title="MCP Project PoC")

# Auth
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Auth")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bad auth")
    token = parts[1]
    if ":" not in token:
        raise HTTPException(status_code=401, detail="Bad token format")
    user_id, role = token.split(":", 1)
    return {"id": user_id, "role": role}

# Request Models
class SearchRequest(BaseModel):
    q: str
    rows: Optional[int] = 5

class SummarizeRequest(BaseModel):
    doi: List[str]

class ImportRequest(BaseModel):
    doi: str

# Mock Connectors
def crossref_search(q, rows=5):
    return [{"title": f"Paper {i+1} about {q}", "doi": f"10.1000/{i+1}"} for i in range(rows)]

def crossref_get(doi):
    return {"title": f"Paper {doi}", "abstract": "Abstract text here", "authors": ["Alice Smith", "Bob Jones"], "year": 2024, "url": f"https://doi.org/{doi}"}

def summarize_with_openai(prompt):
    return f"Summary for prompt: {prompt[:50]}..."

def import_to_zotero(items):
    return {"imported": items, "status": "success"}

# Endpoints
@app.post("/api/v1/search")
def search(req: SearchRequest, user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], "can_search"):
        raise HTTPException(status_code=403, detail="Policy denied")
    papers = crossref_search(req.q, rows=req.rows)
    session = SessionLocal()
    entry = AuditLog(user_id=user["id"], action="search", resource="papers", details={"query": req.q})
    session.add(entry); session.commit(); session.close()
    return {"results": papers}

@app.get("/api/v1/paper/{doi}")
def get_paper(doi: str, user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], "can_search"):
        raise HTTPException(status_code=403, detail="Policy denied")
    paper = crossref_get(doi)
    session = SessionLocal()
    entry = AuditLog(user_id=user["id"], action="get_paper", resource=doi)
    session.add(entry); session.commit(); session.close()
    return paper

@app.post("/api/v1/summarize")
def summarize(req: SummarizeRequest, user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], "can_summarize"):
        raise HTTPException(status_code=403, detail="Policy denied")
    papers = [crossref_get(doi) for doi in req.doi]
    prompt = "Summarize each paper in one short paragraph (<=120 words) and list 2 unique contributions.\n\n"
    for i, p in enumerate(papers, 1):
        abstract = apply_privacy_filter({"abstract": p.get("abstract", "")}, user["role"])["abstract"]
        prompt += f"Paper {i}: Title: {p.get('title','')}\nAbstract: {abstract}\n\n"
    summary = summarize_with_openai(prompt)
    session = SessionLocal()
    entry = AuditLog(user_id=user["id"], action="summarize", resource=",".join(req.doi), details={"prompt": prompt})
    session.add(entry); session.commit(); session.close()
    return {"summary": summary}

@app.post("/api/v1/import")
def import_doi(req: ImportRequest, user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], "can_share"):
        raise HTTPException(status_code=403, detail="Policy denied")
    paper = crossref_get(req.doi)
    item = {"itemType": "journalArticle","title": paper.get("title"),"creators":[{"creatorType":"author","firstName":a.split()[0],"lastName":" ".join(a.split()[1:]) if len(a.split())>1 else ""} for a in paper.get("authors", [])],"date":str(paper.get("year") or ""),"url":paper.get("url"),"abstractNote":paper.get("abstract")}
    res = import_to_zotero([item])
    session = SessionLocal()
    entry = AuditLog(user_id=user["id"], action="import", resource=req.doi, details={"items":[item]})
    session.add(entry); session.commit(); session.close()
    return {"result": res}

@app.get("/api/v1/admin/audit")
def admin_audit(user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], "can_audit"):
        raise HTTPException(status_code=403, detail="Policy denied")
    session = SessionLocal()
    rows = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
    out = [{"id": r.id,"timestamp": r.timestamp.isoformat(),"user_id": r.user_id,"action": r.action,"resource": r.resource,"details": r.details} for r in rows]
    session.close()
    return {"entries": out}

@app.get("/")
def root():
    return {"msg": "MCP PoC API running."}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
