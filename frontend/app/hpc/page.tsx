import { AppShell } from "@/components/AppShell";
import { HPCWorkerPanel } from "@/components/HPCWorkerPanel";
import { apiGet } from "@/lib/api";
import type { HPCJob, HPCStatus } from "@/lib/types";

export default async function HPCPage() {
  const key = process.env.ADMIN_API_KEY;
  const headers = key ? { "x-admin-api-key": key } : undefined;
  const status = headers ? await apiGet<HPCStatus>("/hpc/status", { headers }).catch(() => undefined) : undefined;
  const jobs = headers ? await apiGet<HPCJob[]>("/hpc/jobs", { headers }).catch(() => []) : [];
  return (
    <AppShell>
      <HPCWorkerPanel initialStatus={status} initialJobs={jobs} />
    </AppShell>
  );
}
