'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, Send, CheckCircle, AlertCircle, Calendar, Clock, Video } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import GradientButton from '@/components/ui/GradientButton'
import Link from 'next/link'

const DIENSTEN = [
  { value: '', label: 'Kies een dienst...' },
  { value: 'full-stack', label: 'Full-Stack Development' },
  { value: 'ai-ml', label: 'AI / Machine Learning' },
  { value: 'iot', label: 'IoT & Embedded' },
  { value: 'consulting', label: 'IT Consulting' },
]

const CAL_LINK = 'https://cal.com/koen-vorsters'

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
      const res = await fetch('/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data?.detail || data?.message || `HTTP ${res.status}`)
      }
      setStatus('success')
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Iets ging mis.')
      setStatus('error')
    }
  }

  if (status === 'success') {
    return (
      <div className="flex items-center justify-center min-h-[70vh] px-4">
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
          <p className="text-slate-400 mb-6">
            Bedankt voor je bericht. Ik neem zo snel mogelijk contact met je op.
          </p>
          <a
            href={CAL_LINK}
            target="_blank"
            rel="noopener noreferrer"
            data-testid="cal-link-success"
            className="inline-flex items-center gap-2 text-green-400 hover:text-green-300 font-medium transition-colors"
          >
            <Calendar className="w-4 h-4" /> Of plan direct een gesprek →
          </a>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="py-12 sm:py-20 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-10 sm:mb-12"
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
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Heb je een project in gedachten? Stuur een bericht of plan direct een vrijblijvend gesprek in.
          </p>
        </motion.div>

        {/* Two-column layout on large screens */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 lg:gap-8 items-start">
          {/* Contact form — 3/5 width */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="lg:col-span-3"
          >
            <GlassCard className="p-8">
              <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                <Mail className="w-5 h-5 text-green-400" /> Stuur een bericht
              </h2>
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
                      data-testid="field-naam"
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
                      data-testid="field-email"
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
                      data-testid="field-bedrijf"
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
                      data-testid="field-dienst"
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
                    data-testid="field-bericht"
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
                  data-testid="submit-contact"
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

          {/* Cal.com booking — 2/5 width */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="lg:col-span-2 flex flex-col gap-4"
          >
            {/* Booking card */}
            <GlassCard className="p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-xl bg-green-500/20">
                  <Calendar className="w-5 h-5 text-green-400" />
                </div>
                <h2 className="text-lg font-semibold text-white">Plan een gesprek</h2>
              </div>
              <p className="text-slate-400 text-sm mb-6 leading-relaxed">
                Liever direct inplannen? Kies een moment dat jou past voor een gratis
                kennismakingsgesprek van 30 minuten.
              </p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-3 text-slate-300 text-sm">
                  <Clock className="w-4 h-4 text-green-400 shrink-0" />
                  30 minuten — gratis & vrijblijvend
                </li>
                <li className="flex items-center gap-3 text-slate-300 text-sm">
                  <Video className="w-4 h-4 text-green-400 shrink-0" />
                  Google Meet of Teams
                </li>
                <li className="flex items-center gap-3 text-slate-300 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                  Direct bevestiging via e-mail
                </li>
              </ul>
              <a
                href={CAL_LINK}
                target="_blank"
                rel="noopener noreferrer"
                data-testid="cal-booking-btn"
                className="block w-full"
              >
                <GradientButton variant="primary" className="w-full py-4 text-base flex items-center justify-center gap-2">
                  <Calendar className="w-4 h-4" /> Kies een moment →
                </GradientButton>
              </a>
            </GlassCard>

            {/* Direct e-mail */}
            <GlassCard className="p-6">
              <p className="text-slate-400 text-sm mb-3">Liever direct mailen?</p>
              <a
                href="mailto:koen@vorsters.dev"
                className="flex items-center gap-2 text-green-400 hover:text-green-300 font-medium text-sm transition-colors"
                data-testid="direct-email-link"
              >
                <Mail className="w-4 h-4" /> koen@vorsters.dev
              </a>
            </GlassCard>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
