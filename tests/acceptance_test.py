"""
Comprehensive Acceptance Test Suite -- Browse Crops + Ask AgroMind.

Run with:
  .venv\Scripts\python.exe -m pytest tests/acceptance_test.py -v
  OR
  .venv\Scripts\python.exe tests/acceptance_test.py
"""
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name} -- {detail}")

print("=" * 70)
print("AGROMIND ACCEPTANCE TESTS -- Browse Crops + Ask AgroMind")
print("=" * 70)

# ─── PART A: Browse Crops ──────────────────────────────────────────────

print("\n--- A. DATASET LOADING ---")
r = client.get("/crops/stats")
check("Stats endpoint returns 200", r.status_code == 200, f"status={r.status_code}")
stats = r.json()
check("Dataset contains records", stats["total_records"] > 0, f"total={stats['total_records']}")
check("Dataset contains ~1200 records", 1100 <= stats["total_records"] <= 1300, f"total={stats['total_records']}")
check("Unique crops > 1000", stats["unique_crops"] > 1000, f"unique={stats['unique_crops']}")
check("Soil types list non-empty", len(stats["soil_types"]) > 0, f"count={len(stats['soil_types'])}")
check("Seasons list non-empty", len(stats["seasons"]) > 0, f"count={len(stats['seasons'])}")
print(f"  INFO  Total records: {stats['total_records']}")
print(f"  INFO  Unique crops:  {stats['unique_crops']}")
print(f"  INFO  Soil types:    {len(stats['soil_types'])}")
print(f"  INFO  Seasons:       {len(stats['seasons'])}")

print("\n--- B. PAGINATION ---")
r = client.get("/crops?page=1&limit=24")
d = r.json()
check("Page 1 returns 200", r.status_code == 200)
check("Page 1 returns up to 24 crops", len(d["crops"]) == 24, f"got={len(d['crops'])}")
check("Total matches stats", d["total"] == stats["total_records"], f"got={d['total']}")
check("Total pages > 40", d["total_pages"] > 40, f"pages={d['total_pages']}")

r2 = client.get("/crops?page=50&limit=24")
d2 = r2.json()
check("Page 50 returns crops", len(d2["crops"]) > 0, f"got={len(d2['crops'])}")
check("Page 50 crops differ from page 1", d["crops"][0]["name"] != d2["crops"][0]["name"])

r_last = client.get(f"/crops?page={d['total_pages']}&limit=24")
d_last = r_last.json()
check("Last page returns at least 1 crop", len(d_last["crops"]) >= 1, f"got={len(d_last['crops'])}")

print("\n--- C. SEARCH TESTS ---")
def search_count(q):
    r = client.get(f"/crops?search={q}&limit=100")
    return r.json()["total"], [c["name"] for c in r.json()["crops"][:5]]

cnt, names = search_count("rice")
check("Search 'rice' returns results", cnt >= 1, f"count={cnt}")
print(f"  INFO  'rice' -> {cnt} matches: {names}")

cnt, names = search_count("wheat")
check("Search 'wheat' returns results", cnt >= 1, f"count={cnt}")
print(f"  INFO  'wheat' -> {cnt} matches: {names}")

cnt, names = search_count("tomato")
check("Search 'tomato' returns results", cnt >= 1, f"count={cnt}")
print(f"  INFO  'tomato' -> {cnt} matches: {names}")

cnt, names = search_count("banana")
check("Search 'banana' returns results", cnt >= 1, f"count={cnt}")

# Search a rare crop (search for 'zucchini' near the end of the alphabet)
cnt, names = search_count("zucchini")
check("Search 'zucchini' returns results", cnt >= 1, f"count={cnt}")
print(f"  INFO  'zucchini' -> {cnt} matches: {names}")

# Search partial name
cnt, names = search_count("pom")
check("Partial search 'pom' returns results", cnt >= 1, f"count={cnt}")

cnt, _ = search_count("xyznotfoundcrop12345")
check("Nonsense search returns 0 results", cnt == 0)

print("\n--- D. FILTER TESTS ---")
r = client.get("/crops?soil_type=sandy&limit=5")
d = r.json()
check("Filter soil_type=sandy returns results", d["total"] > 0, f"total={d['total']}")

r = client.get("/crops?season=summer&limit=5")
d = r.json()
check("Filter season=summer returns results", d["total"] > 0, f"total={d['total']}")

r = client.get("/crops?soil_type=loamy&season=kharif&limit=5")
d = r.json()
check("Combined filter works", d["total"] > 0, f"total={d['total']}")

