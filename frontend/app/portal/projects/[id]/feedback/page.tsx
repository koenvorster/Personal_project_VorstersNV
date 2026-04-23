"use client"

/**
 * Interactieve feedbackpagina voor klanten – VorstersNV Portal
 *
 * Sterrenrating (1–5) per sectie: kwaliteit, duidelijkheid, bruikbaarheid,
 * volledigheid, aanbevelingen. Vrij tekstveld voor opmerkingen.
 * Verzend via POST /api/portal/projects/{id}/feedback.
 */

import { useParams, useSearchParams } from "next/navigation"
import { useState } from "react"

// ── TypeScript types ──────────────────────────────────────────────────────────

type FeedbackSectie =
  | "kwaliteit"
  | "duidelijkheid"
  | "bruikbaarheid"
  | "volledigheid"
  | "aanbevelingen"

interface FeedbackFormData {
  agent_name: string
  prompt_version: string
  ratings: Record<FeedbackSectie, number>
  opmerking?: string
  beoordelaar: "klant"
}

// ── Constanten ────────────────────────────────────────────────────────────────

const SECTIES: { id: FeedbackSectie; label: string; beschrijving: string }[] = [
  {
    id: "kwaliteit",
    label: "Kwaliteit",
    beschrijving: "Is de output van hoge kwaliteit?",
  },
  {
    id: "duidelijkheid",
    label: "Duidelijkheid",
    beschrijving: "Is het antwoord helder en begrijpelijk?",
  },
  {
    id: "bruikbaarheid",
    label: "Bruikbaarheid",
    beschrijving: "Kunt u direct met dit resultaat aan de slag?",
  },
  {
    id: "volledigheid",
    label: "Volledigheid",
    beschrijving: "Wordt uw vraag volledig beantwoord?",
  },
  {
    id: "aanbevelingen",
    label: "Aanbevelingen",
    beschrijving: "Zijn de aanbevelingen concreet en relevant?",
  },
]

const DEFAULT_RATINGS: Record<FeedbackSectie, number> = {
  kwaliteit: 0,
  duidelijkheid: 0,
  bruikbaarheid: 0,
  volledigheid: 0,
  aanbevelingen: 0,
}

// ── StarRating component ──────────────────────────────────────────────────────

interface StarRatingProps {
  sectie: FeedbackSectie
  waarde: number
  hover: number
  onHover: (n: number) => void
  onLeave: () => void
  onKlik: (n: number) => void
  uitgeschakeld: boolean
}

function StarRating({
  sectie,
  waarde,
  hover,
  onHover,
  onLeave,
  onKlik,
  uitgeschakeld,
}: StarRatingProps) {
  return (
    <div className="flex gap-1" onMouseLeave={onLeave}>
      {[1, 2, 3, 4, 5].map((n) => {
        const actief = n <= (hover || waarde)
        return (
          <button
            key={n}
            type="button"
            data-testid={`star-${sectie}-${n}`}
            aria-label={`${n} ster${n !== 1 ? "ren" : ""} voor ${sectie}`}
            disabled={uitgeschakeld}
            onMouseEnter={() => onHover(n)}
            onClick={() => onKlik(n)}
            className={[
              "text-2xl transition-colors duration-100 focus:outline-none",
              "focus-visible:ring-2 focus-visible:ring-amber-400 rounded",
              uitgeschakeld
                ? "cursor-not-allowed opacity-50"
                : "cursor-pointer hover:scale-110",
              actief ? "text-amber-400" : "text-gray-300",
            ].join(" ")}
          >
            ★
          </button>
        )
      })}
    </div>
  )
}

// ── Hoofd pagina ──────────────────────────────────────────────────────────────

