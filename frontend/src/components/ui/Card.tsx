import { forwardRef, type HTMLAttributes } from 'react'
import { motion, type MotionProps } from 'framer-motion'
import { cn } from '@/lib/utils'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'elevated' | 'outlined'
  hover?: boolean
  animate?: boolean
}

const Card = forwardRef<HTMLDivElement, CardProps & MotionProps>(
  ({ className, variant = 'default', hover = true, animate = true, children, ...props }, ref) => {
    const variants = {
      default: 'bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800',
      glass: 'bg-white/80 dark:bg-neutral-900/80 backdrop-blur-xl border border-neutral-200/50 dark:border-neutral-800/50',
      elevated: 'bg-white dark:bg-neutral-900 border border-neutral-100 dark:border-neutral-800 shadow-xl shadow-black/5 dark:shadow-black/20',
      outlined: 'bg-transparent border-2 border-neutral-200 dark:border-neutral-700',
    }

    const hoverStyles = hover
      ? 'transition-all duration-300 hover:shadow-xl hover:-translate-y-1 hover:border-forest-200 dark:hover:border-forest-800'
      : ''

    const Component = animate ? motion.div : 'div'

    return (
      <Component
        ref={ref}
        initial={animate ? { opacity: 0, y: 20 } : undefined}
        whileInView={animate ? { opacity: 1, y: 0 } : undefined}
        viewport={animate ? { once: true, margin: '-50px' } : undefined}
        transition={animate ? { duration: 0.5, ease: [0.22, 1, 0.36, 1] } : undefined}
        className={cn('rounded-2xl p-6', variants[variant], hoverStyles, className)}
        {...props}
      >
        {children}
      </Component>
    )
  }
)

Card.displayName = 'Card'
export default Card