import type { Gap } from "@/lib/types";
import { ScoreBadge } from "./ScoreBadge";

export function GapScoreCard({ gap }: { gap: Gap }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <ScoreBadge label="Novelty" value={gap.novelty_score} />
      <ScoreBadge label="Feasibility" value={gap.feasibility_score} />
      <ScoreBadge label="Boundary evidence" value={gap.boundary_evidence_score} />
      <ScoreBadge label="Uncertainty" value={gap.uncertainty_score} />
    </div>
  );
}
