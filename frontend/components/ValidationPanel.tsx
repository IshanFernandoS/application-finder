import type { Pathway } from "@/lib/types";

export function ValidationPanel({ pathway }: { pathway?: Pathway }) {
  return (
    <section className="panel p-5">
      <h2 className="text-base font-semibold">Validation</h2>
      <div className="mt-4 grid gap-3 text-sm text-muted">
        <div className="rounded border border-line bg-shell p-3">pymatgen structure parsing</div>
        <div className="rounded border border-line bg-shell p-3">Materials Project and property lookup hooks</div>
        <div className="rounded border border-line bg-shell p-3">DFT workflow export</div>
        <div className="rounded border border-line bg-shell p-3">CST/HFSS/COMSOL export placeholder</div>
      </div>
      {pathway?.contradictions?.length ? <p className="mt-4 text-sm text-coral">{pathway.contradictions.join(" ")}</p> : null}
    </section>
  );
}
