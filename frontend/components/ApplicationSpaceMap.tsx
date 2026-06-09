"use client";

import dynamic from "next/dynamic";
import { RotateCcw, Search } from "lucide-react";
import type { ApplicationSpace, Gap } from "@/lib/types";
import { EmptyState } from "./EmptyState";

const Plot = dynamic<any>(() => import("react-plotly.js"), { ssr: false });

export function ApplicationSpaceMap({
  space,
  selectedGapId,
  onSelectGap
}: {
  space?: ApplicationSpace;
  selectedGapId?: string;
  onSelectGap?: (gap: Gap) => void;
}) {
  if (!space || !space.nodes.length) {
    return <EmptyState title="No Application Space yet" body="Ingest real EM literature, extract descriptors, then build the scoped Application Space." />;
  }
  const clusterColor = (cluster?: string) => {
    const palette = ["#0ea5a5", "#2f80ed", "#f59e0b", "#ef6f6c", "#7c8a2a", "#22a06b", "#8b5cf6", "#f97316"];
    const index = Math.abs((cluster || "0").split("").reduce((acc, char) => acc + char.charCodeAt(0), 0)) % palette.length;
    return palette[index];
  };
  const nodeTrace = {
    x: space.nodes.map((node) => node.coordinates?.[0] || 0),
    y: space.nodes.map((node) => node.coordinates?.[1] || 0),
    type: "scattergl",
    mode: "markers",
    name: "Application nodes",
    text: space.nodes.map(
      (node) =>
        `<b>${node.label}</b><br>${node.domain}<br>${node.operating_frequency_or_wavelength || ""}<br>${node.device_type || ""}<br>${node.physical_em_mechanism || ""}<br>${node.material_class || ""}<br>${node.evidence_count} evidence links`
    ),
    hoverinfo: "text",
    marker: {
      size: space.nodes.map((node) => Math.max(7, Math.min(18, 6 + node.evidence_count * 2))),
      color: space.nodes.map((node) => clusterColor(node.cluster_id)),
      opacity: 0.82,
      line: { color: "rgba(255,255,255,0.7)", width: 1 }
    }
  };
  const gapTrace = {
    x: space.gaps.map((gap) => gap.coordinates[0]),
    y: space.gaps.map((gap) => gap.coordinates[1]),
    type: "scattergl",
    mode: "markers",
    name: "Detected gaps",
    text: space.gaps.map(
      (gap) =>
        `<b>${gap.title}</b><br>Novelty ${Math.round(gap.novelty_score * 100)}%<br>Feasibility ${Math.round(
          gap.feasibility_score * 100
        )}%<br>Boundary evidence ${Math.round(gap.boundary_evidence_score * 100)}%<br>${gap.pseudo_application_hypotheses[0] || ""}`
    ),
    hoverinfo: "text",
    marker: {
      symbol: "diamond",
      size: space.gaps.map((gap) => (gap.gap_id === selectedGapId ? 20 : 14)),
      color: space.gaps.map((gap) => (gap.gap_id === selectedGapId ? "#ef6f6c" : "#f59e0b")),
      line: { color: "#111827", width: 1 }
    }
  };
  return (
    <section className="panel overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div>
          <h2 className="text-base font-semibold">Electromagnetic Application Space</h2>
          <p className="text-xs text-muted">
            {space.build.node_count} nodes, {space.build.cluster_count} clusters, {space.gaps.length} gaps
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted" aria-hidden />
            <input className="focus-ring h-9 w-64 rounded border border-line bg-shell pl-9 pr-3 text-sm" placeholder="Search descriptors" />
          </label>
          <button className="focus-ring rounded border border-line p-2" title="Reset view" type="button">
            <RotateCcw className="h-4 w-4" aria-hidden />
          </button>
        </div>
      </div>
      <Plot
        data={[nodeTrace, gapTrace] as any}
        layout={
          {
            height: 620,
            margin: { l: 24, r: 24, t: 20, b: 32 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            hovermode: "closest",
            dragmode: "pan",
            xaxis: { zeroline: false, showgrid: true, gridcolor: "rgba(148,163,184,0.18)", title: "" },
            yaxis: { zeroline: false, showgrid: true, gridcolor: "rgba(148,163,184,0.18)", title: "" },
            legend: { orientation: "h", x: 0.02, y: 1.04 }
          } as any
        }
        config={{ responsive: true, displaylogo: false, modeBarButtonsToAdd: ["toImage"] as any }}
        useResizeHandler
        className="h-[620px] w-full"
        onClick={(event: any) => {
          const point = event.points?.[0];
          if (point?.data?.name === "Detected gaps") {
            const gap = space.gaps[point.pointIndex];
            onSelectGap?.(gap);
          }
        }}
      />
    </section>
  );
}
