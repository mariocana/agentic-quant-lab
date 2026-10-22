// Top-level tabs: the data lake (this app) and the desks mounted by the server
// under /cot and /equity (GET /api/apps). The active tab lives in the URL hash.
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Database } from "lucide-react";
import { api, type DeskApp } from "@/lib/api";
import { cn } from "@/lib/cn";

const fromHash = () => window.location.hash.replace(/^#/, "") || "data";

export function useDeskTab() {
  const [tab, setTabState] = useState<string>(fromHash);
  const [visited, setVisited] = useState<Set<string>>(() => new Set([fromHash()]));
  const appsQuery = useQuery({ queryKey: ["apps"], queryFn: api.apps, staleTime: Infinity });
  const apps = appsQuery.data?.apps ?? [];

  const setTab = (t: string) => {
    setTabState(t);
    setVisited((v) => (v.has(t) ? v : new Set(v).add(t)));
    window.history.replaceState(null, "", t === "data" ? window.location.pathname : `#${t}`);
  };
  useEffect(() => {
    const onHash = () => setTab(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  // a hash for a desk that is not mounted falls back to the data tab
  useEffect(() => {
    if (appsQuery.isSuccess && tab !== "data" && !apps.some((a) => a.key === tab)) setTab("data");
  }, [appsQuery.isSuccess, tab]);
  return { tab, setTab, apps, visited };
}

export function TopTabs({ tab, apps, onChange }: { tab: string; apps: DeskApp[]; onChange: (t: string) => void }) {
  const tabs = [{ key: "data", label: "Dati" }, ...apps];
  return (
    <nav className="flex h-10 shrink-0 items-center gap-1 border-b border-border bg-bg-panel px-3">
      <Database className="mr-2 h-4 w-4 text-accent" />
      <span className="mr-4 font-mono text-xs font-semibold tracking-wide">QUANTLAKE</span>
      {tabs.map((t) => (
        <button
          key={t.key}
          onClick={() => onChange(t.key)}
          className={cn(
            "rounded px-3 py-1 font-mono text-xs tracking-wide transition-colors",
            tab === t.key ? "bg-accent text-bg" : "text-fg-muted hover:bg-bg-elevated hover:text-fg",
          )}
        >
          {t.label.toUpperCase()}
        </button>
      ))}
    </nav>
  );
}
