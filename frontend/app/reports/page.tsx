import { AppShell } from "@/components/AppShell";
import { ReportPanel, type ReportRecord } from "@/components/ReportPanel";
import { apiGet } from "@/lib/api";

export default async function ReportsPage() {
  const reports = await apiGet<ReportRecord[]>("/reports").catch(() => []);
  return (
    <AppShell>
      <ReportPanel reports={reports} />
    </AppShell>
  );
}
