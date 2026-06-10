"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { GitBranch, Loader2, RadioTower } from "lucide-react";
import { apiPost } from "@/lib/api";
import type { ApplicationSpace, Gap } from "@/lib/types";

export function ApplicationSpaceActions({ hasSpace, gapCount = 0 }: { hasSpace?: boolean; gapCount?: number }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | undefined>();
  const [message, setMessage] = useState<string | undefined>();
  const [error, setError] = useState<string | undefined>();

  async function run<T>(name: string, action: () => Promise<T>, onSuccess: (result: T) => void) {
    setBusy(name);
    setError(undefined);
    setMessage(undefined);
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

  return (
    <section className="panel p-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold">Application Space Workflow</h2>
          <p className="mt-1 text-sm text-muted">
            {hasSpace ? `${gapCount} gaps currently available for FBS-PM reasoning.` : "Build the map after descriptor extraction, then detect application-space gaps."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="focus-ring inline-flex items-center gap-2 rounded bg-accent px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
            disabled={Boolean(busy)}
            onClick={() =>
              run("build", () => apiPost<ApplicationSpace>("/application-space/build"), (space) =>
                setMessage(`Application Space built with ${space.nodes.length} nodes and ${space.clusters.length} clusters`)
              )
            }
            type="button"
          >
            {busy === "build" ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <RadioTower className="h-4 w-4" aria-hidden />}
            Build space
          </button>
          <button
            className="focus-ring inline-flex items-center gap-2 rounded border border-line px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60"
            disabled={Boolean(busy)}
            onClick={() =>
              run("detect", () => apiPost<Gap[]>("/gaps/detect"), (gaps) =>
                setMessage(`${gaps.length} application-space gaps detected`)
              )
            }
            type="button"
          >
            {busy === "detect" ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <GitBranch className="h-4 w-4" aria-hidden />}
            Detect gaps
          </button>
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
    // Keep the raw message when the backend did not return JSON.
  }
  return raw;
}
