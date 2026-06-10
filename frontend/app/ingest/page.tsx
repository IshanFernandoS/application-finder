import { AppShell } from "@/components/AppShell";
import { IngestionPanel } from "@/components/IngestionPanel";
import { apiGet } from "@/lib/api";

export default async function IngestPage() {
  const status = await apiGet<{ documents: number; evidence_chunks: number; application_nodes?: number }>("/ingest/status").catch(() => undefined);
  return (
    <AppShell>
      <div className="grid gap-5">
        <IngestionPanel initialStatus={status} />
      </div>
    </AppShell>
  );
}
