/*
 * ESP32-WROOM — UART → MQTT bridge (WiFi prototype).
 * 1) Read STM32 line M:42,T:31,H:68,PH:64,R:0 over Serial2
 * 2) Validate ranges, add device_id/field_id/timestamp
 * 3) Publish to agromind/{device_id}/telemetry via MQTT over WiFi.
 * For cellular, replace WiFiClient with TinyGSM (SIM800L/SIM7600) — same publish logic.
 *
 * Device identity is flashed per-node (unique AGRO_NODE_xxx). Do NOT take field_id from phone.
 */
#include <WiFi.h>
#include <PubSubClient.h>

const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASS = "YOUR_PASS";
const char* MQTT_HOST = "YOUR_MQTT_BROKER"; // e.g. test.mosquitto.org or your FastAPI host
const int MQTT_PORT = 1883;
const char* DEVICE_ID = "AGRO_NODE_001";
const char* FIELD_ID = "FIELD_8C57E9"; // provisioned field, matches backend

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

bool parseLine(const String& line, float &m, float &t, float &h, float &ph, int &rain) {
  int _ph10;
  if (sscanf(line.c_str(), "M:%f,T:%f,H:%f,PH:%d,R:%d", &m, &t, &h, &_ph10, &rain)==5) {
    ph = _ph10 / 10.0f;
    return (m>=0&&m<=100 && h>=0&&h<=100 && ph>=0&&ph<=14);
  }
  return false;
}

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, 16, 17); // RX=16 TX=17 to STM32
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status()!=WL_CONNECTED) delay(500);
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
}

void loop() {
  if (!mqtt.connected()) {
    String cid = String("agromind-") + DEVICE_ID;
    mqtt.connect(cid.c_str());
  }
  mqtt.loop();

  if (Serial2.available()) {
    String line = Serial2.readStringUntil('\n');
    line.trim();
    float m,t,h,ph; int rain;
    if (!parseLine(line, m,t,h,ph,rain)) return;

    String topic = String("agromind/") + DEVICE_ID + "/telemetry";
    String payload = String("{\"device_id\":\"") + DEVICE_ID +
      "\",\"field_id\":\"" + FIELD_ID +
      "\",\"soil_moisture\":" + m +
      ",\"temperature\":" + t +
      ",\"humidity\":" + h +
      ",\"soil_ph\":" + ph +
      ",\"rain\":" + (rain? "true":"false") +
      ",\"timestamp\":\"" + String(__DATE__) + "\"}";

    // Also support HTTP ingest for WiFi-first testing:
    // POST http://YOUR_BACKEND/field/ingest with same JSON (no MQTT needed initially)
    mqtt.publish(topic.c_str(), payload.c_str());
  }
}
