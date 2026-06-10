"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, ClipboardList, Download, FlaskConical, Play, RefreshCw, Shield, StopCircle, Terminal, type LucideIcon } from "lucide-react";
import type { HPCCheckResult, HPCJob, HPCStatus } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

const adminProxyBase = "/api/backend";

export function HPCWorkerPanel({ initialStatus, initialJobs = [] }: { initialStatus?: HPCStatus; initialJobs?: HPCJob[] }) {
  const [status, setStatus] = useState<HPCStatus | undefined>(initialStatus);
  const [jobs, setJobs] = useState<HPCJob[]>(initialJobs);
  const [check, setCheck] = useState<HPCCheckResult | undefined>();
  const [busy, setBusy] = useState<string | undefined>();
  const [error, setError] = useState<string | undefined>();

  const latestJob = useMemo(() => jobs[0], [jobs]);
  const queueOnly = Boolean(status?.queue_only);

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    setError(undefined);
    const response = await fetch(`${adminProxyBase}${path}`, {
      ...init,
      headers: {
        "content-type": "application/json",
        ...(init?.headers || {})
      }
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `Request failed: ${response.status}`);
    }
    return response.json() as Promise<T>;
  }

  async function runCheck(kind: "connection" | "slurm" | "mattergen") {
    setBusy(kind);
    try {
      const path = kind === "connection" ? "/hpc/check-connection" : kind === "slurm" ? "/hpc/check-slurm" : "/hpc/check-mattergen";
      setCheck(await request<HPCCheckResult>(path, { method: "POST" }));
      setStatus(await request<HPCStatus>("/hpc/status"));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusy(undefined);
    }
  }

  async function refreshJobs() {
    setBusy("refresh");
    try {
      setStatus(await request<HPCStatus>("/hpc/status"));
      setJobs(await request<HPCJob[]>("/hpc/jobs"));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusy(undefined);
    }
  }

  async function submitTestJob() {
    setBusy("submit");
    try {
      const job = await request<HPCJob>("/hpc/jobs", {
        method: "POST",
        body: JSON.stringify({
          job_type: "custom_user_job_placeholder",
          payload: { submitted_from: "Application Finder HPC Worker page" }
        })
      });
      setJobs((current) => [job, ...current.filter((item) => item.job_id !== job.job_id)]);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusy(undefined);
    }
  }

  async function jobAction(jobId: string, action: "poll" | "retrieve" | "cancel") {
    setBusy(`${action}:${jobId}`);
    try {
      const job = await request<HPCJob>(`/hpc/jobs/${jobId}/${action}`, { method: "POST" });
      setJobs((current) => current.map((item) => (item.job_id === job.job_id ? job : item)));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusy(undefined);
    }
  }

  return (
    <div className="grid gap-5">
      <section className="panel p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">HPC Worker</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted">
              {queueOnly
                ? "Queued site submissions are relayed to Slurm by the local Mac worker, keeping personal SSH credentials off Render."
                : "SSH/Slurm compute worker for MatterGen generation, validation, indexing, PDF processing, and future DFT or EM simulation workflows."}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge status={status?.enabled ? "available" : "setup_needed"} />
            <StatusBadge status={status?.configured ? "available" : "setup_needed"} />
          </div>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-4">
          <State label="Worker enabled" ok={status?.enabled} />
          <State label={queueOnly ? "Relay mode" : "Safe SSH auth"} ok={queueOnly || status?.safe_authentication} detail={queueOnly ? "Render queues jobs" : undefined} />
          <State label="Slurm mode" ok={status?.scheduler_configured} />
          <State label="MatterGen env" ok={status?.mattergen_hpc_env_configured} />
        </div>
        {queueOnly ? (
          <div className="mt-4 rounded border border-teal/40 bg-teal/10 p-4 text-sm">
            <div className="font-medium text-ink">How site submission works</div>
            <p className="mt-2 text-muted">
              The website creates queued jobs on Render. A local relay running on your Mac submits them to QMUL Slurm, polls status, retrieves outputs, and syncs results back here.
            </p>
            <pre className="mt-3 overflow-auto rounded bg-shell p-3 text-xs text-muted">scripts/hpc/start_control_master.sh{"\n"}scripts/hpc/start_local_relay.sh</pre>
          </div>
        ) : null}
        {status?.warnings?.length ? (
          <div className="mt-4 grid gap-2">
            {status.warnings.map((warning) => (
              <div key={warning} className="flex gap-2 rounded border border-amber/40 bg-amber/10 p-3 text-sm text-ink">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber" aria-hidden />
                <span>{warning}</span>
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section className="panel p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {queueOnly ? null : (
              <>
                <Action icon={Shield} label="Check HPC connection" busy={busy === "connection"} onClick={() => runCheck("connection")} />
                <Action icon={Terminal} label="Check Slurm" busy={busy === "slurm"} onClick={() => runCheck("slurm")} />
                <Action icon={FlaskConical} label="Check MatterGen environment" busy={busy === "mattergen"} onClick={() => runCheck("mattergen")} />
              </>
            )}
            <Action icon={Play} label={queueOnly ? "Queue test job" : "Submit test job"} busy={busy === "submit"} onClick={submitTestJob} />
            <Action icon={RefreshCw} label="Refresh" busy={busy === "refresh"} onClick={refreshJobs} />
          </div>
        </div>
        {queueOnly ? (
          <div className="mt-4 rounded border border-line bg-shell p-4 text-sm text-muted">
            Direct Render-to-HPC SSH checks are intentionally skipped in relay mode because Render does not store SSH credentials. Use the local relay commands above, then refresh this page to watch queued jobs move to Slurm.
          </div>
        ) : null}
        {check ? (
          <div className="mt-4 rounded border border-line bg-shell p-4 text-sm">
            <div className="flex items-center gap-2 font-medium">
              {check.ok ? <CheckCircle2 className="h-4 w-4 text-teal" aria-hidden /> : <AlertTriangle className="h-4 w-4 text-coral" aria-hidden />}
              {check.message}
            </div>
            {check.details.length ? <pre className="mt-3 max-h-40 overflow-auto whitespace-pre-wrap text-xs text-muted">{check.details.join("\n")}</pre> : null}
          </div>
        ) : null}
        {error ? <div className="mt-4 rounded border border-coral/40 bg-coral/10 p-3 text-sm">{error}</div> : null}
      </section>

      <section className="panel p-5">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Recent HPC jobs</h2>
          <div className="text-xs text-muted">{latestJob ? `Latest: ${latestJob.job_id}` : "No jobs yet"}</div>
        </div>
        <div className="mt-4 grid gap-3">
          {jobs.length ? (
            jobs.map((job) => (
              <article key={job.job_id} className="rounded border border-line bg-shell p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <ClipboardList className="h-4 w-4 text-accent" aria-hidden />
                      <span className="font-medium">{job.job_type}</span>
                      <StatusBadge status={job.status} />
                    </div>
                    <div className="mt-2 grid gap-1 text-xs text-muted sm:grid-cols-2 lg:grid-cols-4">
                      <span>Job {job.job_id}</span>
                      <span>Slurm {job.slurm_job_id || "not submitted"}</span>
                      <span>Pathway {job.pathway_id || "none"}</span>
                      <span>{new Date(job.updated_at).toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Action icon={RefreshCw} label="Poll" busy={busy === `poll:${job.job_id}`} onClick={() => jobAction(job.job_id, "poll")} />
                    <Action icon={Download} label="Retrieve outputs" busy={busy === `retrieve:${job.job_id}`} onClick={() => jobAction(job.job_id, "retrieve")} />
                    <Action icon={StopCircle} label="Cancel job" busy={busy === `cancel:${job.job_id}`} onClick={() => jobAction(job.job_id, "cancel")} />
                  </div>
                </div>
                {job.output_files.length ? <FileList files={job.output_files} /> : null}
                {job.log_excerpt ? <pre className="mt-3 max-h-52 overflow-auto whitespace-pre-wrap rounded bg-panel p-3 text-xs text-muted">{job.log_excerpt}</pre> : null}
                {job.error ? <div className="mt-3 rounded border border-coral/40 bg-coral/10 p-3 text-sm">{job.error}</div> : null}
              </article>
            ))
          ) : (
            <div className="rounded border border-line bg-shell p-4 text-sm text-muted">No HPC jobs recorded.</div>
          )}
        </div>
      </section>
    </div>
  );
}

function State({ label, ok, detail }: { label: string; ok?: boolean; detail?: string }) {
  return (
    <div className="rounded border border-line bg-shell p-3 text-sm">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-2 flex items-center gap-2 font-medium">
        {ok ? <CheckCircle2 className="h-4 w-4 text-teal" aria-hidden /> : <AlertTriangle className="h-4 w-4 text-amber" aria-hidden />}
        {detail || (ok ? "Ready" : "Needs setup")}
      </div>
    </div>
  );
}

function Action({ icon: Icon, label, busy, onClick }: { icon: LucideIcon; label: string; busy?: boolean; onClick: () => void }) {
  return (
    <button
      className="focus-ring inline-flex items-center gap-2 rounded bg-accent px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
      type="button"
      onClick={onClick}
      disabled={busy}
    >
      <Icon className={`h-4 w-4 ${busy ? "animate-spin" : ""}`} aria-hidden />
      {label}
    </button>
  );
}

function FileList({ files }: { files: string[] }) {
  return (
    <div className="mt-3 grid gap-1 rounded border border-line bg-panel p-3 text-xs text-muted">
      {files.slice(0, 12).map((file) => (
        <span key={file}>{file}</span>
      ))}
      {files.length > 12 ? <span>+{files.length - 12} more files</span> : null}
    </div>
  );
}
