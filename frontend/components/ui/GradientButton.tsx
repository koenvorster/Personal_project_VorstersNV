import { cn } from '@/lib/utils'

interface GradientButtonProps {
  children: React.ReactNode
  onClick?: () => void
  className?: string
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  variant?: 'primary' | 'outline'
  'data-testid'?: string
}

export default function GradientButton({
  children,
  onClick,
  className,
  type = 'button',
  disabled = false,
  variant = 'primary',
  'data-testid': dataTestId,
}: GradientButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      data-testid={dataTestId}
      className={cn(
        'px-6 py-3 rounded-xl font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed',
        variant === 'primary' &&
          'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:shadow-lg hover:shadow-green-500/25 hover:scale-105',
        variant === 'outline' &&
          'border border-white/20 text-white hover:bg-white/10 hover:border-white/40',
        className
      )}
    >
      {children}
    </button>
  )
}
