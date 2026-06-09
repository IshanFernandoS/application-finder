export interface ReportRecord {
  report_id: string;
  gap_id: string;
  markdown_path: string;
  json_path: string;
  evidence_csv_path: string;
  created_at: string;
}

export function ReportPanel({ reports = [] }: { reports?: ReportRecord[] }) {
  return (
    <section className="panel p-5">
      <h2 className="text-base font-semibold">Reports</h2>
      <div className="mt-4 grid gap-3">
        {reports.length ? (
          reports.map((report) => (
            <article key={report.report_id} className="rounded border border-line bg-shell p-4 text-sm">
              <div className="font-medium">{report.gap_id}</div>
              <div className="mt-1 text-muted">{new Date(report.created_at).toLocaleString()}</div>
              <div className="mt-3 grid gap-1 text-xs text-muted">
                <span>{report.markdown_path}</span>
                <span>{report.json_path}</span>
                <span>{report.evidence_csv_path}</span>
              </div>
            </article>
          ))
        ) : (
          <p className="text-sm text-muted">No exported reports yet.</p>
        )}
      </div>
    </section>
  );
}
