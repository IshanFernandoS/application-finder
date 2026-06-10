"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import type { ReactNode } from "react";
import { useState } from "react";
import {
  ArrowRight,
  Boxes,
  Crosshair,
  Database,
  FlaskConical,
  GitBranch,
  Layers3,
  LocateFixed,
  RadioTower,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  Workflow
} from "lucide-react";
import type { ApplicationCluster, ApplicationNode, ApplicationSpace, Gap } from "@/lib/types";
import { EmptyState } from "./EmptyState";
import type { ApplicationSpaceFilters } from "./SidebarFilters";

const Plot = dynamic<any>(() => import("react-plotly.js"), { ssr: false });

type ColorMode = "cluster" | "confidence" | "evidence" | "recency";
type ViewMode = "atlas" | "gaps" | "evidence" | "materials";

const viewModes: Array<{ mode: ViewMode; label: string; icon: typeof RadioTower }> = [
  { mode: "atlas", label: "Atlas", icon: RadioTower },
  { mode: "gaps", label: "Gaps", icon: Target },
  { mode: "evidence", label: "Evidence", icon: Database },
  { mode: "materials", label: "Materials", icon: FlaskConical }
];

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
  const [viewMode, setViewMode] = useState<ViewMode>("atlas");
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
  const rankedGaps = [...filteredGaps].sort((a, b) => b.overall_gap_score - a.overall_gap_score);
  const clusterById = new Map(space.clusters.map((cluster) => [cluster.cluster_id, cluster]));
  const nodeById = new Map(space.nodes.map((node) => [node.node_id, node]));
  const visibleClusters = space.clusters.filter((cluster) => visibleClusterIds.has(cluster.cluster_id));
  const selectedNode = space.nodes.find((node) => node.node_id === selectedNodeId) || filteredNodes[0];
  const selectedGap = rankedGaps.find((gap) => gap.gap_id === selectedGapId) || rankedGaps[0];
  const selectedBoundaryNodes = selectedGap?.nearby_application_ids.map((id) => nodeById.get(id)).filter((node): node is ApplicationNode => Boolean(node)) || [];
  const selectedBoundaryClusters = selectedGap?.nearby_cluster_ids.map((id) => clusterById.get(id)).filter((cluster): cluster is ApplicationCluster => Boolean(cluster)) || [];
  const materialNames = unique(selectedBoundaryNodes.flatMap((node) => node.material_names || [])).slice(0, 7);
  const propertyTerms = selectedGap ? unique(Object.values(selectedGap.boundary_descriptors || {}).flat()).slice(0, 7) : [];
  const confidenceAverage = average(filteredNodes.map((node) => node.confidence));
  const evidenceTotal = filteredNodes.reduce((total, node) => total + node.evidence_count, 0);
  const mostRecentYear = Math.max(...filteredNodes.map((node) => node.year || 0), 0);
  const xRange = coordinateRange([
    ...filteredNodes.map((node) => node.coordinates?.[0] || 0),
    ...filteredGaps.map((gap) => gap.coordinates[0]),
    ...visibleClusters.map((cluster) => cluster.centroid[0])
  ]);
  const yRange = coordinateRange([
    ...filteredNodes.map((node) => node.coordinates?.[1] || 0),
    ...filteredGaps.map((gap) => gap.coordinates[1]),
    ...visibleClusters.map((cluster) => cluster.centroid[1])
  ]);

  const regionTraces = visibleClusters.flatMap((cluster) => clusterRegionTrace(cluster, filteredNodes));
  const densityTrace =
    filteredNodes.length > 3
      ? {
          x: filteredNodes.map((node) => node.coordinates?.[0] || 0),
          y: filteredNodes.map((node) => node.coordinates?.[1] || 0),
          type: "histogram2dcontour",
          name: "application density",
          ncontours: 14,
          showscale: false,
          hoverinfo: "skip",
          contours: { coloring: "heatmap", showlines: false },
          colorscale: [
            [0, "rgba(14,165,165,0)"],
            [0.32, "rgba(14,165,165,0.16)"],
            [0.68, "rgba(47,128,237,0.2)"],
            [1, "rgba(245,158,11,0.24)"]
          ],
          opacity: viewMode === "atlas" ? 0.84 : 0.56
        }
      : undefined;

  const nodeTrace = {
    x: filteredNodes.map((node) => node.coordinates?.[0] || 0),
    y: filteredNodes.map((node) => node.coordinates?.[1] || 0),
    type: "scattergl",
    mode: "markers",
    name: "application descriptors",
    text: filteredNodes.map((node) => nodeHoverText(node)),
    hoverinfo: "text",
    marker: {
      size: filteredNodes.map((node) => nodeMarkerSize(node, viewMode)),
      color: markerColors(filteredNodes, colorMode),
      colorscale: colorMode === "cluster" ? undefined : colorScaleFor(colorMode),
      cmin: colorMode === "confidence" ? 0 : undefined,
      cmax: colorMode === "confidence" ? 1 : undefined,
      showscale: colorMode !== "cluster",
      colorbar: colorMode !== "cluster" ? { title: colorBarTitle(colorMode), thickness: 10, len: 0.38 } : undefined,
      opacity: viewMode === "gaps" ? 0.58 : 0.88,
      line: {
        color: filteredNodes.map((node) => (node.node_id === selectedNode?.node_id ? "#0f172a" : "rgba(255,255,255,0.78)")),
        width: filteredNodes.map((node) => (node.node_id === selectedNode?.node_id ? 2.5 : 1))
      }
    }
  };

  const clusterTrace = {
    x: visibleClusters.map((cluster) => cluster.centroid[0]),
    y: visibleClusters.map((cluster) => cluster.centroid[1]),
    type: "scatter",
    mode: "markers+text",
    name: "cluster anchors",
    text: visibleClusters.map((cluster) => cluster.label),
    textposition: "top center",
    hoverinfo: "text",
    hovertext: visibleClusters.map((cluster) => clusterHoverText(cluster)),
    marker: {
      symbol: "circle-open",
      size: visibleClusters.map((cluster) => (selectedGap?.nearby_cluster_ids.includes(cluster.cluster_id) ? 30 : 22)),
      color: visibleClusters.map((cluster) => clusterColor(cluster.cluster_id)),
      line: { width: visibleClusters.map((cluster) => (selectedGap?.nearby_cluster_ids.includes(cluster.cluster_id) ? 3 : 2)) }
    },
    textfont: { size: 11, color: "#334155" }
  };

  const gapTrace = {
    x: filteredGaps.map((gap) => gap.coordinates[0]),
    y: filteredGaps.map((gap) => gap.coordinates[1]),
    type: "scattergl",
    mode: "markers",
    name: "application gaps",
    text: filteredGaps.map((gap) => gapHoverText(gap)),
    hoverinfo: "text",
    marker: {
      symbol: "diamond",
      size: filteredGaps.map((gap) => (gap.gap_id === selectedGap?.gap_id ? 26 : 15 + Math.round(gap.overall_gap_score * 9))),
      color: filteredGaps.map((gap) => gapColor(gap)),
      opacity: viewMode === "atlas" ? 0.9 : 0.98,
      line: { color: "#0f172a", width: filteredGaps.map((gap) => (gap.gap_id === selectedGap?.gap_id ? 2 : 1)) }
    }
  };

  const selectedBoundaryTrace =
    selectedBoundaryNodes.length > 0
      ? {
          x: selectedBoundaryNodes.map((node) => node.coordinates?.[0] || 0),
          y: selectedBoundaryNodes.map((node) => node.coordinates?.[1] || 0),
          type: "scatter",
          mode: "markers",
          name: "boundary evidence",
          text: selectedBoundaryNodes.map((node) => nodeHoverText(node)),
          hoverinfo: "text",
          marker: {
            symbol: "circle-open",
            size: selectedBoundaryNodes.map((node) => Math.max(18, nodeMarkerSize(node, "evidence") + 5)),
            color: "#22a06b",
            line: { color: "#22a06b", width: 2.4 }
          }
        }
      : undefined;

  const selectedGapTrace =
    selectedGap
      ? {
          x: [selectedGap.coordinates[0]],
          y: [selectedGap.coordinates[1]],
          type: "scatter",
          mode: "markers",
          name: "selected opportunity",
          hoverinfo: "skip",
          marker: {
            symbol: "diamond-open",
            size: 38,
            color: "#ef6f6c",
            line: { color: "#ef6f6c", width: 3 }
          },
          showlegend: false
        }
      : undefined;
  const plotData = [densityTrace, ...regionTraces, nodeTrace, clusterTrace, gapTrace, selectedBoundaryTrace, selectedGapTrace].filter(Boolean);

  const connectorShapes = selectedGap
    ? selectedGap.nearby_cluster_ids.flatMap((clusterId) => {
        const cluster = clusterById.get(clusterId);
        if (!cluster) return [];
        return [
          {
            type: "line",
            x0: cluster.centroid[0],
            y0: cluster.centroid[1],
            x1: selectedGap.coordinates[0],
            y1: selectedGap.coordinates[1],
            line: { color: "rgba(239,111,108,0.48)", width: 2, dash: "dot" }
          }
        ];
      })
    : [];

  return (
    <section className="panel overflow-hidden">
      <header className="border-b border-line bg-panel px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-accent">
              <Sparkles className="h-4 w-4" aria-hidden />
              Electromagnetic Application Space
            </div>
            <h2 className="mt-2 text-2xl font-semibold">Application Space Atlas</h2>
            <p className="mt-2 text-sm leading-6 text-muted">
              {filteredNodes.length} of {space.build.node_count} descriptors, {visibleClusters.length} of {space.build.cluster_count} clusters, {filteredGaps.length} of {space.gaps.length} gaps
              {activeFilterCount ? `, ${activeFilterCount} active filter${activeFilterCount === 1 ? "" : "s"}` : ""}.
            </p>
          </div>
          <div className="grid min-w-[280px] grid-cols-3 gap-2">
            <AtlasMetric label="Coverage" value={String(filteredNodes.length)} detail="visible nodes" />
            <AtlasMetric label="Evidence" value={String(evidenceTotal)} detail="links" />
            <AtlasMetric label="Confidence" value={`${Math.round(confidenceAverage * 100)}%`} detail={mostRecentYear ? `latest ${mostRecentYear}` : "scored"} />
          </div>
        </div>

        <div className="mt-4 grid gap-3 xl:grid-cols-[minmax(0,1fr)_260px_310px]">
          <div className="flex flex-wrap items-center gap-2">
            {viewModes.map((item) => {
              const Icon = item.icon;
              const active = viewMode === item.mode;
              return (
                <button
                  key={item.mode}
                  className={`focus-ring inline-flex h-9 items-center gap-2 rounded border px-3 text-xs font-medium ${
                    active ? "border-accent bg-accent text-white" : "border-line bg-shell text-muted hover:text-ink"
                  }`}
                  onClick={() => setViewMode(item.mode)}
                  type="button"
                >
                  <Icon className="h-4 w-4" aria-hidden />
                  {item.label}
                </button>
              );
            })}
          </div>
          <label className="grid gap-1 text-xs text-muted">
            Color lens
            <select className="focus-ring h-9 rounded border border-line bg-shell px-2 text-sm text-ink" value={colorMode} onChange={(event) => setColorMode(event.target.value as ColorMode)}>
              <option value="cluster">Semantic cluster</option>
              <option value="confidence">Descriptor confidence</option>
              <option value="evidence">Evidence strength</option>
              <option value="recency">Publication recency</option>
            </select>
          </label>
          <div className="flex items-end gap-2">
            <label className="relative min-w-0 flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted" aria-hidden />
              <input
                className="focus-ring h-9 w-full rounded border border-line bg-shell pl-9 pr-3 text-sm"
                placeholder="Search descriptors, mechanisms, materials"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <button className="focus-ring h-9 rounded border border-line p-2 text-muted hover:text-ink" onClick={() => setQuery("")} title="Clear search" type="button">
              <RotateCcw className="h-4 w-4" aria-hidden />
            </button>
          </div>
        </div>
      </header>

      <div className="grid xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="min-w-0 border-b border-line xl:border-b-0 xl:border-r">
          <Plot
            data={plotData as any}
            layout={
              {
                height: 720,
                margin: { l: 34, r: 24, t: 28, b: 40 },
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(248,250,252,0.68)",
                hovermode: "closest",
                dragmode: "pan",
                shapes: connectorShapes,
                xaxis: { range: xRange, zeroline: false, showgrid: true, gridcolor: "rgba(148,163,184,0.16)", title: "", fixedrange: false, tickformat: ".2f" },
                yaxis: { range: yRange, zeroline: false, showgrid: true, gridcolor: "rgba(148,163,184,0.16)", title: "", fixedrange: false, tickformat: ".2f" },
                legend: { orientation: "h", x: 0.02, y: 1.06, bgcolor: "rgba(255,255,255,0.78)", bordercolor: "rgba(203,213,225,0.8)", borderwidth: 1 },
                annotations: selectedGap
                  ? [
                      {
                        x: selectedGap.coordinates[0],
                        y: selectedGap.coordinates[1],
                        text: "selected gap",
                        showarrow: true,
                        arrowhead: 3,
                        ax: 30,
                        ay: -30,
                        font: { size: 11, color: "#ef6f6c" },
                        arrowcolor: "#ef6f6c"
                      }
                    ]
                  : []
              } as any
            }
            config={{ responsive: true, displaylogo: false, modeBarButtonsToAdd: ["toImage"] as any }}
            useResizeHandler
            className="h-[720px] w-full"
            onClick={(event: any) => {
              const point = event.points?.[0];
              if (point?.data?.name === "application gaps") {
                const gap = filteredGaps[point.pointIndex];
                onSelectGap?.(gap);
              }
              if (point?.data?.name === "application descriptors") {
                const node = filteredNodes[point.pointIndex];
                setSelectedNodeId(node?.node_id);
              }
            }}
          />
          {(normalizedQuery || activeFilterCount > 0) && !filteredNodes.length && !filteredGaps.length ? (
            <div className="border-t border-line px-4 py-3 text-sm text-muted">No application nodes or gaps match the current search and filters.</div>
          ) : null}
        </div>

        <aside className="grid content-start gap-4 bg-shell/70 p-4">
          <OpportunityStack gaps={rankedGaps.slice(0, 7)} selectedGapId={selectedGap?.gap_id} onSelectGap={onSelectGap} />
          <NodeFocus node={selectedNode} />
          <ClusterFocus clusters={selectedBoundaryClusters.length ? selectedBoundaryClusters : visibleClusters.slice(0, 4)} />
        </aside>
      </div>

      <ReasoningRail gap={selectedGap} boundaryNodes={selectedBoundaryNodes} materials={materialNames} propertyTerms={propertyTerms} />
    </section>
  );
}

