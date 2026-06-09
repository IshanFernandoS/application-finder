import { SlidersHorizontal } from "lucide-react";

export function SidebarFilters() {
  const filters = ["Domain", "Frequency", "Mechanism", "Device family", "Material class", "Year", "Evidence"];
  return (
    <aside className="panel p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <SlidersHorizontal className="h-4 w-4 text-accent" aria-hidden />
        Filters
      </div>
      <div className="grid gap-3">
        {filters.map((filter) => (
          <label key={filter} className="grid gap-1 text-xs text-muted">
            {filter}
            <select className="focus-ring h-9 rounded border border-line bg-shell px-2 text-sm text-ink">
              <option>All</option>
            </select>
          </label>
        ))}
      </div>
    </aside>
  );
}
