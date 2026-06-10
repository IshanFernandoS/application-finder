"use client";

import { useState } from "react";
import { CheckSquare, ExternalLink, Loader2, PlusCircle, Search, Square, UploadCloud } from "lucide-react";
import { apiPost } from "@/lib/api";
import type { LiteratureIngestSummary, LiteratureResult } from "@/lib/types";

export function IngestionPanel() {
  const [query, setQuery] = useState("electromagnetic metamaterial inverse design high permittivity low loss");
  const [limit, setLimit] = useState(20);
  const [results, setResults] = useState<LiteratureResult[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState<string | undefined>();
  const [message, setMessage] = useState<string | undefined>();
  const [error, setError] = useState<string | undefined>();

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
    await runAction(
      "search",
      () => apiPost<LiteratureResult[]>("/ingest/public-search", { query, limit }),
      (items) => {
        setResults(items);
        setSelected(new Set(items.filter((item) => !isFailure(item)).slice(0, 8).map(resultKey)));
        setMessage(`${items.length} papers found`);
      }
    );
  }

  async function ingestSelected() {
    const selectedResults = results.filter((item) => selected.has(resultKey(item)) && !isFailure(item));
    await runAction(
      "ingest-selected",
      () => apiPost<LiteratureIngestSummary>("/ingest/public-search/ingest", { results: selectedResults }),
      (summary) => {
        setMessage(`${summary.documents_added} papers and ${summary.evidence_chunks_added} evidence chunks added`);
        setSelected(new Set());
      }
    );
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

  const selectedCount = selected.size;

  return (
    <section className="panel grid gap-5 p-5">
      <div>
        <h2 className="text-base font-semibold">Literature Ingestion</h2>
        <p className="mt-2 text-sm text-muted">Local files, Zotero exports, public scholarly metadata, and descriptor extraction feed the evidence corpus.</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          className="focus-ring inline-flex items-center gap-2 rounded bg-accent px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
          disabled={Boolean(busy)}
          onClick={() =>
            runAction("local", () => apiPost("/ingest/files"), () => setMessage("Local files ingested"))
          }
          type="button"
        >
          <UploadCloud className="h-4 w-4" aria-hidden />
          Ingest local files
        </button>
        <button
          className="focus-ring rounded border border-line px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60"
          disabled={Boolean(busy)}
          onClick={() => runAction("zotero", () => apiPost("/ingest/zotero"), () => setMessage("Zotero exports imported"))}
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
              () => apiPost("/ingest/extract-descriptors?scope_id=electromagnetic_functional_materials&limit=50"),
              () => setMessage("Descriptor extraction requested")
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
              max={50}
              type="number"
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value || 20))}
            />
          </label>
          <button
            className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-accent px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60 lg:self-end"
            disabled={busy === "search" || !query.trim()}
            type="submit"
          >
            {busy === "search" ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Search className="h-4 w-4" aria-hidden />}
            Search papers
          </button>
        </div>
        {results.length ? (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-muted">{selectedCount} selected</div>
            <button
              className="focus-ring inline-flex items-center gap-2 rounded border border-line px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60"
              disabled={busy === "ingest-selected" || selectedCount === 0}
              onClick={() => void ingestSelected()}
              type="button"
            >
              {busy === "ingest-selected" ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <PlusCircle className="h-4 w-4" aria-hidden />}
              Ingest selected
            </button>
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
                    {item.url ? (
                      <a className="focus-ring mt-3 inline-flex items-center gap-1 rounded text-xs font-medium text-accent" href={item.url} rel="noreferrer" target="_blank">
                        Open source
                        <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                      </a>
                    ) : null}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : null}
    </section>
  );
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
