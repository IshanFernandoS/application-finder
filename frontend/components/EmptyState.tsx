import { Database } from "lucide-react";

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="panel flex min-h-44 flex-col items-center justify-center px-8 text-center">
      <Database className="mb-3 h-8 w-8 text-muted" aria-hidden />
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 max-w-xl text-sm text-muted">{body}</p>
    </div>
  );
}
