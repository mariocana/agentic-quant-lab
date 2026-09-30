#!/usr/bin/env python3
"""Genera la board HTML della pipeline prop da pipeline_status.json.

Uso: python3 mc/docs/pipeline_board.py  -> scrive mc/docs/pipeline_board.html
Poi la pagina viene ripubblicata come Artifact (stesso URL).
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "pipeline_status.json")
OUT = os.path.join(HERE, "pipeline_board.html")

LABEL = {"pass": "passato", "waiver": "passato per override registrato",
         "active": "in corso", "blocked": "bloccato",
         "fail": "fallito", "pending": "da fare", "na": "n/a"}
SYMBOL = {"pass": "✓", "waiver": "!", "active": "●", "blocked": "■", "fail": "✕",
          "pending": "·", "na": "—"}


def esc(s):
    return html.escape(str(s))


def md(text):
    """Escape + **grassetto** + `code` (il resto resta testo)."""
    out = esc(text)
    while out.count("**") >= 2:
        out = out.replace("**", "<b>", 1).replace("**", "</b>", 1)
    while out.count("`") >= 2:
        out = out.replace("`", "<code>", 1).replace("`", "</code>", 1)
    return out


def current_stage(strat, stages):
    """Stage su cui la strategia si trova ora (ultimo non-pending)."""
    st = strat.get("stages", {})
    cur = None
    for s in stages:
        v = st.get(str(s["id"]))
        if v in ("pass", "active", "blocked", "fail"):
            cur = s
    return cur


def build(d):
    stages = d["stages"]
    strategies = d["strategies"]

    # --- riga per strategia -------------------------------------------------
    rows = []
    for s in strategies:
        st = s.get("stages", {})
        cells = []
        for g in stages:
            v = st.get(str(g["id"]), "pending")
            cells.append(f'<td><span class="chip {v}" title="{esc(g["name"])}: {LABEL[v]}">'
                         f'<span class="sym">{SYMBOL[v]}</span></span></td>')
        cur = current_stage(s, stages)
        where = f'Stage {cur["id"]} · {cur["name"]}' if cur else "non iniziata"
        state = st.get(str(cur["id"])) if cur else "pending"
        m = s.get("metrics")
        metrics = ""
        if m:
            if "trade" in m:
                body = (f'{m["trade"]} trade · WR {m["wr"]} · avg {m["avg"]} · DD {m["dd"]}'
                        f' <span class="muted">({esc(m["period"])})</span>')
            else:
                # schema libero: coppie chiave/valore (metriche dichiarate, vincoli, ecc.)
                body = " · ".join(f'<span class="muted">{esc(k)}</span> {md(str(v))}'
                                  for k, v in m.items())
            metrics = f'<div class="metrics mono">{body}</div>'
        rows.append(f"""
        <tr class="strat">
          <th scope="row">
            <div class="name">{esc(s["name"])}</div>
            <div class="meta">{esc(s["family"])} · <span class="mono">{esc(s["instrument"])}</span></div>
          </th>
          {''.join(cells)}
          <td class="where"><span class="pill {state}">{esc(where)}</span></td>
        </tr>
        <tr class="note"><td colspan="{len(stages) + 2}"><div class="notetext">{md(s["note"])}</div>{metrics}</td></tr>""")

    head_cells = "".join(
        f'<th scope="col"><span class="stnum">{g["id"]}</span><span class="stname">{esc(g["short"])}</span></th>'
        for g in stages)

    # --- conteggi ------------------------------------------------------------
    n_all = len(strategies)
    n_started = sum(1 for s in strategies if s.get("stages"))
    n_blocked = sum(1 for s in strategies if "blocked" in s.get("stages", {}).values())
    furthest = 0
    for s in strategies:
        for k, v in s.get("stages", {}).items():
            if v == "pass":
                furthest = max(furthest, int(k))

    # --- diario per strategia ---
    diaries = []
    for st in strategies:
        cur = current_stage(st, stages)
        state = st.get("stages", {}).get(str(cur["id"])) if cur else "pending"
        where = f'Stage {cur["id"]} · {cur["name"]}' if cur else "non iniziata"
        entries = "".join(
            f'<li><span class="mono date">{esc(e["date"])}</span><span>{md(e["text"])}</span></li>'
            for e in st.get("log", []))
        if not entries:
            entries = '<li class="empty"><span></span><span class="muted">nessuna voce</span></li>'
        nxt = st.get("next")
        nxt_html = (f'<div class="next"><span class="lbl">prossimo</span>{md(nxt)}</div>') if nxt else ""
        diaries.append(f"""
        <section class="card diary">
          <div class="dhead">
            <h3>{esc(st["name"])}</h3>
            <span class="pill {state}">{esc(where)}</span>
          </div>
          <div class="meta mono">{esc(st["instrument"])}</div>
          {nxt_html}
          <ul class="plain log">{entries}</ul>
        </section>""")

    gates = "".join(
        f'<li><span class="gnum mono">{g["id"]}</span><div><b>{esc(g["name"])}</b>'
        f'<div class="gate">{esc(g["gate"])}</div></div></li>' for g in stages)
    blockers = "".join(f"<li>{md(b)}</li>" for b in d.get("blockers", []))
    log = "".join(
        f'<li><span class="mono date">{esc(e["date"])}</span><span>{md(e["text"])}</span></li>'
        for e in d.get("log", []))

    return f"""<title>Pipeline Prop</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --bg:#F4F6F8; --surface:#FFFFFF; --ink:#1A222C; --muted:#5F6B77; --line:#D8DEE5; --line-soft:#E9EDF1;
  --accent:#0F6E7A; --accent-ink:#0A4F58;
  --pass:#1F8A4C; --pass-bg:#DDF3E5; --active:#B86E00; --active-bg:#FBEBD0;
  --blocked:#B3261E; --blocked-bg:#F9DEDC; --pending:#8A95A0; --pending-bg:#EEF1F4; --na:#B8C0C8; --na-bg:#F2F4F6;
  --display:"IBM Plex Sans Condensed","Arial Narrow",system-ui,sans-serif;
  --body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#0F1419; --surface:#171D24; --ink:#E7EBEF; --muted:#9AA5B0; --line:#2B343E; --line-soft:#222A33;
    --accent:#4FB3BF; --accent-ink:#8ED3DB;
    --pass:#5ED28A; --pass-bg:#173B27; --active:#F2B45A; --active-bg:#3E2C10;
    --blocked:#F28B82; --blocked-bg:#4A1F1B; --pending:#7F8A95; --pending-bg:#1F262E; --na:#5C6670; --na-bg:#1A2027;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#0F1419; --surface:#171D24; --ink:#E7EBEF; --muted:#9AA5B0; --line:#2B343E; --line-soft:#222A33;
  --accent:#4FB3BF; --accent-ink:#8ED3DB;
  --pass:#5ED28A; --pass-bg:#173B27; --active:#F2B45A; --active-bg:#3E2C10;
  --blocked:#F28B82; --blocked-bg:#4A1F1B; --pending:#7F8A95; --pending-bg:#1F262E; --na:#5C6670; --na-bg:#1A2027;
}}
body {{ background:var(--bg); color:var(--ink); font-family:var(--body); font-size:14px; line-height:1.5;
       padding-inline:clamp(16px,3vw,40px); padding-block:24px 48px; }}
