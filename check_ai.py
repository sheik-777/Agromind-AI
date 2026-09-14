from fastapi.testclient import TestClient
from backend.app import app
client = TestClient(app)

# Clean DB state for test - re-create tables fresh
from backend.config.database import engine, Base
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Register user
r = client.post("/auth/register", json={"name":"Test Farmer","email":"farmer@example.com","password":"password123","confirm_password":"password123"})
assert r.status_code==200, r.text
token = r.json()["token"]
hdr = {"Authorization": f"Bearer {token}"}

# Ingest two readings
for m in [38, 31]:
    r = client.post("/field/ingest", json={"device_id":"AGRO_NODE_001","field_id":"FIELD_TEST","soil_moisture":m,"temperature":30,"humidity":65,"soil_ph":6.2,"rain":False})
    assert r.status_code==200, r.text

# Check latest returns newest moisture 31
r = client.get("/field/latest", headers=hdr)
print("latest", r.json())
assert r.json()["soil_moisture"]==31

# Check history
r = client.get("/field/history?days=5", headers=hdr)
print("history len", len(r.json()))

# AI 10 questions
questions = [
 "Should I irrigate now?",
 "Why is my soil moisture falling?",
 "Why are my leaves turning yellow?",
 "Is my soil suitable for tomato?",
 "What should I do today?",
 "Will rain affect my irrigation?",
 "What fertilizer should I apply?",
 "What happened to my field during the last 5 days?",
 "What disease could affect my crop?",
 "Explain my latest soil report.",
]
intents = set()
for q in questions:
    r = client.post("/ai/ask", json={"question":q}, headers=hdr)
    j = r.json()
    intents.add(j["intent"])
    print(q, "->", j["intent"], "|", j["inferred"][:90].replace("\n"," "))
print("distinct intents", intents, len(intents))
assert len(intents) >= 6, "AI intents not diverse enough"

# Ownership: second user cannot see first's field
r2 = client.post("/auth/register", json={"name":"Other","email":"other@example.com","password":"password123","confirm_password":"password123"})
token2 = r2.json()["token"]
hdr2 = {"Authorization": f"Bearer {token2}"}
r = client.get("/field/latest", headers=hdr2)
print("other user latest", r.status_code, r.json())
assert r.status_code==404

print("ALL TESTS PASSED")