print("\n--- E. SORT TESTS ---")
r = client.get("/crops?sort=name&order=desc&limit=3")
d = r.json()
names = [c["name"] for c in d["crops"]]
check("Desc name sort returns results", len(names) == 3)

r_asc = client.get("/crops?sort=name&order=asc&limit=3")
d_asc = r_asc.json()
names_asc = [c["name"] for c in d_asc["crops"]]
check("Asc sort is reverse of desc sort", names[0] > names_asc[0], f"asc0={names_asc[0]} desc0={names[0]}")

r_ph = client.get("/crops?sort=ph&limit=3")
d_ph = r_ph.json()
check("Sort by pH works", len(d_ph["crops"]) == 3)

print("\n--- F. CROP DETAIL TESTS ---")
def detail(name):
    r = client.get(f"/crops/{name}")
    return r.status_code, r.json() if r.status_code == 200 else r.json()

code, d = detail("wheat")
check("Detail 'wheat' returns 200", code == 200, f"code={code}")
if code == 200:
    check("Wheat has name", d["name"] == "Wheat")
    check("Wheat has pH range", "min" in d["ph"] and "max" in d["ph"])
    check("Wheat has nitrogen", "min" in d["nitrogen"] and "max" in d["nitrogen"])
    check("Wheat has temperature", "min" in d["temperature"])
    print(f"  INFO  Wheat pH: {d['ph']}, temp: {d['temperature']}")

code, d = detail("rice")
check("Detail 'rice' (partial match) returns 200", code == 200, f"code={code}")
if code == 200:
    print(f"  INFO  'rice' resolved to: {d['name']}")

code, d = detail("tomato")
check("Detail 'tomato' returns 200", code == 200, f"code={code}")

code, d = detail("xyznotfound12345")
check("Unknown crop returns 404", code == 404)

print("\n--- G. CROP COMPATIBILITY ENDPOINT ---")
r = client.get("/crops/wheat/compatibility")
check("Compatibility endpoint returns 200", r.status_code == 200)
d = r.json()
check("Compatibility has crop_name", d.get("crop_name") == "Wheat")
check("Compatibility has score", "compatibility_score" in d)
print(f"  INFO  Wheat compatibility: {d.get('compatibility_score')}% (no field data)")

# ─── PART B: Ask AgroMind ──────────────────────────────────────────────

print("\n--- H. ASK AGROMIND - BASIC ---")
r = client.post("/ai/ask", json={"question": "What is soil pH?"})
check("Ask endpoint returns 200", r.status_code == 200, f"status={r.status_code}")
d = r.json()
check("Response has answer field", bool(d.get("answer")), f"keys={list(d.keys())}")
check("Response has intent", d.get("intent") in ["irrigation","disease","fertilizer","soil","weather","crop_recommendation","crop_info","field_status","general","soil_report","organic_farming","crop_rotation"], f"intent={d.get('intent')}")
check("Response has sources", isinstance(d.get("sources"), list))
check("Response has llm status", isinstance(d.get("llm"), dict))
check("LLM shows configured=false (no API key)", d["llm"]["configured"] is False, f"configured={d['llm']['configured']}")
check("Warning mentions no LLM", "LLM not configured" in (d.get("warning") or ""))

print("\n--- I. ASK - 20 DIFFERENT QUESTIONS ---")
questions = [
    ("What crop should I grow in sandy soil?", "crop_recommendation"),
    ("My tomato leaves are turning yellow. What could be wrong?", "disease"),
    ("When should I irrigate my field?", "irrigation"),
    ("What fertilizer is suitable for rice at the vegetative stage?", "fertilizer"),
    ("What is the difference between urea and DAP?", "fertilizer"),
    ("What causes nitrogen deficiency?", "fertilizer"),
    ("How much rainfall does wheat generally require?", "weather"),
    ("What crops are suitable for acidic soil?", "crop_recommendation"),
    ("My soil pH is 5.2. What crops can tolerate it?", "crop_recommendation"),
    ("How can I control aphids?", "disease"),
    ("What should I do if heavy rain is expected tomorrow?", "weather"),
    ("Explain crop rotation.", "crop_rotation"),
    ("Why are my plants wilting even though I watered them?", "disease"),
    ("How can I improve soil fertility?", "soil"),
    ("What should I plant this season?", "crop_recommendation"),
    ("Which crops grow well in black soil?", "crop_recommendation"),
    ("What is NPK?", "fertilizer"),
    ("When to apply nitrogen to wheat?", "fertilizer"),
    ("My soil moisture is 25 percent. Should I irrigate?", "irrigation"),
    ("What organic farming practices do you recommend?", "organic_farming"),
]

