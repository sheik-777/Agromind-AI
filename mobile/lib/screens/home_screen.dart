import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/field.dart';
import '../providers/providers.dart';
import '../widgets/common.dart';
import '../widgets/grove_view.dart';
import 'soil_screen.dart';
import 'irrigation_screen.dart';
import 'weather_screen.dart';
import 'camera_screen.dart';
import 'devices_screen.dart';
import 'notifications_screen.dart';

/// Home = the farmer's command center. Strong hierarchy, no card soup:
/// living grove → health → conditions → latest recommendation → modules.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final snapshot = ref.watch(snapshotProvider);
    final auth = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('AgroMind'),
            Text('Intelligent agriculture system',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500)),
          ],
        ),
        actions: [
          if (auth.demo)
            const Padding(
              padding: EdgeInsets.only(right: 8),
              child: Chip(label: Text('DEMO', style: TextStyle(fontSize: 10)), visualDensity: VisualDensity.compact),
            ),
          IconButton(
            tooltip: 'Notifications',
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const NotificationsScreen()),
            ),
          ),
        ],
      ),
      body: snapshot.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => _BackendError(message: e.toString()),
        data: (field) => ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            // Living grove
            Card(
              child: Column(
                children: [
                  SizedBox(
                    height: 300,
                    width: double.infinity,
                    child: ClipRRect(
                      borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                      child: GroveView(stressed: field.sensors.moisturePct < 35),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
                    child: Row(
                      children: [
                        Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                            color: field.sensors.moisturePct < 35 ? Colors.amber : Colors.green,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            field.sensors.moisturePct < 35
                                ? 'Field needs attention — moisture ${field.sensors.moisturePct.toStringAsFixed(0)}% is below target'
                                : 'Field looks healthy — touch the grove, buds bloom where you linger',
                            style: const TextStyle(fontSize: 13),
                          ),
                        ),
                        if (field.source == DataSource.demo) const DemoChip(),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            // Conditions strip
            Row(
              children: [
                _cond(context, '${field.sensors.moisturePct.toStringAsFixed(0)}%', 'Moisture', Icons.water_drop_outlined),
                _cond(context, '${field.sensors.airTempC.toStringAsFixed(1)}°', 'Temp', Icons.thermostat_outlined),
                _cond(context, '${field.sensors.humidityPct.toStringAsFixed(0)}%', 'Humidity', Icons.opacity_outlined),
                _cond(context, field.device.online ? 'Online' : 'Offline', 'IoT', Icons.sensors_outlined),
              ],
            ),
            const SizedBox(height: 16),
            // Latest AI recommendation (explainable)
            const SectionTitle('Latest recommendation', demo: true),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(field.insights.first.title,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                    const SizedBox(height: 4),
                    Text(field.insights.first.detail),
                    const SizedBox(height: 8),
                    ...field.insights.first.why.map((w) => Padding(
                          padding: const EdgeInsets.only(top: 2),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('·  '),
                              Expanded(child: Text(w, style: const TextStyle(fontSize: 13))),
                            ],
                          ),
                        )),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            const SectionTitle('Farm modules'),
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.6,
              children: [
                _module(context, 'Soil report', 'Upload lab PDF', Icons.science_outlined, const SoilScreen()),
                _module(context, 'Irrigation', field.irrigation.state, Icons.water_outlined, const IrrigationScreen()),
                _module(context, 'Weather', '${field.weatherNow.tempC.toStringAsFixed(0)}°C · 💧${field.weatherNow.rainProbPct.toStringAsFixed(0)}%', Icons.cloud_outlined, const WeatherScreen()),
                _module(context, 'Crop health', '5 scans / day', Icons.photo_camera_outlined, const CameraScreen()),
                _module(context, 'Devices', field.device.deviceId, Icons.router_outlined, const DevicesScreen()),
                _module(context, 'Alerts', '3 notices', Icons.notifications_outlined, const NotificationsScreen()),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _cond(BuildContext context, String value, String label, IconData icon) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Column(
            children: [
              Icon(icon, size: 20, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 4),
              Text(value, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
              Text(label, style: const TextStyle(fontSize: 11)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _module(BuildContext context, String title, String sub, IconData icon, Widget screen) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen)),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 8),
              Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
              Text(sub, style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
            ],
          ),
        ),
      ),
    );
  }
}

class _BackendError extends ConsumerWidget {
  final String message;
  const _BackendError({required this.message});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 60),
        const Text('⚠️', style: TextStyle(fontSize: 48), textAlign: TextAlign.center),
        const SizedBox(height: 12),
        const Text('Field backend unreachable', textAlign: TextAlign.center,
            style: TextStyle(fontWeight: FontWeight.w700, fontSize: 18)),
        const SizedBox(height: 8),
        Text(message, textAlign: TextAlign.center),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: () {
            ref.read(appConfigProvider.notifier).setDemoMode(true);
            ref.invalidate(snapshotProvider);
          },
          child: const Text('Continue in demo mode'),
        ),
      ],
    );
  }
}
