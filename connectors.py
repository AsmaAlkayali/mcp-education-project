import httpx
import os

# -------------------------
# CrossRef Connector
# -------------------------
async def search_crossref(query: str, rows: int = 5):
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "rows": rows,
        "mailto": os.getenv("CROSSREF_MAILTO", "you@example.com"),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        return [
            {
                "title": item["title"][0] if item.get("title") else "",
                "doi": item.get("DOI"),
                "year": item.get("issued", {}).get("date-parts", [[None]])[0][0],
            }
            for item in data["message"]["items"]
        ]


# -------------------------
# Semantic Scholar Connector
# -------------------------
async def search_semantic(query: str, limit: int = 5):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": limit, "fields": "title,year,authors,url"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        return [
            {
                "title": item.get("title"),
                "year": item.get("year"),
                "authors": [a["name"] for a in item.get("authors", [])],
                "url": item.get("url"),
            }
            for item in data.get("data", [])
        ]


# -------------------------
# Zotero Connector
# -------------------------
async def add_to_zotero(api_key: str, user_id: str, item: dict):
    """
    Add a reference to Zotero library
    """
    url = f"https://api.zotero.org/users/{user_id}/items"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=[item])
        resp.raise_for_status()
        return resp.json()
