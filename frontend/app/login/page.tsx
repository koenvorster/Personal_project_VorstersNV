'use client'

import { signIn, useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { LogIn, Shield } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import GradientButton from '@/components/ui/GradientButton'

export default function LoginPage() {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (session) router.push('/dashboard')
  }, [session, router])

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center px-4">
      {/* Background orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/3 w-80 h-80 bg-blue-600/15 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/3 w-72 h-72 bg-violet-600/15 rounded-full blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="text-center mb-8">
          <span className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-violet-500 bg-clip-text text-transparent">
            Koen Vorsters
          </span>
          <p className="text-slate-400 text-sm mt-2">Admin paneel</p>
        </div>

        <GlassCard className="p-8 flex flex-col items-center gap-6">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 border border-white/10 flex items-center justify-center">
            <Shield className="w-8 h-8 text-blue-400" />
          </div>

          <div className="text-center">
            <h2 className="text-white font-semibold text-lg">Beveiligde aanmelding</h2>
            <p className="text-slate-400 text-sm mt-1">
              Aanmelden via Keycloak SSO
            </p>
          </div>

          <GradientButton
            variant="primary"
            onClick={() => signIn('keycloak', { callbackUrl: '/dashboard' })}
            className="w-full py-3.5 text-base flex items-center justify-center gap-3"
          >
            <LogIn className="w-4 h-4" />
            Aanmelden met Keycloak
          </GradientButton>

          <p className="text-xs text-slate-500 text-center">
            U wordt doorgestuurd naar de beveiligde aanmeldpagina
          </p>
        </GlassCard>
      </motion.div>
    </div>
  )
}

