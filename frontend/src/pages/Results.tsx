import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import ProgressBar from '@/components/ui/ProgressBar'
import AnimatedCounter from '@/components/ui/AnimatedCounter'
import { getColorForScore, ensureArray, ensureString, splitNewlines } from '@/lib/utils'
import type { SoilReportResponse, CropRecommendation, SoilParameter } from '@/services/api'

const CHART_COLORS = ['#16a34a', '#10b981', '#84cc16', '#f59e0b', '#ef4444']

function getScoreBadgeVariant(score: number) {
  if (score >= 90) return 'success' as const
  if (score >= 75) return 'secondary' as const
  if (score >= 50) return 'warning' as const
  return 'danger' as const
}

function renderStars(count: number) {
  return Array.from({ length: 5 }, (_, i) => (
    <span key={i} className={i < count ? 'text-amber-400' : 'text-neutral-300 dark:text-neutral-600'}>
      ★
    </span>
  ))
}

function RecommendationBlock({ title, icon, text }: { title: string; icon: string; text: string }) {
  const lines = splitNewlines(text)
  if (lines.length === 0) return null
  return (
    <Card variant="glass" className="p-6">
      <h3 className="text-lg font-bold text-neutral-900 dark:text-white mb-3">{icon} {title}</h3>
      <div className="space-y-2">
        {lines.map((line, i) => (
          <p key={i} className="text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed">
            {line}
          </p>
        ))}
      </div>
    </Card>
  )
}

