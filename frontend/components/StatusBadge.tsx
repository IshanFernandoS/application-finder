import { CheckCircle2, Clock3, XCircle } from "lucide-react";

const styles: Record<string, string> = {
  ok: "border-teal/30 bg-teal/10 text-teal",
  available: "border-teal/30 bg-teal/10 text-teal",
  completed: "border-teal/30 bg-teal/10 text-teal",
  output_retrieved: "border-teal/30 bg-teal/10 text-teal",
  running: "border-accent/30 bg-accent/10 text-accent",
  submitted: "border-accent/30 bg-accent/10 text-accent",
  transferring_inputs: "border-accent/30 bg-accent/10 text-accent",
  retrieving_outputs: "border-accent/30 bg-accent/10 text-accent",
  created: "border-line bg-shell text-muted",
  queued: "border-amber/30 bg-amber/10 text-amber",
  unknown: "border-amber/30 bg-amber/10 text-amber",
  setup_needed: "border-amber/30 bg-amber/10 text-amber",
  path_missing: "border-coral/30 bg-coral/10 text-coral",
  dependency_missing: "border-coral/30 bg-coral/10 text-coral",
  gpu_unavailable: "border-coral/30 bg-coral/10 text-coral",
  failed: "border-coral/30 bg-coral/10 text-coral",
  cancelled: "border-coral/30 bg-coral/10 text-coral"
};

export function StatusBadge({ status }: { status: string }) {
  const Icon =
    status === "ok" || status === "available" || status === "completed" || status === "output_retrieved"
      ? CheckCircle2
      : status.includes("missing") || status === "failed" || status === "cancelled"
        ? XCircle
        : Clock3;
  return (
    <span className={`inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium ${styles[status] || "border-line bg-shell text-muted"} border`}>
      <Icon aria-hidden className="h-3.5 w-3.5" />
      {status.replaceAll("_", " ")}
    </span>
  );
}
