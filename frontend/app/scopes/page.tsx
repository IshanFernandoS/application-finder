import { AppShell } from "@/components/AppShell";
import { ScopeEditor } from "@/components/ScopeEditor";
import { apiGet } from "@/lib/api";
import type { Scope } from "@/lib/types";

export default async function ScopesPage() {
  const scope = await apiGet<Scope>("/scopes/electromagnetic_functional_materials").catch(() => undefined);
  return (
    <AppShell>
      <ScopeEditor scope={scope} />
    </AppShell>
  );
}
