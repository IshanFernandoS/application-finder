import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { ApplicationSpaceMap } from "@/components/ApplicationSpaceMap";
import { StatusBadge } from "@/components/StatusBadge";
import { apiGet } from "@/lib/api";
import { compactDate } from "@/lib/formatters";
import type { ApplicationSpace, EvaluationRun, MatterGenStatus } from "@/lib/types";

async function safe<T>(promise: Promise<T>): Promise<T | undefined> {
  try {
    return await promise;
  } catch {
    return undefined;
  }
}

export default async function HomePage() {
  const health = await safe<{ openai_configured: boolean; mattergen_status: string }>(apiGet("/health"));
  const ingest = await safe<{ documents: number; evidence_chunks: number }>(apiGet("/ingest/status"));
  const space = await safe<ApplicationSpace>(apiGet("/application-space"));
  const mattergen = await safe<MatterGenStatus>(apiGet("/mattergen/status"));
  const evals = await safe<EvaluationRun[]>(apiGet("/evals/results"));

  return (
    <AppShell>
      <div className="grid gap-5">
        <section className="panel p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-4xl">
              <h1 className="text-3xl font-semibold">Application Finder</h1>
              <p className="mt-2 text-base text-muted">Electromagnetic Application-Space-Guided Generative Inverse Materials Design Platform</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge status={health?.openai_configured ? "available" : "setup_needed"} />
              <StatusBadge status={mattergen?.status || health?.mattergen_status || "setup_needed"} />
            </div>
          </div>
          <div className="mt-6 grid gap-3 md:grid-cols-5">
            <Metric label="Indexed documents" value={ingest?.documents ?? 0} />
            <Metric label="Evidence chunks" value={ingest?.evidence_chunks ?? 0} />
            <Metric label="Application nodes" value={space?.build.node_count ?? 0} />
            <Metric label="Detected gaps" value={space?.gaps.length ?? 0} />
            <Metric label="Latest build" value={compactDate(space?.build.created_at)} />
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            <CTA href="/ingest" label="Ingest Literature" />
            <CTA href="/application-space" label="Explore Electromagnetic Application Space" />
            <CTA href="/evals" label="Run Evaluations" />
          </div>
        </section>
        <ApplicationSpaceMap space={space} />
        <section className="panel p-5">
          <h2 className="text-base font-semibold">Gap-to-material reasoning path</h2>
          <div className="mt-4 grid gap-2 text-sm md:grid-cols-3 xl:grid-cols-5">
            {[
              "Electromagnetic Application Space",
              "Gap",
              "Pseudo-application",
              "Boundary evidence",
              "FBS-PM pathway",
              "EM property envelope",
              "Known material candidates",
              "MatterGen candidates",
              "Validation",
              "Report"
            ].map((step, index) => (
              <div key={step} className="rounded border border-line bg-shell p-3">
                <div className="text-xs text-muted">Step {index + 1}</div>
                <div className="mt-1 font-medium">{step}</div>
              </div>
            ))}
          </div>
        </section>
        <section className="grid gap-5 lg:grid-cols-2">
          <div className="panel p-5">
            <h2 className="text-base font-semibold">Latest Application Space</h2>
            <p className="mt-2 text-sm text-muted">
              {space ? `${space.build.reducer} + ${space.build.clusterer}, built ${compactDate(space.build.created_at)}` : "No build has been generated yet."}
            </p>
          </div>
          <div className="panel p-5">
            <h2 className="text-base font-semibold">Latest Evaluation</h2>
            <p className="mt-2 text-sm text-muted">
              {evals?.[0] ? `${evals[0].mode} run with ${evals[0].metrics.length} metrics` : "No evaluation run has been recorded yet."}
            </p>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded border border-line bg-shell p-4">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-2 text-xl font-semibold">{value}</div>
    </div>
  );
}

function CTA({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href} className="focus-ring rounded bg-accent px-4 py-2 text-sm font-medium text-white">
      {label}
    </Link>
  );
}
