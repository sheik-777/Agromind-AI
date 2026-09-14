import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../widgets/common.dart';

/// Smart irrigation: automatic by design. The farmer sees state, reasoning,
/// history and usage — manual pump control is intentionally NOT offered
/// (safe override requires backend support that does not exist yet).
class IrrigationScreen extends ConsumerWidget {
  const IrrigationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final snapshot = ref.watch(snapshotProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Smart irrigation')),
      body: snapshot.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Padding(padding: const EdgeInsets.all(24), child: Text('$e'))),
        data: (field) {
          final irr = field.irrigation;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 12,
                            height: 12,
                            decoration: BoxDecoration(
                              color: irr.state == 'running' ? Colors.green : Colors.amber,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text('Pump ${irr.state.toUpperCase()}',
                              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                          const Spacer(),
                          const DemoChip(),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Moisture ${irr.currentMoisturePct.toStringAsFixed(0)}% · target ${irr.targetMinPct.toStringAsFixed(0)}–${irr.targetMaxPct.toStringAsFixed(0)}%',
                      ),
                      const SizedBox(height: 8),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: LinearProgressIndicator(
                          value: (irr.currentMoisturePct / 100).clamp(0.0, 1.0),
                          minHeight: 10,
                          backgroundColor: Colors.grey.shade200,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.4),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text('WHY: ${irr.reason}'),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.history),
                      title: const Text('Last irrigation'),
                      subtitle: Text(irr.lastRunAt == null ? 'No runs yet' : irr.lastRunAt.toString()),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.schedule),
                      title: const Text('Next evaluation'),
                      subtitle: Text(irr.nextRunAt == null ? '—' : irr.nextRunAt.toString()),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.water_drop),
                      title: const Text('Water usage today'),
                      subtitle: Text('${irr.waterUsageLToday.toStringAsFixed(0)} L · rain probability ${irr.rainProbPct.toStringAsFixed(0)}%'),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              const Text(
                'Fertilizer stays manual: the farmer applies it physically. AgroMind only recommends — see crop profiles.',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          );
        },
      ),
    );
  }
}
