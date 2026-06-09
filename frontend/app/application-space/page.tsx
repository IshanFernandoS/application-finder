import { AppShell } from "@/components/AppShell";
import { ApplicationSpaceWorkspace } from "@/components/ApplicationSpaceWorkspace";
import { EmptyState } from "@/components/EmptyState";
import { apiGet } from "@/lib/api";
import type { ApplicationSpace } from "@/lib/types";

export default async function ApplicationSpacePage() {
  const space = await apiGet<ApplicationSpace>("/application-space").catch(() => undefined);
  return (
    <AppShell>
      {space ? (
        <ApplicationSpaceWorkspace space={space} />
      ) : (
        <EmptyState title="Application Space is not built" body="Run local ingestion, descriptor extraction, and the application-space build endpoint to populate the map." />
      )}
    </AppShell>
  );
}
