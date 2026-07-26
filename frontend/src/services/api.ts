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