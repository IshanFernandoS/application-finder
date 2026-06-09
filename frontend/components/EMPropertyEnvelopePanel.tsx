import type { PropertyRequirement } from "@/lib/types";

export function EMPropertyEnvelopePanel({ requirements }: { requirements?: PropertyRequirement[] }) {
  return (
    <section className="panel p-5">
      <h2 className="text-base font-semibold">EM Property Envelope</h2>
      <div className="mt-4 grid gap-3">
        {(requirements || []).map((req) => (
          <article key={`${req.property_name}-${req.target_range_or_qualitative_requirement}`} className="rounded border border-line bg-shell p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold">{req.property_name}</h3>
                <p className="mt-1 text-xs text-muted">{req.property_category} / {req.desired_direction}</p>
              </div>
              <span className="rounded bg-panel px-2 py-1 text-xs text-muted">{req.mattergen_direct_support}</span>
            </div>
            <p className="mt-3 text-sm text-muted">{req.target_range_or_qualitative_requirement}</p>
            <p className="mt-2 text-sm leading-6 text-muted">{req.why_required}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
