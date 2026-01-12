from fastapi import FastAPI, Request
import os, json, base64, urllib.request, urllib.error

app = FastAPI()

GITHUB_TOKEN = os.environ.get("github_personal_access_token")
REPO = os.environ.get("saves_repo")
SAVE_KEY = os.environ.get("AES_save_key", "").encode()  # bytes

def encrypt(text):
    text_bytes = text.encode()
    key = SAVE_KEY
    if not key:
        return base64.b64encode(text_bytes).decode()
    encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(text_bytes)])
    return base64.b64encode(encrypted).decode()

def push_to_github(filename, content):
    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"
    sha = None
    try:
        req = urllib.request.Request(url, headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        })
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read())
            sha = resp.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    data = {"message": f"update save {filename}", "content": content}
    if sha:
        data["sha"] = sha

    req = urllib.request.Request(url, data=json.dumps(data).encode(), method="PUT",
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"
        })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

@app.post("/save")
async def save(req: Request):
    data = await req.json()
    uuid = data.get("uuid")
    save_content = data.get("content")
    if not uuid or not save_content:
        return {"error": "uuid and content required"}

    filename = f"{uuid}.json"
    encrypted = encrypt(save_content)
    result = push_to_github(filename, encrypted)
    return {"ok": True, "filename": filename, "github_sha": result.get("content", {}).get("sha")}
