import { motion } from 'framer-motion'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import type { CropListItem } from '@/services/api'

interface Props {
  crop: CropListItem
  onClose: () => void
}

const RangeBar = ({ min, max, label, unit }: { min: number; max: number; label: string; unit?: string }) => {
  const avg = (min + max) / 2
  const range = max - min
  const displayRange = range < 0.5 ? `${min}${unit || ''} (fixed)` : `${min}–${max}${unit || ''}`
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">{label}</span>
        <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300">{displayRange}</span>
      </div>
      <div className="relative h-2 rounded-full bg-neutral-100 dark:bg-neutral-800">
        <div
          className="absolute inset-y-0 rounded-full bg-forest-200 dark:bg-forest-800"
          style={{ left: `${Math.max(0, (avg / (avg * 2 || 1)) * 100 - 15)}%`, width: `${Math.min(40, range / (avg || 1) * 100)}%` }}
        />
      </div>
    </div>
  )
}

export default function CropDetailModal({ crop, onClose }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 20 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl max-h-[90vh] overflow-y-auto"
      >
        <Card variant="elevated" className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-neutral-900 dark:text-white">{crop.name}</h2>
              <div className="flex flex-wrap gap-2 mt-2">
                <Badge variant="primary" size="sm">{crop.season.replace(/_/g, ' ')}</Badge>
                <Badge variant="accent" size="sm">{crop.soil_type.replace(/_/g, ' ')}</Badge>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
              aria-label="Close"
            >
              <svg className="w-5 h-5 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Growing Requirements */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-white mb-3 uppercase tracking-wide">Growing Requirements</h3>
            <div className="space-y-3">
              <RangeBar min={crop.ph_min} max={crop.ph_max} label="Soil pH" />
              <RangeBar min={crop.temp_min} max={crop.temp_max} label="Temperature" unit="°C" />
              <RangeBar min={crop.humidity_min} max={crop.humidity_max} label="Humidity" unit="%" />
              <RangeBar min={crop.rain_min} max={crop.rain_max} label="Rainfall" unit=" mm" />
              <RangeBar min={crop.moisture_min} max={crop.moisture_max} label="Soil Moisture" unit="%" />
            </div>
          </div>

          {/* Nutrient Requirements */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-white mb-3 uppercase tracking-wide">Nutrient Requirements (kg/ha)</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 rounded-xl bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800">
                <p className="text-xs font-medium text-green-600 dark:text-green-400 mb-1">Nitrogen (N)</p>
                <p className="text-sm font-bold text-green-800 dark:text-green-300">{crop.nitrogen_min} – {crop.nitrogen_max}</p>
              </div>
              <div className="text-center p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
                <p className="text-xs font-medium text-amber-600 dark:text-amber-400 mb-1">Phosphorus (P₂O₅)</p>
                <p className="text-sm font-bold text-amber-800 dark:text-amber-300">{crop.phosphorus_min} – {crop.phosphorus_max}</p>
              </div>
              <div className="text-center p-3 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800">
                <p className="text-xs font-medium text-blue-600 dark:text-blue-400 mb-1">Potassium (K₂O)</p>
                <p className="text-sm font-bold text-blue-800 dark:text-blue-300">{crop.potassium_min} – {crop.potassium_max}</p>
              </div>
            </div>
          </div>

          {/* Quick Summary */}
          <div className="p-4 rounded-xl bg-neutral-50 dark:bg-neutral-800/60 border border-neutral-200 dark:border-neutral-700">
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-white mb-2">Summary</h3>
            <p className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
              {crop.name} prefers {crop.soil_type.replace(/_/g, ' ')} soil with pH {crop.ph_min}–{crop.ph_max}, 
              temperatures of {crop.temp_min}–{crop.temp_max}°C, 
              and {crop.rain_min}–{crop.rain_max} mm annual rainfall. 
              Growing season: {crop.season.replace(/_/g, ' ')}. 
              Nutrient requirements: N {crop.nitrogen_min}–{crop.nitrogen_max}, 
              P₂O₅ {crop.phosphorus_min}–{crop.phosphorus_max}, 
              K₂O {crop.potassium_min}–{crop.potassium_max} kg/ha.
            </p>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  )
}