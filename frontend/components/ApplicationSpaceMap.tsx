"use client";

import dynamic from "next/dynamic";
import type { ReactNode } from "react";
import { useState } from "react";
import { RotateCcw, Search } from "lucide-react";
import type { ApplicationNode, ApplicationSpace, Gap } from "@/lib/types";
import { EmptyState } from "./EmptyState";
import type { ApplicationSpaceFilters } from "./SidebarFilters";

const Plot = dynamic<any>(() => import("react-plotly.js"), { ssr: false });

type ColorMode = "cluster" | "confidence";

export function ApplicationSpaceMap({
  space,
  filters,
  selectedGapId,
  onSelectGap
}: {
  space?: ApplicationSpace;
  filters?: ApplicationSpaceFilters;
  selectedGapId?: string;
  onSelectGap?: (gap: Gap) => void;
}) {
  const [query, setQuery] = useState("");
  const [colorMode, setColorMode] = useState<ColorMode>("cluster");
  const [selectedNodeId, setSelectedNodeId] = useState<string | undefined>(space?.nodes[0]?.node_id);
  if (!space || !space.nodes.length) {
    return <EmptyState title="No Application Space yet" body="Ingest real EM literature, extract descriptors, then build the scoped Application Space." />;
  }

  const normalizedQuery = query.trim().toLowerCase();
  const activeFilters = filters || {
    domain: "",
    frequency: "",
    mechanism: "",
    deviceType: "",
    materialClass: "",
    year: "",
    minEvidence: ""
  };
  const activeFilterCount = Object.values(activeFilters).filter(Boolean).length;
  const filteredNodes = space.nodes.filter((node) => matchesNodeFilters(node, activeFilters) && (!normalizedQuery || nodeText(node).includes(normalizedQuery)));
  const visibleNodeIds = new Set(filteredNodes.map((node) => node.node_id));
  const visibleClusterIds = new Set(filteredNodes.map((node) => node.cluster_id).filter(Boolean));
  const filteredGaps = space.gaps.filter(
    (gap) =>
      (!normalizedQuery || gapText(gap).includes(normalizedQuery)) &&
      (!activeFilterCount ||
        gap.nearby_application_ids.some((nodeId) => visibleNodeIds.has(nodeId)) ||
        gap.nearby_cluster_ids.some((clusterId) => visibleClusterIds.has(clusterId)))
  );
  const clusterById = new Map(space.clusters.map((cluster) => [cluster.cluster_id, cluster]));
  const visibleClusters = space.clusters.filter((cluster) => visibleClusterIds.has(cluster.cluster_id));
  const selectedNode = space.nodes.find((node) => node.node_id === selectedNodeId) || filteredNodes[0];
  const selectedGap = space.gaps.find((gap) => gap.gap_id === selectedGapId) || filteredGaps[0];
  const pipeline = [
    "application space",
    "gap",
    "pseudo-application",
    "boundary evidence",
    "FBS-PM",
    "property envelope",
    "materials",
    "validation"
  ];

  const densityTrace =
    filteredNodes.length > 3
      ? {
          x: filteredNodes.map((node) => node.coordinates?.[0] || 0),
          y: filteredNodes.map((node) => node.coordinates?.[1] || 0),
          type: "histogram2dcontour",
          name: "Application density",
          ncontours: 12,
          showscale: false,
          hoverinfo: "skip",
          contours: { coloring: "heatmap", showlines: false },
          colorscale: [
            [0, "rgba(14,165,165,0)"],
            [0.35, "rgba(14,165,165,0.18)"],
            [0.7, "rgba(47,128,237,0.22)"],
            [1, "rgba(245,158,11,0.26)"]
          ],
          opacity: 0.72
        }
      : undefined;

  const nodeTrace = {
    x: filteredNodes.map((node) => node.coordinates?.[0] || 0),
    y: filteredNodes.map((node) => node.coordinates?.[1] || 0),
    type: "scattergl",
    mode: "markers",
    name: "Application nodes",
    text: filteredNodes.map(
      (node) =>
        `<b>${escapeHtml(node.label)}</b><br>${escapeHtml(node.domain)}<br>${escapeHtml(node.function)}<br>${escapeHtml(
          node.device_type || "device not extracted"
        )}<br>${escapeHtml(node.physical_em_mechanism || "mechanism not extracted")}<br>${node.evidence_count} evidence links`
    ),
    hoverinfo: "text",
    marker: {
      size: filteredNodes.map((node) => Math.max(8, Math.min(22, 7 + node.evidence_count * 2))),
      color: colorMode === "confidence" ? filteredNodes.map((node) => node.confidence) : filteredNodes.map((node) => clusterColor(node.cluster_id)),
      colorscale: colorMode === "confidence" ? "Viridis" : undefined,
      cmin: colorMode === "confidence" ? 0 : undefined,
      cmax: colorMode === "confidence" ? 1 : undefined,
      showscale: colorMode === "confidence",
      colorbar: colorMode === "confidence" ? { title: "confidence", thickness: 10, len: 0.44 } : undefined,
      opacity: 0.86,
      line: {
        color: filteredNodes.map((node) => (node.node_id === selectedNode?.node_id ? "#111827" : "rgba(255,255,255,0.78)")),
        width: filteredNodes.map((node) => (node.node_id === selectedNode?.node_id ? 2 : 1))
      }
    }
  };

  const clusterTrace = {
    x: visibleClusters.map((cluster) => cluster.centroid[0]),
    y: visibleClusters.map((cluster) => cluster.centroid[1]),
    type: "scatter",
    mode: "markers+text",
    name: "Cluster centroids",
    text: visibleClusters.map((cluster) => cluster.label),
    textposition: "top center",
    hoverinfo: "text",
    hovertext: visibleClusters.map((cluster) => `<b>${escapeHtml(cluster.label)}</b><br>${escapeHtml(cluster.summary)}<br>${cluster.evidence_count} evidence links`),
    marker: {
      symbol: "circle-open",
      size: 22,
      color: visibleClusters.map((cluster) => clusterColor(cluster.cluster_id)),
      line: { width: 2 }
    },
    textfont: { size: 11, color: "#334155" }
  };

  const gapTrace = {
    x: filteredGaps.map((gap) => gap.coordinates[0]),
    y: filteredGaps.map((gap) => gap.coordinates[1]),
    type: "scattergl",
    mode: "markers",
    name: "Detected gaps",
    text: filteredGaps.map(
      (gap) =>
        `<b>${escapeHtml(gap.title)}</b><br>Overall gap score ${Math.round(gap.overall_gap_score * 100)}%<br>Novelty ${Math.round(
          gap.novelty_score * 100
        )}%<br>Feasibility ${Math.round(gap.feasibility_score * 100)}%<br>Boundary evidence ${Math.round(
          gap.boundary_evidence_score * 100
        )}%<br>${escapeHtml(gap.pseudo_application_hypotheses[0] || "")}`
    ),
    hoverinfo: "text",
    marker: {
      symbol: "diamond",
      size: filteredGaps.map((gap) => (gap.gap_id === selectedGapId ? 23 : 15 + Math.round(gap.overall_gap_score * 7))),
      color: filteredGaps.map((gap) => (gap.gap_id === selectedGapId ? "#ef6f6c" : "#f59e0b")),
      opacity: 0.92,
      line: { color: "#111827", width: 1 }
    }
  };

  const connectorShapes = filteredGaps.flatMap((gap) =>
    gap.nearby_cluster_ids.slice(0, 3).flatMap((clusterId) => {
      const cluster = clusterById.get(clusterId);
      if (!cluster) return [];
      return [
        {
          type: "line",
          x0: cluster.centroid[0],
          y0: cluster.centroid[1],
          x1: gap.coordinates[0],
          y1: gap.coordinates[1],
          line: { color: gap.gap_id === selectedGapId ? "rgba(239,111,108,0.45)" : "rgba(100,116,139,0.24)", width: gap.gap_id === selectedGapId ? 2 : 1, dash: "dot" }
        }
      ];
    })
  );

  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-line px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold">Electromagnetic Application Space</h2>
            <p className="text-xs text-muted">
              {filteredNodes.length} of {space.build.node_count} nodes, {visibleClusters.length} of {space.build.cluster_count} clusters, {filteredGaps.length} of {space.gaps.length} gaps
              {activeFilterCount ? `, ${activeFilterCount} active filter${activeFilterCount === 1 ? "" : "s"}` : ""}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex rounded border border-line bg-shell p-0.5">
              <button
                className={`focus-ring rounded px-3 py-1.5 text-xs font-medium ${colorMode === "cluster" ? "bg-panel text-ink shadow-sm" : "text-muted"}`}
                onClick={() => setColorMode("cluster")}
                type="button"
              >
                Clusters
              </button>
              <button
                className={`focus-ring rounded px-3 py-1.5 text-xs font-medium ${colorMode === "confidence" ? "bg-panel text-ink shadow-sm" : "text-muted"}`}
                onClick={() => setColorMode("confidence")}
                type="button"
              >
                Confidence
              </button>
            </div>
            <label className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted" aria-hidden />
              <input
                className="focus-ring h-9 w-64 rounded border border-line bg-shell pl-9 pr-3 text-sm"
                placeholder="Search descriptors"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <button className="focus-ring rounded border border-line p-2" onClick={() => setQuery("")} title="Clear search" type="button">
              <RotateCcw className="h-4 w-4" aria-hidden />
            </button>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {pipeline.map((step, index) => (
            <span key={step} className="inline-flex items-center gap-2 text-xs text-muted">
              <span className={`rounded border px-2 py-1 ${index < 4 ? "border-accent/30 bg-accent/10 text-accent" : "border-line bg-shell"}`}>{step}</span>
              {index < pipeline.length - 1 ? <span aria-hidden>{"->"}</span> : null}
            </span>
          ))}
        </div>
      </div>

      <Plot
        data={[densityTrace, nodeTrace, clusterTrace, gapTrace].filter(Boolean) as any}
        layout={
          {
            height: 650,
            margin: { l: 24, r: 24, t: 24, b: 34 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            hovermode: "closest",
            dragmode: "pan",
            shapes: connectorShapes,
            xaxis: { zeroline: false, showgrid: true, gridcolor: "rgba(148,163,184,0.16)", title: "", fixedrange: false },
            yaxis: { zeroline: false, showgrid: true, gridcolor: "rgba(148,163,184,0.16)", title: "", fixedrange: false },
            legend: { orientation: "h", x: 0.02, y: 1.05, bgcolor: "rgba(255,255,255,0.72)" }
          } as any
        }
        config={{ responsive: true, displaylogo: false, modeBarButtonsToAdd: ["toImage"] as any }}
        useResizeHandler
        className="h-[650px] w-full"
        onClick={(event: any) => {
          const point = event.points?.[0];
          if (point?.data?.name === "Detected gaps") {
            const gap = filteredGaps[point.pointIndex];
            onSelectGap?.(gap);
          }
          if (point?.data?.name === "Application nodes") {
            const node = filteredNodes[point.pointIndex];
            setSelectedNodeId(node?.node_id);
          }
        }}
      />

      {(normalizedQuery || activeFilterCount > 0) && !filteredNodes.length && !filteredGaps.length ? (
        <div className="border-t border-line px-4 py-3 text-sm text-muted">No application nodes or gaps match the current search and filters.</div>
      ) : null}

      <div className="grid gap-3 border-t border-line bg-shell/70 p-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_minmax(0,1fr)]">
        <NodeFocus node={selectedNode} />
        <GapFocus gap={selectedGap} />
        <ClusterLegend clusters={visibleClusters.slice(0, 5)} />
      </div>
    </section>
  );
}

