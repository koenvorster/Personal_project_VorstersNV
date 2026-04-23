/**
 * Projectdetail — Wave 9
 *
 * Server Component: haalt projectstatus op via GET /api/portal/projects/{id}/status
 * en toont naam, klant, statusbadge, voortgangsbalk en navigatielinks naar
 * rapport, diagrammen en feedback.
 */

import Link from "next/link";

// ── Types ─────────────────────────────────────────────────────────────────────

interface ProjectStatus {
  project_id: string;
  project_naam: string;
  klant_naam: string;
  status: string;
  voortgang_percent: number;
  geschatte_minuten: number | null;
  rapport_beschikbaar: boolean;
  aangemaakt_op: string;
  bijgewerkt_op: string;
}

// ── Status configuratie ───────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; kleur: string }> = {
  draft:          { label: "Concept",        kleur: "bg-gray-100 text-gray-700 border-gray-300" },
  actief:         { label: "Actief",          kleur: "bg-blue-100 text-blue-700 border-blue-300" },
  in_analyse:     { label: "In analyse",      kleur: "bg-yellow-100 text-yellow-800 border-yellow-300" },
  rapport_gereed: { label: "Rapport gereed",  kleur: "bg-green-100 text-green-700 border-green-300" },
  gesloten:       { label: "Gesloten",        kleur: "bg-red-100 text-red-700 border-red-300" },
};

function statusCfg(status: string) {
  return STATUS_CONFIG[status] ?? { label: status, kleur: "bg-gray-100 text-gray-700 border-gray-300" };
}

// ── Data ophalen ──────────────────────────────────────────────────────────────

