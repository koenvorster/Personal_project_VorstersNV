/**
 * Projectoverzicht — Wave 9
 *
 * Server Component: haalt projecten op via GET /api/portal/projects
 * en toont ze als kaarten met statusbadge en voortgangsbalk.
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

const STATUS_CONFIG: Record<
  string,
  { label: string; kleur: string }
> = {
  draft:          { label: "Concept",         kleur: "bg-gray-100 text-gray-700 border-gray-300" },
  actief:         { label: "Actief",           kleur: "bg-blue-100 text-blue-700 border-blue-300" },
  in_analyse:     { label: "In analyse",       kleur: "bg-yellow-100 text-yellow-800 border-yellow-300" },
  rapport_gereed: { label: "Rapport gereed",   kleur: "bg-green-100 text-green-700 border-green-300" },
  gesloten:       { label: "Gesloten",         kleur: "bg-red-100 text-red-700 border-red-300" },
};

function statusConfig(status: string) {
  return STATUS_CONFIG[status] ?? { label: status, kleur: "bg-gray-100 text-gray-700 border-gray-300" };
}

// ── ProjectCard ───────────────────────────────────────────────────────────────

function ProjectCard({
  project,
  index,
}: {
  project: ProjectStatus;
  index: number;
}) {
  const cfg = statusConfig(project.status);

  return (
    <Link
      href={`/portal/projects/${project.project_id}`}
      data-testid={`project-card-${index}`}
      className="block bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-5"
    >
      {/* Bovenste rij: naam + statusbadge */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="min-w-0">
          <h2
            className="text-base font-bold text-gray-900 truncate"
            data-testid={`project-naam-${index}`}
          >
            {project.project_naam}
          </h2>
          <p className="text-sm text-gray-500 mt-0.5 truncate">
            {project.klant_naam}
          </p>
        </div>

        <span
          className={`inline-flex shrink-0 items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cfg.kleur}`}
          data-testid={`project-status-${index}`}
        >
          {cfg.label}
        </span>
      </div>

      {/* Voortgangsbalk */}
      <div
        className="relative h-2 w-full bg-gray-100 rounded-full overflow-hidden"
        role="progressbar"
        aria-valuenow={project.voortgang_percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Voortgang: ${project.voortgang_percent}%`}
        data-testid={`project-progress-${index}`}
      >
        <div
          className="absolute inset-y-0 left-0 bg-blue-500 rounded-full transition-all"
          style={{ width: `${project.voortgang_percent}%` }}
        />
      </div>
      <p className="text-xs text-gray-400 mt-1">
        {project.voortgang_percent}% voltooid
        {project.geschatte_minuten !== null && (
          <> · ~{project.geschatte_minuten} min</>
        )}
      </p>

      {/* Rapport beschikbaar indicator */}
      {project.rapport_beschikbaar && (
        <p className="mt-2 text-xs font-medium text-green-600">
          ✓ Rapport beschikbaar
        </p>
      )}

      {/* Aanmaakdatum */}
      <p className="mt-2 text-xs text-gray-400">
        Aangemaakt:{" "}
        {new Date(project.aangemaakt_op).toLocaleDateString("nl-BE", {
          day: "2-digit",
          month: "short",
          year: "numeric",
        })}
      </p>
    </Link>
  );
}

// ── Data ophalen ──────────────────────────────────────────────────────────────

async function haalProjectenOp(): Promise<ProjectStatus[]> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/portal/projects`,
      { cache: "no-store" },
    );
    if (!res.ok) {
      return [];
    }
    return (await res.json()) as ProjectStatus[];
  } catch {
    return [];
  }
}

// ── Pagina component ──────────────────────────────────────────────────────────

export default async function ProjectenOverzichtPagina() {
  const projecten = await haalProjectenOp();

  return (
    <div
      className="min-h-screen bg-gray-50 py-10 px-4 sm:px-6 lg:px-8"
      data-testid="projects-page"
    >
      <div className="max-w-4xl mx-auto">
        {/* Paginaheader */}
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Mijn projecten</h1>
            <p className="mt-1 text-sm text-gray-500">
              Overzicht van al uw consultancy analyseprojecten
            </p>
          </div>

          <Link
            href="/portal/projects/nieuw"
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 transition-colors"
          >
            + Nieuw project
          </Link>
        </div>

        {/* Lege staat */}
        {projecten.length === 0 && (
          <div
            className="rounded-xl border border-dashed border-gray-300 bg-white py-20 text-center"
            data-testid="empty-state"
          >
            <svg
              className="mx-auto h-12 w-12 text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="text-lg font-medium text-gray-500">
              Nog geen projecten
            </p>
            <p className="mt-1 text-sm text-gray-400">
              Maak uw eerste analyseproject aan om te beginnen.
            </p>
            <Link
              href="/portal/projects/nieuw"
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              + Nieuw project aanmaken
            </Link>
          </div>
        )}

        {/* Projectenlijst */}
        {projecten.length > 0 && (
          <div className="space-y-4">
            {projecten.map((project, index) => (
              <ProjectCard key={project.project_id} project={project} index={index} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
