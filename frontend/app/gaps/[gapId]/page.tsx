import { AppShell } from "@/components/AppShell";
import { BoundaryEvidencePanel } from "@/components/BoundaryEvidencePanel";
import { GapInspector } from "@/components/GapInspector";
import { apiGet, apiPost } from "@/lib/api";
import type { EvidenceChunk, Gap } from "@/lib/types";

export default async function GapPage({ params }: { params: Promise<{ gapId: string }> }) {
  const { gapId } = await params;
  const gap = await apiGet<Gap>(`/gaps/${gapId}`).catch(() => undefined);
  const evidence = await apiPost<EvidenceChunk[]>(`/gaps/${gapId}/retrieve-evidence`).catch(() => []);
  return (
    <AppShell>
      <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
        <GapInspector gap={gap} />
        <BoundaryEvidencePanel evidence={evidence} />
      </div>
    </AppShell>
  );
}
