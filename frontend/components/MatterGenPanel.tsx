import Link from "next/link";
import type { MatterGenStatus, Pathway } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

export function MatterGenPanel({ status, pathway }: { status?: MatterGenStatus; pathway?: Pathway }) {
  return (
    <section className="panel p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">MatterGen</h2>
          <p className="mt-1 text-sm text-muted">Structure generation is optional and requires a GPU-capable local or remote worker.</p>
        </div>
        {status ? <StatusBadge status={status.status} /> : null}
      </div>
      {status ? (
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <Info label="Mode" value={status.mode} />
          <Info label="GPU" value={status.gpu_available ? "available" : "not detected"} />
          <Info label="Importable" value={status.importable ? "yes" : "no"} />
          <Info label="Checkpoints" value={status.checkpoints_found ? "found" : "missing"} />
        </dl>
      ) : null}
      {pathway?.mattergen_constraints ? (
        <div className="mt-4 rounded border border-line bg-shell p-4 text-sm text-muted">
          <div className="font-medium text-ink">Constraint translation</div>
          <div className="mt-2">Compatibility {Math.round(pathway.mattergen_constraints.compatibility_score * 100)}%</div>
          <div className="mt-2">{pathway.mattergen_constraints.unsupported_em_properties.length} unsupported EM properties retained for validation.</div>
        </div>
      ) : null}
      {status && status.status !== "available" ? (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded border border-line bg-shell p-4 text-sm">
          <div>
            <div className="font-medium text-ink">Run MatterGen on HPC</div>
            <div className="mt-1 text-muted">Submit generation from an FBS-PM pathway through the admin-only Slurm worker.</div>
          </div>
          <Link href="/hpc" className="focus-ring rounded bg-accent px-3 py-2 text-sm font-medium text-white">
            Open HPC Worker
          </Link>
        </div>
      ) : null}
      {status?.details?.length ? (
        <ul className="mt-4 space-y-2 text-sm text-muted">
          {status.details.map((detail) => (
            <li key={detail} className="rounded border border-line bg-shell p-3">
              {detail}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-line bg-shell px-3 py-2">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  );
}
