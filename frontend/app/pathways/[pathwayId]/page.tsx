import { AppShell } from "@/components/AppShell";
import { EMPropertyEnvelopePanel } from "@/components/EMPropertyEnvelopePanel";
import { MaterialCandidateTable } from "@/components/MaterialCandidateTable";
import { MatterGenPanel } from "@/components/MatterGenPanel";
import { PathwayGraph } from "@/components/PathwayGraph";
import { ValidationPanel } from "@/components/ValidationPanel";
import { apiGet } from "@/lib/api";
import type { MatterGenStatus, Pathway } from "@/lib/types";

export default async function PathwayPage({ params }: { params: Promise<{ pathwayId: string }> }) {
  const { pathwayId } = await params;
  const pathway = await apiGet<Pathway>(`/pathways/${pathwayId}`).catch(() => undefined);
  const status = await apiGet<MatterGenStatus>("/mattergen/status").catch(() => undefined);
  return (
    <AppShell>
      <div className="grid gap-5">
        <PathwayGraph pathway={pathway} />
        <div className="grid gap-5 xl:grid-cols-2">
          <EMPropertyEnvelopePanel requirements={pathway?.material_property_envelope} />
          <MatterGenPanel status={status} pathway={pathway} />
        </div>
        <MaterialCandidateTable candidates={pathway?.candidate_materials} />
        <ValidationPanel pathway={pathway} />
      </div>
    </AppShell>
  );
}
