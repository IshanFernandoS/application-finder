import { AppShell } from "@/components/AppShell";
import { ApplicationSpaceActions } from "@/components/ApplicationSpaceActions";
import { ApplicationSpaceWorkspace } from "@/components/ApplicationSpaceWorkspace";
import { EmptyState } from "@/components/EmptyState";
import { apiGet } from "@/lib/api";
import type { ApplicationSpace } from "@/lib/types";

export default async function ApplicationSpacePage() {
  const space = await apiGet<ApplicationSpace>("/application-space").catch(() => undefined);
  return (
    <AppShell>
      <div className="grid gap-5">
        <ApplicationSpaceActions hasSpace={Boolean(space)} gapCount={space?.gaps.length ?? 0} />
        {space ? (
          <ApplicationSpaceWorkspace space={space} />
        ) : (
          <EmptyState title="Application Space is not built" body="Ingest literature, extract descriptors, then use Build space to populate the map." />
        )}
      </div>
    </AppShell>
  );
}
