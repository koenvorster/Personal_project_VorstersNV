"use client";

/**
 * DiagramViewer — Wave 9
 *
 * Toont alle Mermaid-diagrammen van een project. Rendert via Mermaid.js (client-side)
 * als de library beschikbaar is. Fallback: toon broncode in <pre> blok.
 *
 * Endpoint: GET /api/portal/projects/{id}/diagrams
 * - Terug: DiagramData[]
 * - Mock data als endpoint nog niet beschikbaar is (404/netwerk-fout)
 */

import { useEffect, useState } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface DiagramData {
  diagram_id: string;
  diagram_type: string;
  title: string;
  mermaid_source: string;
  render_success: boolean;
  svg_content: string | null;
  png_path: string | null;
  error_message: string | null;
}

interface DiagramCardProps {
  diagram: DiagramData;
  index: number;
}

// ── Mock data (fallback als API nog niet beschikbaar is) ──────────────────────

const MOCK_DIAGRAMS: DiagramData[] = [
  {
    diagram_id: "mock-001",
    diagram_type: "flowchart",
    title: "Orderverwerking Flow",
    mermaid_source:
      "flowchart TD\n    A[Order ontvangen] --> B{Fraude check}\n    B -->|OK| C[Betaling verwerken]\n    B -->|Verdacht| D[HITL review]\n    C --> E[Voorraad updaten]\n    E --> F[Verzenden]",
    render_success: false,
    svg_content: null,
    png_path: null,
    error_message: "Mock diagram",
  },
  {
    diagram_id: "mock-002",
    diagram_type: "sequence",
    title: "Mollie Betaalflow",
    mermaid_source:
      "sequenceDiagram\n    participant K as Klant\n    participant W as Webshop\n    participant M as Mollie\n    K->>W: Checkout\n    W->>M: Create payment\n    M-->>W: Payment URL\n    W-->>K: Redirect\n    K->>M: Betaalt\n    M->>W: Webhook\n    W-->>K: Bevestiging",
    render_success: false,
    svg_content: null,
    png_path: null,
    error_message: "Mock diagram",
  },
];

// ── Mermaid renderer component (dynamisch geladen, client-side only) ─────────
// Vereist: npm install mermaid
// Type-definitie voor de render-resultaat van Mermaid
interface MermaidRenderResult {
  svg: string;
  bindFunctions?: (element: Element) => void;
}

// Minimale interface zodat we mermaid zonder zijn package-types kunnen aanroepen
interface MermaidInstance {
  initialize: (config: Record<string, unknown>) => void;
  render: (id: string, source: string) => Promise<MermaidRenderResult>;
}

/**
 * Client-side Mermaid renderer. Laadt mermaid dynamisch in useEffect zodat:
 * - SSR volledig vermeden wordt (Mermaid werkt alleen in de browser)
 * - De build niet faalt als mermaid niet geïnstalleerd is
 * - Fallback naar <pre> als rendering mislukt
 */
function MermaidDiagram({
  source,
  diagramId,
}: {
  source: string;
  diagramId: string;
}) {
  const [svgContent, setSvgContent] = useState<string | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const elementId = `mermaid-${diagramId.replace(/[^a-z0-9]/gi, "-")}`;

    const renderDiagram = async () => {
      setIsLoading(true);
      try {
        // Dynamische import: werkt ook als mermaid niet geïnstalleerd is (catch vangt het op)
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        const mod = (await import(
          /* webpackChunkName: "mermaid" */
          // @ts-expect-error – optionele peer-dependency. Installeer via: npm install mermaid
          "mermaid"
        )) as { default: MermaidInstance };

        const mermaid: MermaidInstance = mod.default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "default",
          securityLevel: "loose",
          fontFamily: "Inter, system-ui, sans-serif",
        });

        const { svg } = await mermaid.render(elementId, source);
        if (!cancelled) {
          setSvgContent(svg);
          setRenderError(null);
        }
      } catch (err) {
        if (!cancelled) {
          const msg =
            err instanceof Error
              ? err.message
              : "Mermaid niet beschikbaar (npm install mermaid)";
          setRenderError(msg);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    void renderDiagram();
    return () => {
      cancelled = true;
    };
  }, [source, diagramId]);

  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center h-24 text-gray-400 text-sm"
        data-testid={`mermaid-loading-${diagramId}`}
      >
        <svg
          className="animate-spin h-5 w-5 mr-2 text-blue-500"
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
            d="M4 12a8 8 0 018-8v8z"
          />
        </svg>
        Diagram laden…
      </div>
    );
  }

  if (renderError) {
    return (
      <pre
        className="text-xs text-amber-700 bg-amber-50 border border-amber-200 p-3 rounded overflow-x-auto whitespace-pre-wrap"
        data-testid={`mermaid-error-${diagramId}`}
      >
        {source}
      </pre>
    );
  }

  return (
    <div
      className="overflow-x-auto"
      // eslint-disable-next-line @typescript-eslint/naming-convention
      dangerouslySetInnerHTML={{ __html: svgContent ?? "" }}
      data-testid={`mermaid-svg-${diagramId}`}
    />
  );
}

