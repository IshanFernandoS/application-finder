interface AnalyticsSummary {
  visits_today: number;
  unique_anonymous_visitors_today: number;
  average_request_time_ms: number;
  top_routes: { route: string; count: number }[];
  top_referrers: { referrer_domain: string; count: number }[];
  errors_by_endpoint: Record<string, number>;
  deployment_env: string;
}

export function AccessAnalyticsDashboard({ summary }: { summary?: AnalyticsSummary }) {
  return (
    <section className="panel p-5">
      <h2 className="text-base font-semibold">Anonymous Access Analytics</h2>
      {!summary ? <p className="mt-3 text-sm text-muted">Analytics require an admin API key.</p> : null}
      {summary ? (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <Metric label="Visits today" value={summary.visits_today} />
            <Metric label="Unique anonymous visitors" value={summary.unique_anonymous_visitors_today} />
            <Metric label="Average request" value={`${summary.average_request_time_ms} ms`} />
            <Metric label="Environment" value={summary.deployment_env} />
          </div>
          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <List title="Top routes" rows={summary.top_routes.map((row) => [row.route, row.count])} />
            <List title="Referrers" rows={summary.top_referrers.map((row) => [row.referrer_domain, row.count])} />
          </div>
        </>
      ) : null}
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

function List({ title, rows }: { title: string; rows: [string, number][] }) {
  return (
    <div className="rounded border border-line bg-shell p-4">
      <div className="text-sm font-semibold">{title}</div>
      <div className="mt-3 space-y-2 text-sm text-muted">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-3">
            <span>{label}</span>
            <span>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
