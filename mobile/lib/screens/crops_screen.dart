import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/crop.dart';
import '../providers/providers.dart';
import '../widgets/common.dart';

/// Crop knowledge hub. Compares CROP REQUIREMENTS vs YOUR FIELD with an
/// explainable compatibility verdict — never a bare unexplained score.
class CropsScreen extends ConsumerStatefulWidget {
  const CropsScreen({super.key});

  @override
  ConsumerState<CropsScreen> createState() => _CropsScreenState();
}

class _CropsScreenState extends ConsumerState<CropsScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final crops = ref.watch(cropsProvider);
    final field = ref.watch(snapshotProvider).when(
          data: (d) => d,
          loading: () => null,
          error: (_, _) => null,
        );
    final list = crops.where((c) => c.name.toLowerCase().contains(_query.toLowerCase())).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Crop knowledge')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: TextField(
              decoration: const InputDecoration(hintText: 'Search crops…', prefixIcon: Icon(Icons.search)),
              onChanged: (v) => setState(() => _query = v),
            ),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: list.length,
              itemBuilder: (context, i) {
                final crop = list[i];
                final compat = field == null ? null : compatibilityOf(crop, field.sensors);
                return Card(
                  child: ExpansionTile(
                    leading: const Text('🌾', style: TextStyle(fontSize: 28)),
                    title: Text(crop.name, style: const TextStyle(fontWeight: FontWeight.w700)),
                    subtitle: Text('${crop.category} · ${crop.season} · ${crop.duration}'),
                    trailing: compat == null
                        ? null
                        : _verdictChip(compat.verdict, compat.pct),
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(crop.overview),
                            const SizedBox(height: 10),
                            if (compat != null) ...[
                              Row(children: [
                                const Text('Your field: ',
                                    style: TextStyle(fontWeight: FontWeight.w700)),
                                Text(compat.verdict,
                                    style: const TextStyle(fontWeight: FontWeight.w700)),
                                const SizedBox(width: 6),
                                const DemoChip(),
                              ]),
                              ...compat.reasons.map((r) => Padding(
                                    padding: const EdgeInsets.only(top: 2),
                                    child: Text('· $r', style: const TextStyle(fontSize: 13)),
                                  )),
                              const SizedBox(height: 10),
                            ],
                            _kv('Soil pH', '${crop.phMin}–${crop.phMax}'),
                            _kv('Temperature', '${crop.tempMinC}–${crop.tempMaxC}°C'),
                            _kv('Moisture', '${crop.moistureMinPct.toStringAsFixed(0)}–${crop.moistureMaxPct.toStringAsFixed(0)}% (field-relative bands)'),
                            _kv('Water need', crop.water),
                            _kv('Nutrients', crop.nutrients.join('; ')),
                            _kv('Diseases', crop.diseases.join(', ')),
                            _kv('Prevention', crop.prevention.join('; ')),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _verdictChip(String verdict, int pct) {
    final color = verdict == 'Compatible'
        ? Colors.green
        : verdict == 'Needs attention'
            ? Colors.amber.shade800
            : Colors.red;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(20)),
      child: Text('$pct%', style: TextStyle(color: color, fontWeight: FontWeight.w800, fontSize: 12)),
    );
  }

  Widget _kv(String k, String v) => Padding(
        padding: const EdgeInsets.only(top: 4),
        child: RichText(
          text: TextSpan(
            style: const TextStyle(fontSize: 13, color: Colors.black87),
            children: [
              TextSpan(text: '$k: ', style: const TextStyle(fontWeight: FontWeight.w700)),
              TextSpan(text: v),
            ],
          ),
        ),
      );
}
