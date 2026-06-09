export function BaselineComparisonPanel() {
  const modes = ["baseline_direct_llm", "baseline_standard_rag", "baseline_nearest_neighbour", "baseline_fbs_pm_no_boundary_rag", "full_method"];
  return (
    <section className="panel p-5">
      <h2 className="text-base font-semibold">Baseline Comparison</h2>
      <div className="mt-4 grid gap-2">
        {modes.map((mode) => (
          <div key={mode} className="flex items-center justify-between rounded border border-line bg-shell px-3 py-2 text-sm">
            <span>{mode}</span>
            <span className="text-muted">available through evaluation API</span>
          </div>
        ))}
      </div>
    </section>
  );
}
