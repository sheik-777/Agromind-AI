import 'package:dio/dio.dart';
import '../models/field.dart';

/// HONEST MOCK — every value tagged demo. Shape matches the future REST
/// responses so the UI swap is mechanical. Delete when routes exist.
class MockFieldRepository implements FieldRepository {
  @override
  Future<FieldSnapshot> getSnapshot() async {
    final now = DateTime.now();
    DateTime ago(Duration d) => now.subtract(d);
    DateTime ahead(Duration d) => now.add(d);
    const ds = DataSource.demo;
    return FieldSnapshot(
      source: ds,
      fetchedAt: now,
      sensors: SensorReading(
        moisturePct: 31,
        soilTempC: 27.4,
        airTempC: 28.1,
        humidityPct: 62,
        ph: 6.2,
        rainLast24hMm: 0,
        recordedAt: ago(const Duration(minutes: 9)),
        source: ds,
      ),
      device: DeviceStatus(
        deviceId: 'AGRO_NODE_001',
        fieldId: 'FIELD_001',
        online: true,
        lastSeenAt: ago(const Duration(minutes: 9)),
        simSignalPct: 76,
        nextReportInMin: 6,
        source: ds,
      ),
      camera: CameraSchedule(
        scansPerDay: 5,
        lastScanAt: ago(const Duration(hours: 3)),
        nextScanAt: ahead(const Duration(hours: 2)),
        lastFinding: 'No visible stress on sampled leaves',
        source: ds,
      ),
      irrigation: IrrigationStatus(
        state: 'scheduled',
        currentMoisturePct: 31,
        targetMinPct: 35,
        targetMaxPct: 55,
        lastRunAt: ago(const Duration(hours: 26)),
        nextRunAt: ahead(const Duration(hours: 5)),
        waterUsageLToday: 0,
        reason:
            'Soil moisture (31%) is below the 35–55% target band and rain probability is low (10%), so a morning cycle is scheduled.',
        rainProbPct: 10,
        source: ds,
      ),
      weatherNow: const WeatherNow(
        tempC: 28.1,
        humidityPct: 62,
        rainProbPct: 10,
        windKph: 11,
        condition: 'Partly cloudy',
        provider: 'open-meteo',
        source: ds,
      ),
      forecast: const [
        _Day(0, 22, 30, 10, 'Partly cloudy'),
        _Day(1, 23, 31, 15, 'Sunny intervals'),
        _Day(2, 22, 29, 45, 'Showers likely'),
        _Day(3, 21, 28, 60, 'Rain expected'),
        _Day(4, 22, 30, 20, 'Cloudy breaks'),
      ].map((d) {
        final date = DateTime.now().add(Duration(days: d.offset));
        return WeatherDay(
          date: DateTime(date.year, date.month, date.day),
          tempMinC: d.min,
          tempMaxC: d.max,
          rainProbPct: d.rain,
          condition: d.label,
        );
      }).toList(),
      insights: const [
        AIInsight(
          id: 'irr-1',
          title: 'Irrigate tomorrow morning, ~25 minutes',
          detail: 'Bring the root zone back into the 35–55% band before midday heat.',
          why: [
            'Soil moisture 31% is below the 35% crop target',
            'Rain probability only 10% in the next 24h',
            'No irrigation in the last 26 hours',
          ],
          severity: InsightSeverity.warning,
          source: ds,
        ),
        AIInsight(
          id: 'leaf-1',
          title: 'Canopy looks clear in the last scan',
          detail: 'Midday camera sample shows no visible stress signatures.',
          why: [
            'Last scan 3h ago: no yellowing or spot patterns flagged',
            'Humidity 62% — within normal band',
          ],
          severity: InsightSeverity.info,
          source: ds,
        ),
      ],
      history: const [
        _H(5, 38, 27.1, 66),
        _H(4, 36, 28.4, 63),
        _H(3, 34, 29.2, 58),
        _H(2, 33, 28.8, 60),
        _H(1, 32, 27.9, 61),
        _H(0, 31, 28.1, 62),
      ].map((h) {
        final date = DateTime.now().subtract(Duration(days: h.daysAgo));
        return HistoryPoint(
          at: DateTime(date.year, date.month, date.day),
          moisturePct: h.moisture,
          tempC: h.temp,
          humidityPct: h.humidity,
        );
      }).toList(),
    );
  }
}

class _Day {
  final int offset;
  final double min;
  final double max;
  final double rain;
  final String label;
  const _Day(this.offset, this.min, this.max, this.rain, this.label);
}

