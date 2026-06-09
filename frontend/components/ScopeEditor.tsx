import type { Scope } from "@/lib/types";

export function ScopeEditor({ scope }: { scope?: Scope }) {
  return (
    <section className="panel p-5">
      <h2 className="text-base font-semibold">Scope Editor</h2>
      <p className="mt-2 text-sm text-muted">{scope?.description || "Load a scope to edit included domains, mechanisms, material classes, and descriptor weights."}</p>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <TokenList title="Domains" values={scope?.included_domains || []} />
        <TokenList title="Material classes" values={scope?.included_material_classes || []} />
        <TokenList title="Device families" values={scope?.included_device_families || []} />
        <TokenList title="Mechanisms" values={scope?.included_mechanisms || []} />
      </div>
    </section>
  );
}

function TokenList({ title, values }: { title: string; values: string[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="mt-2 flex flex-wrap gap-2">
        {values.map((value) => (
          <span key={value} className="rounded border border-line bg-shell px-2 py-1 text-xs text-muted">
            {value}
          </span>
        ))}
      </div>
    </div>
  );
}
