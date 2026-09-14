/**
 * Field-data contracts for the farmer platform.
 *
 * These types mirror the future backend shape (device → MQTT → FastAPI →
 * PostgreSQL → REST). The app must only consume these interfaces — never raw
 * sensor payloads — so swapping the mock source for REST later is a one-file change.
 */

export type DataSource = 'live' | 'demo'

export interface SensorReading {
  moisturePct: number
  soilTempC: number
  airTempC: number
  humidityPct: number
  ph: number
  rainLast24hMm: number
  recordedAt: string
  source: DataSource
}

export interface DeviceStatus {
  deviceId: string
  online: boolean
  lastSeenAt: string
  simSignalPct: number
  nextReportInMin: number
  source: DataSource
}

export interface CameraSchedule {
  scansPerDay: number
  lastScanAt: string
  nextScanAt: string
  lastFinding: string
  source: DataSource
}

export interface IrrigationStatus {
  state: 'idle' | 'scheduled' | 'running'
  currentMoisturePct: number
  targetMinPct: number
  targetMaxPct: number
  lastRunAt: string | null
  nextRunAt: string | null
  waterUsageLToday: number
  reason: string
  rainProbPct: number
  source: DataSource
}

export interface WeatherNow {
  tempC: number
  humidityPct: number
  rainProbPct: number
  windKph: number
  condition: string
  provider: 'open-meteo'
  source: DataSource
}

export interface WeatherDay {
  date: string
  tempMinC: number
  tempMaxC: number
  rainProbPct: number
  condition: string
}

export type InsightSeverity = 'info' | 'warning' | 'critical'

export interface AIInsight {
  id: string
  title: string
  detail: string
  /** Explainable AI: the observed values behind the recommendation. */
  why: string[]
  severity: InsightSeverity
  source: DataSource
}

export interface HistoryPoint {
  at: string
  moisturePct: number
  tempC: number
  humidityPct: number
}

export interface FieldSnapshot {
  sensors: SensorReading
  device: DeviceStatus
  camera: CameraSchedule
  irrigation: IrrigationStatus
  weatherNow: WeatherNow
  forecast: WeatherDay[]
  insights: AIInsight[]
  history: HistoryPoint[]
  /** Overall provenance of this snapshot. */
  source: DataSource
  fetchedAt: string
}
