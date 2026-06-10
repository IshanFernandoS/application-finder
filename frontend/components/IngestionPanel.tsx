"use client";

import { useEffect, useState } from "react";
import { CheckSquare, ExternalLink, Loader2, PlusCircle, Search, Square, UploadCloud } from "lucide-react";
import { apiGet, apiPost, apiUpload } from "@/lib/api";
import type { ApplicationNode, IngestionStatus, LiteratureIngestAndExtractSummary, LiteratureIngestSummary, LiteratureResult } from "@/lib/types";

const DESCRIPTOR_BATCH_SIZE = 5;
const DESCRIPTOR_CHUNKS_PER_PAPER = 5;
const MAX_DESCRIPTOR_EXTRACTION = 100;
const MAX_RECENT_DESCRIPTOR_DISPLAY = 25;
const INGESTION_STORAGE_KEY = "application-finder.ingestion-workspace.v1";

interface PersistedIngestionState {
  query?: string;
  limit?: number;
  results?: LiteratureResult[];
  selectedKeys?: string[];
  recentNodes?: ApplicationNode[];
}

export function IngestionPanel({ initialStatus }: { initialStatus?: IngestionStatus }) {
  const [query, setQuery] = useState("electromagnetic metamaterial inverse design high permittivity low loss");
  const [limit, setLimit] = useState(20);
  const [results, setResults] = useState<LiteratureResult[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [recentNodes, setRecentNodes] = useState<ApplicationNode[]>([]);
  const [status, setStatus] = useState<IngestionStatus | undefined>(initialStatus);
  const [busy, setBusy] = useState<string | undefined>();
  const [message, setMessage] = useState<string | undefined>();
  const [error, setError] = useState<string | undefined>();
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const restored = readPersistedIngestionState();
    if (restored) {
      if (typeof restored.query === "string") {
        setQuery(restored.query);
      }
      if (typeof restored.limit === "number") {
        setLimit(Math.max(5, Math.min(restored.limit, 200)));
      }
      if (Array.isArray(restored.results)) {
        setResults(restored.results.map(normalizeLiteratureResult));
      }
      if (Array.isArray(restored.selectedKeys)) {
        setSelected(new Set(restored.selectedKeys));
      }
      if (Array.isArray(restored.recentNodes)) {
        setRecentNodes(restored.recentNodes.slice(0, MAX_RECENT_DESCRIPTOR_DISPLAY));
      }
    }
    setHydrated(true);
    void refreshRecentDescriptors();
    void refreshStatus().catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!hydrated) {
      return;
    }
    persistIngestionState({
      query,
      limit,
      results: results.map(pruneLiteratureResultForStorage),
      selectedKeys: Array.from(selected),
      recentNodes: recentNodes.slice(0, MAX_RECENT_DESCRIPTOR_DISPLAY)
    });
  }, [hydrated, limit, query, recentNodes, results, selected]);

  async function runAction<T>(name: string, action: () => Promise<T>, onSuccess?: (result: T) => void) {
    setBusy(name);
    setError(undefined);
    setMessage(undefined);
    try {
      const result = await action();
      onSuccess?.(result);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusy(undefined);
    }
  }

  async function searchLiterature() {
    const searchLimit = Math.max(5, Math.min(limit, 200));
    const params = new URLSearchParams({ query: query.trim(), limit: String(searchLimit) });
    await runAction(
      "search",
      () => apiPost<LiteratureResult[]>(`/ingest/public-search?${params.toString()}`),
      (items) => {
        const normalized = items.map(normalizeLiteratureResult);
        setResults(normalized);
        setSelected(new Set());
        setMessage(`${normalized.length} papers found`);
      }
    );
  }

  async function ingestSelected(extractDescriptors = false) {
    const selectedResults = selectedLiteratureResults(results, selected);
    const actionName = extractDescriptors ? "ingest-extract-selected" : "ingest-selected";
    await runAction(
      actionName,
      async () => {
        const directResult = extractDescriptors ? await ingestAndExtractResults(selectedResults) : undefined;
        const summary = directResult?.ingestion || (await ingestResults(selectedResults));
        const nodes = directResult?.application_nodes || [];
        const latestStatus = await apiGet<IngestionStatus>("/ingest/status").catch(() => undefined);
        return { summary, nodes, latestStatus };
      },
      ({ summary, nodes, latestStatus }) => {
        setMessage(
          extractDescriptors
            ? `${summary.documents_added} papers ingested; ${nodes.length} descriptors extracted`
            : `${summary.documents_added} papers and ${summary.evidence_chunks_added} evidence chunks added`
        );
        setStatus(
          latestStatus || {
            documents: summary.documents,
            evidence_chunks: summary.evidence_chunks,
            application_nodes: status?.application_nodes
          }
        );
        rememberExtractedNodes(nodes);
        setSelected(new Set());
      }
    );
  }

  async function ingestSingleResult(item: LiteratureResult) {
    const key = resultKey(item);
    await runAction(
      `ingest-extract-result:${key}`,
      async () => {
        const result = await ingestAndExtractResults([item]);
        const latestStatus = await apiGet<IngestionStatus>("/ingest/status").catch(() => undefined);
        return { result, latestStatus };
      },
      ({ result, latestStatus }) => {
        setMessage(`Paper processed; ${result.application_nodes.length} descriptors extracted`);
        setStatus(
          latestStatus || {
            documents: result.ingestion.documents,
            evidence_chunks: result.ingestion.evidence_chunks,
            application_nodes: status?.application_nodes
          }
        );
        rememberExtractedNodes(result.application_nodes);
        setSelected((current) => {
          const next = new Set(current);
          next.delete(key);
          return next;
        });
      }
    );
  }

  async function refreshStatus() {
    const nextStatus = await apiGet<IngestionStatus>("/ingest/status");
    setStatus(nextStatus);
    return nextStatus;
  }

  async function refreshRecentDescriptors() {
    try {
      const nodes = await apiGet<ApplicationNode[]>("/ingest/descriptors?scope_id=electromagnetic_functional_materials&limit=25");
      setRecentNodes(nodes.slice(0, MAX_RECENT_DESCRIPTOR_DISPLAY));
      return nodes;
    } catch {
      return [];
    }
  }

  function rememberExtractedNodes(nodes: ApplicationNode[]) {
    if (!nodes.length) {
      return;
    }
    setRecentNodes((current) => mergeApplicationNodes(nodes, current).slice(0, MAX_RECENT_DESCRIPTOR_DISPLAY));
  }

  function toggleResult(item: LiteratureResult) {
    const key = resultKey(item);
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  const selectedCount = selectedLiteratureResults(results, selected).length;
  const selectableCount = results.filter((item) => !isFailure(item)).length;

  return (
    <section className="panel grid gap-5 p-5">
      <div>
        <h2 className="text-base font-semibold">Literature Ingestion</h2>
        <p className="mt-2 text-sm text-muted">Local files, Zotero exports, open full text when available, public scholarly metadata, and descriptor extraction feed the evidence corpus.</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          className="focus-ring inline-flex items-center gap-2 rounded bg-accent px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
          disabled={Boolean(busy)}
          onClick={() =>
            runAction("local", () => apiPost("/ingest/files"), () => {
              setMessage("Local files ingested");
              void refreshStatus().catch(() => undefined);
            })
          }
          type="button"
        >
          <UploadCloud className="h-4 w-4" aria-hidden />
          Ingest local files
        </button>
        <button
          className="focus-ring rounded border border-line px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60"
          disabled={Boolean(busy)}
          onClick={() =>
            runAction("zotero", () => apiPost("/ingest/zotero"), () => {
              setMessage("Zotero exports imported");
              void refreshStatus().catch(() => undefined);
            })
          }
          type="button"
        >
          Import Zotero exports
        </button>
        <button
          className="focus-ring rounded border border-line px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60"
          disabled={Boolean(busy)}
          onClick={() =>
            runAction(
              "descriptors",
              () => apiPost<ApplicationNode[]>("/ingest/extract-descriptors?scope_id=electromagnetic_functional_materials&limit=50"),
              (nodes) => {
                setMessage(`${nodes.length} application descriptors extracted`);
                rememberExtractedNodes(nodes);
                void refreshStatus().catch(() => undefined);
              }
            )
          }
          type="button"
        >
          Extract descriptors
        </button>
      </div>

      <form
        className="grid gap-3 border-t border-line pt-5"
        onSubmit={(event) => {
          event.preventDefault();
          void searchLiterature();
        }}
      >
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_120px_auto]">
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Literature search</span>
            <input
              className="focus-ring rounded border border-line bg-shell px-3 py-2"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Limit</span>
            <input
              className="focus-ring rounded border border-line bg-shell px-3 py-2"
              min={5}
              max={200}
              type="number"
              value={limit}
              onChange={(event) => setLimit(Math.max(5, Math.min(Number(event.target.value || 20), 200)))}
            />
          </label>
          <button
            className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-accent px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60 lg:self-end"
            disabled={Boolean(busy) || !query.trim()}
            type="submit"
          >
            {busy === "search" ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Search className="h-4 w-4" aria-hidden />}
            Search papers
          </button>
        </div>
        {results.length ? (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <div className="text-sm text-muted">{selectedCount} of {selectableCount} papers selected</div>
              <button
                className="focus-ring rounded bg-accent px-3 py-1.5 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={Boolean(busy) || selectableCount === 0}
                onClick={() => setSelected(new Set(results.filter((item) => !isFailure(item)).map(resultKey)))}
                type="button"
              >
                Select all papers
              </button>
              <button
                className="focus-ring rounded border border-line px-3 py-1.5 text-xs font-medium disabled:cursor-not-allowed disabled:opacity-60"
                disabled={Boolean(busy) || selectedCount === 0}
                onClick={() => setSelected(new Set())}
                type="button"
              >
                Clear
              </button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                className="focus-ring inline-flex items-center gap-2 rounded border border-line px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60"
                disabled={Boolean(busy) || selectedCount === 0}
                onClick={() => void ingestSelected(false)}
                type="button"
              >
                {busy === "ingest-selected" ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <PlusCircle className="h-4 w-4" aria-hidden />}
                Ingest selected
              </button>
              <button
                className="focus-ring inline-flex items-center gap-2 rounded bg-accent px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={Boolean(busy) || selectedCount === 0}
                onClick={() => void ingestSelected(true)}
                type="button"
              >
                {busy === "ingest-extract-selected" ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <PlusCircle className="h-4 w-4" aria-hidden />}
                Ingest + extract descriptors
              </button>
            </div>
          </div>
        ) : null}
      </form>

      {message ? <div className="rounded border border-teal/40 bg-teal/10 p-3 text-sm">{message}</div> : null}
      {error ? <div className="rounded border border-coral/40 bg-coral/10 p-3 text-sm">{error}</div> : null}

      {results.length ? (
        <div className="grid gap-3">
          {results.map((item) => {
            const key = resultKey(item);
            const failed = isFailure(item);
            const checked = selected.has(key);
            const resultBusy = busy === `ingest-extract-result:${key}`;
            return (
              <article key={key} className="rounded border border-line bg-shell p-4">
                <div className="grid gap-3 sm:grid-cols-[32px_minmax(0,1fr)]">
                  <button
                    aria-label={checked ? "Deselect paper" : "Select paper"}
                    className="focus-ring mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded border border-line disabled:cursor-not-allowed disabled:opacity-40"
                    disabled={failed}
                    onClick={() => toggleResult(item)}
                    type="button"
                  >
                    {checked ? <CheckSquare className="h-4 w-4 text-accent" aria-hidden /> : <Square className="h-4 w-4 text-muted" aria-hidden />}
                  </button>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                      <span className="rounded border border-line px-2 py-0.5">{item.source}</span>
                      {item.year ? <span>{item.year}</span> : null}
                      {item.doi ? <span>{item.doi}</span> : null}
                    </div>
                    <h3 className="mt-2 text-sm font-semibold">{item.title}</h3>
                    {item.authors.length ? <div className="mt-1 text-xs text-muted">{item.authors.slice(0, 6).join(", ")}</div> : null}
                    {item.abstract ? <p className="mt-2 line-clamp-3 text-sm text-muted">{stripTags(item.abstract)}</p> : null}
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <button
                        className="focus-ring inline-flex items-center gap-1.5 rounded bg-accent px-3 py-1.5 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={Boolean(busy) || failed}
                        onClick={() => void ingestSingleResult(item)}
                        type="button"
                      >
                        {resultBusy ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <PlusCircle className="h-3.5 w-3.5" aria-hidden />}
                        Ingest + extract descriptors
                      </button>
                      {item.url ? (
                        <a className="focus-ring inline-flex items-center gap-1 rounded px-1.5 py-1 text-xs font-medium text-accent" href={item.url} rel="noreferrer" target="_blank">
                          Open source
                          <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                        </a>
                      ) : null}
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : null}

      {recentNodes.length ? (
        <section className="grid gap-3 border-t border-line pt-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold">Recent Extracted Descriptors</h2>
              <p className="mt-2 text-sm text-muted">Saved Application Finder descriptors from the corpus, restored when you return to this tab.</p>
            </div>
            <button
              className="focus-ring rounded border border-line px-3 py-1.5 text-xs font-medium disabled:cursor-not-allowed disabled:opacity-60"
              disabled={Boolean(busy)}
              onClick={() => void refreshRecentDescriptors()}
              type="button"
            >
              Refresh
            </button>
          </div>
          <div className="grid gap-3 lg:grid-cols-2">
            {recentNodes.map((node) => (
              <DescriptorCard key={node.node_id} node={node} />
            ))}
          </div>
        </section>
      ) : null}

      <section className="border-t border-line pt-5">
        <h2 className="text-base font-semibold">Corpus Status</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <Metric label="Documents" value={status?.documents ?? 0} />
          <Metric label="Evidence chunks" value={status?.evidence_chunks ?? 0} />
          <Metric label="Application descriptors" value={status?.application_nodes ?? 0} />
        </div>
      </section>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded border border-line bg-shell p-4">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-2 text-xl font-semibold">{value}</div>
    </div>
  );
}

function DescriptorCard({ node }: { node: ApplicationNode }) {
  const requirements = Array.isArray(node.em_property_requirements) ? node.em_property_requirements : [];
  return (
    <article className="rounded border border-line bg-shell p-4">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
        <span className="rounded border border-line px-2 py-0.5">{node.domain || "electromagnetic"}</span>
        {node.year ? <span>{node.year}</span> : null}
        <span>{Math.round((node.confidence || 0) * 100)}% confidence</span>
      </div>
      <h3 className="mt-2 text-sm font-semibold">{node.label || node.node_id}</h3>
      <p className="mt-2 line-clamp-3 text-sm text-muted">{node.application_text || "No descriptor text available."}</p>
      <div className="mt-3 grid gap-2 text-xs text-muted">
        {node.device_type ? <div><span className="font-medium text-ink">Device:</span> {node.device_type}</div> : null}
        {node.physical_em_mechanism ? <div><span className="font-medium text-ink">Mechanism:</span> {node.physical_em_mechanism}</div> : null}
        {requirements.length ? (
          <div><span className="font-medium text-ink">EM requirements:</span> {requirements.slice(0, 3).join("; ")}</div>
        ) : null}
      </div>
    </article>
  );
}

function selectedLiteratureResults(results: LiteratureResult[], selected: Set<string>) {
  return results.filter((item) => selected.has(resultKey(item)) && !isFailure(item)).map(normalizeLiteratureResult);
}

function normalizeLiteratureResult(item: LiteratureResult): LiteratureResult {
  return {
    ...item,
    authors: Array.isArray(item.authors) ? item.authors : [],
    abstract: item.abstract || undefined,
    extra: item.extra && typeof item.extra === "object" && !Array.isArray(item.extra) ? item.extra : {}
  };
}

function descriptorLimit(results: LiteratureResult[]) {
  return Math.min(MAX_DESCRIPTOR_EXTRACTION, Math.max(results.length * DESCRIPTOR_CHUNKS_PER_PAPER, 1));
}

function resultKey(item: LiteratureResult) {
  return `${item.source}:${item.doi || item.url || item.title}`;
}

function isFailure(item: LiteratureResult) {
  return item.title.endsWith(" search failed");
}

function stripTags(value: string) {
  return value.replace(/<[^>]+>/g, "");
}

function mergeApplicationNodes(primary: ApplicationNode[], secondary: ApplicationNode[]) {
  const seen = new Set<string>();
  const merged: ApplicationNode[] = [];
  for (const node of [...primary, ...secondary]) {
    if (!node.node_id || seen.has(node.node_id)) {
      continue;
    }
    seen.add(node.node_id);
    merged.push(node);
  }
  return merged;
}

function pruneLiteratureResultForStorage(item: LiteratureResult): LiteratureResult {
  const normalized = normalizeLiteratureResult(item);
  return {
    ...normalized,
    abstract: normalized.abstract ? stripTags(normalized.abstract).slice(0, 5000) : normalized.abstract
  };
}

function readPersistedIngestionState(): PersistedIngestionState | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  try {
    const raw = window.sessionStorage.getItem(INGESTION_STORAGE_KEY);
    return raw ? JSON.parse(raw) as PersistedIngestionState : undefined;
  } catch {
    return undefined;
  }
}

function persistIngestionState(state: PersistedIngestionState) {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.sessionStorage.setItem(INGESTION_STORAGE_KEY, JSON.stringify(state));
  } catch {
    window.sessionStorage.removeItem(INGESTION_STORAGE_KEY);
  }
}

async function ingestResults(results: LiteratureResult[]) {
  const normalizedResults = results.map(normalizeLiteratureResult);
  try {
    return await apiPost<LiteratureIngestSummary>("/ingest/public-search/ingest", { results: normalizedResults });
  } catch (exc) {
    if (!isNotFoundError(exc)) {
      throw exc;
    }
    return ingestResultsAsEvidenceFiles(normalizedResults);
  }
}

async function ingestAndExtractResults(results: LiteratureResult[]): Promise<LiteratureIngestAndExtractSummary> {
  const normalizedResults = results.map(normalizeLiteratureResult);
  try {
    const ingestion = await ingestResults(normalizedResults);
    const evidenceIds = (ingestion.evidence_ids || []).slice(0, descriptorLimit(normalizedResults));
    const application_nodes: ApplicationNode[] = [];
    for (const batch of chunk(evidenceIds, DESCRIPTOR_BATCH_SIZE)) {
      const nodes = await apiPost<ApplicationNode[]>(
        `/ingest/extract-descriptors?scope_id=electromagnetic_functional_materials&limit=${batch.length}`,
        { evidence_ids: batch }
      );
      application_nodes.push(...nodes);
    }
    return { ingestion, evidence_ids: evidenceIds, application_nodes };
  } catch (exc) {
    if (!isNotFoundError(exc)) {
      throw exc;
    }
    const ingestion = await ingestResults(normalizedResults);
    const application_nodes = await apiPost<ApplicationNode[]>(
      `/ingest/extract-descriptors?scope_id=electromagnetic_functional_materials&limit=${descriptorLimit(normalizedResults)}`
    );
    return { ingestion, evidence_ids: [], application_nodes };
  }
}

function chunk<T>(values: T[], size: number) {
  const chunks: T[][] = [];
  for (let index = 0; index < values.length; index += size) {
    chunks.push(values.slice(index, index + size));
  }
  return chunks;
}

async function ingestResultsAsEvidenceFiles(results: LiteratureResult[]): Promise<LiteratureIngestSummary> {
  const formData = new FormData();
  results.forEach((item, index) => {
    const filename = `application-finder-literature-${String(index + 1).padStart(2, "0")}-${slugify(item.doi || item.title)}.md`;
    formData.append("files", new File([literatureMarkdown(item)], filename, { type: "text/markdown" }));
  });
  const summary = await apiUpload<{ documents: number; chunks: number; skipped: number }>("/ingest/files", formData);
  const status = await apiGet<IngestionStatus>("/ingest/status").catch(() => undefined);
  return {
    documents_added: summary.documents,
    evidence_chunks_added: summary.chunks,
    skipped: summary.skipped,
    documents: status?.documents ?? summary.documents,
    evidence_chunks: status?.evidence_chunks ?? summary.chunks
  };
}

function literatureMarkdown(item: LiteratureResult) {
  const lines = [
    item.title,
    "",
    item.authors.length ? `Authors: ${item.authors.join(", ")}` : "",
    item.year ? `Year: ${item.year}` : "",
    item.doi ? `DOI: ${item.doi}` : "",
    item.url ? `URL: ${item.url}` : "",
    `Source: ${item.source}`,
    "",
    "Abstract",
    "",
    stripTags(item.abstract || "No abstract was available from the public metadata source.")
  ];
  return lines.filter((line, index) => line || index < 2).join("\n");
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/https?:\/\//g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "paper";
}

function isNotFoundError(exc: unknown) {
  const message = exc instanceof Error ? exc.message : String(exc);
  return message.includes('"detail":"Not Found"') || message.includes("404") || message.includes("Not Found");
}
