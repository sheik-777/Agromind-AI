"""
MQTT → PostgreSQL bridge (run alongside FastAPI).
Subscribes to agromind/+/telemetry, validates, inserts via POST /field/ingest
or directly via SQLAlchemy. Requires paho-mqtt. Configure MQTT_HOST in env.
"""
import json
import os
import paho.mqtt.client as mqtt
import httpx

MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        # Validate minimal schema
        assert "device_id" in data and "field_id" in data
        # Forward to backend ingest (handles auth + validation + ownership)
        r = httpx.post(f"{BACKEND_URL}/field/ingest", json=data, timeout=10)
        print(f"ingest {data['device_id']} -> {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"bridge error {e} payload {msg.payload[:200]}")

client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.subscribe("agromind/+/telemetry")
print(f"Bridge listening on {MQTT_HOST}:{MQTT_PORT} → {BACKEND_URL}")
client.loop_forever()