function NodeFocus({ node }: { node?: ApplicationNode }) {
  if (!node) {
    return <FocusPanel title="Selected Node" value="No node selected" />;
  }
  return (
    <FocusPanel title="Selected Node" value={node.label}>
      <div className="mt-2 grid gap-2 text-xs text-muted sm:grid-cols-2">
        <span>{node.domain}</span>
        <span>{node.device_type || "device not extracted"}</span>
        <span>{node.physical_em_mechanism || "mechanism not extracted"}</span>
        <span>{Math.round(node.confidence * 100)}% confidence</span>
      </div>
    </FocusPanel>
  );
}

function GapFocus({ gap }: { gap?: Gap }) {
  if (!gap) {
    return <FocusPanel title="Highest-Value Gap" value="No gap detected" />;
  }
  return (
    <FocusPanel title="Selected Gap" value={gap.title}>
      <div className="mt-2 flex flex-wrap gap-2 text-xs">
        <Pill label={`gap ${Math.round(gap.overall_gap_score * 100)}%`} />
        <Pill label={`novelty ${Math.round(gap.novelty_score * 100)}%`} />
        <Pill label={`MatterGen ${Math.round(gap.mattergen_compatibility_score * 100)}%`} />
      </div>
    </FocusPanel>
  );
}

function ClusterLegend({ clusters }: { clusters: ApplicationSpace["clusters"] }) {
  return (
    <FocusPanel title="Visible Clusters" value={`${clusters.length} labelled regions`}>
      <div className="mt-2 grid gap-1.5">
        {clusters.map((cluster) => (
          <div key={cluster.cluster_id} className="flex min-w-0 items-center gap-2 text-xs text-muted">
            <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: clusterColor(cluster.cluster_id) }} />
            <span className="truncate">{cluster.label}</span>
          </div>
        ))}
      </div>
    </FocusPanel>
  );
}

