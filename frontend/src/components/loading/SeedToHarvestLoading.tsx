import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface LoadingStage {
  emoji: string
  label: string
  duration: number
}

const stages: LoadingStage[] = [
  { emoji: '🌱', label: 'Uploading report...', duration: 2000 },
  { emoji: '💧', label: 'Converting PDF...', duration: 2500 },
  { emoji: '🌿', label: 'Reading report...', duration: 3000 },
  { emoji: '🍃', label: 'Extracting soil parameters...', duration: 3500 },
  { emoji: '🌳', label: 'Analysing soil...', duration: 2500 },
  { emoji: '🌸', label: 'Comparing crop database...', duration: 3000 },
  { emoji: '🥭', label: 'Running recommendation engine...', duration: 2500 },
  { emoji: '✨', label: 'Preparing dashboard...', duration: 2000 },
  { emoji: '👨‍🌾', label: 'Farmer arrives...', duration: 1500 },
  { emoji: '🌾', label: 'Farmer harvests mango...', duration: 1500 },
  { emoji: '😊', label: 'Farmer smiles...', duration: 1000 },
]

interface SeedToHarvestLoadingProps {
  onComplete?: () => void
  currentStep?: number
}

export default function SeedToHarvestLoading({ onComplete, currentStep }: SeedToHarvestLoadingProps) {
  const [activeIndex, setActiveIndex] = useState(0)
  const [isComplete, setIsComplete] = useState(false)

  const advance = useCallback(() => {
    setActiveIndex((prev) => {
      if (prev < stages.length - 1) return prev + 1
      setIsComplete(true)
      onComplete?.()
      return prev
    })
  }, [onComplete])

  useEffect(() => {
    if (isComplete || currentStep !== undefined) return
    const timer = setTimeout(advance, stages[activeIndex].duration)
    return () => clearTimeout(timer)
  }, [activeIndex, advance, isComplete, currentStep])

  useEffect(() => {
    if (currentStep !== undefined) {
      setActiveIndex(Math.min(currentStep, stages.length - 1))
      if (currentStep >= stages.length) {
        setIsComplete(true)
        onComplete?.()
      }
    }
  }, [currentStep, onComplete])

  const progress = ((activeIndex + 1) / stages.length) * 100

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {/* Animation area */}
      <div className="relative w-48 h-48 mb-12">
        {/* Animated background circle */}
        <motion.div
          className="absolute inset-0 rounded-full bg-gradient-to-br from-forest-100 to-emerald-100 dark:from-forest-950/30 dark:to-emerald-950/30"
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.5, 0.8, 0.5],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />

        {/* Floating particles */}
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 rounded-full bg-forest-300 dark:bg-forest-700"
            style={{
              left: `${20 + Math.random() * 60}%`,
              top: `${20 + Math.random() * 60}%`,
            }}
            animate={{
              y: [0, -20, 0],
              opacity: [0.3, 0.8, 0.3],
              scale: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 2 + Math.random() * 2,
              repeat: Infinity,
              delay: i * 0.3,
              ease: 'easeInOut',
            }}
          />
        ))}

        {/* Main emoji */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeIndex}
            className="absolute inset-0 flex items-center justify-center"
            initial={{ scale: 0, rotate: -180, opacity: 0 }}
            animate={{ scale: 1, rotate: 0, opacity: 1 }}
            exit={{ scale: 0.5, rotate: 180, opacity: 0 }}
            transition={{
              type: 'spring',
              stiffness: 200,
              damping: 15,
              duration: 0.6,
            }}
          >
            <span className="text-8xl select-none" role="img" aria-label={stages[activeIndex].label}>
              {stages[activeIndex].emoji}
            </span>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Progress bar */}
      <div className="w-full max-w-md mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
            Step {activeIndex + 1} of {stages.length}
          </span>
          <span className="text-xs font-semibold text-forest-600 dark:text-forest-400">
            {Math.round(progress)}%
          </span>
        </div>
        <div className="h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-forest-600 via-emerald-500 to-leaf-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          />
        </div>
      </div>

      {/* Status message */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeIndex}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
          className="text-center"
        >
          <p className="text-lg font-medium text-neutral-700 dark:text-neutral-300">
            {stages[activeIndex].label}
          </p>
        </motion.div>
      </AnimatePresence>

      {/* Stage dots */}
      <div className="flex items-center gap-2 mt-8">
        {stages.map((_, i) => (
          <motion.div
            key={i}
            className={`w-2 h-2 rounded-full transition-colors duration-300 ${
              i <= activeIndex
                ? 'bg-forest-500'
                : 'bg-neutral-200 dark:bg-neutral-700'
            }`}
            animate={i === activeIndex ? { scale: [1, 1.3, 1] } : {}}
            transition={{ duration: 0.5, repeat: Infinity }}
          />
        ))}
      </div>
    </div>
  )
}