import { cn } from '@/lib/utils'

interface GlassCardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  glow?: boolean
}

export default function GlassCard({ children, className, hover = false, glow = false }: GlassCardProps) {
  return (
    <div
      className={cn(
        'backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl',
        hover && 'hover:bg-white/10 transition-all duration-200 cursor-pointer',
        glow && 'hover:border-green-500/30 hover:shadow-lg hover:shadow-green-500/5 transition-all duration-300',
        className
      )}
    >
      {children}
    </div>
  )
}
