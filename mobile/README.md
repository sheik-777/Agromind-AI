# AgroMind Mobile (Flutter)

Farmer-facing Android app. Talks to the same FastAPI backend as the web app.
Default boots into labeled **demo mode** (fully offline); point it at a real
backend from Profile → Settings.

## Toolchain (already installed on this machine)

| Tool | Location |
|---|---|
| Flutter 3.47.4 / Dart 3.13.3 | `E:\AgroMind_Tools\flutter` |
| JDK 17 (Temurin) | `E:\AgroMind_Tools\jdk17\jdk-17` |
| Android SDK 36, build-tools 36 | `E:\AgroMind_Tools\android-sdk` |
| Gradle home / pub cache | `E:\AgroMind_Tools\gradle-home`, `...\pub-cache` |

Load env first: `. E:\AgroMind_Tools\env.ps1`

## Run / build

```powershell
cd E:\AgroMind_Project_Structure\mobile
flutter pub get
flutter analyze
flutter run                    # device or emulator
flutter build apk --release    # → build/app/outputs/flutter-apk/app-release.apk
```

APK copy: `mobile/apks/agromind-release.apk` (debug-signed → installable;
replace with Play signing before any store release).

## Connect a real backend

Profile → Settings → Backend base URL → turn demo mode OFF.
Emulator: `http://10.0.2.2:8000` · Physical phone: PC LAN IP, e.g.
`http://192.168.1.10:8000`. Live today: `POST /soil/upload`. Field routes
(`GET /field/latest`, …) are documented in `lib/services/field_repository.dart`
and fall back with a named error until the backend implements them.

## Connect real IoT hardware

Phone never touches the STM32. Chain: STM32 → ESP32 → SIM800L/4G →
MQTT (`agromind/{device_id}/telemetry|status|camera|irrigation`, see
`lib/core/config.dart`) → broker → FastAPI → PostgreSQL → `GET /field/latest`.
Device ↔ farm mapping is by `device_id` (see `DeviceStatus.fieldId`).

## Weather / AI keys / camera / irrigation

- Weather: Open-Meteo → FastAPI → cache → app (`GET /weather`). No key needed;
  never call a provider from the client.
- AI: no client keys. Demo advisor is local; real path is `POST /ai/chat`
  with field context server-side.
- Camera: 5 scans/day (`CameraPolicy.scansPerDay`). Live view needs a
  4G-class modem; SIM800L = telemetry only.
- Irrigation is automatic; the UI explains WHY and offers no manual pump
  override (no safe-override backend exists).

## Known limitations

- Debug-signed APK (installable, not store-ready).
- Launch verified by build + analyze only — no Android emulator on this
  machine; install on a phone to smoke-test.
- 3D = interactive 2.5D grove + touch bloom (`widgets/grove_view.dart`);
  drop a `tree.glb` into `assets/3d/` and wire a model viewer when ready.
- Push = local notifications; FCM needs `google-services.json` + a Firebase project.
- Machine has 8 GB RAM: Gradle is capped (`-Xmx2G`, 1 worker) in
  `android/gradle.properties` — release builds take ~7–10 min.
