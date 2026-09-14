// Field-data contracts. Mirror of the web `services/field` types and of the
// future REST shape (GET /api/field/latest, /irrigation/status, /weather,
// /insights, /field/history). `source` marks every value live / demo.

enum DataSource { live, demo }

class SensorReading {
  final double moisturePct;
  final double soilTempC;
  final double airTempC;
  final double humidityPct;
  final double ph;
  final double rainLast24hMm;
  final DateTime recordedAt;
  final DataSource source;

  const SensorReading({
    required this.moisturePct,
    required this.soilTempC,
    required this.airTempC,
    required this.humidityPct,
    required this.ph,
    required this.rainLast24hMm,
    required this.recordedAt,
    required this.source,
  });
}

class DeviceStatus {
  final String deviceId;
  final String fieldId;
  final bool online;
  final DateTime lastSeenAt;
  final int simSignalPct;
  final int nextReportInMin;
  final DataSource source;

  const DeviceStatus({
    required this.deviceId,
    required this.fieldId,
    required this.online,
    required this.lastSeenAt,
    required this.simSignalPct,
    required this.nextReportInMin,
    required this.source,
  });
}

class CameraSchedule {
  final int scansPerDay;
  final DateTime lastScanAt;
  final DateTime nextScanAt;
  final String lastFinding;
  final DataSource source;

  const CameraSchedule({
    required this.scansPerDay,
    required this.lastScanAt,
    required this.nextScanAt,
    required this.lastFinding,
    required this.source,
  });
}

class IrrigationStatus {
  final String state; // idle | scheduled | running
  final double currentMoisturePct;
  final double targetMinPct;
  final double targetMaxPct;
  final DateTime? lastRunAt;
  final DateTime? nextRunAt;
  final double waterUsageLToday;
  final String reason;
  final double rainProbPct;
  final DataSource source;

  const IrrigationStatus({
    required this.state,
    required this.currentMoisturePct,
    required this.targetMinPct,
    required this.targetMaxPct,
    required this.lastRunAt,
    required this.nextRunAt,
    required this.waterUsageLToday,
    required this.reason,
    required this.rainProbPct,
    required this.source,
  });
}

class WeatherNow {
  final double tempC;
  final double humidityPct;
  final double rainProbPct;
  final double windKph;
  final String condition;
  final String provider;
  final DataSource source;

  const WeatherNow({
    required this.tempC,
    required this.humidityPct,
    required this.rainProbPct,
    required this.windKph,
    required this.condition,
    required this.provider,
    required this.source,
  });
}

class WeatherDay {
  final DateTime date;
  final double tempMinC;
  final double tempMaxC;
  final double rainProbPct;
  final String condition;

  const WeatherDay({
    required this.date,
    required this.tempMinC,
    required this.tempMaxC,
    required this.rainProbPct,
    required this.condition,
  });
}

enum InsightSeverity { info, warning, critical }

class AIInsight {
  final String id;
  final String title;
  final String detail;
  final List<String> why;
  final InsightSeverity severity;
  final DataSource source;

  const AIInsight({
    required this.id,
    required this.title,
    required this.detail,
    required this.why,
    required this.severity,
    required this.source,
  });
}

class HistoryPoint {
  final DateTime at;
  final double moisturePct;
  final double tempC;
  final double humidityPct;

  const HistoryPoint({
    required this.at,
    required this.moisturePct,
    required this.tempC,
    required this.humidityPct,
  });
}

class FieldSnapshot {
  final SensorReading sensors;
  final DeviceStatus device;
  final CameraSchedule camera;
  final IrrigationStatus irrigation;
  final WeatherNow weatherNow;
  final List<WeatherDay> forecast;
  final List<AIInsight> insights;
  final List<HistoryPoint> history;
  final DataSource source;
  final DateTime fetchedAt;

  const FieldSnapshot({
    required this.sensors,
    required this.device,
    required this.camera,
    required this.irrigation,
    required this.weatherNow,
    required this.forecast,
    required this.insights,
    required this.history,
    required this.source,
    required this.fetchedAt,
  });
}
