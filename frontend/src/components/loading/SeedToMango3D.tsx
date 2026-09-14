import { useCallback, useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'

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

interface SeedToMango3DProps {
  onComplete?: () => void
  currentStep?: number
}

// Deterministic particles (no Math.random in render) floating at varied depths
const PARTICLES = [
  { x: '18%', y: '30%', z: 40, size: 7, delay: 0, duration: 3.2 },
  { x: '78%', y: '24%', z: 70, size: 5, delay: 0.4, duration: 2.7 },
  { x: '66%', y: '66%', z: 30, size: 8, delay: 0.9, duration: 3.6 },
  { x: '26%', y: '68%', z: 60, size: 5, delay: 0.2, duration: 2.9 },
  { x: '50%', y: '14%', z: 90, size: 4, delay: 1.2, duration: 3.1 },
  { x: '86%', y: '52%', z: 50, size: 6, delay: 0.6, duration: 3.4 },
  { x: '12%', y: '50%', z: 80, size: 4, delay: 1.5, duration: 2.8 },
  { x: '40%', y: '80%', z: 35, size: 6, delay: 1.0, duration: 3.3 },
]

export default function SeedToMango3D({ onComplete, currentStep }: SeedToMango3DProps) {
  const [activeIndex, setActiveIndex] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const reduceMotion = useReducedMotion()

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
  const t = progress / 100

  // Growth phases driven by overall progress (0 → seed, 1 → mango)
  const growth = useMemo(() => {
    const clamp01 = (v: number) => Math.min(1, Math.max(0, v))
    return {
      seed: clamp01(t / 0.18),
      sprout: clamp01((t - 0.15) / 0.3),
      leaves: clamp01((t - 0.4) / 0.3),
      mango: clamp01((t - 0.65) / 0.3),
    }
  }, [t])

  const tiltX = reduceMotion ? 0 : 8 - t * 10
  const tiltY = reduceMotion ? 0 : Math.sin(t * Math.PI * 2) * 10

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {/* 3D stage */}
      <div className="relative w-56 h-56 mb-10" style={{ perspective: 1200 }}>
        {/* Ambient glow + shadow */}
        <motion.div
          className="absolute inset-0 rounded-full bg-gradient-to-br from-forest-100 via-emerald-100 to-leaf-100 dark:from-forest-950/40 dark:via-emerald-950/30 dark:to-leaf-950/20"
          animate={reduceMotion ? {} : { scale: [1, 1.08, 1], opacity: [0.55, 0.85, 0.55] }}
          transition={{ duration: 3.2, repeat: Infinity, ease: 'easeInOut' }}
        />
        <div className="absolute left-1/2 top-[86%] h-5 w-32 -translate-x-1/2 rounded-[100%] bg-forest-900/15 blur-md dark:bg-black/40" />

        {/* Floating depth particles */}
        {!reduceMotion &&
          PARTICLES.map((p, i) => (
            <motion.span
              key={i}
              className="absolute rounded-full bg-forest-300/80 dark:bg-forest-600/80"
              style={{
                left: p.x,
                top: p.y,
                width: p.size,
                height: p.size,
                transform: `translateZ(${p.z}px)`,
              }}
              animate={{ y: [0, -18, 0], opacity: [0.25, 0.85, 0.25], scale: [0.6, 1, 0.6] }}
              transition={{ duration: p.duration, repeat: Infinity, delay: p.delay, ease: 'easeInOut' }}
            />
          ))}

        {/* Tilting 3D plant */}
        <motion.div
          className="absolute inset-0"
          style={{ transformStyle: 'preserve-3d' }}
          initial={false}
          animate={{ rotateX: tiltX, rotateY: tiltY }}
          transition={reduceMotion ? { duration: 0 } : { type: 'spring', stiffness: 60, damping: 14 }}
        >
          <svg viewBox="0 0 200 200" className="h-full w-full" role="img" aria-label={stages[activeIndex].label}>
            <defs>
              <linearGradient id="m3d-soil" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8a6b4f" />
                <stop offset="100%" stopColor="#5d4632" />
              </linearGradient>
              <linearGradient id="m3d-stem" x1="0" y1="1" x2="0" y2="0">
                <stop offset="0%" stopColor="#2f7a3d" />
                <stop offset="100%" stopColor="#57c06a" />
              </linearGradient>
              <linearGradient id="m3d-leaf" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#34d399" />
                <stop offset="100%" stopColor="#15803d" />
              </linearGradient>
              <radialGradient id="m3d-mango" cx="0.35" cy="0.3" r="0.9">
                <stop offset="0%" stopColor="#ffe9a8" />
                <stop offset="45%" stopColor="#fbbf24" />
                <stop offset="100%" stopColor="#ea580c" />
              </radialGradient>
            </defs>

            {/* Soil mound */}
            <ellipse cx="100" cy="162" rx="58" ry="13" fill="url(#m3d-soil)" opacity="0.95" />
            <ellipse cx="100" cy="158" rx="44" ry="8" fill="#a07f5c" opacity="0.55" />

            {/* Seed — sinks as sprout takes over */}
            <motion.ellipse
              cx="100"
              cy="150"
              rx="11"
              ry="8"
              fill="#6b4a2f"
              initial={false}
              animate={{
                opacity: 1 - growth.sprout * 0.85,
                scale: 1 - growth.sprout * 0.45,
                y: growth.sprout * 6,
              }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            />

            {/* Stem draws upward */}
            <motion.path
              d="M100 156 C 99 132, 101 108, 100 84"
              fill="none"
              stroke="url(#m3d-stem)"
              strokeWidth="6"
              strokeLinecap="round"
              initial={false}
              animate={{ pathLength: growth.sprout, opacity: growth.sprout > 0.02 ? 1 : 0 }}
              transition={{ duration: 0.7, ease: 'easeOut' }}
            />

            {/* Leaves unfurl */}
            <motion.g
              initial={false}
              animate={{
                opacity: growth.leaves > 0.05 ? 1 : 0,
                scale: 0.3 + growth.leaves * 0.7,
                rotate: -8 + growth.leaves * 8,
              }}
              style={{ originX: '100px', originY: '118px' }}
              transition={{ type: 'spring', stiffness: 120, damping: 13 }}
            >
              <path d="M100 118 C 78 112, 62 100, 56 82 C 76 84, 94 96, 100 118 Z" fill="url(#m3d-leaf)" />
              <path d="M100 118 C 122 112, 138 100, 144 82 C 124 84, 106 96, 100 118 Z" fill="url(#m3d-leaf)" opacity="0.9" />
            </motion.g>

            {/* Mango forms + slow 3D sway */}
            <motion.g
              initial={false}
              animate={{
                opacity: growth.mango > 0.03 ? 1 : 0,
                scale: 0.2 + growth.mango * 0.8,
                rotateY: reduceMotion ? 0 : [0, 14, -14, 0],
              }}
              style={{ originX: '100px', originY: '62px' }}
              transition={
                reduceMotion
                  ? { duration: 0.4 }
                  : {
                      scale: { type: 'spring', stiffness: 110, damping: 11 },
                      rotateY: { duration: 5, repeat: Infinity, ease: 'easeInOut' },
                    }
              }
            >
              <ellipse cx="100" cy="60" rx="21" ry="25" fill="url(#m3d-mango)" />
              <ellipse cx="93" cy="51" rx="6" ry="8" fill="#fff7d6" opacity="0.75" />
              <path d="M100 36 C 100 30, 104 26, 110 24" stroke="#2f7a3d" strokeWidth="4" fill="none" strokeLinecap="round" />
              <path d="M110 24 C 118 20, 126 22, 130 28 C 122 32, 114 30, 110 24 Z" fill="url(#m3d-leaf)" />
            </motion.g>
          </svg>
        </motion.div>

        {/* Stage emoji chip with depth pop */}
        <div className="absolute -bottom-2 left-1/2 -translate-x-1/2" style={{ transform: 'translateZ(90px)' }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={activeIndex}
              className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/90 text-3xl shadow-xl shadow-forest-900/15 ring-1 ring-forest-900/10 backdrop-blur dark:bg-neutral-900/90"
              initial={reduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.4, rotateY: -90 }}
              animate={reduceMotion ? { opacity: 1 } : { opacity: 1, scale: 1, rotateY: 0 }}
              exit={reduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.5, rotateY: 90 }}
              transition={{ type: 'spring', stiffness: 260, damping: 20 }}
            >
              <span role="img" aria-label={stages[activeIndex].label}>
                {stages[activeIndex].emoji}
              </span>
            </motion.div>
          </AnimatePresence>
        </div>
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
            className="h-full bg-gradient-to-r from-forest-600 via-emerald-500 to-amber-400 rounded-full"
            initial={false}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
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
              i <= activeIndex ? 'bg-forest-500' : 'bg-neutral-200 dark:bg-neutral-700'
            }`}
            animate={i === activeIndex && !reduceMotion ? { scale: [1, 1.35, 1] } : {}}
            transition={{ duration: 0.6, repeat: Infinity }}
          />
        ))}
      </div>
    </div>
  )
}