export default function Results() {
  const navigate = useNavigate()
  const [data, setData] = useState<SoilReportResponse | null>(null)
  const [activeCrop, setActiveCrop] = useState<CropRecommendation | null>(null)

  useEffect(() => {
    const stored = sessionStorage.getItem('soilReport')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        setData(parsed)
        if (parsed.parsed_report?.[0]?.crop_recommendations?.length) {
          setActiveCrop(parsed.parsed_report[0].crop_recommendations[0])
        }
      } catch {
        sessionStorage.removeItem('soilReport')
        navigate('/analyze')
      }
    } else {
      navigate('/analyze')
    }
  }, [navigate])

  if (!data || !data.parsed_report?.length) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="text-center">
          <span className="text-6xl block mb-4">📋</span>
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">No results found</h2>
          <p className="text-neutral-500 dark:text-neutral-400 mb-4">Upload a soil report to see analysis results.</p>
          <Button onClick={() => navigate('/analyze')}>Analyze a Report</Button>
        </div>
      </div>
    )
  }

  const report = data.parsed_report[0]
  const labAnalysis = report.laboratory_analysis
  const firstSample = labAnalysis?.samples?.[0]
  const soilParams: SoilParameter[] = firstSample?.parameters || []
  const interpretationParams = report.interpretation?.[0]?.parameters || {}
  const recommendations = report.recommendations || {}
  const crops = report.crop_recommendations || []
  const metadata = report.metadata || {}
  const warnings = ensureArray<string>(report.warnings)

  const cropScores = crops.map((c, idx) => ({
    name: c.crop,
    score: c.score,
    fill: CHART_COLORS[idx % CHART_COLORS.length],
  }))

  return (
    <div className="min-h-screen py-8 lg:py-12">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight font-display text-neutral-900 dark:text-white">
              Soil Analysis Results
            </h1>
            <p className="text-neutral-500 dark:text-neutral-400 mt-1">
              {data.filename} — {metadata.client || 'Unknown Client'}
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" size="sm" onClick={() => navigate('/analyze')}>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Analysis
            </Button>
            <Button size="sm">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800"
        >
          <div className="flex items-start gap-3">
            <span className="text-amber-500 text-lg">⚠️</span>
            <div>
              <h4 className="font-medium text-amber-800 dark:text-amber-200 mb-1">Warnings</h4>
              <ul className="text-sm text-amber-700 dark:text-amber-300 space-y-1">
                {warnings.map((w, i) => (
                  <li key={i}>• {w}</li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>
      )}

      {/* Metadata Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
      >
        {[
          { label: 'Lab #', value: metadata.lab_number || '—' },
          { label: 'Client', value: metadata.client || '—' },
          { label: 'County', value: metadata.county || '—' },
          { label: 'Area', value: metadata.area_designation || '—' },
        ].map((item) => (
          <Card key={item.label} variant="glass" className="p-4">
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-1">{item.label}</p>
            <p className="font-semibold text-neutral-900 dark:text-white truncate">{item.value}</p>
          </Card>
        ))}
      </motion.div>

      {/* Top Crop Recommendation */}
      {crops.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <Card variant="glass" className="p-6 md:p-8 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-forest-500/5 to-emerald-500/5" />
            <div className="relative">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-2xl">🏆</span>
                <h2 className="text-xl font-bold text-neutral-900 dark:text-white">Top Recommendation</h2>
              </div>
              <div className="flex flex-col md:flex-row md:items-center gap-6">
                <div className="flex-1">
                  <h3 className="text-3xl font-bold font-display text-neutral-900 dark:text-white mb-2">
                    {crops[0].crop}
                  </h3>
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl font-bold text-forest-600 dark:text-forest-400">
                      <AnimatedCounter value={crops[0].score} suffix="%" />
                    </span>
                    <Badge variant={getScoreBadgeVariant(crops[0].score)}>
                      {crops[0].match}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1 text-lg">
                    {renderStars(crops[0].stars)}
                  </div>
                  <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-2">
                    {crops[0].confidence}
                  </p>
                </div>
                <div className="w-full md:w-64">
                  <ResponsiveContainer width="100%" height={200}>
                    <RadarChart data={Object.entries(crops[0].parameter_scores || {}).map(([k, v]) => ({
                      parameter: k.charAt(0).toUpperCase() + k.slice(1),
                      score: v.score,
                      fullMark: 100,
                    }))}>
                      <PolarGrid stroke="#e5e7eb" />
                      <PolarAngleAxis dataKey="parameter" tick={{ fontSize: 12 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                      <Radar name="Score" dataKey="score" stroke="#16a34a" fill="#16a34a" fillOpacity={0.3} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        {/* Soil Parameters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2"
        >
          <Card variant="glass" className="p-6">
            <h3 className="text-lg font-bold text-neutral-900 dark:text-white mb-4">
              🧪 Soil Parameters
            </h3>
            <div className="space-y-4">
              {soilParams.length > 0 ? (
                soilParams.map((param) => {
                  const interp = interpretationParams[param.parameter]
                  const interpLabel = interp ? interp.display_name : param.display_name
                  const numericValue = typeof param.value === 'number' ? param.value : parseFloat(String(param.value))
                  const isNumeric = !isNaN(numericValue)
                  return (
                    <div key={param.parameter} className="flex items-center gap-4">
                      <div className="w-24 flex-shrink-0">
                        <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">{param.display_name}</span>
                      </div>
                      <div className="flex-1">
                        {isNumeric ? (
                          <ProgressBar value={Math.min(numericValue, 100)} variant="gradient" size="sm" />
                        ) : (
                          <div className="h-1.5 w-full rounded-full bg-neutral-100 dark:bg-neutral-800" />
                        )}
                      </div>
                      <div className="w-20 text-right">
                        <span className="text-sm font-semibold text-neutral-900 dark:text-white">
                          {param.value}{param.unit ? ` ${param.unit}` : ''}
                        </span>
                      </div>
                      <div className="w-24">
                        <Badge variant="default" size="sm">
                          {interpLabel}
                        </Badge>
                      </div>
                    </div>
                  )
                })
              ) : (
                <p className="text-sm text-neutral-500 dark:text-neutral-400">No soil parameters available.</p>
              )}
            </div>
          </Card>
        </motion.div>

        {/* Crop Scores Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card variant="glass" className="p-6 h-full">
            <h3 className="text-lg font-bold text-neutral-900 dark:text-white mb-4">
              🌾 Crop Scores
            </h3>
            {cropScores.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={cropScores}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="score"
                      nameKey="name"
                    >
                      {cropScores.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-wrap gap-2 mt-2">
                  {crops.map((c) => (
                    <button
                      key={c.crop}
                      onClick={() => setActiveCrop(c)}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                        activeCrop?.crop === c.crop
                          ? 'bg-forest-600 text-white'
                          : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700'
                      }`}
                    >
                      {c.crop}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm text-neutral-500 dark:text-neutral-400 text-center py-8">No crop data available.</p>
            )}
          </Card>
        </motion.div>
      </div>

      {/* All Crop Recommendations */}
      {crops.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mb-8"
        >
          <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-4">
            🌾 Top {crops.length} Crop Recommendations
          </h3>
          <div className={`grid gap-4 ${crops.length === 1 ? 'grid-cols-1' : crops.length === 2 ? 'grid-cols-2' : crops.length === 3 ? 'grid-cols-3' : 'md:grid-cols-5'}`}>
            {crops.map((crop, i) => (
              <Card
                key={crop.crop}
                variant="glass"
                className={`p-4 cursor-pointer transition-all ${
                  activeCrop?.crop === crop.crop ? 'ring-2 ring-forest-500 shadow-lg' : ''
                }`}
                onClick={() => setActiveCrop(crop)}
              >
                <div className="text-center">
                  <span className="text-3xl font-bold text-neutral-200 dark:text-neutral-700">#{i + 1}</span>
                  <h4 className="font-bold text-neutral-900 dark:text-white mt-2 mb-1">{crop.crop}</h4>
                  <div className={`text-2xl font-bold ${getColorForScore(crop.score)}`}>{crop.score}%</div>
                  <div className="flex items-center justify-center gap-0.5 mt-1">{renderStars(crop.stars)}</div>
                </div>
              </Card>
            ))}
          </div>
        </motion.div>
      )}

      {crops.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 text-center py-12"
        >
          <span className="text-6xl block mb-4">🌾</span>
          <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">No crop recommendations</h3>
          <p className="text-neutral-500 dark:text-neutral-400">No crop recommendations were generated for this report.</p>
        </motion.div>
      )}

      {/* Active crop details */}
      {activeCrop && (
        <motion.div
          key={activeCrop.crop}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Card variant="glass" className="p-6">
            <h3 className="text-lg font-bold text-neutral-900 dark:text-white mb-4">
              📋 {activeCrop.crop} — Detailed Breakdown
            </h3>
            <div className="grid md:grid-cols-2 gap-6">
              {/* Parameter Scores */}
              <div>
                <h4 className="font-semibold text-neutral-700 dark:text-neutral-300 mb-3">Parameter Scores</h4>
                <div className="space-y-3">
                  {Object.entries(activeCrop.parameter_scores || {}).map(([key, param]) => (
                    <div key={key}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-neutral-600 dark:text-neutral-400 capitalize">{key}</span>
                        <span className={`font-semibold ${getColorForScore(param.score)}`}>{param.score}%</span>
                      </div>
                      <ProgressBar value={param.score} variant={param.score >= 75 ? 'success' : param.score >= 50 ? 'warning' : 'danger'} size="sm" />
                      <p className="text-xs text-neutral-400 mt-1">
                        Value: {param.value} | Ideal: {param.ideal_range?.[0] ?? '—'}–{param.ideal_range?.[1] ?? '—'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Environment */}
              <div>
                <h4 className="font-semibold text-neutral-700 dark:text-neutral-300 mb-3">Recommended Environment</h4>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(activeCrop.recommended_environment || {}).map(([key, value]) => (
                    <div key={key} className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
                      <p className="text-xs text-neutral-500 dark:text-neutral-400 capitalize mb-1">
                        {key.replace(/_/g, ' ')}
                      </p>
                      <p className="font-semibold text-neutral-900 dark:text-white text-sm">{value}</p>
                    </div>
                  ))}
                </div>

                {/* Summary */}
                <div className="mt-4">
                  <h4 className="font-semibold text-neutral-700 dark:text-neutral-300 mb-2">Summary</h4>
                  {ensureArray<string>(activeCrop.summary?.strengths).length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs font-medium text-green-600 dark:text-green-400 mb-1">Strengths</p>
                      {ensureArray<string>(activeCrop.summary?.strengths).map((s, i) => (
                        <p key={i} className="text-sm text-neutral-600 dark:text-neutral-400">✓ {s}</p>
                      ))}
                    </div>
                  )}
                  {ensureArray<string>(activeCrop.summary?.improvements).length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-amber-600 dark:text-amber-400 mb-1">Improvements</p>
                      {ensureArray<string>(activeCrop.summary?.improvements).map((s, i) => (
                        <p key={i} className="text-sm text-neutral-600 dark:text-neutral-400">⚠ {s}</p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Recommendations */}
      {(ensureString(recommendations.lime_to_apply) || ensureString(recommendations.fertilizer_to_apply)) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="grid md:grid-cols-2 gap-6"
        >
          {ensureString(recommendations.lime_to_apply) && (
            <RecommendationBlock
              title="Lime to Apply"
              icon="🧱"
              text={recommendations.lime_to_apply}
            />
          )}
          {ensureString(recommendations.fertilizer_to_apply) && (
            <RecommendationBlock
              title="Fertilizer to Apply"
              icon="🧪"
              text={recommendations.fertilizer_to_apply}
            />
          )}
          {ensureString(recommendations.cultural_and_management_tips) && (
            <RecommendationBlock
              title="Cultural & Management Tips"
              icon="🌿"
              text={recommendations.cultural_and_management_tips}
            />
          )}
          {ensureString(recommendations.references_and_resources) && (
            <RecommendationBlock
              title="References & Resources"
              icon="📚"
              text={recommendations.references_and_resources}
            />
          )}
        </motion.div>
      )}

      {/* CTA */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="mt-12 text-center"
      >
        <Link to="/analyze">
          <Button size="lg">
            Analyze Another Report
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </Button>
        </Link>
      </motion.div>
    </div>
  )
}
