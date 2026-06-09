import { AppShell } from "@/components/AppShell";
import { MatterGenPanel } from "@/components/MatterGenPanel";
import { apiGet } from "@/lib/api";
import type { MatterGenStatus } from "@/lib/types";

export default async function MatterGenPage() {
  const status = await apiGet<MatterGenStatus>("/mattergen/status").catch(() => undefined);
  return (
    <AppShell>
      <MatterGenPanel status={status} />
    </AppShell>
  );
}
