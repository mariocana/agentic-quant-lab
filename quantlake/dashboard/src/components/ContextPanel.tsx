// Pre-session context (Stucchi playbook): the same numbers as section 0 of the
// session sheet (applications/contesto.py), laid out to be read at a glance.
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { api, type ContextCard, type InstrumentContext, type Session } from "@/lib/api";
import { cn } from "@/lib/cn";

const SYMBOLS = ["ES", "NQ"] as const;
const IT: Record<string, string> = {
  low: "bassa", high: "alta", up: "su", down: "giù", positive: "positivo", negative: "negativo",
};

const num = (x: number | null | undefined, d = 0) =>
  x === null || x === undefined || !Number.isFinite(x)
    ? "–"
    : x.toLocaleString("it-IT", { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: true });
const pct = (x: number | null | undefined) => (x === null || x === undefined ? "–" : `${Math.round(x * 100)}%`);
const it = (x: string | null | undefined) => (x ? IT[x] ?? x : "–");
const rome = (iso: string | null | undefined, withDay = false) =>
  iso
    ? new Date(iso).toLocaleString("it-IT", {
        timeZone: "Europe/Rome",
        ...(withDay ? { day: "2-digit", month: "2-digit" } : {}),
        hour: "2-digit",
        minute: "2-digit",
      })
    : "–";

// London until 14:00 Rome, then NY.
const defaultSession = (): Session =>
  Number(new Date().toLocaleString("en-GB", { timeZone: "Europe/Rome", hour: "2-digit", hour12: false })) < 14
    ? "london"
    : "ny";

export function ContextPanel() {
  const [session, setSession] = useState<Session>(defaultSession);
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["context"], queryFn: api.context, staleTime: 60_000 });
  const upd = useMutation({
    mutationFn: (s: Session) => api.updateContext(s),
    onSuccess: (data) => qc.setQueryData(["context"], data),
  });
  const c = q.data;

  return (
    <div className="h-full overflow-y-auto scrollbar-thin">
      <div className="mx-auto max-w-6xl px-6 py-5">
        <header className="flex flex-wrap items-center gap-3 border-b border-border pb-4">
          <div>
            <div className="font-mono text-xs tracking-widest text-accent">◆ CONTESTO SESSIONE</div>
            <div className="mt-1 text-xl font-semibold tracking-tight">
              {c ? new Date(c.session_date).toLocaleDateString("it-IT", { weekday: "long", day: "numeric", month: "long" }) : "…"}
            </div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <div className="flex rounded border border-border-strong p-0.5 font-mono text-xs">
              {(["london", "ny"] as Session[]).map((s) => (
                <button
                  key={s}
                  onClick={() => setSession(s)}
                  className={cn(
                    "rounded px-3 py-1.5 transition-colors",
                    session === s ? "bg-accent text-bg" : "text-fg-muted hover:text-fg",
                  )}
                >
                  {s === "london" ? "LONDRA 09:00" : "NY 15:30"}
                </button>
              ))}
            </div>
            <button
              onClick={() => upd.mutate(session)}
              disabled={upd.isPending}
              className="flex items-center gap-1.5 rounded border border-border-strong px-3 py-2 font-mono text-xs text-fg transition-colors hover:border-accent hover:text-accent disabled:opacity-60"
              title={session === "ny" ? "Scarica i dati e scatta una foto della catena SPX (~20 s)" : "Scarica i dati (~20 s)"}
            >
              <RefreshCw className={cn("h-3.5 w-3.5", upd.isPending && "animate-spin")} />
              {upd.isPending ? "aggiorno… ~20 s" : "aggiorna dati"}
            </button>
          </div>
          {c && (
            <div className="w-full font-mono text-[11px] text-fg-dim">
              calcolato alle {rome(c.generated_at)} · barre ES fino alle {rome(c.instruments.ES.last_bar, true)} ·
              VIX/GEX della chiusura precedente
            </div>
          )}
        </header>

        {q.isLoading && <div className="py-16 text-center font-mono text-sm text-fg-muted">carico il contesto…</div>}
        {(q.error || upd.error) && (
          <Warn text={`Errore: ${String((upd.error ?? q.error) as Error)}`} />
        )}

        {c && (
          <div className="mt-4 space-y-4">
            {c.warnings.map((w) => <Warn key={w} text={w} />)}
            <RegimeStrip c={c} session={session} />
            {session === "london" ? <London c={c} /> : <NewYork c={c} />}
          </div>
        )}
      </div>
    </div>
  );
}

