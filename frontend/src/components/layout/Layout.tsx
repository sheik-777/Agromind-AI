import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'
import Header from './Header'
import Footer from './Footer'

interface LayoutProps {
  children: ReactNode
  className?: string
  showHeader?: boolean
  showFooter?: boolean
  fullScreen?: boolean
}

export default function Layout({
  children,
  className,
  showHeader = true,
  showFooter = true,
  fullScreen = false,
}: LayoutProps) {
  return (
    <div className={cn('min-h-screen flex flex-col', className)}>
      {showHeader && <Header />}
      <main className={cn(
        'flex-1',
        showHeader && 'pt-16 lg:pt-20',
        !fullScreen && 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full'
      )}>
        {children}
      </main>
      {showFooter && <Footer />}
    </div>
  )
}