function FocusPanel({ title, value, children }: { title: string; value: string; children?: ReactNode }) {
  return (
    <div className="rounded border border-line bg-panel p-3">
      <div className="text-xs uppercase text-muted">{title}</div>
      <div className="mt-1 text-sm font-semibold">{value}</div>
      {children}
    </div>
  );
}

function Pill({ label }: { label: string }) {
  return <span className="rounded border border-line bg-shell px-2 py-1 text-muted">{label}</span>;
}

function clusterColor(cluster?: string) {
  const palette = ["#0ea5a5", "#2f80ed", "#f59e0b", "#ef6f6c", "#64748b", "#22a06b", "#8b5cf6", "#f97316", "#14b8a6", "#6366f1"];
  const index = Math.abs((cluster || "0").split("").reduce((acc, char) => acc + char.charCodeAt(0), 0)) % palette.length;
  return palette[index];
}

function matchesNodeFilters(node: ApplicationNode, filters: ApplicationSpaceFilters) {
  const minEvidence = Number(filters.minEvidence.replace("+", "") || 0);
  return (
    matches(filters.domain, node.domain) &&
    matches(filters.frequency, node.operating_frequency_or_wavelength) &&
    matches(filters.mechanism, node.physical_em_mechanism) &&
    matches(filters.deviceType, node.device_type) &&
    matches(filters.materialClass, node.material_class) &&
    (!filters.year || String(node.year || "") === filters.year) &&
    (!minEvidence || node.evidence_count >= minEvidence)
  );
}

function matches(filterValue: string, nodeValue?: string | null) {
  return !filterValue || nodeValue === filterValue;
}

function nodeText(node: ApplicationSpace["nodes"][number]) {
  return [
    node.label,
    node.application_text,
    node.domain,
    node.function,
    node.operating_frequency_or_wavelength,
    node.device_type,
    node.physical_em_mechanism,
    node.material_class,
    ...node.material_names,
    ...node.em_property_requirements
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function gapText(gap: Gap) {
  return [
    gap.title,
    gap.explanation,
    ...gap.nearby_cluster_ids,
    ...gap.pseudo_application_hypotheses,
    ...Object.values(gap.boundary_descriptors).flat()
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, (char) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    };
    return entities[char] || char;
  });
}