function Warn({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-2 rounded border border-amber-700/60 bg-amber-950/30 px-3 py-2 text-sm text-amber-200">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
      <span>{text}</span>
    </div>
  );
}

function Badge({ label, value, sub, tone = "neutral" }: {
  label: string; value: string; sub?: string; tone?: "neutral" | "warn" | "good";
}) {
  return (
    <div
      className={cn(
        "rounded border bg-bg-panel px-4 py-3",
        tone === "warn" ? "border-red-500/60" : tone === "good" ? "border-emerald-600/50" : "border-border",
      )}
    >
      <div className="font-mono text-[10px] uppercase tracking-widest text-fg-muted">{label}</div>
      <div className={cn("mt-1 text-lg font-semibold", tone === "warn" && "text-red-400")}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-fg-muted">{sub}</div>}
    </div>
  );
}

function RegimeStrip({ c, session }: { c: ContextCard; session: Session }) {
  const g = c.regime;
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        <Badge label="Volatilità" value={it(g.vol_regime)} sub={`${pct(g.iv_pct)} dell'anno`} />
        <Badge label="Trend 20 giorni" value={it(g.trend20)} sub={`quadrante ${g.quadrant ?? "–"}`} />
        <Badge
          label="GEX"
          value={g.gex_low ? "BASSO" : it(g.gex_regime)}
          sub={`${pct(g.gex_pct)} dell'anno`}
          tone={g.gex_low ? "warn" : "neutral"}
        />
        <Badge
          label="VIX9D / VIX"
          value={num(g.term_9d, 2)}
          sub={(g.term_9d ?? 0) > 1 ? "stress a breve" : "struttura normale"}
          tone={(g.term_9d ?? 0) > 1 ? "warn" : "neutral"}
        />
      </div>
      {g.gex_low && (
        <div className="rounded border border-red-500/50 bg-red-950/30 px-3 py-2 text-sm text-red-200">
          GEX basso: i trend day sono {pct(g.trend_rate_gex_low)} contro {pct(g.trend_rate_gex_high)}.{" "}
          {session === "london"
            ? "Interruttore trend day (§2.0) con un solo segnale."
            : "Il trend è più probabile, ma il setup C si accende solo con accettazione fuori IB."}
        </div>
      )}
    </div>
  );
}

function Big({ label, value, unit, sub, accent }: {
  label: string; value: string; unit?: string; sub?: React.ReactNode; accent?: boolean;
}) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-widest text-fg-muted">{label}</div>
      <div className={cn("mt-1 font-mono text-3xl font-semibold tabular-nums", accent && "text-accent")}>
        {value}
        {unit && <span className="ml-1 text-base font-normal text-fg-muted">{unit}</span>}
      </div>
      {sub && <div className="mt-1 text-xs text-fg-muted">{sub}</div>}
    </div>
  );
}

