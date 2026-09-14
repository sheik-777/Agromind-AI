import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../widgets/common.dart';

/// Camera health: the camera is NOT continuous — 5 scheduled scans/day.
/// Shows last/next scan, findings with sensor context, honest live-view gate.
class CameraScreen extends ConsumerWidget {
  const CameraScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final snapshot = ref.watch(snapshotProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Crop health camera')),
      body: snapshot.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Padding(padding: const EdgeInsets.all(24), child: Text('$e'))),
        data: (field) {
          final cam = field.camera;
          final s = field.sensors;
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
                        const Text('📷', style: TextStyle(fontSize: 32)),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Text('Scheduled inspections',
                              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                        ),
                        const DemoChip(),
                      ]),
                      const SizedBox(height: 12),
                      _row('Scans per day', '${cam.scansPerDay} (configurable)'),
                      _row('Last scan', '${_ago(cam.lastScanAt)} — ${cam.lastFinding}'),
                      _row('Next scan', _in(cam.nextScanAt)),
                      const SizedBox(height: 12),
                      FilledButton.tonal(
                        onPressed: () => _liveUnavailable(context),
                        child: const Text('Request live view'),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Live view needs a 4G-class modem (SIM7600/A7670). The SIM800L link carries telemetry only.',
                        style: TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const SectionTitle('Environmental context at last scan', demo: true),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    'Moisture ${s.moisturePct.toStringAsFixed(0)}% · Temp ${s.airTempC.toStringAsFixed(1)}°C · '
                    'Humidity ${s.humidityPct.toStringAsFixed(0)}% · pH ${s.ph.toStringAsFixed(1)}\n\n'
                    'A yellowing leaf is an OBSERVATION, not a diagnosis. Possible causes: nutrient deficiency, '
                    'water stress, disease, environmental stress — ranked only when a real model scores them.',
                  ),
                ),
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

  void _liveUnavailable(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Live camera is unavailable: no 4G modem link on this device. Scheduled scans continue.'),
      ),
    );
  }
}
