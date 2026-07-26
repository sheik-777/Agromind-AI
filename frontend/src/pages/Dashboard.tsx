import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import type { SoilReportResponse } from '@/services/api'

export default function Dashboard() {
  const navigate = useNavigate()
  const [recentReports, setRecentReports] = useState<SoilReportResponse[]>([])

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
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight font-display text-neutral-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-neutral-500 dark:text-neutral-400 mt-1">
          Welcome to your AgroMind command center.
        </p>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Reports Analyzed', value: recentReports.length.toString(), icon: '📊', color: 'from-forest-500 to-emerald-500' },
          { label: 'Crops Recommended', value: recentReports.length > 0 ? recentReports.reduce((sum, r) => sum + (r.parsed_report?.[0]?.crop_recommendations?.length || 0), 0).toString() : '0', icon: '🌾', color: 'from-emerald-500 to-leaf-500' },
          { label: 'Parameters Tracked', value: recentReports.length > 0 ? recentReports.reduce((sum, r) => sum + (r.parsed_report?.[0]?.laboratory_analysis?.samples?.[0]?.parameters?.length || 0), 0).toString() : '0', icon: '🧪', color: 'from-leaf-500 to-lime-500' },
          { label: 'AI Insights', value: recentReports.length > 0 ? 'Active' : 'None', icon: '🤖', color: 'from-forest-600 to-forest-400' },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Card variant="glass" className="p-5">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center text-2xl shadow-lg`}>
                  {stat.icon}
                </div>
                <div>
                  <p className="text-2xl font-bold text-neutral-900 dark:text-white">{stat.value}</p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">{stat.label}</p>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-8"
      >
        <h2 className="text-xl font-bold text-neutral-900 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid sm:grid-cols-3 gap-4">
          {[
            { title: 'New Analysis', description: 'Upload a new soil report', icon: '🔬', href: '/analyze' },
            { title: 'Browse Crops', description: 'Explore crop database', icon: '🌾', href: '/crops' },
            { title: 'AI Assistant', description: 'Ask farming questions', icon: '🤖', href: '/assistant' },
          ].map((action) => (
            <Link key={action.title} to={action.href}>
              <Card variant="glass" className="p-6 h-full cursor-pointer hover:border-forest-300 dark:hover:border-forest-700 transition-colors">
                <span className="text-3xl block mb-3">{action.icon}</span>
                <h3 className="font-semibold text-neutral-900 dark:text-white mb-1">{action.title}</h3>
                <p className="text-sm text-neutral-500 dark:text-neutral-400">{action.description}</p>
              </Card>
            </Link>
          ))}
        </div>
      </motion.div>

      {/* Recent Reports */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <h2 className="text-xl font-bold text-neutral-900 dark:text-white mb-4">Recent Reports</h2>
        {recentReports.length > 0 ? (
          <div className="space-y-4">
            {recentReports.map((report, i) => {
              const meta = report.parsed_report?.[0]?.metadata || {}
              const crops = report.parsed_report?.[0]?.crop_recommendations || []
              return (
                <Card key={i} variant="glass" className="p-5 cursor-pointer" onClick={() => {
                  sessionStorage.setItem('soilReport', JSON.stringify(report))
                  navigate('/results')
                }}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-forest-500 to-emerald-500 flex items-center justify-center text-2xl text-white shadow-lg shadow-forest-500/20">
                        📄
                      </div>
                      <div>
                        <h4 className="font-semibold text-neutral-900 dark:text-white">{report.filename}</h4>
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
                      <svg className="w-5 h-5 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
      </motion.div>
    </div>
  )
}