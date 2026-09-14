import { lazy, Suspense } from 'react'
import { motion } from 'framer-motion'
import { useReducedMotion } from 'motion/react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import { useFieldHealth } from '@/hooks/useFieldHealth'

const TreeCanvas = lazy(() => import('@/components/3d/TreeCanvas'))

const features = [
  {
    icon: '🔬',
    title: 'Advanced Soil Analysis',
    description: 'Upload your lab report and get instant, comprehensive analysis of 18+ soil parameters with AI-powered insights.',
  },
  {
    icon: '🌾',
    title: 'Smart Crop Matching',
    description: 'Our algorithm cross-references your soil data against a database of hundreds of crops to find the best matches.',
  },
  {
    icon: '📊',
    title: 'Interactive Dashboard',
    description: 'Visualize your soil health with beautiful charts, nutrient breakdowns, and actionable recommendations.',
  },
  {
    icon: '🤖',
    title: 'AI Assistant',
    description: 'Ask questions about your soil, crops, or farming practices and get expert-level answers instantly.',
  },
]

const steps = [
  { number: '01', title: 'Upload Report', description: 'Drag & drop your soil lab report PDF' },
  { number: '02', title: 'AI Analyzes', description: 'Our engine extracts and processes all data' },
  { number: '03', title: 'Get Results', description: 'View detailed analysis and crop matches' },
]

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
}

export default function Landing() {
  const health = useFieldHealth()
  const reduceMotion = useReducedMotion() ?? false

  return (
    <div className="min-h-screen">
      {/* Hero — the tree is the environment, not a widget */}
      <section className="relative overflow-hidden min-h-[660px] lg:min-h-[84vh] flex items-center">
        {/* Full-bleed 3D grove */}
        <div className="absolute inset-0">
          <Suspense fallback={null}>
            <TreeCanvas health={health} reducedMotion={reduceMotion} />
          </Suspense>
        </div>

        {/* Blend washes: readability for copy, seamless melt into the page below */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-[#fafafa] via-[#fafafa]/45 to-transparent dark:from-[#09090b] dark:via-[#09090b]/40 dark:to-transparent" />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#fafafa] via-transparent to-transparent dark:from-[#09090b] dark:via-transparent" />

        {/* Copy floats above the grove — fully pointer-transparent except controls,
            so hover/orbit events reach the canvas everywhere else */}
        <div className="relative w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 pointer-events-none">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="max-w-xl pointer-events-none"
          >
            <p className="text-xs font-semibold tracking-[0.2em] text-forest-600 dark:text-forest-400 mb-5">
              INTELLIGENT AGRICULTURE SYSTEM
            </p>

            <h1 className="text-5xl md:text-6xl font-bold tracking-tight font-display mb-6">
              <span className="text-neutral-900 dark:text-white">Grow with </span>
              <span className="text-forest-700 dark:text-forest-400">intelligence.</span>
            </h1>

            <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-lg mb-8 leading-relaxed">
              AgroMind connects soil intelligence, real-time field sensing, computer vision and
              AI-driven recommendations into one living view of your farm.
            </p>

            <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-8">
              <Link to="/analyze" className="pointer-events-auto">
                <Button size="lg" className="text-base px-8">
                  Analyze My Soil
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </Button>
              </Link>
              <a href="#how-it-works" className="pointer-events-auto">
                <Button variant="outline" size="lg" className="text-base px-8">
                  Explore AgroMind
                </Button>
              </a>
            </div>

            <div
              className="pointer-events-auto flex items-center gap-3 rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white/70 dark:bg-neutral-900/70 backdrop-blur-sm px-4 py-3 max-w-lg"
              title={health.detail}
            >
              <span
                className={cn(
                  'w-2.5 h-2.5 rounded-full flex-shrink-0',
                  health.status === 'warning' ? 'bg-amber-500' : 'bg-forest-500'
                )}
              />
              <div>
                <p className="text-sm font-medium text-neutral-900 dark:text-white">
                  Field status: {health.label}
                </p>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{health.detail}</p>
              </div>
            </div>
          </motion.div>
        </div>

        <p className="pointer-events-none absolute bottom-4 left-1/2 -translate-x-1/2 px-4 text-center text-xs text-neutral-500 dark:text-neutral-400">
          Hover the tree — flowers bloom around your cursor · Drag to look around
        </p>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-20 lg:py-32 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight font-display text-neutral-900 dark:text-white mb-4">
              How It Works
            </h2>
            <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto">
              Three simple steps to transform your farming decisions
            </p>
          </motion.div>

          <motion.div
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid md:grid-cols-3 gap-8"
          >
            {steps.map((step) => (
              <motion.div key={step.number} variants={item}>
                <Card className="text-center h-full" variant="glass">
                  <div className="text-5xl font-bold bg-gradient-to-br from-forest-600 to-emerald-500 bg-clip-text text-transparent mb-4 font-display">
                    {step.number}
                  </div>
                  <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">
                    {step.title}
                  </h3>
                  <p className="text-neutral-600 dark:text-neutral-400">
                    {step.description}
                  </p>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 lg:py-32 bg-neutral-50 dark:bg-neutral-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight font-display text-neutral-900 dark:text-white mb-4">
              Everything You Need
            </h2>
            <p className="text-lg text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto">
              Powerful features to optimize your agricultural decisions
            </p>
          </motion.div>

          <motion.div
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid md:grid-cols-2 gap-8"
          >
            {features.map((feature) => (
              <motion.div key={feature.title} variants={item}>
                <Card className="h-full" hover>
                  <div className="text-4xl mb-4">{feature.icon}</div>
                  <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-neutral-600 dark:text-neutral-400 leading-relaxed">
                    {feature.description}
                  </p>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 lg:py-32">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <Card variant="glass" className="p-12 md:p-16 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-forest-500/5 to-emerald-500/5" />
              <div className="relative">
                <h2 className="text-3xl md:text-4xl font-bold tracking-tight font-display text-neutral-900 dark:text-white mb-4">
                  Ready to Transform Your Farm?
                </h2>
                <p className="text-lg text-neutral-600 dark:text-neutral-400 mb-8 max-w-xl mx-auto">
                  Upload a lab report to see what your soil is really telling you.
                </p>
                <Link to="/analyze">
                  <Button size="lg" className="text-base px-10">
                    Start Free Analysis
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </Button>
                </Link>
              </div>
            </Card>
          </motion.div>
        </div>
      </section>
    </div>
  )
}