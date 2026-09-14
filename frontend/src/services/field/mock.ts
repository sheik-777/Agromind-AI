import type { FieldSnapshot } from './types'

/**
 * HONEST MOCK — clearly labeled `demo` everywhere it surfaces.
 *
 * Shape matches the future REST responses so replacement is mechanical:
 *   GET /api/field/latest       -> sensors + device + camera
 *   GET /api/irrigation/status  -> irrigation
 *   GET /api/weather            -> weatherNow + forecast (backend calls Open-Meteo)
 *   GET /api/insights           -> insights
 *   GET /api/field/history?days=5 -> history
 *
 * Delete this file (or stop importing it) the moment those routes exist.
 * See `index.ts` for the single swap point.
 */

const HOUR = 3_600_000
const DAY = 24 * HOUR

function iso(offsetMs: number): string {
  return new Date(Date.now() - offsetMs).toISOString()
}

export function getMockSnapshot(): FieldSnapshot {
  return {
    source: 'demo',
    fetchedAt: new Date().toISOString(),
    sensors: {
      moisturePct: 31,
      soilTempC: 27.4,
      airTempC: 28.1,
      humidityPct: 62,
      ph: 6.2,
      rainLast24hMm: 0,
      recordedAt: iso(9 * 60_000),
      source: 'demo',
    },
    device: {
      deviceId: 'AGRO_NODE_001',
      online: true,
      lastSeenAt: iso(9 * 60_000),
      simSignalPct: 76,
      nextReportInMin: 6,
      source: 'demo',
    },
    camera: {
      scansPerDay: 5,
      lastScanAt: iso(3 * HOUR),
      nextScanAt: new Date(Date.now() + 2 * HOUR).toISOString(),
      lastFinding: 'No visible stress on sampled leaves',
      source: 'demo',
    },
    irrigation: {
      state: 'scheduled',
      currentMoisturePct: 31,
      targetMinPct: 35,
      targetMaxPct: 55,
      lastRunAt: iso(26 * HOUR),
      nextRunAt: new Date(Date.now() + 5 * HOUR).toISOString(),
      waterUsageLToday: 0,
      reason:
        'Soil moisture (31%) is below the 35–55% target band and rain probability is low (10%), so a morning cycle is scheduled.',
      rainProbPct: 10,
      source: 'demo',
    },
    weatherNow: {
      tempC: 28.1,
      humidityPct: 62,
      rainProbPct: 10,
      windKph: 11,
      condition: 'Partly cloudy',
      provider: 'open-meteo',
      source: 'demo',
    },
    forecast: [
      { date: iso(0), tempMinC: 22, tempMaxC: 30, rainProbPct: 10, condition: 'Partly cloudy' },
      { date: iso(-1 * DAY), tempMinC: 23, tempMaxC: 31, rainProbPct: 15, condition: 'Sunny intervals' },
      { date: iso(-2 * DAY), tempMinC: 22, tempMaxC: 29, rainProbPct: 45, condition: 'Showers likely' },
      { date: iso(-3 * DAY), tempMinC: 21, tempMaxC: 28, rainProbPct: 60, condition: 'Rain expected' },
      { date: iso(-4 * DAY), tempMinC: 22, tempMaxC: 30, rainProbPct: 20, condition: 'Cloudy breaks' },
    ],
    insights: [
      {
        id: 'irr-1',
        title: 'Irrigate tomorrow morning, ~25 minutes',
        detail: 'Bring the root zone back into the 35–55% band before midday heat.',
        why: [
          'Soil moisture 31% is below the 35% crop target',
          'Rain probability only 10% in the next 24h',
          'No irrigation in the last 26 hours',
        ],
        severity: 'warning',
        source: 'demo',
      },
      {
        id: 'leaf-1',
        title: 'Canopy looks clear in the last scan',
        detail: 'Midday camera sample shows no visible stress signatures.',
        why: ['Last scan 3h ago: no yellowing or spot patterns flagged', 'Humidity 62% — within normal band'],
        severity: 'info',
        source: 'demo',
      },
    ],
    history: [5, 4, 3, 2, 1, 0].map((d) => ({
      at: iso(d * DAY),
      moisturePct: [38, 36, 34, 33, 32, 31][5 - d],
      tempC: [27.1, 28.4, 29.2, 28.8, 27.9, 28.1][5 - d],
      humidityPct: [66, 63, 58, 60, 61, 62][5 - d],
    })),
  }
}
