import { cn } from '@/lib/utils'

interface BadgeProps {
  role?: 'admin' | 'viewer' | 'tester' | string
  children: React.ReactNode
  className?: string
}

export default function Badge({ role, children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold',
        role === 'admin' && 'bg-violet-500/20 text-violet-300 border border-violet-500/30',
        role === 'viewer' && 'bg-blue-500/20 text-blue-300 border border-blue-500/30',
        role === 'tester' && 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
        !role && 'bg-slate-500/20 text-slate-300 border border-slate-500/30',
        className
      )}
    >
      {children}
    </span>
  )
}
