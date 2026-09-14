enum NoticeSeverity { info, warning, critical }

/// Local notification record. Live push (FCM) is a documented swap:
/// add google-services.json + firebase_messaging, keep this model unchanged.
class AppNotice {
  final String id;
  final String title;
  final String body;
  final NoticeSeverity severity;
  final DateTime at;
  final bool demo;

  const AppNotice({
    required this.id,
    required this.title,
    required this.body,
    required this.severity,
    required this.at,
    this.demo = true,
  });
}
