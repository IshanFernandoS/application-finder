import { pct } from "@/lib/formatters";

export function ScoreBadge({ label, value }: { label: string; value: number }) {
  const tone = value >= 0.7 ? "text-teal" : value >= 0.4 ? "text-amber" : "text-coral";
  return (
    <div className="rounded border border-line bg-shell px-3 py-2">
      <div className="text-xs text-muted">{label}</div>
      <div className={`text-lg font-semibold ${tone}`}>{pct(value)}</div>
    </div>
  );
}
