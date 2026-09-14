import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../widgets/common.dart';

/// Field monitoring: current conditions + device status + 5-day history.
/// Charts use fl_chart; data source is labeled, never implied live.
class FieldScreen extends ConsumerWidget {
  const FieldScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final snapshot = ref.watch(snapshotProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Field monitoring')),
      body: snapshot.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Padding(padding: const EdgeInsets.all(24), child: Text('$e'))),
        data: (field) => ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            const SectionTitle('Current conditions', demo: true),
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.5,
              children: [
                MetricTile(value: '${field.sensors.moisturePct.toStringAsFixed(0)}%', label: 'Soil moisture', hint: 'Target 35–55%'),
                MetricTile(value: '${field.sensors.airTempC.toStringAsFixed(1)}°C', label: 'Air temp', hint: 'Soil ${field.sensors.soilTempC.toStringAsFixed(1)}°C'),
                MetricTile(value: '${field.sensors.humidityPct.toStringAsFixed(0)}%', label: 'Humidity', hint: 'Normal band'),
                MetricTile(value: field.sensors.ph.toStringAsFixed(1), label: 'Soil pH', hint: 'Slightly acidic'),
              ],
            ),
            const SizedBox(height: 20),
            const SectionTitle('Device status', demo: true),
            Card(
              child: ListTile(
                leading: Icon(
                  Icons.sensors,
                  color: field.device.online ? Colors.green : Colors.red,
                  size: 32,
                ),
                title: Text('${field.device.deviceId} · ${field.device.online ? 'ONLINE' : 'OFFLINE'}'),
                subtitle: Text(
                  'Field ${field.device.fieldId}\n'
                  'Last communication ${_ago(field.device.lastSeenAt)} · '
                  'SIM ${field.device.simSignalPct}% · next report in ${field.device.nextReportInMin} min',
                ),
                isThreeLine: true,
              ),
            ),
            const SizedBox(height: 20),
            const SectionTitle('5-day history', demo: true),
            Card(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(8, 16, 16, 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Padding(
                      padding: EdgeInsets.only(left: 8, bottom: 8),
                      child: Text('Soil moisture %', style: TextStyle(fontWeight: FontWeight.w600)),
                    ),
                    SizedBox(height: 180, child: _historyChart(context, field.history.map((h) => h.moisturePct).toList(), const Color(0xFF2D752D))),
                    const SizedBox(height: 12),
                    const Padding(
                      padding: EdgeInsets.only(left: 8, bottom: 8),
                      child: Text('Temperature °C', style: TextStyle(fontWeight: FontWeight.w600)),
                    ),
                    SizedBox(height: 180, child: _historyChart(context, field.history.map((h) => h.tempC).toList(), const Color(0xFFD97706))),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _ago(DateTime t) {
    final m = DateTime.now().difference(t).inMinutes;
    if (m < 1) return 'just now';
    if (m < 60) return '$m min ago';
    return '${m ~/ 60}h ago';
  }

  Widget _historyChart(BuildContext context, List<double> values, Color color) {
    final spots = [for (var i = 0; i < values.length; i++) FlSpot(i.toDouble(), values[i])];
    return LineChart(
      LineChartData(
        gridData: const FlGridData(show: true, drawVerticalLine: false),
        titlesData: FlTitlesData(
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              getTitlesWidget: (v, _) {
                const days = ['-5d', '-4d', '-3d', '-2d', '-1d', 'now'];
                final i = v.toInt();
                if (i < 0 || i >= days.length) return const SizedBox.shrink();
                return Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(days[i], style: const TextStyle(fontSize: 10)),
                );
              },
            ),
          ),
        ),
        borderData: FlBorderData(show: false),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: color,
            barWidth: 3,
            dotData: const FlDotData(show: true),
            belowBarData: BarAreaData(show: true, color: color.withValues(alpha: 0.18)),
          ),
        ],
      ),
    );
  }
}
