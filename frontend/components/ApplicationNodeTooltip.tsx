import type { ApplicationNode } from "@/lib/types";

export function ApplicationNodeTooltip({ node }: { node: ApplicationNode }) {
  return (
    <div className="space-y-1 text-xs">
      <div className="font-semibold">{node.label}</div>
      <div>{node.domain}</div>
      <div>{node.operating_frequency_or_wavelength || "frequency not extracted"}</div>
      <div>{node.device_type || "device not extracted"}</div>
      <div>{node.physical_em_mechanism || "mechanism not extracted"}</div>
      <div>{node.material_class || "material class not extracted"}</div>
      <div>{node.evidence_count} evidence links</div>
      {node.year ? <div>{node.year}</div> : null}
    </div>
  );
}
