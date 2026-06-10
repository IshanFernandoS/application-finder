"use client";

import { useMemo, useState } from "react";
import { Loader2, Plus, RotateCcw, Save, X } from "lucide-react";
import { apiPost } from "@/lib/api";
import type { Scope } from "@/lib/types";

type ScopeListField =
  | "included_domains"
  | "included_material_classes"
  | "included_device_families"
  | "included_mechanisms"
  | "included_property_types"
  | "excluded_domains"
  | "excluded_material_classes"
  | "validation_methods"
  | "default_search_queries";

const listSections: Array<{ key: ScopeListField; title: string }> = [
  { key: "included_domains", title: "Domains" },
  { key: "included_material_classes", title: "Material Classes" },
  { key: "included_device_families", title: "Device Families" },
  { key: "included_mechanisms", title: "Mechanisms" },
  { key: "included_property_types", title: "Property Types" },
  { key: "validation_methods", title: "Validation Methods" },
  { key: "default_search_queries", title: "Search Queries" },
  { key: "excluded_domains", title: "Excluded Domains" },
  { key: "excluded_material_classes", title: "Excluded Materials" }
];

const fallbackScope: Scope = {
  scope_id: "electromagnetic_functional_materials",
  title: "Electromagnetic Functional Materials and Devices",
  description: "",
  included_domains: [],
  included_material_classes: [],
  included_device_families: [],
  included_mechanisms: [],
  included_property_types: [],
  excluded_domains: [],
  excluded_material_classes: [],
  mattergen_compatibility_notes: [],
  validation_methods: [],
  default_search_queries: [],
  descriptor_weights: {}
};

export function ScopeEditor({ scope }: { scope?: Scope }) {
  const initialScope = useMemo(() => normalizeScope(scope), [scope]);
  const [draft, setDraft] = useState<Scope>(initialScope);
  const [savedScope, setSavedScope] = useState<Scope>(initialScope);
  const [newValues, setNewValues] = useState<Partial<Record<ScopeListField, string>>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | undefined>();
  const [error, setError] = useState<string | undefined>();
  const dirty = JSON.stringify(normalizeScope(draft)) !== JSON.stringify(savedScope);

  async function saveScope() {
    setBusy(true);
    setMessage(undefined);
    setError(undefined);
    try {
      const saved = await apiPost<Scope>("/scopes", normalizeScope(draft));
      const normalized = normalizeScope(saved);
      setDraft(normalized);
      setSavedScope(normalized);
      setMessage("Scope saved");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusy(false);
    }
  }

  function updateList(key: ScopeListField, values: string[]) {
    setDraft((current) => ({ ...current, [key]: values }));
  }

  function addListValue(key: ScopeListField) {
    const value = (newValues[key] || "").trim();
    if (!value) return;
    const existing = draft[key] || [];
    updateList(key, Array.from(new Set([...existing, value])));
    setNewValues((current) => ({ ...current, [key]: "" }));
  }

  function updateWeight(key: string, value: string) {
    const parsed = Number(value);
    setDraft((current) => ({
      ...current,
      descriptor_weights: {
        ...current.descriptor_weights,
        [key]: Number.isFinite(parsed) ? parsed : 0
      }
    }));
  }

  return (
    <section className="panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Scope Editor</h2>
          <div className="mt-1 text-xs text-muted">{draft.scope_id}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="focus-ring inline-flex items-center gap-2 rounded border border-line px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60"
            disabled={busy || !dirty}
            onClick={() => {
              setDraft(savedScope);
              setMessage(undefined);
              setError(undefined);
            }}
            type="button"
          >
            <RotateCcw className="h-4 w-4" aria-hidden />
            Reset
          </button>
          <button
            className="focus-ring inline-flex items-center gap-2 rounded bg-accent px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
            disabled={busy || !draft.title.trim()}
            onClick={() => void saveScope()}
            type="button"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Save className="h-4 w-4" aria-hidden />}
            Save Scope
          </button>
        </div>
      </div>

      {message ? <div className="mt-4 rounded border border-teal/40 bg-teal/10 p-3 text-sm">{message}</div> : null}
      {error ? <div className="mt-4 rounded border border-coral/40 bg-coral/10 p-3 text-sm">{error}</div> : null}

      <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="grid gap-4">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="grid gap-1 text-sm">
              <span className="font-medium">Title</span>
              <input
                className="focus-ring rounded border border-line bg-shell px-3 py-2"
                value={draft.title}
                onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
              />
            </label>
            <label className="grid gap-1 text-sm">
              <span className="font-medium">Scope ID</span>
              <input className="rounded border border-line bg-shell px-3 py-2 text-muted" value={draft.scope_id} readOnly />
            </label>
          </div>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">Description</span>
            <textarea
              className="focus-ring min-h-24 rounded border border-line bg-shell px-3 py-2"
              value={draft.description}
              onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))}
            />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            {listSections.map((section) => (
              <TokenListEditor
                key={section.key}
                title={section.title}
                value={newValues[section.key] || ""}
                values={draft[section.key] || []}
                onValueChange={(value) => setNewValues((current) => ({ ...current, [section.key]: value }))}
                onAdd={() => addListValue(section.key)}
                onRemove={(value) => updateList(section.key, draft[section.key].filter((item) => item !== value))}
              />
            ))}
          </div>
        </div>

        <aside className="rounded border border-line bg-shell p-4">
          <h3 className="text-sm font-semibold">Descriptor Weights</h3>
          <div className="mt-3 grid gap-3">
            {Object.entries(draft.descriptor_weights).map(([key, value]) => (
              <label key={key} className="grid gap-1 text-xs text-muted">
                {labelFromKey(key)}
                <input
                  className="focus-ring rounded border border-line bg-panel px-3 py-2 text-sm text-ink"
                  min={0}
                  max={5}
                  step={0.1}
                  type="number"
                  value={value}
                  onChange={(event) => updateWeight(key, event.target.value)}
                />
              </label>
            ))}
          </div>
        </aside>
      </div>
    </section>
  );
}

