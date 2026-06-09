import type { EvaluationRun } from "@/lib/types";
import { pct } from "@/lib/formatters";

export function EvaluationDashboard({ runs = [] }: { runs?: EvaluationRun[] }) {
  const latest = runs[0];
  return (
    <section className="panel p-5">
      <h2 className="text-base font-semibold">Research-Readiness Metrics</h2>
      {!latest ? <p className="mt-3 text-sm text-muted">No evaluation runs yet.</p> : null}
      {latest ? (
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {latest.metrics.map((metric) => (
            <div key={metric.name} className="rounded border border-line bg-shell p-4">
              <div className="text-xs text-muted">{metric.name.replaceAll("_", " ")}</div>
              <div className="mt-2 text-2xl font-semibold">{pct(metric.value)}</div>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
