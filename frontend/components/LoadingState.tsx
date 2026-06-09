export function LoadingState({ label = "Loading research data" }: { label?: string }) {
  return (
    <div className="panel flex min-h-44 items-center justify-center text-sm text-muted">
      <div className="h-2 w-2 animate-pulse rounded-full bg-accent" />
      <span className="ml-3">{label}</span>
    </div>
  );
}
