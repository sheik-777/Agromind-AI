import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type ParsedReport } from '../services/api'

export const queryKeys = {
  soilReport: (id: string) => ['soilReport', id] as const,
  soilReports: ['soilReports'] as const,
  cropRecommendations: (reportId: string) => ['cropRecommendations', reportId] as const,
  health: ['health'] as const,
}

export function useUploadSoilReport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => api.uploadSoilReport(file),
    onMutate: async (_file) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.soilReports })
      const previousReports = queryClient.getQueryData(queryKeys.soilReports)
      return { previousReports }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.soilReports })
      return data
    },
    onError: (error, _file, context) => {
      if (context?.previousReports) {
        queryClient.setQueryData(queryKeys.soilReports, context.previousReports)
      }
      throw error
    },
  })
}

export function useSoilReport(reportId: string | null) {
  return useQuery({
    queryKey: reportId ? queryKeys.soilReport(reportId) : ['soilReport', 'null'],
    queryFn: async () => {
      if (!reportId) throw new Error('No report ID provided')
      throw new Error('Not implemented - use upload response directly')
    },
    enabled: !!reportId,
  })
}

export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => api.getHealth(),
    refetchInterval: 30000,
    retry: 3,
  })
}

export function useCropRecommendations(parsedReport: ParsedReport | null) {
  return useQuery({
    queryKey: ['cropRecommendations', parsedReport?.laboratory_analysis?.samples?.[0]?.parameters],
    queryFn: () => {
      if (!parsedReport) throw new Error('No parsed report')
      return parsedReport.crop_recommendations || []
    },
    enabled: !!parsedReport,
    staleTime: Infinity,
  })
}

export function useBestCrop(parsedReport: ParsedReport | null) {
  return useQuery({
    queryKey: ['bestCrop', parsedReport?.crop_recommendations],
    queryFn: () => {
      if (!parsedReport?.crop_recommendations?.length) return null
      return parsedReport.crop_recommendations[0]
    },
    enabled: !!parsedReport?.crop_recommendations?.length,
    staleTime: Infinity,
  })
}

export function useSoilSummary(parsedReport: ParsedReport | null) {
  return useQuery({
    queryKey: ['soilSummary', parsedReport?.laboratory_analysis?.samples?.[0]?.parameters],
    queryFn: () => {
      if (!parsedReport) return null
      const params = parsedReport?.laboratory_analysis?.samples?.[0]?.parameters
      if (!params?.length) return null

      const interpretationParams = parsedReport.interpretation?.[0]?.parameters || {}
      const warnings = parsedReport.warnings || []

      const parameters = params.map((p) => ({
        key: p.parameter,
        value: p.value,
        display_name: p.display_name,
        unit: p.unit,
        interpretation: interpretationParams[p.parameter]?.display_name || p.display_name,
      }))

      return {
        parameters,
        warnings,
        hasWarnings: warnings.length > 0,
      }
    },
    enabled: !!parsedReport?.laboratory_analysis?.samples?.[0]?.parameters?.length,
    staleTime: Infinity,
  })
}

