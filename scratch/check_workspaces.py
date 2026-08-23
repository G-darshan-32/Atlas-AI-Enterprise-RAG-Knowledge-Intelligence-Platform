import requests

BASE_URL = "http://localhost:8000"
res = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": "admin@atlas-ai.com", "password": "Admin@123456"})
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

workspaces = requests.get(f"{BASE_URL}/api/v1/workspaces", headers=headers).json()
for w in workspaces:
    print(f"Workspace: {w['name']} (ID: {w['id']})")
    docs = requests.get(f"{BASE_URL}/api/v1/workspaces/{w['id']}/documents", headers=headers).json()
    print("  Docs:", [d.get("title") for d in docs[:5]])
