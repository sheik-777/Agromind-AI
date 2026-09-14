import { useMemo } from 'react'

export type FieldHealthStatus = 'healthy' | 'warning' | 'critical'

export interface FieldHealth {
  status: FieldHealthStatus
  /** True when derived from the user's own data; false = showcase default */
  live: boolean
  /** 0..1 leaf vibrance multiplier */
  vibrance: number
  /** Max bloom 0..1 gate for the flower system */
  bloomCeiling: number
  /** Sway amplitude 0..1 */
  sway: number
  label: string
  detail: string
}

const SHOWCASE: FieldHealth = {
  status: 'healthy',
  live: false,
  vibrance: 1,
  bloomCeiling: 1,
  sway: 1,
  label: 'Showcase grove',
  detail: 'Upload a soil report to link the tree to your field',
}

/**
 * Farm-health abstraction for the 3D tree.
 *
 * Real signals today: advisories (`warnings[]`) from the user's latest soil
 * report in sessionStorage (written by AnalyzeSoil after POST /soil/upload).
 *
 * Future sensor slots (soil moisture, temperature, humidity, pH, irrigation,
 * disease alerts) plug in here: extend the derivation below to return
 * 'warning' | 'critical' with adjusted vibrance/bloomCeiling/sway.
 * Visual components must only consume this interface — never raw sensors.
 */
export function useFieldHealth(): FieldHealth {
  return useMemo(() => {
    try {
      const raw = sessionStorage.getItem('soilReport')
      if (!raw) return SHOWCASE
      const data: unknown = JSON.parse(raw)
      const reports = Array.isArray(data) ? data : [data]
      let warningCount = 0
      for (const r of reports) {
        const w = (r as { warnings?: unknown })?.warnings
        if (Array.isArray(w)) warningCount += w.length
      }
      if (warningCount > 0) {
        return {
          status: 'warning',
          live: true,
          vibrance: 0.82,
          bloomCeiling: 0.55,
          sway: 0.7,
          label: 'Needs attention',
          detail: `${warningCount} soil advisor${warningCount === 1 ? 'y' : 'ies'} in your latest report`,
        }
      }
      return {
        status: 'healthy',
        live: true,
        vibrance: 1,
        bloomCeiling: 1,
        sway: 1,
        label: 'Healthy',
        detail: 'Latest soil report shows no advisories',
      }
    } catch {
      return SHOWCASE
    }
  }, [])
}