function AtlasMetric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded border border-line bg-shell p-3">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 text-lg font-semibold">{value}</div>
      <div className="mt-0.5 text-[11px] text-muted">{detail}</div>
    </div>
  );
}

function OpportunityStack({ gaps, selectedGapId, onSelectGap }: { gaps: Gap[]; selectedGapId?: string; onSelectGap?: (gap: Gap) => void }) {
  return (
    <section className="rounded border border-line bg-panel p-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Crosshair className="h-4 w-4 text-coral" aria-hidden />
          Opportunity Stack
        </div>
        <span className="rounded border border-line bg-shell px-2 py-1 text-xs text-muted">{gaps.length} ranked</span>
      </div>
      <div className="mt-3 grid gap-2">
        {gaps.map((gap, index) => {
          const active = gap.gap_id === selectedGapId;
          return (
            <button
              key={gap.gap_id}
              className={`focus-ring rounded border p-3 text-left transition ${
                active ? "border-coral bg-coral/10" : "border-line bg-shell hover:border-accent hover:bg-panel"
              }`}
              onClick={() => onSelectGap?.(gap)}
              type="button"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="text-[11px] font-medium uppercase text-muted">Rank {index + 1}</div>
                  <div className="mt-1 line-clamp-2 text-sm font-semibold">{gap.title}</div>
                </div>
                <span className="rounded bg-panel px-2 py-1 text-xs font-semibold">{Math.round(gap.overall_gap_score * 100)}%</span>
              </div>
              <div className="mt-3 grid gap-1.5">
                <ScoreBar label="novelty" value={gap.novelty_score} />
                <ScoreBar label="feasible" value={gap.feasibility_score} />
                <ScoreBar label="evidence" value={gap.boundary_evidence_score} />
              </div>
            </button>
          );
        })}
        {!gaps.length ? <div className="rounded border border-line bg-shell p-3 text-sm text-muted">No visible gaps under the current filters.</div> : null}
      </div>
    </section>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="grid grid-cols-[68px_minmax(0,1fr)_36px] items-center gap-2 text-[11px] text-muted">
      <span>{label}</span>
      <span className="h-1.5 overflow-hidden rounded bg-line">
        <span className="block h-full rounded bg-accent" style={{ width: `${pct}%` }} />
      </span>
      <span className="text-right">{pct}%</span>
    </div>
  );
}