class _H {
  final int daysAgo;
  final double moisture;
  final double temp;
  final double humidity;
  const _H(this.daysAgo, this.moisture, this.temp, this.humidity);
}

/// Thrown when demo mode is OFF but a backend route does not exist yet.
/// Message names the missing route so the failure is diagnosable, not silent.
class FieldBackendException implements Exception {
  final String message;
  const FieldBackendException(this.message);
  @override
  String toString() => message;
}

abstract class FieldRepository {
  Future<FieldSnapshot> getSnapshot();
}

/// Live repository — wired endpoint by endpoint as the backend lands.
/// Endpoints it will call (documented, several missing server-side today):
///   GET /api/field/latest, /api/irrigation/status, /api/weather,
///   /api/insights, /api/field/history
class ApiFieldRepository implements FieldRepository {
  final Dio dio;
  ApiFieldRepository(this.dio);

  @override
  Future<FieldSnapshot> getSnapshot() async {
    try {
      final res = await dio.get('/field/latest');
      var snap = _snapshotFromJson(res.data as Map<String, dynamic>);
      // Try to enrich with real history (non-fatal if missing)
      try {
        final h = await dio.get('/field/history', queryParameters: {'days': 5});
        final list = (h.data as List).cast<Map<String, dynamic>>();
        final history = list
            .map((e) => HistoryPoint(
                  at: DateTime.tryParse(e['at']?.toString() ?? '') ?? DateTime.now(),
                  moisturePct: (e['soil_moisture'] as num?)?.toDouble() ?? 0,
                  tempC: (e['temperature'] as num?)?.toDouble() ?? 0,
                  humidityPct: (e['humidity'] as num?)?.toDouble() ?? 0,
                ))
            .toList();
        if (history.isNotEmpty) {
          snap = FieldSnapshot(
            sensors: snap.sensors,
            device: snap.device,
            camera: snap.camera,
            irrigation: snap.irrigation,
            weatherNow: snap.weatherNow,
            forecast: snap.forecast,
            insights: snap.insights,
            history: history,
            source: snap.source,
            fetchedAt: snap.fetchedAt,
          );
        }
      } catch (_) {}
      return snap;
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw const FieldBackendException(
          'GET /field/latest does not exist on this backend yet. '
          'Enable Demo mode in Profile → Settings, or deploy the field routes.',
        );
      }
      throw FieldBackendException('Field backend unreachable: ${e.message}');
    }
  }

  FieldSnapshot _snapshotFromJson(Map<String, dynamic> j) {
    // Minimal mapping; extended as routes land. Falls back to demo shape gaps.
    final now = DateTime.now();
    T get<T>(String key, T fallback) {
      final v = j[key];
      return v is T ? v : fallback;
    }
    return FieldSnapshot(
      source: DataSource.live,
      fetchedAt: now,
      sensors: SensorReading(
        moisturePct: (get<num>('soil_moisture', 0)).toDouble(),
        soilTempC: (get<num>('soil_temperature', 0)).toDouble(),
        airTempC: (get<num>('temperature', 0)).toDouble(),
        humidityPct: (get<num>('humidity', 0)).toDouble(),
        ph: (get<num>('soil_ph', 7)).toDouble(),
        rainLast24hMm: 0,
        recordedAt: DateTime.tryParse(get<String>('timestamp', '')) ?? now,
        source: DataSource.live,
      ),
      device: DeviceStatus(
        deviceId: get<String>('device_id', 'unknown'),
        fieldId: get<String>('field_id', 'unknown'),
        online: true,
        lastSeenAt: now,
        simSignalPct: 0,
        nextReportInMin: 0,
        source: DataSource.live,
      ),
      camera: CameraSchedule(
        scansPerDay: 5,
        lastScanAt: now,
        nextScanAt: now,
        lastFinding: 'No scan data yet',
        source: DataSource.live,
      ),
      irrigation: IrrigationStatus(
        state: 'idle',
        currentMoisturePct: (get<num>('soil_moisture', 0)).toDouble(),
        targetMinPct: 35,
        targetMaxPct: 55,
        lastRunAt: null,
        nextRunAt: null,
        waterUsageLToday: 0,
        reason: 'Live reading shown; recommendations arrive with /irrigation/status.',
        rainProbPct: 0,
        source: DataSource.live,
      ),
      weatherNow: const WeatherNow(
        tempC: 0,
        humidityPct: 0,
        rainProbPct: 0,
        windKph: 0,
        condition: '—',
        provider: 'open-meteo',
        source: DataSource.live,
      ),
      forecast: const [],
      insights: const [],
      history: const [],
    );
  }
}
