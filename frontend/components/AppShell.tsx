"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Boxes,
  FileText,
  FlaskConical,
  GitBranch,
  Home,
  Layers3,
  LineChart,
  RadioTower,
  Search,
  ShieldCheck
} from "lucide-react";
import { ScopeSelector } from "./ScopeSelector";

const nav = [
  { href: "/", label: "Home", icon: Home },
  { href: "/ingest", label: "Ingestion", icon: Search },
  { href: "/scopes", label: "Scope Editor", icon: Layers3 },
  { href: "/application-space", label: "Application Space", icon: RadioTower },
  { href: "/mattergen", label: "MatterGen", icon: FlaskConical },
  { href: "/hpc", label: "HPC Worker", icon: LineChart },
  { href: "/evals", label: "Evaluation", icon: BarChart3 },
  { href: "/analytics", label: "Analytics", icon: Activity },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/privacy", label: "Privacy", icon: ShieldCheck }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="grid min-h-screen grid-cols-[272px_1fr] bg-shell text-ink max-lg:grid-cols-1">
      <aside className="border-r border-line bg-panel px-4 py-5 max-lg:hidden">
        <div className="mb-7 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-accent text-white">
            <Boxes className="h-5 w-5" aria-hidden />
          </div>
          <div>
            <div className="text-sm font-semibold">Application Finder</div>
            <div className="text-xs text-muted">Inverse materials design</div>
          </div>
        </div>
        <nav className="space-y-1">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`focus-ring flex items-center gap-3 rounded px-3 py-2 text-sm ${
                  active ? "bg-accent text-white" : "text-muted hover:bg-shell hover:text-ink"
                }`}
              >
                <Icon className="h-4 w-4" aria-hidden />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-col">
        <header className="flex min-h-16 items-center justify-between gap-4 border-b border-line bg-panel px-6 py-3 max-lg:flex-col max-lg:items-stretch max-lg:px-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
              <span>Electromagnetic Application Space</span>
              <span>/</span>
              <span>Gap</span>
              <span>/</span>
              <span>Pathway</span>
              <span>/</span>
              <span>Material</span>
              <span>/</span>
              <span>Validation</span>
            </div>
            <div className="mt-1 flex items-center gap-2 text-sm font-medium">
              <GitBranch className="h-4 w-4 text-accent" aria-hidden />
              Scoped EM discovery workflow
            </div>
          </div>
          <ScopeSelector />
        </header>
        <nav className="hidden gap-2 overflow-x-auto border-b border-line bg-panel px-4 py-2 max-lg:flex">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`focus-ring inline-flex shrink-0 items-center gap-2 rounded px-3 py-2 text-xs ${
                  active ? "bg-accent text-white" : "text-muted hover:bg-shell hover:text-ink"
                }`}
              >
                <Icon className="h-3.5 w-3.5" aria-hidden />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <main className="min-w-0 flex-1 p-6 max-lg:p-3">{children}</main>
      </div>
    </div>
  );
}