function TokenListEditor({
  title,
  values,
  value,
  onValueChange,
  onAdd,
  onRemove
}: {
  title: string;
  values: string[];
  value: string;
  onValueChange: (value: string) => void;
  onAdd: () => void;
  onRemove: (value: string) => void;
}) {
  return (
    <section className="rounded border border-line bg-shell p-3">
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="mt-3 flex gap-2">
        <input
          className="focus-ring min-w-0 flex-1 rounded border border-line bg-panel px-2 py-1.5 text-sm"
          value={value}
          onChange={(event) => onValueChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              onAdd();
            }
          }}
        />
        <button className="focus-ring rounded border border-line p-2 text-accent" onClick={onAdd} title={`Add ${title}`} type="button">
          <Plus className="h-4 w-4" aria-hidden />
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {values.map((item) => (
          <span key={item} className="inline-flex max-w-full items-center gap-1 rounded border border-line bg-panel px-2 py-1 text-xs text-muted">
            <span className="truncate">{item}</span>
            <button className="focus-ring rounded p-0.5 text-muted hover:text-coral" onClick={() => onRemove(item)} title={`Remove ${item}`} type="button">
              <X className="h-3.5 w-3.5" aria-hidden />
            </button>
          </span>
        ))}
      </div>
    </section>
  );
}

function normalizeScope(scope?: Scope): Scope {
  const base = { ...fallbackScope, ...(scope || {}) };
  return {
    ...base,
    included_domains: scope?.included_domains || [],
    included_material_classes: scope?.included_material_classes || [],
    included_device_families: scope?.included_device_families || [],
    included_mechanisms: scope?.included_mechanisms || [],
    included_property_types: scope?.included_property_types || [],
    excluded_domains: scope?.excluded_domains || [],
    excluded_material_classes: scope?.excluded_material_classes || [],
    mattergen_compatibility_notes: scope?.mattergen_compatibility_notes || [],
    validation_methods: scope?.validation_methods || [],
    default_search_queries: scope?.default_search_queries || [],
    descriptor_weights: scope?.descriptor_weights || {}
  };
}

function labelFromKey(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
