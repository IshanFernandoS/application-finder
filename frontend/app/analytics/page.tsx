import { AccessAnalyticsDashboard } from "@/components/AccessAnalyticsDashboard";
import { AppShell } from "@/components/AppShell";
import { apiGet } from "@/lib/api";

export default async function AnalyticsPage() {
  const key = process.env.ADMIN_API_KEY || process.env.FRONTEND_ADMIN_API_KEY;
  const summary = key ? await apiGet<any>("/analytics/summary", { headers: { "x-admin-api-key": key } }).catch(() => undefined) : undefined;
  return (
    <AppShell>
      <AccessAnalyticsDashboard summary={summary} />
    </AppShell>
  );
}
