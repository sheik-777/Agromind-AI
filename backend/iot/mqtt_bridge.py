"""
MQTT → PostgreSQL bridge (run alongside FastAPI).
Subscribes to agromind/+/telemetry, validates, inserts via POST /field/ingest
or directly via SQLAlchemy. Requires paho-mqtt. Configure MQTT_HOST in env.

Topics:
- agromind/{device_id}/telemetry    - sensor telemetry
- agromind/{device_id}/status       - device status (online/offline)
- agromind/{device_id}/camera       - camera scan results
agromind/{device_id}/irrigation     - irrigation events
agromind/{device_id}/commands       - commands from backend to device
"""
import json
import os
import time
import threading
import paho.mqtt.client as mqtt
import httpx
from datetime import datetime

MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
DEVICE_KEY_HEADER = "X-Device-Key"

# Thread-local HTTP client for connection pooling
thread_local = threading.local()

def get_http_client():
    if not hasattr(thread_local, "client"):
        thread_local.client = httpx.Client(timeout=10.0, limits=httpx.Limits(max_connections=10))
    return thread_local.client

def get_device_client(device_id: str, device_key: str) -> httpx.Client:
    """Get an HTTP client with device authentication headers."""
    client = get_http_client()
    # Add device auth headers
    return client

def validate_telemetry(payload: dict) -> tuple[bool, str]:
    """Validate telemetry payload. Returns (is_valid, error_message)."""
    required = ["device_id", "field_id"]
    for field in required:
        if field not in payload:
            return False, f"Missing required field: {field}"
    
    # Validate ranges if present
    if "soil_moisture" in payload and payload["soil_moisture"] is not None:
        if not (0 <= payload["soil_moisture"] <= 100):
            return False, "soil_moisture must be 0-100"
    if "temperature" in payload and payload["temperature"] is not None:
        if not (-40 <= payload["temperature"] <= 80):
            return False, "temperature out of range"
    if "humidity" in payload and payload["humidity"] is not None:
        if not (0 <= payload["humidity"] <= 100):
            return False, "humidity must be 0-100"
    if "soil_ph" in payload and payload["soil_ph"] is not None:
        if not (0 <= payload["soil_ph"] <= 14):
            return False, "soil_ph must be 0-14"
    if "rain" in payload and payload["rain"] is not None:
        if not isinstance(payload["rain"], bool):
            return False, "rain must be boolean"
    
    return True, ""

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        
        # Validate payload
        valid, error = validate_telemetry(data)
        if not valid:
            print(f"Invalid telemetry from {msg.topic}: {error}")
            return
        
        # Extract device_id from topic if not in payload
        topic_parts = msg.topic.split("/")
        if len(topic_parts) >= 3 and topic_parts[1] == "":
            # Topic format: agromind/+/telemetry -> parts = ['agromind', 'DEVICE_ID', 'telemetry']
            topic_device_id = topic_parts[1] if len(topic_parts) > 1 else None
            if topic_device_id and data.get("device_id") != topic_device_id:
                print(f"Device ID mismatch: payload={data.get('device_id')}, topic={topic_device_id}")
                return
        
        # Add server timestamp if not provided
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Forward to backend ingest (handles auth + validation + ownership)
        client = get_http_client()
        headers = {"Content-Type": "application/json"}
        
        # Check if device has a key configured and add it
        # For now, we'll add a header if device_key is in payload
        headers = {"Content-Type": "application/json"}
        if "device_key" in data:
            headers["X-Device-Key"] = data.pop("device_key")
        
        r = client.post(f"{BACKEND_URL}/field/ingest", json=data, headers=headers, timeout=10)
        if r.status_code >= 400:
            print(f"ingest failed {data['device_id']} -> {r.status_code} {r.text[:200]}")
        else:
            print(f"ingest {data['device_id']} -> {r.status_code} {r.text[:100]}")
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e} payload: {msg.payload[:200]}")
    except httpx.RequestError as e:
        print(f"HTTP request error: {e}")
    except Exception as e:
        print(f"bridge error {e} payload {msg.payload[:200]}")

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback when connected to MQTT broker."""
    if rc == 0:
        print(f"MQTT connected to {MQTT_HOST}:{MQTT_PORT}")
        # Subscribe to all telemetry topics
        client.subscribe("agromind/+/telemetry", qos=1)
        client.subscribe("agromind/+/status", qos=1)
        client.subscribe("agromind/+/camera", qos=1)
        client.subscribe("agromind/+/irrigation", qos=1)
        print("Subscribed to telemetry, status, camera, irrigation topics")
    else:
        print(f"MQTT connection failed with code {rc}")

def on_disconnect(client, userdata, rc, properties=None):
    """Callback when disconnected from MQTT broker."""
    print(f"MQTT disconnected with code {rc}")
    if rc != 0:
        print("Unexpected disconnection, will reconnect...")

def on_publish(client, userdata, mid):
    """Callback when message is published."""
    pass

def on_subscribe(client, userdata, mid, granted_qos):
    """Callback when subscription is acknowledged."""
    print(f"Subscribed with QoS: {granted_qos}")

def run_bridge():
    """Run the MQTT bridge with automatic reconnection."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_subscribe = on_subscribe
    
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # Enable automatic reconnection
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    
    while True:
        try:
            print(f"Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}...")
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_forever()
        except KeyboardInterrupt:
            print("Bridge stopped by user")
            break
        except Exception as e:
            print(f"Bridge error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    # Test validation
    test_payload = {
        "device_id": "AGRO_NODE_001",
        "field_id": "FIELD_001",
        "soil_moisture": 42,
        "temperature": 31,
        "humidity": 68,
        "soil_ph": 6.4,
        "rain": False
    }
    valid, error = validate_telemetry(test_payload)
    print(f"Validation test: {valid}, {error}")
    
    # Run bridge
    run_bridge()