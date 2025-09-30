import os , uvicorn , json
from fastapi import FastAPI , Depends , HTTPException , Header
from pydantic import BaseModel
from typing import List , Optional

from db import init_db
from policy import check_policy , privacy_filter , write_audit
from connectors import crossref_search , crossref_get , summarize_with_openai , import_to_zotero


init_db()
app= FastAPI(title= "MCP Project")

def get_current_user(authorization:Optional[str]=Header(None)):
  if not authorization:
    raise HTTPException(status_code= 401 , detail = "Missing Auth")
    parts=authorization.split()
    if len(parts) !=2 or parts[0].lower() !="bearer":
      raise HTTPException(status_code=401 , detail = "Bad auth")
    token=parts[1]
    if ":" not in token:
      raise HTTPException(status_code=401 , detail ="Bad token format (expected user_id:role)")
    user_id, role= token.split(":", 1)
    return {"id" : user_id , "role": role}

class SearchRequest(BaseModel):
  q:str
  rows:Optional[int]=5
  
class SummarizeRequest(BaseModel):
  doi:List[str]
class ImportRequest(BaseModel):
  doi:str






@app.post("/api/v1/search")
def search(req: SearchRequest, user: dict = Depends(get_current_user)):
    pol = check_policy(user, resource="paper", action="search", context={"q": req.q})
    if not pol["allow"]:
        raise HTTPException(status_code=403, detail=f"Policy denied: {pol}")
    papers = crossref_search(req.q, rows=req.rows)
    write_audit(user_id=user["id"], action="search", resource="crossref", inputs=req.q, outputs=json.dumps([p["id"] for p in papers]), details={"policies": pol["policies"]})
    return {"results": papers, "policy": pol}

@app.get("/api/v1/paper/{doi}")
def get_paper(doi: str, user: dict = Depends(get_current_user)):
    pol = check_policy(user, resource="paper", action="view", context={"doi": doi})
    if not pol["allow"]:
        raise HTTPException(status_code=403, detail="Policy denied")
    p = crossref_get(doi)
    write_audit(user_id=user["id"], action="get_paper", resource=doi, details={"policies": pol["policies"]})
    return p

@app.post("/api/v1/summarize")
def summarize(req: SummarizeRequest, user: dict = Depends(get_current_user)):
    pol = check_policy(user, resource="paper", action="summarize", context={"dois": req.dois})
    if not pol["allow"]:
        raise HTTPException(status_code=403, detail="Policy denied")
    papers = [crossref_get(doi) for doi in req.dois]
    prompt = "Summarize each paper in one short paragraph (<=120 words) and list 2 unique contributions.\n\n"
    for i,p in enumerate(papers,1):
        abstract = privacy_filter(p.get("abstract",""))
        prompt += f"Paper {i}: Title: {p.get('title','')}\nAbstract: {abstract}\n\n"
    out = summarize_with_openai(prompt)
    write_audit(user_id=user["id"], action="summarize", resource=",".join(req.dois), inputs=prompt, outputs=out, details={"policies": pol["policies"]})
    return {"summary": out, "policy": pol}

@app.post("/api/v1/import")
def import_doi(req: ImportRequest, user: dict = Depends(get_current_user)):
    pol = check_policy(user, resource="library", action="import", context={"doi": req.doi})
    if not pol["allow"]:
        raise HTTPException(status_code=403, detail="Policy denied")
    paper = crossref_get(req.doi)
    item = {
        "itemType": "journalArticle",
        "title": paper.get("title"),
        "creators": [{"creatorType": "author", "firstName": a.split()[0], "lastName": " ".join(a.split()[1:]) if len(a.split())>1 else ""} for a in paper.get("authors",[])],
        "date": str(paper.get("year") or ""),
        "url": paper.get("url"),
        "abstractNote": paper.get("abstract")
    }
    res = import_to_zotero([item])
    write_audit(user_id=user["id"], action="import", resource=req.doi, inputs=json.dumps(item, ensure_ascii=False), outputs=json.dumps(res, ensure_ascii=False), details={"policies": pol["policies"]})
    return {"result": res, "policy": pol}

@app.get("/api/v1/admin/audit")
def admin_audit(user: dict = Depends(get_current_user)):
    pol = check_policy(user, resource="audit", action="admin:audit", context={})
    if not pol["allow"]:
        raise HTTPException(status_code=403, detail="Policy denied")
    from db import SessionLocal, AuditLog
    session = SessionLocal()
    rows = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "user_id": r.user_id,
            "action": r.action,
            "resource": r.resource,
            "inputs_hash": r.inputs_hash,
            "output_hash": r.output_hash,
            "details": r.details
        })
    session.close()
    return {"entries": out}

@app.get("/")
def root():
    return {"msg": "MCP PoC API running. Read README to configure env vars."}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
