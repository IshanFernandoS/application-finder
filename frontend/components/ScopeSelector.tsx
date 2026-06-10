"use client";

import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { apiGet } from "@/lib/api";
import type { Scope } from "@/lib/types";

export function ScopeSelector() {
  const [scopes, setScopes] = useState<Scope[]>([]);
  const [selected, setSelected] = useState("electromagnetic_functional_materials");

  useEffect(() => {
    apiGet<Scope[]>("/scopes").then(setScopes).catch(() => setScopes([]));
  }, []);

  return (
    <label className="relative block min-w-0">
      <span className="sr-only">Scope</span>
      <select
        className="focus-ring h-10 w-full min-w-0 appearance-none truncate rounded border border-line bg-panel px-3 pr-9 text-sm lg:min-w-72"
        value={selected}
        onChange={(event) => setSelected(event.target.value)}
      >
        {(scopes.length ? scopes : [{ scope_id: selected, title: "Electromagnetic Functional Materials and Devices" } as Scope]).map((scope) => (
          <option key={scope.scope_id} value={scope.scope_id}>
            {scope.title}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-3 top-3 h-4 w-4 text-muted" aria-hidden />
    </label>
  );
}
