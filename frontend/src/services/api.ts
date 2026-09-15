import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 120000, // 2 minutes for PDF processing
    })

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('auth_token')
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  async uploadSoilReport(file: File): Promise<SoilReportResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.client.post<SoilReportResponse>('/soil/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          this.onUploadProgress?.(progress)
        }
      },
    })

    return response.data
  }

  async getHealth(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/health')
    return response.data
  }

  getBaseURL(): string {
    return this.client.defaults.baseURL || ''
  }

  onUploadProgress?: (progress: number) => void

  async getCrops(params: CropListParams): Promise<CropListResponse> {
    const searchParams = new URLSearchParams()
    if (params.page) searchParams.set('page', String(params.page))
    if (params.limit) searchParams.set('limit', String(params.limit))
    if (params.search) searchParams.set('search', params.search)
    if (params.soil_type) searchParams.set('soil_type', params.soil_type)
    if (params.season) searchParams.set('season', params.season)
    if (params.sort) searchParams.set('sort', params.sort)
    if (params.order) searchParams.set('order', params.order)
    const response = await this.client.get<CropListResponse>(`/crops?${searchParams.toString()}`)
    return response.data
  }

  async getCropStats(): Promise<CropStatsResponse> {
    const response = await this.client.get<CropStatsResponse>('/crops/stats')
    return response.data
  }

  async getCropDetail(cropName: string): Promise<CropDetail> {
    const response = await this.client.get<CropDetail>(`/crops/${encodeURIComponent(cropName)}`)
    return response.data
  }

  async getCropCompatibility(cropName: string): Promise<CropCompatibility> {
    const response = await this.client.get<CropCompatibility>(`/crops/${encodeURIComponent(cropName)}/compatibility`)
    return response.data
  }

  async askAgroMind(payload: { question: string; conversation?: { role: string; content: string }[] }): Promise<AiAskResponse> {
    const response = await this.client.post<AiAskResponse>('/ai/ask', payload)
    return response.data
  }
}

export const api = new ApiClient()

export interface SoilReportResponse {
  success: boolean
  message: string
  filename: string
  pages_converted: number
  generated_images: string[]
  parsed_report: ParsedReport[]
}

export interface ParsedReport {
  metadata: ReportMetadata
  laboratory_analysis: LaboratoryAnalysis
  interpretation: InterpretationEntry[]
  recommendations: Recommendations
  warnings: string[]
  crop_recommendations: CropRecommendation[]
}

export interface ReportMetadata {
  lab_number: string | null
  account: string | null
  client: string | null
  county: string | null
  date_received: string | null
  date_processed: string | null
  send_to: string | null
  area_type: string | null
  area_designation: string | null
}

export interface LaboratoryAnalysis {
  samples: LabSample[]
  unknown_parameters: unknown[]
}

export interface LabSample {
  sample_id: string
  parameters: SoilParameter[]
  unknown_parameters: unknown[]
}

export interface SoilParameter {
  parameter: string
  display_name: string
  original_name: string
  value: number | string
  unit: string
}

export interface InterpretationEntry {
  categories_header: string | null
  parameters: Record<string, InterpretationParam>
}

export interface InterpretationParam {
  display_name: string
  original_name: string
  breakpoints: number[]
}

export interface Recommendations {
  lime_to_apply: string
  fertilizer_to_apply: string
  cultural_and_management_tips: string
  references_and_resources: string
}

export interface CropRecommendation {
  crop: string
  score: number
  stars: number
  match: string
  confidence: string
  parameter_scores: Record<string, ParameterScore>
  recommended_environment: Environment
  summary: Summary
}

export interface ParameterScore {
  value: number
  ideal_range: [number, number]
  score: number
  rating: string
}

export interface Environment {
  temperature: string
  humidity: string
  rainfall: string
  soil_type: string
  season: string
}

export interface Summary {
  strengths: string[]
  improvements: string[]
}

export interface CropListItem {
  id: string
  name: string
  soil_type: string
  season: string
  ph_min: number
  ph_max: number
  temp_min: number
  temp_max: number
  humidity_min: number
  humidity_max: number
  rain_min: number
  rain_max: number
  nitrogen_min: number
  nitrogen_max: number
  phosphorus_min: number
  phosphorus_max: number
  potassium_min: number
  potassium_max: number
  moisture_min: number
  moisture_max: number
}

export interface CropListParams {
  page?: number
  limit?: number
  search?: string
  soil_type?: string
  season?: string
  sort?: string
  order?: string
}

export interface CropListResponse {
  crops: CropListItem[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface CropStatsResponse {
  total_records: number
  unique_crops: number
  soil_types: { name: string; count: number }[]
  seasons: { name: string; count: number }[]
  columns: string[]
}

export interface CropDetail {
  id: string
  name: string
  soil_type: string
  season: string
  nitrogen: { min: number; max: number }
  phosphorus: { min: number; max: number }
  potassium: { min: number; max: number }
  ph: { min: number; max: number }
  temperature: { min: number; max: number }
  humidity: { min: number; max: number }
  rainfall: { min: number; max: number }
  moisture: { min: number; max: number }
}

export interface CropCompatibility {
  crop_name: string
  compatibility_score: number
  matched: string[]
  constraints: string[]
  scores: Record<string, number | null>
  field_used: boolean
}

export interface AiAskResponse {
  answer: string
  intent: string
  confidence: string
  answer_mode: string
  field_context_used: boolean
  crop_context_used: boolean
  weather_context_used: boolean
  observed: string[]
  sources: { title: string; source: string; url?: string }[]
  warning?: string
  llm?: { configured: boolean; provider?: string; model?: string } | null
}