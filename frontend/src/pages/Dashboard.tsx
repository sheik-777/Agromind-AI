import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { cn } from '@/lib/utils'
import type { SoilReportResponse } from '@/services/api'
import { useFieldData } from '@/hooks/useFieldData'
import { useFieldHealth } from '@/hooks/useFieldHealth'
import type { InsightSeverity } from '@/services/field'

function timeAgo(iso: string): string {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000))
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 48) return `${hrs}h ago`
  return `${Math.round(hrs / 24)}d ago`
}

function futureIn(iso: string): string {
  const mins = Math.round((new Date(iso).getTime() - Date.now()) / 60000)
  if (mins <= 0) return 'due now'
  if (mins < 60) return `in ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `in ${hrs}h ${mins % 60}m`
  return `in ${Math.floor(hrs / 24)}d ${hrs % 24}h`
}

function DemoBadge() {
  return (
    <span
      className="inline-flex items-center rounded-full bg-amber-100 dark:bg-amber-900/30 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-400"
      title="Demo data — connect your IoT node to go live"
    >
      Demo
    </span>
  )
}

function SectionTitle({ children, demo }: { children: React.ReactNode; demo?: boolean }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <h2 className="text-xl font-bold text-neutral-900 dark:text-white">{children}</h2>
      {demo && <DemoBadge />}
    </div>
  )
}

const severityStyles: Record<InsightSeverity, string> = {
  info: 'border-info/30 bg-info/5',
  warning: 'border-amber-500/30 bg-amber-500/5',
  critical: 'border-danger/30 bg-danger/5',
}

const severityDot: Record<InsightSeverity, string> = {
  info: 'bg-info',
  warning: 'bg-amber-500',
  critical: 'bg-danger',
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [recentReports, setRecentReports] = useState<SoilReportResponse[]>([])
  const { data: field, isLoading: fieldLoading } = useFieldData()
  const health = useFieldHealth()

  useEffect(() => {
    const stored = sessionStorage.getItem('soilReport')
    if (stored) {
      try {
        setRecentReports([JSON.parse(stored)])
      } catch {
        sessionStorage.removeItem('soilReport')
      }
    }
  }, [])

  return (
    <div className="min-h-screen py-8 lg:py-12">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight font-display text-neutral-900 dark:text-white">
          Farm command center
        </h1>
        <p className="text-neutral-500 dark:text-neutral-400 mt-1">
          Field health, live conditions, irrigation and weather — one living view.
        </p>
      </motion.div>

      {/* Honest provenance banner */}
      <div className="mb-8 rounded-2xl border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-800 dark:text-amber-300">
        Showing <strong>demo field data</strong> — sensor, irrigation, weather and insight panels go live
        when your IoT node and backend routes are connected. Soil reports below are your real uploads.
      </div>

      {/* Row 1 — Field health (real) + current conditions (demo) */}
      <div className="grid lg:grid-cols-3 gap-4 mb-8">
        <Card variant="glass" className="p-6 lg:col-span-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400 mb-4">
            Field health
          </p>
          <div className="flex items-center gap-4">
            <span
              className={cn(
                'w-14 h-14 rounded-2xl flex items-center justify-center text-3xl',
                health.status === 'warning' ? 'bg-amber-500/15' : 'bg-forest-500/15'
              )}
              role="img"
              aria-label={health.label}
            >
              {health.status === 'warning' ? '⚠️' : '🌿'}
            </span>
            <div>
              <p className="text-2xl font-bold text-neutral-900 dark:text-white">{health.label}</p>
              <p className="text-sm text-neutral-500 dark:text-neutral-400">{health.detail}</p>
            </div>
          </div>
          {!health.live && (
            <Link to="/analyze" className="block mt-5">
              <Button variant="outline" size="sm" className="w-full">
                Upload a soil report
              </Button>
            </Link>
          )}
        </Card>

        <Card variant="glass" className="p-6 lg:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
              Current conditions
            </p>
            <DemoBadge />
          </div>
          {fieldLoading || !field ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="h-20 rounded-xl bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: 'Soil moisture', value: `${field.sensors.moisturePct}%`, hint: 'Target 35–55%' },
                { label: 'Air temp', value: `${field.sensors.airTempC.toFixed(1)}°C`, hint: `Soil ${field.sensors.soilTempC.toFixed(1)}°C` },
                { label: 'Humidity', value: `${field.sensors.humidityPct}%`, hint: 'In normal band' },
                { label: 'Soil pH', value: field.sensors.ph.toFixed(1), hint: 'Slightly acidic' },
              ].map((c) => (
                <div key={c.label} className="rounded-xl bg-neutral-50 dark:bg-neutral-800/60 px-4 py-3">
                  <p className="text-xl font-bold text-neutral-900 dark:text-white">{c.value}</p>
                  <p className="text-xs font-medium text-neutral-600 dark:text-neutral-300">{c.label}</p>
                  <p className="text-[11px] text-neutral-400 dark:text-neutral-500">{c.hint}</p>
                </div>
              ))}
              <p className="col-span-2 sm:col-span-4 text-[11px] text-neutral-400 dark:text-neutral-500">
                Last sensor signal {timeAgo(field.sensors.recordedAt)} · No rain in the last 24h (
                {field.sensors.rainLast24hMm} mm)
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* Row 2 — Activity + irrigation */}
      <div className="grid lg:grid-cols-2 gap-4 mb-8">
        <div>
          <SectionTitle demo>Field activity</SectionTitle>
          <Card variant="glass" className="p-6">
            {fieldLoading || !field ? (
              <div className="h-32 rounded-xl bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
            ) : (
              <ul className="space-y-4 text-sm">
                <li className="flex items-start gap-3">
                  <span className="w-2 h-2 mt-1.5 rounded-full bg-forest-500 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-neutral-900 dark:text-white">
                      {field.device.deviceId} · Online
                    </p>
                    <p className="text-neutral-500 dark:text-neutral-400">
                      Last signal {timeAgo(field.device.lastSeenAt)} · SIM {field.device.simSignalPct}% ·
                      next report {futureIn(new Date(Date.now() + field.device.nextReportInMin * 60000).toISOString())}
                    </p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="w-2 h-2 mt-1.5 rounded-full bg-info flex-shrink-0" />
                  <div>
                    <p className="font-medium text-neutral-900 dark:text-white">
                      Camera scan · {field.camera.lastFinding}
                    </p>
                    <p className="text-neutral-500 dark:text-neutral-400">
                      Last {timeAgo(field.camera.lastScanAt)} · next {futureIn(field.camera.nextScanAt)} ·
                      {field.camera.scansPerDay} scheduled scans per day
                    </p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="w-2 h-2 mt-1.5 rounded-full bg-amber-500 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-neutral-900 dark:text-white">
                      Irrigation {field.irrigation.state} · {field.irrigation.waterUsageLToday} L today
                    </p>
                    <p className="text-neutral-500 dark:text-neutral-400">
                      {field.irrigation.lastRunAt
                        ? `Last run ${timeAgo(field.irrigation.lastRunAt)}`
                        : 'No runs yet'}
                      {field.irrigation.nextRunAt && ` · next ${futureIn(field.irrigation.nextRunAt)}`}
                    </p>
                  </div>
                </li>
              </ul>
            )}
          </Card>
        </div>

        <div>
          <SectionTitle demo>Irrigation</SectionTitle>
          <Card variant="glass" className="p-6">
            {fieldLoading || !field ? (
              <div className="h-32 rounded-xl bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
            ) : (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">
                    Moisture {field.irrigation.currentMoisturePct}% · band{' '}
                    {field.irrigation.targetMinPct}–{field.irrigation.targetMaxPct}%
                  </p>
                  <Badge variant={field.irrigation.state === 'running' ? 'success' : 'warning'}>
                    {field.irrigation.state}
                  </Badge>
                </div>
                <div className="h-2.5 rounded-full bg-neutral-100 dark:bg-neutral-800 overflow-hidden mb-3">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-forest-600 to-emerald-500"
                    style={{ width: `${Math.min(100, field.irrigation.currentMoisturePct)}%` }}
                  />
                </div>
                <p className="text-sm text-neutral-600 dark:text-neutral-300 leading-relaxed">
                  {field.irrigation.reason}
                </p>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Row 3 — AI insights (explainable) */}
      <div className="mb-8">
        <SectionTitle demo>AI insights</SectionTitle>
        {fieldLoading || !field ? (
          <div className="h-28 rounded-2xl bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {field.insights.map((insight) => (
              <div
                key={insight.id}
                className={cn('rounded-2xl border p-5', severityStyles[insight.severity])}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={cn('w-2 h-2 rounded-full', severityDot[insight.severity])} />
                  <h3 className="font-semibold text-neutral-900 dark:text-white">{insight.title}</h3>
                </div>
                <p className="text-sm text-neutral-600 dark:text-neutral-300 mb-3">{insight.detail}</p>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400 dark:text-neutral-500 mb-1">
                  Why
                </p>
                <ul className="text-sm text-neutral-600 dark:text-neutral-300 space-y-1">
                  {insight.why.map((w) => (
                    <li key={w} className="flex gap-2">
                      <span aria-hidden>·</span>
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Row 4 — Weather */}
      <div className="mb-8">
        <SectionTitle demo>Weather · via Open-Meteo</SectionTitle>
        <Card variant="glass" className="p-6">
          {fieldLoading || !field ? (
            <div className="h-28 rounded-xl bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
          ) : (
            <div>
              <div className="flex flex-wrap items-end gap-x-8 gap-y-2 mb-5">
                <p className="text-4xl font-bold text-neutral-900 dark:text-white">
                  {field.weatherNow.tempC.toFixed(0)}°C
                </p>
                <p className="text-sm text-neutral-500 dark:text-neutral-400 pb-1">
                  {field.weatherNow.condition} · Humidity {field.weatherNow.humidityPct}% · Wind{' '}
                  {field.weatherNow.windKph} kph · Rain {field.weatherNow.rainProbPct}%
                </p>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {field.forecast.map((d, i) => (
                  <div
                    key={d.date}
                    className="rounded-xl bg-neutral-50 dark:bg-neutral-800/60 px-3 py-2.5 text-center"
                  >
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400">
                      {i === 0
                        ? 'Today'
                        : new Date(d.date).toLocaleDateString(undefined, { weekday: 'short' })}
                    </p>
                    <p className="text-sm font-bold text-neutral-900 dark:text-white">
                      {d.tempMaxC}° / {d.tempMinC}°
                    </p>
                    <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
                      {d.condition} · 💧{d.rainProbPct}%
                    </p>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-sm text-neutral-600 dark:text-neutral-300">
                Rain expected mid-week — scheduled irrigation may be reduced. Agricultural read, not
                just a forecast.
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* Row 5 — History */}
      <div className="mb-8">
        <SectionTitle demo>5-day trends</SectionTitle>
        {fieldLoading || !field ? (
          <div className="h-48 rounded-2xl bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            <Card variant="glass" className="p-6">
              <p className="text-sm font-medium text-neutral-700 dark:text-neutral-200 mb-3">
                Soil moisture %
              </p>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={field.history}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                      dataKey="at"
                      tickFormatter={(v: string) =>
                        new Date(v).toLocaleDateString(undefined, { weekday: 'short' })
                      }
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis tick={{ fontSize: 11 }} domain={[20, 45]} />
                    <Tooltip contentStyle={{ borderRadius: 12 }} />
                    <Area
                      type="monotone"
                      dataKey="moisturePct"
                      stroke="#2d752d"
                      fill="#3a9238"
                      fillOpacity={0.25}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card variant="glass" className="p-6">
              <p className="text-sm font-medium text-neutral-700 dark:text-neutral-200 mb-3">
                Temperature °C
              </p>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={field.history}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                      dataKey="at"
                      tickFormatter={(v: string) =>
                        new Date(v).toLocaleDateString(undefined, { weekday: 'short' })
                      }
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis tick={{ fontSize: 11 }} domain={[24, 31]} />
                    <Tooltip contentStyle={{ borderRadius: 12 }} />
                    <Line type="monotone" dataKey="tempC" stroke="#d97706" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* Quick actions (preserved) */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-neutral-900 dark:text-white mb-4">Quick actions</h2>
        <div className="grid sm:grid-cols-3 gap-4">
          {[
            { title: 'New Analysis', description: 'Upload a new soil report', icon: '🔬', href: '/analyze' },
            { title: 'Browse Crops', description: 'Explore crop database', icon: '🌾', href: '/crops' },
            { title: 'AI Assistant', description: 'Ask farming questions', icon: '🤖', href: '/assistant' },
          ].map((action) => (
            <Link key={action.title} to={action.href}>
              <Card
                variant="glass"
                className="p-6 h-full cursor-pointer hover:border-forest-300 dark:hover:border-forest-700 transition-colors"
              >
                <span className="text-3xl block mb-3">{action.icon}</span>
                <h3 className="font-semibold text-neutral-900 dark:text-white mb-1">{action.title}</h3>
                <p className="text-sm text-neutral-500 dark:text-neutral-400">{action.description}</p>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent reports — real uploads (preserved) */}
      <div>
        <h2 className="text-xl font-bold text-neutral-900 dark:text-white mb-4">Recent reports</h2>
        {recentReports.length > 0 ? (
          <div className="space-y-4">
            {recentReports.map((report, i) => {
              const meta = report.parsed_report?.[0]?.metadata || {}
              const crops = report.parsed_report?.[0]?.crop_recommendations || []
              return (
                <Card
                  key={i}
                  variant="glass"
                  className="p-5 cursor-pointer"
                  onClick={() => {
                    sessionStorage.setItem('soilReport', JSON.stringify(report))
                    navigate('/results')
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-forest-500 to-emerald-500 flex items-center justify-center text-2xl text-white shadow-lg shadow-forest-500/20">
                        📄
                      </div>
                      <div>
                        <h4 className="font-semibold text-neutral-900 dark:text-white">
                          {report.filename}
                        </h4>
                        <p className="text-sm text-neutral-500 dark:text-neutral-400">
                          {meta.client || 'Unknown'} • {meta.county || 'N/A'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {crops.length > 0 && (
                        <Badge variant="success">
                          Best: {crops[0].crop} ({crops[0].score}%)
                        </Badge>
                      )}
                      <svg
                        className="w-5 h-5 text-neutral-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        ) : (
          <Card variant="glass" className="p-12 text-center">
            <span className="text-6xl block mb-4">📭</span>
            <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">No reports yet</h3>
            <p className="text-neutral-500 dark:text-neutral-400 mb-6">
              Upload your first soil report to see it here.
            </p>
            <Link to="/analyze">
              <Button>
                Analyze Your Soil
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Button>
            </Link>
          </Card>
        )}
      </div>
    </div>
  )
}
