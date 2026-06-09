"use client";

import { UploadCloud } from "lucide-react";
import { apiPost } from "@/lib/api";

export function IngestionPanel() {
  return (
    <section className="panel p-5">
      <h2 className="text-base font-semibold">Literature Ingestion</h2>
      <p className="mt-2 text-sm text-muted">Place PDFs in `data/pdfs/`, notes in `data/evidence/`, or Zotero CSV exports in `data/zotero/`, then trigger ingestion.</p>
      <div className="mt-5 flex flex-wrap gap-3">
        <button className="focus-ring inline-flex items-center gap-2 rounded bg-accent px-4 py-2 text-sm font-medium text-white" onClick={() => apiPost("/ingest/files")} type="button">
          <UploadCloud className="h-4 w-4" aria-hidden />
          Ingest local files
        </button>
        <button className="focus-ring rounded border border-line px-4 py-2 text-sm font-medium" onClick={() => apiPost("/ingest/zotero")} type="button">
          Import Zotero exports
        </button>
        <button
          className="focus-ring rounded border border-line px-4 py-2 text-sm font-medium"
          onClick={() => apiPost("/ingest/extract-descriptors?scope_id=electromagnetic_functional_materials&limit=50")}
          type="button"
        >
          Extract descriptors
        </button>
      </div>
    </section>
  );
}
