import { AppShell } from "@/components/AppShell";
import { analyticsPrivacyCopy } from "@/lib/analytics";

export default function PrivacyPage() {
  return (
    <AppShell>
      <section className="panel max-w-4xl p-6">
        <h1 className="text-2xl font-semibold">{analyticsPrivacyCopy.title}</h1>
        <p className="mt-3 text-sm leading-6 text-muted">{analyticsPrivacyCopy.body}</p>
        <div className="mt-5 grid gap-3 text-sm text-muted">
          <div className="rounded border border-line bg-shell p-4">No names are collected.</div>
          <div className="rounded border border-line bg-shell p-4">Raw IP addresses and raw user-agent strings are disabled by default.</div>
          <div className="rounded border border-line bg-shell p-4">Anonymous visitor hashes rotate with a daily HMAC date component.</div>
          <div className="rounded border border-line bg-shell p-4">No cookies or persistent identifiers are required by the internal analytics layer.</div>
        </div>
      </section>
    </AppShell>
  );
}
