import { AppShell } from "@/components/AppShell";
import { BaselineComparisonPanel } from "@/components/BaselineComparisonPanel";
import { EvaluationDashboard } from "@/components/EvaluationDashboard";
import { apiGet } from "@/lib/api";
import type { EvaluationRun } from "@/lib/types";

export default async function EvalsPage() {
  const runs = await apiGet<EvaluationRun[]>("/evals/results").catch(() => []);
  return (
    <AppShell>
      <div className="grid gap-5">
        <EvaluationDashboard runs={runs} />
        <BaselineComparisonPanel />
      </div>
    </AppShell>
  );
}
