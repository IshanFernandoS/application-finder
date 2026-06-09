import { AppShell } from "@/components/AppShell";
import { IngestionPanel } from "@/components/IngestionPanel";
import { apiGet } from "@/lib/api";

export default async function IngestPage() {
  const status = await apiGet<{ documents: number; evidence_chunks: number }>("/ingest/status").catch(() => undefined);
  return (
    <AppShell>
      <div className="grid gap-5">
        <IngestionPanel />
        <section className="panel p-5">
          <h2 className="text-base font-semibold">Corpus Status</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <Metric label="Documents" value={status?.documents ?? 0} />
            <Metric label="Evidence chunks" value={status?.evidence_chunks ?? 0} />
            <Metric label="Descriptor extraction" value="OpenAI required" />
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
