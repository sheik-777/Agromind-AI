import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'

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
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden py-20 lg:py-32">
        {/* Background gradient mesh */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-forest-400/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-400/10 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-leaf-400/5 rounded-full blur-3xl" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="text-center max-w-4xl mx-auto px-4"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-forest-50 dark:bg-forest-950/30 border border-forest-200 dark:border-forest-800 mb-8"
          >
            <span className="w-2 h-2 rounded-full bg-forest-500 animate-pulse" />
            <span className="text-sm font-medium text-forest-700 dark:text-forest-400">
              Powered by Advanced AI
            </span>
          </motion.div>

          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight font-display mb-6">
            <span className="text-neutral-900 dark:text-white">Grow Smarter,</span>
            <br />
            <span className="bg-gradient-to-r from-forest-600 via-emerald-500 to-leaf-500 bg-clip-text text-transparent">
              Harvest Better
            </span>
          </h1>

          <p className="text-lg md:text-xl text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload your soil lab report and get AI-powered analysis, personalized crop recommendations,
            and actionable farming insights in seconds.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/analyze">
              <Button size="lg" className="text-base px-8">
                Analyze Your Soil
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Button>
            </Link>
            <Link to="/crops">
              <Button variant="outline" size="lg" className="text-base px-8">
                Browse Crops
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* How it works */}
      <section className="py-20 lg:py-32">
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
                  Join thousands of farmers making data-driven decisions with AgroMind.
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