function Rows({ rows }: { rows: [string, React.ReactNode][] }) {
  return (
    <dl className="divide-y divide-border border-t border-border text-sm">
      {rows.map(([k, v]) => (
        <div key={k} className="flex items-baseline justify-between gap-4 py-1.5">
          <dt className="text-fg-muted">{k}</dt>
          <dd className="font-mono tabular-nums">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function Card({ symbol, children }: { symbol: string; children: React.ReactNode }) {
  return (
    <section className="rounded border border-border bg-bg-panel p-5">
      <div className="mb-4 font-mono text-sm font-semibold tracking-wider text-accent">{symbol}</div>
      <div className="space-y-5">{children}</div>
    </section>
  );
}

function RangeBar({ q }: { q: (number | null)[] }) {
  const [p25, p50, p75] = q;
  if (p25 == null || p50 == null || p75 == null) return null;
  const max = p75 * 1.25;
  const w = (x: number) => `${(x / max) * 100}%`;
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-widest text-fg-muted">Range Londra atteso (punti)</div>
      <div className="relative mt-2 h-2 rounded bg-bg-elevated">
        <div className="absolute inset-y-0 rounded bg-accent/30" style={{ left: w(p25), width: `calc(${w(p75)} - ${w(p25)})` }} />
        <div className="absolute inset-y-[-3px] w-0.5 bg-accent" style={{ left: w(p50) }} />
      </div>
      <div className="mt-1.5 flex justify-between font-mono text-xs tabular-nums text-fg-muted">
        <span>p25 {num(p25)}</span>
        <span className="text-fg">mediana {num(p50)}</span>
        <span>p75 {num(p75)}</span>
      </div>
    </div>
  );
}

function London({ c }: { c: ContextCard }) {
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2">
        {SYMBOLS.map((s) => {
          const x: InstrumentContext = c.instruments[s];
          return (
            <Card key={s} symbol={s}>
              <div className="grid grid-cols-2 gap-4">
                <Big label="EM giornaliero" value={num(x.em)} unit="pt"
                     sub={`IV ${num(x.iv, 1)} (${s === "ES" ? "VIX" : "VXN"}), ${pct(x.iv_pct)} dell'anno`} />
                <Big label="Mercato fermo se stop >" value={num(x.stop_max, 1)} unit="pt" accent
                     sub="oltre: si guarda e basta" />
              </div>
              <RangeBar q={x.london_range_q} />
              <Rows rows={[
                ["Ieri RTH high", num(x.prev_high, 2)],
                ["Ieri RTH low", num(x.prev_low, 2)],
                ["Ieri RTH close", num(x.prev_close, 2)],
                ["Asia high / low", `${num(x.asia_high, 2)} / ${num(x.asia_low, 2)}`],
                ["Range asiatico", `${num(x.asia_range, 2)} pt`],
                ["Prezzo ora", num(x.price, 2)],
              ]} />
            </Card>
          );
        })}
      </div>
      <Notes items={[
        "Mercato fermo (§1.3): in un quarto delle mattine Londra fa meno del p25. Se il tuo stop supera la soglia, l'oscillazione attesa non arriva a 2× lo stop.",
        "Il regime della mattina (rotazionale o direzionale) non si prevede da questi numeri: si legge live dall'accettazione.",
      ]} />
    </>
  );
}

function NewYork({ c }: { c: ContextCard }) {
  const e = c.em_0dte;
  const st = c.stucchi_em_stats;
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2">
        {SYMBOLS.map((s) => {
          const x = c.instruments[s];
          const f = x.gap_fill;
          const band = f ? (f.hi ? `gap ${num(f.lo, 2)}–${num(f.hi, 2)} EM` : `gap > ${num(f.lo, 2)} EM`) : "";
          return (
            <Card key={s} symbol={s}>
              <div className="grid grid-cols-2 gap-4">
                <Big label={x.em_0dte_estimated ? "EM 0DTE (stima)" : "EM 0DTE"} value={num(x.em_0dte, 1)} unit="pt" accent
                     sub={x.em_0dte != null ? `dall'open ±${num(x.em_0dte)} / ±${num(1.5 * x.em_0dte)} / ±${num(2 * x.em_0dte)}` : "nessuna foto di oggi"} />
                <Big label="Gap si chiude in RTH" value={pct(f?.rate)}
                     sub={f ? `${band}, ${f.days} giorni` : "–"} />
              </div>
              <Rows rows={[
                ["Gap ora vs chiusura ieri", `${num(x.gap, 2)} pt (${num(x.gap_em, 2)} EM)`],
                ["Ieri RTH close", num(x.prev_close, 2)],
                ["Prezzo ora", num(x.price, 2)],
                ["Range Londra", `${num(x.london_range, 2)} pt (${num(x.london_range_em, 2)} EM)`],
                ["Londra high / low", `${num(x.london_high, 2)} / ${num(x.london_low, 2)}`],
                ["EM giornaliero (VIX/VXN)", `${num(x.em)} pt`],
              ]} />
            </Card>
          );
        })}
      </div>
      <Notes items={[
        e
          ? `EM 0DTE = straddle ATM SPX dalla foto delle ${rome(e.timestamp, true)}, ${e.pre_open ? "prima" : "dopo"} l'apertura cash (${num(e.minutes_to_close)} minuti alla chiusura). Per NQ è scalato con VXN/VIX.`
          : "Nessuna foto 0DTE di oggi: premi «aggiorna dati» sulla scheda NY.",
        `Statistica Stucchi, verificata su ES: ±1 EM toccato nel ~${pct(st.touch_1)} delle sessioni, oltre ±2 EM nel ~${pct(st.beyond_2)}, chiusura entro ±2 EM nel ~${pct(st.close_within_2)}.`,
        "Il GEX da solo non accende il setup C: serve accettazione fuori IB con CVD concorde (§5.1).",
      ]} />
    </>
  );
}

function Notes({ items }: { items: string[] }) {
  return (
    <ul className="space-y-1.5 rounded border border-border bg-bg-panel px-5 py-3 text-sm text-fg-muted">
      {items.map((t) => (
        <li key={t} className="list-inside list-disc marker:text-fg-dim">{t}</li>
      ))}
    </ul>
  );
}
