'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useCartStore } from '@/lib/cartStore'

const VERZENDKOSTEN = 4.95
const BTW = 0.21

function formatPrijs(prijs: number) {
  return new Intl.NumberFormat('nl-BE', { style: 'currency', currency: 'EUR' }).format(prijs)
}

interface FormData {
  naam: string
  email: string
  telefoon: string
  straat: string
  postcode: string
  stad: string
  betaalmethode: 'ideal' | 'creditcard' | 'bancontact' | 'paypal'
}

const defaultForm: FormData = {
  naam: '',
  email: '',
  telefoon: '',
  straat: '',
  postcode: '',
  stad: '',
  betaalmethode: 'ideal',
}

function validate(form: FormData): Partial<Record<keyof FormData, string>> {
  const errors: Partial<Record<keyof FormData, string>> = {}
  if (!form.naam.trim()) errors.naam = 'Naam is verplicht'
  if (!form.email.trim()) errors.email = 'E-mail is verplicht'
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errors.email = 'Ongeldig e-mailadres'
  if (!form.straat.trim()) errors.straat = 'Straat is verplicht'
  if (!form.postcode.trim()) errors.postcode = 'Postcode is verplicht'
  if (!form.stad.trim()) errors.stad = 'Stad is verplicht'
  return errors
}

export default function AfrekenPage() {
  const router = useRouter()
  const { items, totaal, clear } = useCartStore()
  const subtotaal = totaal()
  const verzendkosten = subtotaal >= 50 ? 0 : VERZENDKOSTEN
  const eindtotaal = subtotaal + verzendkosten

  const [form, setForm] = useState<FormData>(defaultForm)
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({})
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    setErrors((prev) => ({ ...prev, [name]: undefined }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const errs = validate(form)
    if (Object.keys(errs).length > 0) {
      setErrors(errs)
      return
    }
    if (items.length === 0) {
      setApiError('Uw winkelwagen is leeg.')
      return
    }

    setLoading(true)
    setApiError('')

    try {
      const res = await fetch('http://localhost:8000/api/bestellingen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: items.map((i) => ({ product_id: i.product_id, aantal: i.aantal })),
          klant_naam: form.naam,
          klant_email: form.email,
          betaalmethode: form.betaalmethode,
        }),
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || 'Bestelling mislukt')
      }

      const data: { order_id: number; bedrag: number; betaal_url: string; status: string } = await res.json()
      clear()

      if (data.betaal_url) {
        window.location.href = data.betaal_url
      } else {
        router.push('/')
      }
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Er is iets misgegaan. Probeer opnieuw.')
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    'w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-purple-500/50 text-sm transition-colors'
  const labelClass = 'block text-white/70 text-xs font-medium mb-1.5'
  const errorClass = 'text-red-400 text-xs mt-1'

  return (
    <div className="min-h-screen px-4 sm:px-6 py-8 sm:py-12">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl sm:text-3xl font-extrabold mb-8">
          <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            Afrekenen
          </span>
        </h1>

        <form onSubmit={handleSubmit} noValidate>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
            {/* Left: form (60%) */}
            <div className="lg:col-span-3 space-y-5">
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6">
                <h2 className="text-white font-semibold mb-5">Contactgegevens</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className={labelClass}>Volledige naam *</label>
                    <input name="naam" value={form.naam} onChange={handleChange} placeholder="Jan Janssen" className={inputClass} />
                    {errors.naam && <p className={errorClass}>{errors.naam}</p>}
                  </div>
                  <div>
                    <label className={labelClass}>E-mailadres *</label>
                    <input name="email" type="email" value={form.email} onChange={handleChange} placeholder="jan@voorbeeld.nl" className={inputClass} />
                    {errors.email && <p className={errorClass}>{errors.email}</p>}
                  </div>
                  <div>
                    <label className={labelClass}>Telefoon</label>
                    <input name="telefoon" type="tel" value={form.telefoon} onChange={handleChange} placeholder="+32 470 00 00 00" className={inputClass} />
                  </div>
                </div>
              </div>

              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6">
                <h2 className="text-white font-semibold mb-5">Leveringsadres</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className={labelClass}>Straat + huisnummer *</label>
                    <input name="straat" value={form.straat} onChange={handleChange} placeholder="Hoofdstraat 1" className={inputClass} />
                    {errors.straat && <p className={errorClass}>{errors.straat}</p>}
                  </div>
                  <div>
                    <label className={labelClass}>Postcode *</label>
                    <input name="postcode" value={form.postcode} onChange={handleChange} placeholder="2000" className={inputClass} />
                    {errors.postcode && <p className={errorClass}>{errors.postcode}</p>}
                  </div>
                  <div>
                    <label className={labelClass}>Stad *</label>
                    <input name="stad" value={form.stad} onChange={handleChange} placeholder="Antwerpen" className={inputClass} />
                    {errors.stad && <p className={errorClass}>{errors.stad}</p>}
                  </div>
                </div>
              </div>

              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6">
                <h2 className="text-white font-semibold mb-5">Betaalmethode</h2>
                <select
                  name="betaalmethode"
                  value={form.betaalmethode}
                  onChange={handleChange}
                  className={inputClass}
                >
                  <option value="ideal">iDEAL</option>
                  <option value="bancontact">Bancontact</option>
                  <option value="creditcard">Creditcard</option>
                  <option value="paypal">PayPal</option>
                </select>
              </div>
            </div>

            {/* Right: order summary (40%) */}
            <div className="lg:col-span-2">
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 sticky top-24">
                <h2 className="text-white font-bold text-lg mb-5">Uw bestelling</h2>

                <div className="space-y-2 mb-5 max-h-60 overflow-y-auto">
                  {items.map((item) => (
                    <div key={item.product_id} className="flex justify-between text-sm">
                      <span className="text-white/70 truncate pr-2">
                        {item.naam} <span className="text-white/40">×{item.aantal}</span>
                      </span>
                      <span className="text-white flex-shrink-0">{formatPrijs(item.prijs * item.aantal)}</span>
                    </div>
                  ))}
                </div>

                <div className="border-t border-white/10 pt-4 space-y-2 text-sm">
                  <div className="flex justify-between text-white/60">
                    <span>Subtotaal</span>
                    <span>{formatPrijs(subtotaal)}</span>
                  </div>
                  <div className="flex justify-between text-white/60">
                    <span>Verzendkosten</span>
                    <span>{verzendkosten === 0 ? 'Gratis' : formatPrijs(verzendkosten)}</span>
                  </div>
                  <div className="flex justify-between font-bold text-white text-base pt-2 border-t border-white/10">
                    <span>Totaal</span>
                    <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                      {formatPrijs(eindtotaal)}
                    </span>
                  </div>
                </div>

                {apiError && (
                  <p className="text-red-400 text-xs mt-4 p-3 bg-red-400/10 rounded-xl border border-red-400/20">
                    {apiError}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={loading || items.length === 0}
                  className="mt-5 w-full flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-xl font-medium transition-all"
                >
                  {loading ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Verwerken…
                    </>
                  ) : (
                    'Betalen →'
                  )}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