export default function FeedbackPage() {
  const params = useParams<{ id: string }>()
  const searchParams = useSearchParams()

  const projectId = params.id
  const agentName =
    searchParams.get("agent") ?? "klantenservice_agent_v2"
  const promptVersion = searchParams.get("versie") ?? "1.0"

  // ── State ──────────────────────────────────────────────────────────────────
  const [ratings, setRatings] =
    useState<Record<FeedbackSectie, number>>(DEFAULT_RATINGS)
  const [hoverState, setHoverState] =
    useState<Record<FeedbackSectie, number>>(DEFAULT_RATINGS)
  const [opmerking, setOpmerking] = useState("")
  const [bezig, setBezig] = useState(false)
  const [succes, setSucces] = useState(false)
  const [fout, setFout] = useState<string | null>(null)

  // ── Handlers ───────────────────────────────────────────────────────────────

  function stelRatingIn(sectie: FeedbackSectie, score: number) {
    setRatings((prev) => ({ ...prev, [sectie]: score }))
  }

  function stelHoverIn(sectie: FeedbackSectie, score: number) {
    setHoverState((prev) => ({ ...prev, [sectie]: score }))
  }

  function resetHover(sectie: FeedbackSectie) {
    setHoverState((prev) => ({ ...prev, [sectie]: 0 }))
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setFout(null)

    // Guard: alle secties moeten beoordeeld zijn
    const onbeoordeeld = SECTIES.filter((s) => ratings[s.id] === 0)
    if (onbeoordeeld.length > 0) {
      setFout(
        `Geef een beoordeling voor: ${onbeoordeeld.map((s) => s.label).join(", ")}`
      )
      return
    }

    const payload: FeedbackFormData = {
      agent_name: agentName,
      prompt_version: promptVersion,
      ratings,
      opmerking: opmerking.trim() || undefined,
      beoordelaar: "klant",
    }

    setBezig(true)
    try {
      const res = await fetch(
        `/api/portal/projects/${projectId}/feedback`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      )

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(
          body?.detail ?? `Serverfout: ${res.status} ${res.statusText}`
        )
      }

      setSucces(true)
    } catch (err: unknown) {
      setFout(
        err instanceof Error
          ? err.message
          : "Er is een onbekende fout opgetreden. Probeer het opnieuw."
      )
    } finally {
      setBezig(false)
    }
  }

  // ── Succes state ───────────────────────────────────────────────────────────

  if (succes) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
          <div className="text-5xl mb-4">🎉</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Bedankt voor uw feedback!
          </h1>
          <p className="text-gray-500 text-sm">
            Uw beoordeling helpt ons de AI-agents verder te verbeteren voor
            VorstersNV.
          </p>
          <button
            type="button"
            onClick={() => {
              setSucces(false)
              setRatings(DEFAULT_RATINGS)
              setOpmerking("")
            }}
            className="mt-6 text-sm text-amber-600 hover:text-amber-700 underline underline-offset-2"
          >
            Nog een beoordeling indienen
          </button>
        </div>
      </main>
    )
  }

  // ── Formulier ──────────────────────────────────────────────────────────────

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-widest text-amber-600 mb-1">
            Kwaliteitsbeoordeling
          </p>
          <h1 className="text-3xl font-bold text-gray-900">
            Feedback op AI-output
          </h1>
          <p className="mt-2 text-gray-500 text-sm">
            Beoordeel de output van{" "}
            <span className="font-medium text-gray-700">{agentName}</span>{" "}
            (v{promptVersion}) voor project{" "}
            <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">
              {projectId}
            </span>
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          {/* Sterrenratings per sectie */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 divide-y divide-gray-100 mb-5">
            {SECTIES.map((sectie) => (
              <div
                key={sectie.id}
                className="flex items-center justify-between px-6 py-5 gap-4"
              >
                <div className="min-w-0">
                  <p className="font-semibold text-gray-800 text-sm">
                    {sectie.label}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {sectie.beschrijving}
                  </p>
                </div>
                <StarRating
                  sectie={sectie.id}
                  waarde={ratings[sectie.id]}
                  hover={hoverState[sectie.id]}
                  onHover={(n) => stelHoverIn(sectie.id, n)}
                  onLeave={() => resetHover(sectie.id)}
                  onKlik={(n) => stelRatingIn(sectie.id, n)}
                  uitgeschakeld={bezig}
                />
              </div>
            ))}
          </div>

          {/* Vrij tekstveld */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-5">
            <label
              htmlFor="feedback-opmerking"
              className="block text-sm font-semibold text-gray-800 mb-2"
            >
              Opmerking{" "}
              <span className="font-normal text-gray-400">(optioneel)</span>
            </label>
            <textarea
              id="feedback-opmerking"
              data-testid="feedback-opmerking"
              value={opmerking}
              onChange={(e) => setOpmerking(e.target.value)}
              disabled={bezig}
              rows={4}
              placeholder="Wat ging goed? Wat kan beter? Elk detail helpt…"
              className={[
                "w-full rounded-lg border border-gray-200 bg-gray-50 px-4 py-3",
                "text-sm text-gray-700 placeholder-gray-400",
                "focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent",
                "resize-none transition-colors",
                bezig ? "opacity-50 cursor-not-allowed" : "",
              ].join(" ")}
            />
          </div>

          {/* Foutmelding */}
          {fout && (
            <div
              role="alert"
              className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-5 py-4 mb-5"
            >
              <span className="font-semibold">Fout: </span>
              {fout}
            </div>
          )}

          {/* Submit knop */}
          <button
            type="submit"
            data-testid="submit-feedback"
            disabled={bezig}
            className={[
              "w-full flex items-center justify-center gap-2",
              "rounded-xl px-6 py-3.5 text-sm font-semibold text-white",
              "transition-all duration-150",
              bezig
                ? "bg-amber-300 cursor-not-allowed"
                : "bg-amber-500 hover:bg-amber-600 active:scale-[0.98] shadow-sm hover:shadow",
            ].join(" ")}
          >
            {bezig ? (
              <>
                {/* Loading spinner */}
                <svg
                  className="animate-spin h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v8H4z"
                  />
                </svg>
                Bezig met verzenden…
              </>
            ) : (
              "Feedback indienen"
            )}
          </button>
        </form>
      </div>
    </main>
  )
}
