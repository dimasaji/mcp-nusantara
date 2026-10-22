import requests, json

s = requests.Session()
r = s.post("http://localhost:8080/api/v1/auths/signin",
           json={"email": "admin@admin.com", "password": "admin123"},
           timeout=10)
print("Login:", r.status_code)
data = r.json()
print("Token:", data.get("token", "")[:20] + "...")

for i in range(5):
    r = s.post("http://localhost:8080/api/v1/chat",
               json={"model": "llama3.2:1b", "messages": [{"role": "user", "content": "Halo, apa kabar?"}]},
               timeout=90)
    ok = r.status_code == 200
    msg = r.json().get("message", {}).get("content", "")[:50]
    print(f"Ujian {i+1}: HTTP {r.status_code} -> {msg}...")
