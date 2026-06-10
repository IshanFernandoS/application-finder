import { RotateCcw, SlidersHorizontal } from "lucide-react";
import type { ApplicationSpace } from "@/lib/types";

export interface ApplicationSpaceFilters {
  domain: string;
  frequency: string;
  mechanism: string;
  deviceType: string;
  materialClass: string;
  year: string;
  minEvidence: string;
}

export const emptyApplicationSpaceFilters: ApplicationSpaceFilters = {
  domain: "",
  frequency: "",
  mechanism: "",
  deviceType: "",
  materialClass: "",
  year: "",
  minEvidence: ""
};

export function SidebarFilters({
  space,
  filters,
  onChange,
  onReset
}: {
  space?: ApplicationSpace;
  filters: ApplicationSpaceFilters;
  onChange: (filters: ApplicationSpaceFilters) => void;
  onReset: () => void;
}) {
  const nodes = space?.nodes || [];
  const options = {
    domain: unique(nodes.map((node) => node.domain)),
    frequency: unique(nodes.map((node) => node.operating_frequency_or_wavelength)),
    mechanism: unique(nodes.map((node) => node.physical_em_mechanism)),
    deviceType: unique(nodes.map((node) => node.device_type)),
    materialClass: unique(nodes.map((node) => node.material_class)),
    year: unique(nodes.map((node) => (node.year ? String(node.year) : undefined))).sort((a, b) => Number(b) - Number(a))
  };
  const activeCount = Object.values(filters).filter(Boolean).length;

  function update(key: keyof ApplicationSpaceFilters, value: string) {
    onChange({ ...filters, [key]: value });
  }

  return (
    <aside className="panel min-w-0 p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <SlidersHorizontal className="h-4 w-4 text-accent" aria-hidden />
          Application Filters
        </div>
        <button
          className="focus-ring rounded border border-line p-1.5 text-muted disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!activeCount}
          onClick={onReset}
          title="Reset filters"
          type="button"
        >
          <RotateCcw className="h-3.5 w-3.5" aria-hidden />
        </button>
      </div>
      <div className="mb-4 rounded border border-line bg-shell p-3 text-xs text-muted">
        {activeCount ? `${activeCount} active filter${activeCount === 1 ? "" : "s"}` : "Filters update the Application Space map, gap list, and visible clusters."}
      </div>
      <div className="grid gap-3">
        <FilterSelect label="Domain" value={filters.domain} options={options.domain} onChange={(value) => update("domain", value)} />
        <FilterSelect label="Frequency" value={filters.frequency} options={options.frequency} onChange={(value) => update("frequency", value)} />
        <FilterSelect label="Mechanism" value={filters.mechanism} options={options.mechanism} onChange={(value) => update("mechanism", value)} />
        <FilterSelect label="Device Family" value={filters.deviceType} options={options.deviceType} onChange={(value) => update("deviceType", value)} />
        <FilterSelect label="Material Class" value={filters.materialClass} options={options.materialClass} onChange={(value) => update("materialClass", value)} />
        <FilterSelect label="Year" value={filters.year} options={options.year} onChange={(value) => update("year", value)} />
        <FilterSelect
          label="Evidence"
          value={filters.minEvidence}
          options={["1+", "2+", "5+", "10+"]}
          onChange={(value) => update("minEvidence", value)}
        />
      </div>
    </aside>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1 text-xs text-muted">
      {label}
      <select
        className="focus-ring h-9 w-full min-w-0 rounded border border-line bg-shell px-2 text-sm text-ink"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function unique(values: Array<string | undefined | null>) {
  return Array.from(new Set(values.map((value) => value?.trim()).filter((value): value is string => Boolean(value)))).sort((a, b) =>
    a.localeCompare(b)
  );
}
