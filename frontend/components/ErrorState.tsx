import { AlertTriangle } from "lucide-react";

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="panel border-coral/40 bg-coral/5 p-5 text-sm text-coral">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5" aria-hidden />
        <p>{message}</p>
      </div>
    </div>
  );
}
