import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../widgets/common.dart';

/// Device management: one card per node. Never hardcodes a single farmer —
/// nodes map device → field → farm; today the demo fleet has one node.
class DevicesScreen extends ConsumerWidget {
  const DevicesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final snapshot = ref.watch(snapshotProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Devices')),
      body: snapshot.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Padding(padding: const EdgeInsets.all(24), child: Text('$e'))),
        data: (field) {
          final d = field.device;
          final cam = field.camera;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        Text(d.deviceId,
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                        const Spacer(),
                        const DemoChip(),
                      ]),
                      const SizedBox(height: 8),
                      Row(children: [
                        Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                            color: d.online ? Colors.green : Colors.red,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(d.online ? 'ONLINE' : 'OFFLINE',
                            style: const TextStyle(fontWeight: FontWeight.w700)),
                      ]),
                      const SizedBox(height: 12),
                      _row('Field', d.fieldId),
                      _row('Last communication', d.lastSeenAt.toString()),
                      _row('Cellular', 'GPRS · SIM ${d.simSignalPct}%'),
                      _row('Sensors', '✓ Moisture  ✓ Temperature  ✓ Humidity  ✓ pH  ✓ Rain'),
                      _row('Camera', 'Scheduled · last ${_ago(cam.lastScanAt)} · next ${_in(cam.nextScanAt)}'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              const Text(
                'Chain: STM32 sensors → ESP32 → cellular → MQTT broker → FastAPI → PostgreSQL → this app. '
                'The phone never talks to hardware directly.',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _row(String k, String v) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: RichText(
          text: TextSpan(
            style: const TextStyle(fontSize: 14, color: Colors.black87),
            children: [
              TextSpan(text: '$k: ', style: const TextStyle(fontWeight: FontWeight.w700)),
              TextSpan(text: v),
            ],
          ),
        ),
      );

  String _ago(DateTime t) {
    final m = DateTime.now().difference(t).inMinutes;
    return m < 60 ? '$m min ago' : '${m ~/ 60}h ago';
  }

  String _in(DateTime t) {
    final m = t.difference(DateTime.now()).inMinutes;
    return m <= 0 ? 'due now' : 'in ${m ~/ 60}h ${m % 60}m';
  }
}
