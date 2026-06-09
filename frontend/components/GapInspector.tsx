"use client";

import { FileDown, GitBranch, Library, PlayCircle } from "lucide-react";
import type { Gap } from "@/lib/types";
import { apiPost } from "@/lib/api";
import { GapScoreCard } from "./GapScoreCard";

export function GapInspector({ gap }: { gap?: Gap }) {
  if (!gap) {
    return (
      <aside className="panel p-5">
        <h2 className="text-base font-semibold">Gap Inspector</h2>
        <p className="mt-2 text-sm text-muted">Select a highlighted gap on the map to inspect evidence, scores, and FBS-PM actions.</p>
      </aside>
    );
  }
  const actions = [
    { label: "Retrieve boundary evidence", icon: Library, run: () => apiPost(`/gaps/${gap.gap_id}/retrieve-evidence`) },
    { label: "Generate FBS-PM pathways", icon: GitBranch, run: () => apiPost(`/gaps/${gap.gap_id}/generate-pathways`) },
    { label: "Run baseline comparison", icon: PlayCircle, run: () => apiPost("/evals/baselines/run", { mode: "baseline_nearest_neighbour", gap_id: gap.gap_id }) },
    { label: "Export report", icon: FileDown, run: () => apiPost(`/reports/${gap.gap_id}`) }
  ];
  return (
    <aside className="panel max-h-[760px] overflow-auto p-5 scrollbar">
      <div className="mb-4">
        <div className="text-xs uppercase text-muted">Selected gap</div>
        <h2 className="mt-1 text-lg font-semibold">{gap.title}</h2>
      </div>
      <GapScoreCard gap={gap} />
      <section className="mt-5">
        <h3 className="text-sm font-semibold">Pseudo-Applications</h3>
        <ul className="mt-2 space-y-2 text-sm text-muted">
          {gap.pseudo_application_hypotheses.map((item) => (
            <li key={item} className="rounded border border-line bg-shell p-3">
              {item}
            </li>
          ))}
        </ul>
      </section>
      <section className="mt-5">
        <h3 className="text-sm font-semibold">Nearby Clusters</h3>
        <div className="mt-2 flex flex-wrap gap-2">
          {gap.nearby_cluster_ids.map((cluster) => (
            <span key={cluster} className="rounded border border-line bg-shell px-2 py-1 text-xs text-muted">
              {cluster}
            </span>
          ))}
        </div>
      </section>
      <section className="mt-5">
        <h3 className="text-sm font-semibold">Why It Matters</h3>
        <p className="mt-2 text-sm leading-6 text-muted">{gap.explanation}</p>
      </section>
      <div className="mt-5 grid gap-2">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.label}
              className="focus-ring flex items-center justify-center gap-2 rounded border border-line bg-shell px-3 py-2 text-sm font-medium hover:border-accent hover:text-accent"
              type="button"
              onClick={() => action.run().catch(() => undefined)}
            >
              <Icon className="h-4 w-4" aria-hidden />
              {action.label}
            </button>
          );
        })}
      </div>
    </aside>
  );
}
