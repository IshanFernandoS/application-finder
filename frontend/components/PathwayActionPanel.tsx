"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { CheckCircle2, FlaskConical, Loader2, Search, Star } from "lucide-react";
import { apiPost } from "@/lib/api";
import type { MaterialCandidate, Pathway } from "@/lib/types";

export function PathwayActionPanel({ pathway }: { pathway?: Pathway }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | undefined>();
  const [message, setMessage] = useState<string | undefined>();
  const [error, setError] = useState<string | undefined>();

  if (!pathway) return null;

  async function run<T>(name: string, action: () => Promise<T>, onSuccess: (result: T) => void) {
    setBusy(name);
    setMessage(undefined);
    setError(undefined);
    try {
      const result = await action();
      onSuccess(result);
      router.refresh();
    } catch (exc) {
      setError(readableError(exc));
    } finally {
      setBusy(undefined);
    }
  }

  const actions = [
    {
      key: "validate",
      label: "Validate evidence chain",
      icon: CheckCircle2,
      run: () =>
        run("validate", () => apiPost<Record<string, unknown>>(`/pathways/${pathway.pathway_id}/validate-evidence`), (result) =>
          setMessage(Boolean(result.valid) ? "Evidence chain validated" : "Evidence validation found gaps")
        )
    },
    {
      key: "rank",
      label: "Rank pathway",
      icon: Star,
      run: () =>
        run("rank", () => apiPost<Record<string, number>>(`/pathways/${pathway.pathway_id}/rank`), (scores) =>
          setMessage(`Pathway ranked: ${Math.round((scores.overall || 0) * 100)}% overall`)
        )
    },
    {
      key: "constraints",
      label: "Translate MatterGen constraints",
      icon: FlaskConical,
      run: () =>
        run("constraints", () => apiPost(`/pathways/${pathway.pathway_id}/mattergen/translate-constraints`), () =>
          setMessage("MatterGen constraints translated from the FBS-PM pathway")
        )
    },
    {
      key: "candidates",
      label: "Retrieve known candidates",
      icon: Search,
      run: () =>
        run("candidates", () => apiPost<MaterialCandidate[]>(`/materials/pathways/${pathway.pathway_id}/retrieve-candidates`), (candidates) =>
          setMessage(`${candidates.length} material candidates retrieved`)
        )
    }
  ];

  return (
    <section className="panel p-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold">Pathway Actions</h2>
          <p className="mt-1 text-sm text-muted">{pathway.title}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {actions.map((action) => {
            const Icon = action.icon;
            return (
              <button
                key={action.key}
                className="focus-ring inline-flex items-center gap-2 rounded border border-line px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60"
                disabled={Boolean(busy)}
                onClick={action.run}
                type="button"
              >
                {busy === action.key ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Icon className="h-4 w-4" aria-hidden />}
                {action.label}
              </button>
            );
          })}
        </div>
      </div>
      {message ? <div className="mt-4 rounded border border-teal/40 bg-teal/10 p-3 text-sm">{message}</div> : null}
      {error ? <div className="mt-4 rounded border border-coral/40 bg-coral/10 p-3 text-sm">{error}</div> : null}
    </section>
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