// ── DiagramCard component ─────────────────────────────────────────────────────

function DiagramCard({ diagram, index }: DiagramCardProps) {
  const [showSource, setShowSource] = useState(false);

  const typeLabels: Record<string, string> = {
    mermaid: "Mermaid",
    plantuml: "PlantUML",
    sequence: "Sequentiediagram",
    flowchart: "Stroomdiagram",
    class_diagram: "Klassediagram",
    er_diagram: "ER-diagram",
  };

  const typeColors: Record<string, string> = {
    sequence: "bg-purple-100 text-purple-800",
    flowchart: "bg-blue-100 text-blue-800",
    class_diagram: "bg-green-100 text-green-800",
    er_diagram: "bg-orange-100 text-orange-800",
    mermaid: "bg-gray-100 text-gray-800",
    plantuml: "bg-yellow-100 text-yellow-800",
  };

  const typeLabel = typeLabels[diagram.diagram_type] ?? diagram.diagram_type;
  const typeColor = typeColors[diagram.diagram_type] ?? "bg-gray-100 text-gray-800";

  return (
    <div
      className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
      data-testid={`diagram-card-${index}`}
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium shrink-0 ${typeColor}`}
          >
            {typeLabel}
          </span>
          <h3
            className="text-sm font-semibold text-gray-800 truncate"
            title={diagram.title}
            data-testid={`diagram-title-${index}`}
          >
            {diagram.title}
          </h3>
        </div>
        <button
          onClick={() => setShowSource((v) => !v)}
          className="shrink-0 text-xs text-blue-600 hover:text-blue-800 hover:underline transition-colors"
          data-testid={`diagram-toggle-source-${index}`}
          aria-expanded={showSource}
          aria-label={showSource ? "Verberg broncode" : "Toon broncode"}
        >
          {showSource ? "Verberg source" : "Toon source"}
        </button>
      </div>

      {/* Diagram content */}
      <div className="p-5">
        {/* SVG van server (als beschikbaar) */}
        {diagram.svg_content ? (
          <div
            className="overflow-x-auto"
            dangerouslySetInnerHTML={{ __html: diagram.svg_content }}
            data-testid={`diagram-svg-${index}`}
          />
        ) : (
          /* Client-side Mermaid rendering */
          <MermaidDiagram
            source={diagram.mermaid_source}
            diagramId={diagram.diagram_id}
          />
        )}

        {/* Broncode (toggle) */}
        {showSource && (
          <pre
            className="mt-4 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg p-4 overflow-x-auto whitespace-pre-wrap leading-relaxed"
            data-testid={`diagram-source-${index}`}
          >
            {diagram.mermaid_source}
          </pre>
        )}

        {/* Foutmelding (niet-kritiek) */}
        {diagram.error_message && !diagram.svg_content && (
          <p
            className="mt-2 text-xs text-amber-600 italic"
            data-testid={`diagram-warning-${index}`}
          >
            ⚠ {diagram.error_message}
          </p>
        )}
      </div>
    </div>
  );
}

// ── Hoofd pagina component ────────────────────────────────────────────────────

interface PageParams {
  params: { id: string };
}

export default function DiagramsPage({ params }: PageParams) {
  const projectId = params.id;

  const [diagrams, setDiagrams] = useState<DiagramData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchDiagrams = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/portal/projects/${encodeURIComponent(projectId)}/diagrams`,
          { headers: { "Content-Type": "application/json" } }
        );

        if (!response.ok) {
          if (response.status === 404) {
            // Endpoint nog niet beschikbaar — gebruik mock data
            if (!cancelled) {
              setDiagrams(MOCK_DIAGRAMS);
            }
            return;
          }
          throw new Error(`API fout ${response.status}: ${response.statusText}`);
        }

        const data: DiagramData[] = await response.json();
        if (!cancelled) {
          setDiagrams(data);
        }
      } catch (err) {
        if (!cancelled) {
          // Netwerk-fout of parse-fout → gebruik mock data als fallback
          console.warn("DiagramsPage: fallback naar mock data:", err);
          setDiagrams(MOCK_DIAGRAMS);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchDiagrams();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  return (
    <div
      className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8"
      data-testid="diagrams-page"
    >
      <div className="max-w-5xl mx-auto">
        {/* Paginaheader */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <a
              href={`/portal/projects/${projectId}`}
              className="hover:text-blue-600 transition-colors"
            >
              Project
            </a>
            <span aria-hidden="true">›</span>
            <span className="text-gray-800 font-medium">Diagrammen</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            Architectuurdiagrammen
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Gegenereerd door AI-analyse-agents • Project:{" "}
            <code className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">
              {projectId}
            </code>
          </p>
        </div>

        {/* Laadindicator */}
        {loading && (
          <div
            className="flex items-center justify-center py-20"
            data-testid="loading-spinner"
            role="status"
            aria-label="Diagrammen laden"
          >
            <svg
              className="animate-spin h-8 w-8 text-blue-500 mr-3"
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
                d="M4 12a8 8 0 018-8v8z"
              />
            </svg>
            <span className="text-gray-600 font-medium">
              Diagrammen laden…
            </span>
          </div>
        )}

        {/* Foutmelding */}
        {!loading && error && (
          <div
            className="bg-red-50 border border-red-200 rounded-xl p-6 text-center"
            data-testid="error-message"
            role="alert"
          >
            <p className="text-red-700 font-medium">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-3 text-sm text-red-600 hover:underline"
            >
              Opnieuw proberen
            </button>
          </div>
        )}

        {/* Lege staat */}
        {!loading && !error && diagrams.length === 0 && (
          <div
            className="text-center py-20 text-gray-400"
            data-testid="empty-state"
          >
            <svg
              className="mx-auto h-12 w-12 mb-4 opacity-40"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7"
              />
            </svg>
            <p className="text-lg font-medium text-gray-500">
              Nog geen diagrammen beschikbaar
            </p>
            <p className="mt-1 text-sm text-gray-400">
              Start een code-analyse om diagrammen te genereren.
            </p>
          </div>
        )}

        {/* Diagram grid */}
        {!loading && !error && diagrams.length > 0 && (
          <>
            {/* Statistieken balk */}
            <div className="mb-6 flex items-center gap-4 text-sm text-gray-500">
              <span>
                <strong className="text-gray-800">{diagrams.length}</strong>{" "}
                diagram{diagrams.length !== 1 ? "men" : ""}
              </span>
              <span>•</span>
              <span>
                <strong className="text-gray-800">
                  {diagrams.filter((d) => d.render_success).length}
                </strong>{" "}
                gerenderd
              </span>
              <span>•</span>
              <span>
                <strong className="text-gray-800">
                  {diagrams.filter((d) => !d.render_success).length}
                </strong>{" "}
                client-side
              </span>
            </div>

            <div className="space-y-6">
              {diagrams.map((diagram, index) => (
                <DiagramCard
                  key={diagram.diagram_id}
                  diagram={diagram}
                  index={index}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
