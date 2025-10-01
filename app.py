import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from db import init_db
from policy import check_permission, apply_privacy_filter, log_audit, get_audit_log
from connectors import crossref_search, crossref_get, summarize_with_openai, import_to_zotero

init_db()
app = FastAPI(title="MCP Project PoC")

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

class SearchRequest(BaseModel):
    q: str
    rows: Optional[int] = 5

class SummarizeRequest(BaseModel):
    doi: List[str]

class ImportRequest(BaseModel):
    doi: str

@app.post("/api/v1/search")
def search(req: SearchRequest, user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], "can_search"):
        raise HTTPException(status_code=403, detail="Policy denied")
    papers = crossref_search(req.q, rows=req.rows)
    log_audit(user["id"], user["role"], "search", "success")
    return {"results": papers}

@app.get("/api/v1/paper/{doi}")
def get_paper(doi: str, user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], "can_search"):
        raise HTTPException(status_code=403, detail="Policy denied")
    paper = crossref_get(doi)
    log_audit(user["id"], user["role"], "get_paper", "success")
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
    log_audit(user["id"], user["role"], "summarize", "success")
    return {"summary": summary}

@app.post("/api/v1/import")
def import_doi(req: ImportRequest, user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], "can_share"):
        raise HTTPException(status_code=403, detail="Policy denied")
    paper = crossref_get(req.doi)
    item = {
        "itemType": "journalArticle",
        "title": paper.get("title"),
        "creators": [{"creatorType": "author", "firstName": a.split()[0], "lastName": " ".join(a.split()[1:]) if len(a.split())>1 else ""} for a in paper.get("authors", [])],
        "date": str(paper.get("year") or ""),
        "url": paper.get("url"),
        "abstractNote": paper.get("abstract")
    }
    res = import_to_zotero([item])
    log_audit(user["id"], user["role"], "import", "success")
    return {"result": res}

@app.get("/api/v1/admin/audit")
def admin_audit(user: dict = Depends(get_current_user)):
    if not check_permission(user["role"], "can_audit"):
        raise HTTPException(status_code=403, detail="Policy denied")
    return {"entries": get_audit_log()}

@app.get("/")
def root():
    return {"msg": "MCP PoC API running."}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
