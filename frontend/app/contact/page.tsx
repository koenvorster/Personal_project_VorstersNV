'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, Send, CheckCircle, AlertCircle } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import GradientButton from '@/components/ui/GradientButton'

const DIENSTEN = [
  { value: '', label: 'Kies een dienst...' },
  { value: 'full-stack', label: 'Full-Stack Development' },
  { value: 'ai-ml', label: 'AI / Machine Learning' },
  { value: 'iot', label: 'IoT & Embedded' },
  { value: 'consulting', label: 'IT Consulting' },
]

export default function ContactPage() {
  const [form, setForm] = useState({ naam: '', email: '', bedrijf: '', dienst: '', bericht: '' })
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')
    try {
      const res = await fetch('http://localhost:8081/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data?.message || `HTTP ${res.status}`)
      }
      setStatus('success')
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Iets ging mis.')
      setStatus('error')
    }
  }

  if (status === 'success') {
    return (
      <main className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="text-center max-w-md"
        >
          <div className="flex justify-center mb-6">
            <div className="p-4 rounded-full bg-green-500/20">
              <CheckCircle className="w-12 h-12 text-green-400" />
            </div>
          </div>
          <h2 className="text-3xl font-bold text-white mb-3">Bericht verzonden!</h2>
          <p className="text-slate-400">
            Bedankt voor je bericht. Ik neem zo snel mogelijk contact met je op.
          </p>
        </motion.div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-slate-950 py-20 px-4">
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <div className="flex justify-center mb-4">
            <div className="p-3 rounded-2xl bg-green-500/20">
              <Mail className="w-8 h-8 text-green-400" />
            </div>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-white mb-4">
            Neem{' '}
            <span className="bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">
              contact
            </span>{' '}
            op
          </h1>
          <p className="text-slate-400 text-lg">
            Heb je een project in gedachten? Laat het me weten en ik kom zo snel mogelijk bij je terug.
          </p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard className="p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Naam <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    name="naam"
                    value={form.naam}
                    onChange={handleChange}
                    required
                    placeholder="Jan Janssen"
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    E-mail <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    required
                    placeholder="jan@bedrijf.be"
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Bedrijf <span className="text-slate-500 text-xs">(optioneel)</span>
                  </label>
                  <input
                    type="text"
                    name="bedrijf"
                    value={form.bedrijf}
                    onChange={handleChange}
                    placeholder="Mijn Bedrijf NV"
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Dienst
                  </label>
                  <select
                    name="dienst"
                    value={form.dienst}
                    onChange={handleChange}
                    className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all"
                  >
                    {DIENSTEN.map((d) => (
                      <option key={d.value} value={d.value} className="bg-slate-900">
                        {d.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Bericht <span className="text-red-400">*</span>
                </label>
                <textarea
                  name="bericht"
                  value={form.bericht}
                  onChange={handleChange}
                  required
                  minLength={10}
                  rows={5}
                  placeholder="Vertel me over je project of vraag..."
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all resize-none"
                />
              </div>
              {status === 'error' && (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {errorMsg}
                </div>
              )}
              <GradientButton
                type="submit"
                variant="primary"
                disabled={status === 'loading'}
                className="w-full text-base py-4 flex items-center justify-center gap-2"
              >
                {status === 'loading' ? (
                  <>
                    <span className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" />
                    Verzenden...
                  </>
                ) : (
                  <>
                    Verstuur bericht <Send className="w-4 h-4" />
                  </>
                )}
              </GradientButton>
            </form>
          </GlassCard>
        </motion.div>
      </div>
    </main>
  )
}
