import os
import requests
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

# مثال بحث CrossRef
def crossref_search(query, rows=5):
    url = f"https://api.crossref.org/works?query={query}&rows={rows}"
    r = requests.get(url)
    return r.json()["message"]["items"]

def crossref_get(doi):
    url = f"https://api.crossref.org/works/{doi}"
    r = requests.get(url)
    return r.json()["message"]

def summarize_with_openai(prompt):
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2
    )
    return resp.choices[0].message.content

def import_to_zotero(items):
    api_key = os.getenv("ZOTERO_API_KEY")
    user_id = os.getenv("ZOTERO_USER_ID")
    headers = {"tmDpOFvZjPTRurr9uizN54EY": api_key, "Content-Type": "application/json"}
    url = f"https://api.zotero.org/users/{user_id}/items"
    r = requests.post(url, headers=headers, json=items)
    return r.json()
