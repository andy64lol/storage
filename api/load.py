from fastapi import FastAPI
import os, json, base64, urllib.request

app = FastAPI()

GITHUB_TOKEN = os.environ.get("github_personal_access_token")
REPO = os.environ.get("saves_repo")
SAVE_KEY = (os.environ.get("AES_save_key") or "").encode()

def decrypt(encoded):
    encrypted = base64.b64decode(encoded)
    key = SAVE_KEY
    decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted)])
    return decrypted.decode()

def fetch_from_github(filename):
    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    })
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())
        return resp["content"]

@app.get("/load")
async def load(uuid: str):
    filename = f"{uuid}.json"
    try:
        encrypted = fetch_from_github(filename)
        decrypted = decrypt(encrypted)
        return {"uuid": uuid, "content": decrypted}
    except Exception:
        return {"error": "file not found"}