"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { FileDown, GitBranch, Library, Loader2, PlayCircle } from "lucide-react";
import type { EvidenceChunk, EvaluationRun, Gap, Pathway } from "@/lib/types";
import { apiPost } from "@/lib/api";
import { GapScoreCard } from "./GapScoreCard";

export function GapInspector({ gap }: { gap?: Gap }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | undefined>();
  const [message, setMessage] = useState<string | undefined>();
  const [error, setError] = useState<string | undefined>();

  async function runAction(name: string, action: () => Promise<void>) {
    setBusy(name);
    setMessage(undefined);
    setError(undefined);
    try {
      await action();
    } catch (exc) {
      setError(readableError(exc));
    } finally {
      setBusy(undefined);
    }
  }

  if (!gap) {
    return (
      <aside className="panel p-5">
        <h2 className="text-base font-semibold">Gap Inspector</h2>
        <p className="mt-2 text-sm text-muted">Select a highlighted gap on the map to inspect evidence, scores, and FBS-PM actions.</p>
      </aside>
    );
  }
  const actions = [
    {
      label: "Retrieve boundary evidence",
      icon: Library,
      run: () =>
        runAction("evidence", async () => {
          const evidence = await apiPost<EvidenceChunk[]>(`/gaps/${gap.gap_id}/retrieve-evidence`);
          setMessage(`${evidence.length} boundary evidence chunks retrieved`);
          router.push(`/gaps/${gap.gap_id}`);
        })
    },
    {
      label: "Generate FBS-PM pathways",
      icon: GitBranch,
      run: () =>
        runAction("pathways", async () => {
          const pathways = await apiPost<Pathway[]>(`/gaps/${gap.gap_id}/generate-pathways`);
          if (pathways[0]?.pathway_id) {
            router.push(`/pathways/${pathways[0].pathway_id}`);
          } else {
            setMessage("No FBS-PM pathways were generated for this gap");
          }
        })
    },
    {
      label: "Run baseline comparison",
      icon: PlayCircle,
      run: () =>
        runAction("baseline", async () => {
          const run = await apiPost<EvaluationRun>("/evals/baselines/run", { mode: "baseline_nearest_neighbour", gap_id: gap.gap_id });
          setMessage(`${run.mode} evaluation recorded with ${run.metrics.length} metrics`);
          router.refresh();
        })
    },
    {
      label: "Export report",
      icon: FileDown,
      run: () =>
        runAction("report", async () => {
          await apiPost(`/reports/${gap.gap_id}`);
          router.push("/reports");
        })
    }
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
              className="focus-ring flex items-center justify-center gap-2 rounded border border-line bg-shell px-3 py-2 text-sm font-medium hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-60"
              disabled={Boolean(busy)}
              type="button"
              onClick={action.run}
            >
              {busy && action.label.toLowerCase().includes(busy) ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Icon className="h-4 w-4" aria-hidden />}
              {action.label}
            </button>
          );
        })}
      </div>
      {message ? <div className="mt-4 rounded border border-teal/40 bg-teal/10 p-3 text-sm">{message}</div> : null}
      {error ? <div className="mt-4 rounded border border-coral/40 bg-coral/10 p-3 text-sm">{error}</div> : null}
    </aside>
  );
}

function readableError(exc: unknown) {
  const raw = exc instanceof Error ? exc.message : String(exc);
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // Leave plain error messages untouched.
  }
  return raw;
}
