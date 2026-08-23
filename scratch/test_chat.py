import requests

BASE_URL = "http://localhost:8000"

res = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": "admin@atlas-ai.com", "password": "Admin@123456"})
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

workspaces = requests.get(f"{BASE_URL}/api/v1/workspaces", headers=headers).json()
ws_id = workspaces[0]["id"]

session_res = requests.post(f"{BASE_URL}/api/v1/workspaces/{ws_id}/chat/sessions", json={"mode": "general"}, headers=headers)
session_id = session_res.json()["id"]

msg_url = f"{BASE_URL}/api/v1/workspaces/{ws_id}/chat/sessions/{session_id}/messages"
print("Sending prompt: Employee Handbook")
s = requests.Session()
with s.post(msg_url, json={"content": "Employee Handbook"}, headers=headers, stream=True) as resp:
    for line in resp.iter_lines():
        if line:
            print(line.decode("utf-8"))
