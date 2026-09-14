import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../widgets/common.dart';

/// Weather, translated into agricultural impact — not a generic widget.
/// Provider chain: Open-Meteo → FastAPI → cache → app. Today: demo-shaped.
class WeatherScreen extends ConsumerWidget {
  const WeatherScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final snapshot = ref.watch(snapshotProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Weather')),
      body: snapshot.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Padding(padding: const EdgeInsets.all(24), child: Text('$e'))),
        data: (field) {
          final w = field.weatherNow;
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
                        Text('${w.tempC.toStringAsFixed(0)}°C',
                            style: const TextStyle(fontSize: 44, fontWeight: FontWeight.w800)),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(w.condition,
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                        ),
                        const DemoChip(),
                      ]),
                      const SizedBox(height: 8),
                      Text(
                        'Humidity ${w.humidityPct.toStringAsFixed(0)}% · Rain ${w.rainProbPct.toStringAsFixed(0)}% · Wind ${w.windKph.toStringAsFixed(0)} kph',
                      ),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.4),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Text(
                          'AGRICULTURAL IMPACT: rain expected mid-week — scheduled irrigation may be reduced. '
                          'High midday heat plus falling moisture raises irrigation demand.',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const SectionTitle('5-day forecast', demo: true),
              ...field.forecast.map((d) => Card(
                    child: ListTile(
                      leading: const Icon(Icons.cloud_outlined),
                      title: Text(
                        '${_weekday(d.date)} · ${d.tempMaxC.toStringAsFixed(0)}° / ${d.tempMinC.toStringAsFixed(0)}°',
                      ),
                      subtitle: Text(d.condition),
                      trailing: Text('💧${d.rainProbPct.toStringAsFixed(0)}%',
                          style: const TextStyle(fontWeight: FontWeight.w700)),
                    ),
                  )),
              const SizedBox(height: 8),
              Text('Provider: ${w.provider} (via backend when live)',
                  style: TextStyle(color: Theme.of(context).hintColor, fontSize: 12)),
            ],
          );
        },
      ),
    );
  }

  String _weekday(DateTime d) {
    const names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return names[d.weekday - 1];
  }
}
