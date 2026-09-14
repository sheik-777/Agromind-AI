from fastapi.testclient import TestClient
from backend.app import app
client = TestClient(app)

# Clean DB state
from backend.config.database import engine, Base
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Register user
r = client.post("/auth/register", json={"name":"Test Farmer","email":"farmer@test.com","password":"password123","confirm_password":"password123"})
assert r.status_code==200, r.text
token = r.json()["token"]
hdr = {"Authorization": f"Bearer {token}"}

# Get the field ID that was created during registration
from backend.config.database import SessionLocal
from backend.models.models import Farm, Field
db = SessionLocal()
farm = db.query(Farm).first()
field = db.query(Field).first()
print("farm:", farm.id, "field:", field.id)
field_id = field.id
db.close()

# Test irrigation decision
client = TestClient(app)
hdr = {"Authorization": f"Bearer {token}"}
r = client.get(f"/irrigation/decision/{field.id}", headers=hdr)
print("irrigation decision:", r.status_code, r.json())
assert r.status_code == 200
assert r.json()["decision"] in ["IRRIGATE", "WAIT", "MONITOR", "SKIP"]

# Test irrigation status
r = client.get(f"/irrigation/status/{field.id}", headers=hdr)
print("irrigation status:", r.status_code, r.json())
assert r.status_code == 200

# Test acknowledge (POST with query param)
r = client.post(f"/irrigation/decision/{field.id}/acknowledge?action=accept", headers=hdr)
print("acknowledge:", r.status_code, r.json())
assert r.status_code == 200

# Test AI with irrigation question
r = client.post("/ai/ask", json={"question": "Should I irrigate now?"}, headers=hdr)
print("AI irrigate:", r.status_code, r.json().get("intent"), r.json().get("inferred")[:100])
assert r.status_code == 200

print("ALL TESTS PASSED")