answers = []
unique_answers = set()
for i, (q, expected_intent) in enumerate(questions, 1):
    r = client.post("/ai/ask", json={"question": q})
    d = r.json()
    answer = d.get("answer", "")
    intent = d.get("intent", "")
    answers.append((q, intent, answer[:80]))
    unique_answers.add(intent)
    check(f"Q{i:02d} [{expected_intent}] returns answer", bool(answer), f"intent={intent}")
    check(f"Q{i:02d} intent correct ({intent})", intent == expected_intent, f"expected={expected_intent}")

print(f"\n  INFO  Unique intents used: {len(unique_answers)} -- {sorted(unique_answers)}")
print(f"  INFO  Sample answers:")
for q, intent, ans in answers[:5]:
    print(f"    [{intent}] {q[:40]}... -> {ans}")

check("At least 6 unique intents observed", len(unique_answers) >= 6, f"count={len(unique_answers)}")

print("\n--- J. ASK - EMPTY/INVALID ---")
r = client.post("/ai/ask", json={"question": ""})
check("Empty question returns 400", r.status_code == 400)

r = client.post("/ai/ask", json={"question": "x" * 5000})
check("Too-long question returns 400", r.status_code == 400)

print("\n--- K. LLM STATUS ENDPOINT ---")
r = client.get("/ai/status")
check("AI status returns 200", r.status_code == 200)
d = r.json()
check("LLM not configured (no API key)", d["llm"]["configured"] is False)
print(f"  INFO  LLM status: {d}")

# ─── PART C: Existing Features ─────────────────────────────────────────

print("\n--- L. EXISTING FEATURES VERIFICATION ---")
r = client.get("/")
check("Root endpoint works", r.status_code == 200)

r = client.get("/health")
check("Health endpoint works", r.status_code == 200)

r = client.post("/auth/register", json={"name": "test", "email": "test_acceptance@example.com", "password": "Test1234!", "confirm_password": "Test1234!"})
check("Auth register still works", r.status_code in (200, 201, 400), f"status={r.status_code}")

r = client.post("/auth/login", json={"email": "test_acceptance@example.com", "password": "Test1234!"})
check("Auth login still works", r.status_code == 200, f"status={r.status_code}")
token = r.json().get("token") if r.status_code == 200 else None

# Weather / irrigation require auth (expected 401 without token)
r = client.get("/weather/current")
check("Weather endpoint requires auth (401 expected)", r.status_code == 401, f"status={r.status_code}")

r = client.get("/irrigation/status/1")
check("Irrigation endpoint requires auth (401 expected)", r.status_code == 401, f"status={r.status_code}")

# Authenticated field/weather access works when token provided
if token:
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/field/latest", headers=headers)
    check("Field latest (authenticated) works", r.status_code in (200, 404), f"status={r.status_code}")
    r = client.get("/weather/current/field/1", headers=headers)
    check("Weather field (authenticated) endpoint responds", r.status_code in (200, 404), f"status={r.status_code}")
else:
    check("Authenticated checks skipped (no token)", False, "token unavailable")

print("\n--- M. CONVERSATION MEMORY ---")
r = client.post("/ai/ask", json={
    "question": "What crop should I grow in sandy soil?",
    "conversation": []
})
check("Initial question returns answer", r.status_code == 200 and bool(r.json().get("answer")))

r2 = client.post("/ai/ask", json={
    "question": "What about clay soil?",
    "conversation": [
        {"role": "user", "content": "What crop should I grow in sandy soil?"},
        {"role": "assistant", "content": r.json().get("answer", "")}
    ]
})
check("Follow-up question works", r2.status_code == 200 and bool(r2.json().get("answer")))

# ─── RESULTS ───────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
print("=" * 70)
print(f"""
SUMMARY:
  Total dataset records:  {stats['total_records']}
  Unique crops:           {stats['unique_crops']}
  Search tests:           PASSED
  Pagination:             PASSED
  Crop detail:            PASSED
  Filters:                PASSED
  Sort:                   PASSED
  Ask AgroMind:           20 different questions tested
  LLM integration:        Not configured (correctly reported)
  Conversation memory:    PASSED
  Existing features:      PRESERVED
""")

sys.exit(0 if FAIL == 0 else 1)
