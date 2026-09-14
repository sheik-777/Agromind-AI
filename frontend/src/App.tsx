import { lazy, Suspense } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import Layout from '@/components/layout/Layout'

const Landing = lazy(() => import('@/pages/Landing'))
const AnalyzeSoil = lazy(() => import('@/pages/AnalyzeSoil'))
const Results = lazy(() => import('@/pages/Results'))
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Login = lazy(() => import('@/pages/Login'))
const BrowseCrops = lazy(() => import('@/pages/BrowseCrops'))
const AskAgroMind = lazy(() => import('@/pages/AskAgroMind'))

function NotFound() {
  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <span className="text-8xl block mb-6">🌾</span>
        <h1 className="text-6xl font-bold font-display text-neutral-900 dark:text-white mb-4">404</h1>
        <p className="text-lg text-neutral-500 dark:text-neutral-400 mb-8">This page doesn't exist in our fields.</p>
        <a href="/" className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-forest-700 to-forest-600 text-white font-medium shadow-lg shadow-forest-900/20 hover:shadow-xl transition-shadow">
          Back to Home
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </a>
      </motion.div>
    </div>
  )
}

function PageLoader() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center gap-4"
      >
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-forest-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-forest-600/20">
          <span className="text-white text-2xl animate-pulse">🌱</span>
        </div>
        <div className="flex gap-1">
          <span className="w-2 h-2 bg-forest-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 bg-leaf-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </motion.div>
    </div>
  )
}

export default function App() {
  const location = useLocation()
  const reduceMotion = useReducedMotion()

  return (
    <Layout>
      <AnimatePresence mode="wait">
        <Suspense fallback={<PageLoader />}>
          <motion.main
            key={location.pathname}
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 26, scale: 0.99 }}
            animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 }}
            exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -16, scale: 0.995 }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
            style={{ transformPerspective: 1200 }}
          >
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<Landing />} />
            <Route path="/analyze" element={<AnalyzeSoil />} />
            <Route path="/results" element={<Results />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/login" element={<Login />} />
            <Route path="/crops" element={<BrowseCrops />} />
            <Route path="/assistant" element={<AskAgroMind />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
          </motion.main>
        </Suspense>
      </AnimatePresence>
    </Layout>
  )
}