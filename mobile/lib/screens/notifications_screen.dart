import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/app_notice.dart';
import '../providers/providers.dart';

/// Notification center: meaningful farm events only — moisture, rain,
/// crop-health, device, irrigation, AI. Local delivery today; FCM is the
/// documented swap (see NotificationService).
class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  Color _color(NoticeSeverity s) => switch (s) {
        NoticeSeverity.info => Colors.blue,
        NoticeSeverity.warning => Colors.amber.shade800,
        NoticeSeverity.critical => Colors.red,
      };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notices = ref.watch(noticesProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Notifications')),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: notices.length,
        itemBuilder: (context, i) {
          final n = notices[i];
          return Card(
            child: ListTile(
              leading: Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(color: _color(n.severity), shape: BoxShape.circle),
              ),
              title: Text(n.title, style: const TextStyle(fontWeight: FontWeight.w700)),
              subtitle: Text('${n.body}\n${_ago(n.at)}${n.demo ? ' · demo' : ''}'),
              isThreeLine: true,
              onTap: () => demoNotify(n.title, n.body),
            ),
          );
        },
      ),
    );
  }

  String _ago(DateTime t) {
    final m = DateTime.now().difference(t).inMinutes;
    if (m < 1) return 'just now';
    if (m < 60) return '$m min ago';
    return '${m ~/ 60}h ago';
  }
}
