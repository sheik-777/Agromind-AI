import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface ProgressBarProps {
  value: number
  max?: number
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'gradient'
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  label?: string
  className?: string
  animate?: boolean
}

export default function ProgressBar({
  value,
  max = 100,
  variant = 'gradient',
  size = 'md',
  showLabel = false,
  label,
  className,
  animate = true,
}: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  const sizeStyles = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  }

  const variantStyles = {
    default: 'bg-neutral-400 dark:bg-neutral-600',
    success: 'bg-green-500',
    warning: 'bg-amber-500',
    danger: 'bg-red-500',
    gradient: 'bg-gradient-to-r from-forest-600 via-emerald-500 to-leaf-500',
  }

  return (
    <div className={cn('w-full', className)}>
      {(showLabel || label) && (
        <div className="flex justify-between items-center mb-2">
          {label && <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">{label}</span>}
          {showLabel && (
            <span className="text-sm font-semibold text-forest-600 dark:text-forest-400">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      <div className={cn('w-full rounded-full bg-neutral-100 dark:bg-neutral-800 overflow-hidden', sizeStyles[size])}>
        <motion.div
          className={cn('h-full rounded-full', variantStyles[variant])}
          initial={animate ? { width: 0 } : { width: `${percentage}%` }}
          animate={{ width: `${percentage}%` }}
          transition={animate ? { duration: 1.5, ease: [0.22, 1, 0.36, 1], delay: 0.3 } : { duration: 0 }}
        />
      </div>
    </div>
  )
}