function NodeFocus({ node }: { node?: ApplicationNode }) {
  if (!node) {
    return <FocusPanel icon={LocateFixed} title="Descriptor Focus" value="No node selected" />;
  }
  return (
    <FocusPanel icon={LocateFixed} title="Descriptor Focus" value={node.label}>
      <div className="mt-3 grid gap-2 text-xs text-muted">
        <MetaLine label="Domain" value={node.domain} />
        <MetaLine label="Device" value={node.device_type || "device not extracted"} />
        <MetaLine label="Mechanism" value={node.physical_em_mechanism || "mechanism not extracted"} />
        <MetaLine label="Confidence" value={`${Math.round(node.confidence * 100)}%`} />
      </div>
    </FocusPanel>
  );
}

function ClusterFocus({ clusters }: { clusters: ApplicationCluster[] }) {
  return (
    <FocusPanel icon={Layers3} title="Boundary Regions" value={`${clusters.length} semantic regions`}>
      <div className="mt-3 grid gap-2">
        {clusters.slice(0, 5).map((cluster) => (
          <div key={cluster.cluster_id} className="rounded border border-line bg-shell p-2">
            <div className="flex min-w-0 items-center gap-2 text-xs font-medium">
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: clusterColor(cluster.cluster_id) }} />
              <span className="truncate">{cluster.label}</span>
            </div>
            <div className="mt-1 line-clamp-2 text-[11px] text-muted">{cluster.summary}</div>
          </div>
        ))}
      </div>
    </FocusPanel>
  );
}