.wrap {{ max-width:1180px; margin:0 auto; display:grid; gap:24px; }}
h1,h2,h3 {{ font-family:var(--display); text-wrap:balance; margin:0; }}
h1 {{ font-size:2rem; font-weight:700; letter-spacing:-.01em; }}
h2 {{ font-size:1.15rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
.mono {{ font-family:var(--mono); font-variant-numeric:tabular-nums; }}
.muted {{ color:var(--muted); }}
header {{ display:grid; gap:8px; }}
header .top {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:12px 20px; }}
header .updated {{ color:var(--muted); font-size:.85rem; }}
header .goal {{ font-size:1.05rem; max-width:65ch; }}
header .facts {{ display:flex; flex-wrap:wrap; gap:8px 24px; font-size:.85rem; color:var(--muted); }}
header .facts b {{ color:var(--ink); font-weight:500; }}
.status {{ display:flex; flex-wrap:wrap; gap:8px 20px; font-size:.9rem; padding:10px 14px; background:var(--surface);
           border:1px solid var(--line); border-radius:6px; }}
.status span b {{ font-family:var(--mono); font-weight:500; }}
.board {{ background:var(--surface); border:1px solid var(--line); border-radius:6px; overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; min-width:760px; }}
thead th {{ font-family:var(--display); font-weight:600; font-size:.8rem; text-transform:uppercase; letter-spacing:.05em;
            color:var(--muted); padding:12px 6px 8px; text-align:center; border-bottom:1px solid var(--line); white-space:nowrap; }}
thead th:first-child {{ text-align:left; padding-left:16px; }}
thead th .stnum {{ display:block; font-family:var(--mono); font-size:.95rem; color:var(--ink); }}
thead th .stname {{ display:block; font-size:.7rem; }}
tr.strat th {{ text-align:left; padding:14px 12px 4px 16px; vertical-align:top; font-weight:400; }}
tr.strat td {{ text-align:center; padding:14px 6px 4px; vertical-align:middle; }}
tr.strat .name {{ font-family:var(--display); font-weight:600; font-size:1.05rem; }}
tr.strat .meta {{ color:var(--muted); font-size:.8rem; }}
tr.note td {{ padding:0 16px 14px 16px; border-bottom:1px solid var(--line-soft); }}
tr.note .notetext {{ color:var(--muted); font-size:.85rem; max-width:80ch; }}
tr.note .metrics {{ font-size:.8rem; margin-top:4px; }}
tbody tr:last-child td {{ border-bottom:0; }}
.chip {{ display:inline-grid; place-items:center; width:30px; height:30px; border-radius:4px; font-weight:600;
         border:1px solid transparent; }}
.chip.pass    {{ background:var(--pass-bg); color:var(--pass); border-color:var(--pass); }}
.chip.waiver  {{ background:var(--active-bg); color:var(--active); border-color:var(--active);
                 border-style:dashed; font-weight:700; }}
.chip.active  {{ background:var(--active-bg); color:var(--active); border-color:var(--active); }}
.chip.blocked {{ background:var(--blocked-bg); color:var(--blocked); border-color:var(--blocked); }}
.chip.fail    {{ background:var(--blocked-bg); color:var(--blocked); border-color:var(--blocked); }}
.chip.pending {{ background:var(--pending-bg); color:var(--pending); }}
.chip.na      {{ background:var(--na-bg); color:var(--na); }}
.where {{ white-space:nowrap; padding-right:16px !important; }}
.pill {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:.78rem; font-weight:500; }}
.pill.pass {{ background:var(--pass-bg); color:var(--pass); }}
.pill.waiver {{ background:var(--active-bg); color:var(--active); border:1px dashed var(--active); }}
.pill.active {{ background:var(--active-bg); color:var(--active); }}
.pill.blocked, .pill.fail {{ background:var(--blocked-bg); color:var(--blocked); }}
.pill.pending {{ background:var(--pending-bg); color:var(--pending); }}
.legend {{ display:flex; flex-wrap:wrap; gap:6px 18px; font-size:.8rem; color:var(--muted); padding:0 4px; }}
.legend .chip {{ width:20px; height:20px; font-size:.75rem; margin-right:6px; vertical-align:middle; }}
.cols {{ display:grid; grid-template-columns:minmax(0,1.3fr) minmax(0,1fr); gap:24px; }}
@media (max-width:820px) {{ .cols {{ grid-template-columns:1fr; }} }}
section.card {{ background:var(--surface); border:1px solid var(--line); border-radius:6px; padding:16px 18px; display:grid; gap:12px; align-content:start; }}
ol.gates, ul.plain {{ list-style:none; margin:0; padding:0; display:grid; gap:10px; }}
ol.gates li {{ display:grid; grid-template-columns:28px 1fr; gap:10px; align-items:start; }}
ol.gates .gnum {{ display:inline-grid; place-items:center; width:26px; height:26px; border-radius:4px; background:var(--pending-bg); color:var(--ink); font-size:.85rem; }}
ol.gates b {{ font-family:var(--display); font-weight:600; }}
ol.gates .gate {{ color:var(--muted); font-size:.85rem; }}
ul.plain li {{ padding-left:14px; position:relative; }}
ul.plain li::before {{ content:""; position:absolute; left:0; top:.6em; width:6px; height:6px; border-radius:50%; background:var(--blocked); }}
ul.log li {{ display:grid; grid-template-columns:88px 1fr; gap:10px; font-size:.9rem; }}
ul.log .date {{ color:var(--muted); font-size:.8rem; padding-top:2px; }}
.sechead {{ margin-top:8px; }}
.diaries {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr)); gap:16px; align-items:start; }}
.diary {{ gap:8px; }}
.diary .dhead {{ display:flex; flex-wrap:wrap; align-items:baseline; justify-content:space-between; gap:8px; }}
.diary h3 {{ font-size:1.1rem; font-weight:600; }}
.diary .meta {{ color:var(--muted); font-size:.8rem; }}
.diary .next {{ font-size:.85rem; border-left:2px solid var(--accent); padding:2px 0 2px 10px; }}
.diary .next .lbl {{ display:block; font-family:var(--display); text-transform:uppercase; letter-spacing:.06em;
                     font-size:.7rem; color:var(--accent-ink); }}
