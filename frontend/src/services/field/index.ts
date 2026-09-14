import type { FieldSnapshot } from './types'
import { getMockSnapshot } from './mock'

/**
 * Single swap point for field data.
 *
 * Today every section resolves to the labeled demo snapshot because the
 * backend exposes no field routes yet (verified: only GET /, GET /health,
 * GET /auth/, POST /soil/upload exist).
 *
 * When the backend lands, replace the body of `getFieldSnapshot` with REST
 * calls and map each response onto the contracts in `types.ts` — no page
 * code changes required:
 *
 *   GET /api/field/latest       -> snapshot.sensors + .device + .camera
 *   GET /api/irrigation/status  -> snapshot.irrigation
 *   GET /api/weather            -> snapshot.weatherNow + .forecast
 *   GET /api/insights           -> snapshot.insights
 *   GET /api/field/history      -> snapshot.history
 */
export async function getFieldSnapshot(): Promise<FieldSnapshot> {
  return getMockSnapshot()
}

export type { FieldSnapshot }
export * from './types'
