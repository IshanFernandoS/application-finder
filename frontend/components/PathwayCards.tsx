import type { Pathway } from "@/lib/types";
import { ScoreBadge } from "./ScoreBadge";

export function PathwayCards({ pathways }: { pathways?: Pathway[] }) {
  if (!pathways?.length) return null;
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {pathways.map((pathway) => (
        <article key={pathway.pathway_id} className="panel p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-xs uppercase text-muted">{pathway.pathway_type}</div>
              <h3 className="mt-1 text-base font-semibold">{pathway.title}</h3>
            </div>
            <span className="rounded bg-shell px-2 py-1 text-xs text-muted">{pathway.validation_status}</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-muted">{pathway.summary}</p>
          <div className="mt-4 grid grid-cols-3 gap-2">
            <ScoreBadge label="Evidence" value={pathway.scores.evidence_support || 0} />
            <ScoreBadge label="Complete" value={pathway.scores.completeness || pathway.scores.fbs_pm_complete || 0} />
            <ScoreBadge label="Overall" value={pathway.scores.overall || 0} />
          </div>
        </article>
      ))}
    </div>
  );
}