.diary ul.log li {{ grid-template-columns:76px 1fr; font-size:.85rem; }}
.diary ul.plain li::before {{ display:none; }}
.diary ul.plain li {{ padding-left:0; }}
li.empty {{ }}
code {{ font-family:var(--mono); font-size:.9em; background:var(--pending-bg); padding:1px 4px; border-radius:3px; }}
a {{ color:var(--accent); }}
footer {{ color:var(--muted); font-size:.8rem; }}
</style>

<div class="wrap">
  <header>
    <div class="top">
      <h1>Pipeline Prop</h1>
      <span class="updated">aggiornata il <span class="mono">{esc(d["updated"])}</span></span>
    </div>
    <p class="goal">{esc(d["goal"])}</p>
    <div class="facts">
      <span><b>Profilo</b> {esc(d["profile"])}</span>
      <span><b>Prop di riferimento</b> {esc(d["prop"])}</span>
    </div>
  </header>

  <div class="status">
    <span>strategie <b>{n_all}</b></span>
    <span>avviate <b>{n_started}</b></span>
    <span>bloccate <b>{n_blocked}</b></span>
    <span>stage più avanzato superato <b>{furthest}</b> / 9</span>
  </div>

  <div class="board">
    <table>
      <thead><tr><th scope="col">Strategia</th>{head_cells}<th scope="col">Dove sta</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
  <div class="legend">
    <span><span class="chip pass">✓</span>gate passato</span>
    <span><span class="chip waiver">!</span>passato per <b>override registrato</b>, non per merito</span>
    <span><span class="chip active">●</span>in corso</span>
    <span><span class="chip blocked">■</span>bloccato (manca qualcosa)</span>
    <span><span class="chip fail">✕</span>fallito → cimitero</span>
    <span><span class="chip pending">·</span>da fare</span>
  </div>

  <div class="cols">
    <section class="card">
      <h2>Gate per stage</h2>
      <ol class="gates">{gates}</ol>
    </section>
    <div style="display:grid;gap:24px;align-content:start">
      <section class="card">
        <h2>Blocchi attuali</h2>
        <ul class="plain">{blockers}</ul>
      </section>
      <section class="card">
        <h2>Decisioni e setup</h2>
        <ul class="plain log">{log}</ul>
      </section>
    </div>
  </div>

  <h2 class="sechead">Diario per strategia</h2>
  <div class="diaries">{''.join(diaries)}</div>

  <footer>Fonte: <span class="mono">mc/docs/pipeline_status.json</span> nel repo · regole complete in <span class="mono">mc/docs/pipeline_prop.md</span></footer>
</div>
"""


if __name__ == "__main__":
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build(data))
    print("scritto", OUT)
