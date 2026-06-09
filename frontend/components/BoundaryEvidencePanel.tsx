import type { EvidenceChunk } from "@/lib/types";
import { EmptyState } from "./EmptyState";

export function BoundaryEvidencePanel({ evidence }: { evidence?: EvidenceChunk[] }) {
  if (!evidence?.length) {
    return <EmptyState title="No boundary evidence loaded" body="Retrieve evidence for a selected gap to populate cited mechanism, device, property, material, and limitation cards." />;
  }
  return (
    <section className="panel p-5">
      <h2 className="text-base font-semibold">Boundary Evidence</h2>
      <div className="mt-4 grid gap-3">
        {evidence.map((item) => (
          <article key={item.evidence_id} className="rounded border border-line bg-shell p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold">{item.title}</h3>
                <p className="mt-1 text-xs text-muted">
                  {item.authors?.slice(0, 3).join(", ") || "Unknown authors"} {item.year ? `(${item.year})` : ""}
                </p>
              </div>
              <span className="rounded bg-panel px-2 py-1 text-xs text-muted">{Math.round(item.relevance_score * 100)}%</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-muted">{item.snippet}</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted">
              <span>{item.source_type}</span>
              {item.doi ? <span>DOI {item.doi}</span> : null}
              {item.page ? <span>p. {item.page}</span> : null}
              {item.section ? <span>{item.section}</span> : null}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
