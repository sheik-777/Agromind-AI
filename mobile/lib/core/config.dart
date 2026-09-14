/// Global app configuration: backend endpoint + data-source mode.
///
/// Demo mode ON (default) = the app runs fully offline on labeled demo data.
/// Turn it OFF in Profile → Settings to talk to a real backend, whose base
/// URL is configurable (emulator default http://10.0.2.2:8000; on a physical
/// phone use your PC's LAN IP, e.g. http://192.168.1.10:8000).
class AppSettings {
  final String baseUrl;
  final bool demoMode;

  const AppSettings({
    this.baseUrl = 'http://10.0.2.2:8000',
    this.demoMode = true,
  });

  AppSettings copyWith({String? baseUrl, bool? demoMode}) => AppSettings(
        baseUrl: baseUrl ?? this.baseUrl,
        demoMode: demoMode ?? this.demoMode,
      );
}

/// MQTT topic tree for the future telemetry bridge (documented, not yet live).
/// Broker → backend bridge → Postgres → REST. Phone never talks to hardware.
class MqttTopics {
  static String telemetry(String deviceId) => 'agromind/$deviceId/telemetry';
  static String status(String deviceId) => 'agromind/$deviceId/status';
  static String camera(String deviceId) => 'agromind/$deviceId/camera';
  static String irrigation(String deviceId) => 'agromind/$deviceId/irrigation';
  static String commands(String deviceId) => 'agromind/$deviceId/commands';
}

/// Camera doctrine: 5 scheduled scans/day, configurable server-side.
/// The app only ever displays last/next scan — never a fake live feed.
class CameraPolicy {
  static const int scansPerDay = 5;
}
