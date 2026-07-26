import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function ensureArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value
  if (value === null || value === undefined) return []
  if (typeof value === 'object' || typeof value === 'function') return []
  return [value as T]
}

export function ensureString(value: unknown, fallback = ''): string {
  if (typeof value === 'string') return value
  if (value === null || value === undefined) return fallback
  return String(value)
}

export function splitNewlines(text: string): string[] {
  if (!text) return []
  return text.split('\n').filter((line) => line.trim().length > 0)
}

export function formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat('en-US', options).format(value)
}

export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(value)
}

export function formatPercent(value: number, decimals = 0): string {
  return `${value.toFixed(decimals)}%`
}

export function formatRange(min: number, max: number, unit: string): string {
  return `${formatNumber(min)}-${formatNumber(max)}${unit}`
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

export function slugify(str: string): string {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

export function throttle<T extends (...args: unknown[]) => unknown>(
  fn: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      fn(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) +
    Math.random().toString(36).substring(2, 15)
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

export function lerp(start: number, end: number, factor: number): number {
  return start + (end - start) * factor
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function getColorForScore(score: number): string {
  if (score >= 90) return 'text-green-600 dark:text-green-400'
  if (score >= 75) return 'text-emerald-600 dark:text-emerald-400'
  if (score >= 50) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

export function getBgColorForScore(score: number): string {
  if (score >= 90) return 'bg-green-500/10 dark:bg-green-500/20'
  if (score >= 75) return 'bg-emerald-500/10 dark:bg-emerald-500/20'
  if (score >= 50) return 'bg-yellow-500/10 dark:bg-yellow-500/20'
  return 'bg-red-500/10 dark:bg-red-500/20'
}

export function getRatingForScore(score: number): { label: string; color: string } {
  if (score >= 90) return { label: 'Excellent', color: 'text-green-600 dark:text-green-400' }
  if (score >= 75) return { label: 'Good', color: 'text-emerald-600 dark:text-emerald-400' }
  if (score >= 50) return { label: 'Moderate', color: 'text-yellow-600 dark:text-yellow-400' }
  return { label: 'Poor', color: 'text-red-600 dark:text-red-400' }
}

export function getStarsForScore(score: number): number {
  return Math.max(1, Math.min(5, Math.round(score / 20)))
}

export function getConfidenceForMatch(match: string): string {
  const confidenceMap: Record<string, string> = {
    'Excellent': 'Highly Recommended',
    'Good': 'Recommended',
    'Moderate': 'Consider with Caution',
    'Poor': 'Not Recommended',
  }
  return confidenceMap[match] || 'Unknown'
}

export function parseSoilParameter(key: string): { label: string; unit: string } | null {
  const parameterMap: Record<string, { label: string; unit: string }> = {
    ph: { label: 'pH', unit: '' },
    nitrogen: { label: 'Nitrogen', unit: 'ppm' },
    phosphorus: { label: 'Phosphorus', unit: 'ppm' },
    potassium: { label: 'Potassium', unit: 'ppm' },
    calcium: { label: 'Calcium', unit: 'ppm' },
    magnesium: { label: 'Magnesium', unit: 'ppm' },
    sulphur: { label: 'Sulphur', unit: 'ppm' },
    zinc: { label: 'Zinc', unit: 'ppm' },
    iron: { label: 'Iron', unit: 'ppm' },
    copper: { label: 'Copper', unit: 'ppm' },
    boron: { label: 'Boron', unit: 'ppm' },
    manganese: { label: 'Manganese', unit: 'ppm' },
    sodium: { label: 'Sodium', unit: 'ppm' },
    sar: { label: 'SAR', unit: '' },
    esp: { label: 'ESP', unit: '%' },
    organic_matter: { label: 'Organic Matter', unit: '%' },
    organic_carbon: { label: 'Organic Carbon', unit: '%' },
    electrical_conductivity: { label: 'Electrical Conductivity', unit: 'dS/m' },
    moisture: { label: 'Moisture', unit: '%' },
  }
  return parameterMap[key] || null
}