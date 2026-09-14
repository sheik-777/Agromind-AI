import 'package:flutter_local_notifications/flutter_local_notifications.dart';

/// Local notification architecture. FCM push is the documented swap
/// (add google-services.json + firebase_messaging; keep this API surface).
class NotificationService {
  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  static bool _ready = false;

  static Future<void> init() async {
    if (_ready) return;
    const settings = InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
    );
    await _plugin.initialize(settings: settings);
    const channel = AndroidNotificationChannel(
      'agromind_alerts',
      'Field alerts',
      description: 'Irrigation events, sensor warnings, AI recommendations',
      importance: Importance.high,
    );
    await _plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
    await _plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.requestNotificationsPermission();
    _ready = true;
  }

  static Future<void> show({
    required int id,
    required String title,
    required String body,
  }) async {
    if (!_ready) return;
    await _plugin.show(
      id: id,
      title: title,
      body: body,
      notificationDetails: const NotificationDetails(
        android: AndroidNotificationDetails(
          'agromind_alerts',
          'Field alerts',
          importance: Importance.high,
          priority: Priority.high,
        ),
      ),
    );
  }
}