function ReasoningRail({
  gap,
  boundaryNodes,
  materials,
  propertyTerms
}: {
  gap?: Gap;
  boundaryNodes: ApplicationNode[];
  materials: string[];
  propertyTerms: string[];
}) {
  const steps = [
    {
      title: "Application Space",
      icon: RadioTower,
      value: gap ? `${gap.nearby_cluster_ids.length} boundary clusters` : "build atlas",
      detail: "semantic EM descriptor topology"
    },
    {
      title: "Gap",
      icon: Target,
      value: gap ? `${Math.round(gap.overall_gap_score * 100)}% opportunity` : "no gap selected",
      detail: gap?.title || "detect gaps from the space"
    },
    {
      title: "Pseudo-Application",
      icon: Sparkles,
      value: `${gap?.pseudo_application_hypotheses.length || 0} hypotheses`,
      detail: gap?.pseudo_application_hypotheses[0] || "candidate use cases appear here"
    },
    {
      title: "Boundary Evidence",
      icon: Database,
      value: `${boundaryNodes.length} descriptors`,
      detail: propertyTerms[0] || "nearest evidence and descriptors"
    },
    {
      title: "FBS-PM",
      icon: GitBranch,
      value: "pathway reasoning",
      detail: "function, behavior, structure, property, material"
    },
    {
      title: "EM Envelope",
      icon: Workflow,
      value: `${propertyTerms.length} property cues`,
      detail: propertyTerms.slice(0, 2).join("; ") || "extract property requirements"
    },
    {
      title: "Known Candidates",
      icon: Boxes,
      value: `${materials.length} materials`,
      detail: materials.slice(0, 3).join(", ") || "rank literature-supported candidates"
    },
    {
      title: "MatterGen",
      icon: FlaskConical,
      value: "constraint handoff",
      detail: "generate structures after FBS-PM constraints"
    },
    {
      title: "Validation",
      icon: ShieldCheck,
      value: gap ? `${Math.round(gap.feasibility_score * 100)}% feasible` : "unstarted",
      detail: "simulation, DFT, evidence checks, report"
    }
  ];

  return (
    <section className="border-t border-line bg-panel p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">Gap-to-Material Reasoning Path</h3>
          <div className="mt-1 text-xs text-muted">Application-space-guided inverse design chain</div>
        </div>
        {gap ? (
          <Link className="focus-ring inline-flex items-center gap-2 rounded bg-accent px-3 py-2 text-xs font-medium text-white" href={`/gaps/${gap.gap_id}`}>
            Open gap workspace
            <ArrowRight className="h-3.5 w-3.5" aria-hidden />
          </Link>
        ) : null}
      </div>
      <div className="grid gap-2 md:grid-cols-3 xl:grid-cols-9">
        {steps.map((step, index) => {
          const Icon = step.icon;
          return (
            <article key={step.title} className="relative min-h-[138px] rounded border border-line bg-shell p-3">
              <div className="flex items-center justify-between gap-2">
                <Icon className="h-4 w-4 text-accent" aria-hidden />
                <span className="text-[11px] text-muted">{String(index + 1).padStart(2, "0")}</span>
              </div>
              <div className="mt-3 text-xs font-semibold">{step.title}</div>
              <div className="mt-1 text-[11px] text-accent">{step.value}</div>
              <p className="mt-2 line-clamp-3 text-[11px] leading-5 text-muted">{step.detail}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function FocusPanel({ icon: Icon, title, value, children }: { icon: typeof RadioTower; title: string; value: string; children?: ReactNode }) {
  return (
    <section className="rounded border border-line bg-panel p-4">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <Icon className="h-4 w-4 text-accent" aria-hidden />
        {title}
      </div>
      <div className="mt-2 line-clamp-3 text-sm font-semibold">{value}</div>
      {children}
    </section>
  );
}

function MetaLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex min-w-0 items-center justify-between gap-3">
      <span>{label}</span>
      <span className="truncate text-right font-medium text-ink">{value}</span>
    </div>
  );
}

function clusterRegionTrace(cluster: ApplicationCluster, nodes: ApplicationNode[]) {
  const clusterNodes = nodes.filter((node) => node.cluster_id === cluster.cluster_id && node.coordinates);
  if (clusterNodes.length < 3) {
    return [];
  }
  const xs = clusterNodes.map((node) => node.coordinates?.[0] || 0);
  const ys = clusterNodes.map((node) => node.coordinates?.[1] || 0);
  const centerX = average(xs);
  const centerY = average(ys);
  const radiusX = Math.max(0.15, standardDeviation(xs) * 2.4);
  const radiusY = Math.max(0.15, standardDeviation(ys) * 2.4);
  const color = clusterColor(cluster.cluster_id);
  const points = Array.from({ length: 40 }, (_, index) => {
    const angle = (Math.PI * 2 * index) / 39;
    return [centerX + Math.cos(angle) * radiusX, centerY + Math.sin(angle) * radiusY];
  });
  return [
    {
      x: points.map((point) => point[0]),
      y: points.map((point) => point[1]),
      type: "scatter",
      mode: "lines",
      name: `${cluster.label} region`,
      hoverinfo: "skip",
      fill: "toself",
      fillcolor: hexToRgba(color, 0.08),
      line: { color: hexToRgba(color, 0.26), width: 1.4 },
      showlegend: false
    }
  ];
}

function nodeMarkerSize(node: ApplicationNode, viewMode: ViewMode) {
  const evidenceBoost = Math.min(14, node.evidence_count * 2);
  const confidenceBoost = Math.round((node.confidence || 0) * 7);
  if (viewMode === "evidence") return Math.max(9, Math.min(28, 8 + evidenceBoost));
  if (viewMode === "materials") return Math.max(9, Math.min(26, 9 + (node.material_names?.length || 0) * 3));
  return Math.max(8, Math.min(24, 8 + confidenceBoost + Math.min(8, node.evidence_count * 1.4)));
}

function markerColors(nodes: ApplicationNode[], colorMode: ColorMode) {
  if (colorMode === "confidence") return nodes.map((node) => node.confidence);
  if (colorMode === "evidence") return nodes.map((node) => node.evidence_count);
  if (colorMode === "recency") return nodes.map((node) => node.year || 0);
  return nodes.map((node) => clusterColor(node.cluster_id));
}

function colorScaleFor(colorMode: ColorMode) {
  if (colorMode === "confidence") return "Viridis";
  if (colorMode === "evidence") return "YlGnBu";
  return "Portland";
}

function colorBarTitle(colorMode: ColorMode) {
  if (colorMode === "confidence") return "confidence";
  if (colorMode === "evidence") return "evidence";
  return "year";
}

function gapColor(gap: Gap) {
  if (gap.overall_gap_score >= 0.72) return "#ef6f6c";
  if (gap.overall_gap_score >= 0.5) return "#f59e0b";
  return "#64748b";
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

function nodeHoverText(node: ApplicationNode) {
  return [
    `<b>${escapeHtml(node.label)}</b>`,
    escapeHtml(node.domain),
    escapeHtml(node.function),
    escapeHtml(node.device_type || "device not extracted"),
    escapeHtml(node.physical_em_mechanism || "mechanism not extracted"),
    `${node.evidence_count} evidence links`,
    `${Math.round(node.confidence * 100)}% confidence`
  ].join("<br>");
}

function clusterHoverText(cluster: ApplicationCluster) {
  return [`<b>${escapeHtml(cluster.label)}</b>`, escapeHtml(cluster.summary), `${cluster.evidence_count} evidence links`].join("<br>");
}

function gapHoverText(gap: Gap) {
  return [
    `<b>${escapeHtml(gap.title)}</b>`,
    `Overall gap score ${Math.round(gap.overall_gap_score * 100)}%`,
    `Novelty ${Math.round(gap.novelty_score * 100)}%`,
    `Feasibility ${Math.round(gap.feasibility_score * 100)}%`,
    `Boundary evidence ${Math.round(gap.boundary_evidence_score * 100)}%`,
    escapeHtml(gap.pseudo_application_hypotheses[0] || "")
  ].join("<br>");
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

function unique(values: Array<string | undefined | null>) {
  return Array.from(new Set(values.map((value) => value?.trim()).filter((value): value is string => Boolean(value))));
}

function average(values: number[]) {
  if (!values.length) return 0;
  return values.reduce((total, value) => total + value, 0) / values.length;
}

function standardDeviation(values: number[]) {
  if (values.length < 2) return 0.16;
  const mean = average(values);
  return Math.sqrt(average(values.map((value) => Math.pow(value - mean, 2))));
}

function coordinateRange(values: number[]) {
  const finite = values.filter((value) => Number.isFinite(value));
  if (!finite.length) return [-1, 1];
  const min = Math.min(...finite);
  const max = Math.max(...finite);
  const span = max - min;
  const padding = span < 0.05 ? 0.8 : Math.max(span * 0.18, 0.18);
  return [min - padding, max + padding];
}

function hexToRgba(hex: string, alpha: number) {
  const raw = hex.replace("#", "");
  const r = parseInt(raw.slice(0, 2), 16);
  const g = parseInt(raw.slice(2, 4), 16);
  const b = parseInt(raw.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}
