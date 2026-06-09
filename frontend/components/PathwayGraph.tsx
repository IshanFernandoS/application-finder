"use client";

import "@xyflow/react/dist/style.css";
import { Background, Controls, ReactFlow } from "@xyflow/react";
import type { Pathway } from "@/lib/types";
import { EmptyState } from "./EmptyState";

export function PathwayGraph({ pathway }: { pathway?: Pathway }) {
  if (!pathway) {
    return <EmptyState title="No pathway selected" body="Generate or open an FBS-PM pathway to inspect the full gap-to-validation reasoning chain." />;
  }
  const nodes = [
    ["gap", "Gap", pathway.gap_id],
    ["pseudo", "Pseudo-application", pathway.pseudo_application],
    ["function", "Function", pathway.function],
    ["mechanism", "EM mechanism", pathway.behaviour_or_mechanism],
    ["structure", "Device route", pathway.structure_or_device_realization],
    ["property", "Property envelope", `${pathway.material_property_envelope.length} requirements`],
    ["material", "Candidate material", `${pathway.candidate_materials.length} candidates`],
    ["validation", "MatterGen / validation", pathway.validation_status]
  ].map(([id, label, detail], index) => ({
    id,
    position: { x: index * 245, y: index % 2 === 0 ? 60 : 190 },
    data: { label: <NodeLabel title={label} detail={detail} /> },
    type: "default",
    style: { width: 210, borderRadius: 8, borderColor: "hsl(var(--line))", background: "hsl(var(--panel))", color: "hsl(var(--ink))" }
  }));
  const edges = nodes.slice(0, -1).map((node, index) => ({
    id: `${node.id}-${nodes[index + 1].id}`,
    source: node.id,
    target: nodes[index + 1].id,
    animated: index < 5,
    style: { stroke: "hsl(var(--accent))" }
  }));
  return (
    <section className="panel h-[460px] overflow-hidden">
      <ReactFlow nodes={nodes as any} edges={edges} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </section>
  );
}

function NodeLabel({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="text-left">
      <div className="text-xs font-semibold text-accent">{title}</div>
      <div className="mt-1 line-clamp-3 text-xs text-muted">{detail}</div>
    </div>
  );
}