async function haalProjectStatusOp(id: string): Promise<ProjectStatus | null> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/portal/projects/${encodeURIComponent(id)}/status`,
      { cache: "no-store" },
    );
    if (!res.ok) return null;
    return (await res.json()) as ProjectStatus;
  } catch {
    return null;
  }
}

// ── Navigatiekaart component ──────────────────────────────────────────────────

function NavKaart({
  href,
  testId,
  icon,
  titel,
  beschrijving,
  beschikbaar,
}: {
  href: string;
  testId: string;
  icon: React.ReactNode;
  titel: string;
  beschrijving: string;
  beschikbaar?: boolean;
}) {
  const klasse =
    "flex items-start gap-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow";

  return (
    <Link href={href} data-testid={testId} className={klasse}>
      <div className="shrink-0 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
        {icon}
      </div>
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-semibold text-gray-900">{titel}</p>
          {beschikbaar === true && (
            <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
              Beschikbaar
            </span>
          )}
          {beschikbaar === false && (
            <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
              Nog niet beschikbaar
            </span>
          )}
        </div>
        <p className="mt-0.5 text-sm text-gray-500">{beschrijving}</p>
      </div>
      <svg
        className="ml-auto h-5 w-5 shrink-0 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 5l7 7-7 7"
        />
      </svg>
    </Link>
  );
}

// ── Pagina component ──────────────────────────────────────────────────────────

interface PageProps {
  params: { id: string };
}

export default async function ProjectDetailPagina({ params }: PageProps) {
  const { id } = params;
  const project = await haalProjectStatusOp(id);

  // Niet gevonden
  if (!project) {
    return (
      <div
        className="min-h-screen bg-gray-50 flex items-center justify-center px-4"
        data-testid="project-detail-page"
      >
        <div className="text-center">
          <p className="text-4xl font-bold text-gray-300 mb-2">404</p>
          <p className="text-lg font-medium text-gray-600">Project niet gevonden</p>
          <p className="mt-1 text-sm text-gray-400">
            Project{" "}
            <code className="font-mono bg-gray-100 px-1.5 py-0.5 rounded text-xs">
              {id}
            </code>{" "}
            bestaat niet of is niet beschikbaar.
          </p>
          <Link
            href="/portal/projects"
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            ← Terug naar overzicht
          </Link>
        </div>
      </div>
    );
  }

  const cfg = statusCfg(project.status);

  return (
    <div
      className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8"
      data-testid="project-detail-page"
    >
      <div className="max-w-3xl mx-auto">
        {/* Breadcrumb */}
        <nav className="mb-6 flex items-center gap-2 text-sm text-gray-500">
          <Link href="/portal/projects" className="hover:text-blue-600 transition-colors">
            Projecten
          </Link>
          <span aria-hidden="true">›</span>
          <span className="text-gray-800 font-medium truncate">
            {project.project_naam}
          </span>
        </nav>

        {/* Header */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h1
                className="text-xl font-bold text-gray-900 truncate"
                data-testid="project-title"
              >
                {project.project_naam}
              </h1>
              <p className="mt-1 text-sm text-gray-500">{project.klant_naam}</p>
            </div>

            <span
              className={`inline-flex shrink-0 items-center px-3 py-1 rounded-full text-sm font-medium border ${cfg.kleur}`}
              data-testid="project-status-badge"
            >
              {cfg.label}
            </span>
          </div>

          {/* Voortgangsbalk */}
          <div className="mt-5">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-medium text-gray-700">Voortgang</span>
              <span className="text-sm text-gray-500">
                {project.voortgang_percent}%
                {project.geschatte_minuten !== null && (
                  <> · ~{project.geschatte_minuten} min resterend</>
                )}
              </span>
            </div>
            <div
              className="relative h-3 w-full bg-gray-100 rounded-full overflow-hidden"
              role="progressbar"
              aria-valuenow={project.voortgang_percent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Projectvoortgang: ${project.voortgang_percent}%`}
              data-testid="progress-bar"
            >
              <div
                className="absolute inset-y-0 left-0 bg-blue-500 rounded-full transition-all duration-500"
                style={{ width: `${project.voortgang_percent}%` }}
              />
            </div>
          </div>

          {/* Metadata */}
          <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <div>
              <dt className="text-gray-400">Project-ID</dt>
              <dd className="font-mono text-xs text-gray-600 truncate" title={project.project_id}>
                {project.project_id}
              </dd>
            </div>
            <div>
              <dt className="text-gray-400">Aangemaakt op</dt>
              <dd className="text-gray-700">
                {new Date(project.aangemaakt_op).toLocaleDateString("nl-BE", {
                  day: "2-digit",
                  month: "long",
                  year: "numeric",
                })}
              </dd>
            </div>
            <div>
              <dt className="text-gray-400">Bijgewerkt op</dt>
              <dd className="text-gray-700">
                {new Date(project.bijgewerkt_op).toLocaleDateString("nl-BE", {
                  day: "2-digit",
                  month: "long",
                  year: "numeric",
                })}
              </dd>
            </div>
          </dl>
        </div>

        {/* Navigatiekaarten */}
        <div className="space-y-3">
          {/* Rapport */}
          <NavKaart
            href={`/portal/projects/${id}/rapport`}
            testId="rapport-link"
            beschikbaar={project.rapport_beschikbaar}
            titel="Analyserapport"
            beschrijving="Volledig Markdown-rapport van de AI-analyse met bevindingen en aanbevelingen."
            icon={
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-6 w-6" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            }
          />

          {/* Diagrammen */}
          <NavKaart
            href={`/portal/projects/${id}/diagrams`}
            testId="diagrams-link"
            titel="Architectuurdiagrammen"
            beschrijving="Mermaid- en PlantUML-diagrammen gegenereerd door de analyse-agents."
            icon={
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-6 w-6" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7"
                />
              </svg>
            }
          />

          {/* Feedback */}
          <NavKaart
            href={`/portal/projects/${id}/feedback`}
            testId="feedback-link"
            titel="Feedback geven"
            beschrijving="Beoordeel de kwaliteit, duidelijkheid en bruikbaarheid van de AI-output."
            icon={
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="h-6 w-6" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            }
          />
        </div>

        {/* Terug knop */}
        <div className="mt-8">
          <Link
            href="/portal/projects"
            className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 transition-colors"
          >
            ← Terug naar overzicht
          </Link>
        </div>
      </div>
    </div>
  );
}
