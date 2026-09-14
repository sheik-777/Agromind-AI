import { useQuery } from '@tanstack/react-query'
import { getFieldSnapshot } from '@/services/field'

/**
 * Farm snapshot for the command center.
 * Polls every 2 minutes (stale after 1) — matches the future telemetry cadence.
 */
export function useFieldData() {
  return useQuery({
    queryKey: ['field', 'snapshot'],
    queryFn: getFieldSnapshot,
    staleTime: 60_000,
    refetchInterval: 120_000,
    refetchOnWindowFocus: false,
  })
}
