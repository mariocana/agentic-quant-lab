#!/usr/bin/env python3
"""Costruisce il banco di lavoro: un sito statico in un solo file con tutto il lavoro del repo.

Uso:  python3 mc/docs/build_site.py   ->  scrive mc/docs/index.html

Un unico HTML autonomo: nessuna rete, nessun CDN, si apre con doppio clic e
funziona anche da chiavetta. Le sezioni della barra laterale:

  Oggi           panoramica + contesto della sessione (numeri da quantlake)
  Prop           board della pipeline, prossimi passi, diario, protocolli
  Strategie      una pagina per strategia (stato + note + SPEC/README/...),
                 le chiuse nel cimitero
  Discrezionale  playbook, calibrazione, schede di sessione, diario trade
  Ricerca, Archivio

Lo stato della pipeline viene da pipeline_status.json. Il contesto di sessione
viene da quantlake (quantlake.context_card, letto con il python del venv): è una
fotografia al momento della build, che rifanno nuova_sessione.sh e
start_frontends.sh. Senza quantlake la pagina dice che non è disponibile.

Dipendenza: `markdown` (pip3 install --user markdown).
"""
import glob
import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime

try:
    import markdown
except ImportError:
    sys.exit("Manca il pacchetto markdown.  pip3 install --user markdown")

try:
    from zoneinfo import ZoneInfo
    ROME = ZoneInfo("Europe/Rome")
except Exception:  # python senza zoneinfo: ora locale
    ROME = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "index.html")
STATUS = os.path.join(HERE, "pipeline_status.json")
QL = os.path.join(ROOT, "python", "quantlake")

# ---------------------------------------------------------------- documenti
# (titolo, percorso relativo alla radice del repo). L'ordine è quello della
# barra laterale: è la mappa del lavoro, non un elenco alfabetico.
PROP_DOCS = [
    ("La pipeline in una pagina", "mc/docs/pipeline_semplice.md"),
    ("La seconda gamba", "mc/docs/seconda_gamba.md"),
    ("Il difetto nel metodo di misura", "mc/docs/bug_misura_primo_tocco.md"),
    ("Prop vs Live: due metodologie", "mc/docs/prop_vs_live.md"),
    ("Il protocollo prop", "mc/docs/pipeline_prop.md"),
    ("Metodologia live (stand-by)", "mc/docs/metodologia_live.md"),
    ("Strumenti e costi LucidFlex", "mc/docs/lucid_strumenti.md"),
    ("Protocollo di test MC", "mc/docs/protocollo_test_mc.md"),
    ("Prompt ricerca strategie", "mc/docs/prompt_ricerca_strategie.md"),
    ("Setup TradeStation", "mc/docs/setup_tradestation.md"),
    ("Digest del corso", "mc/docs/institutional_protocol_digest.md"),
]
DISCR_DOCS = [
    ("Playbook orderflow Londra", "education/enrico_stucchi/PLAYBOOK.md"),
    ("Calibrazione del contesto", "education/enrico_stucchi/CALIBRAZIONE_contesto.md"),
    ("Scheda sessione Londra", "education/enrico_stucchi/sessioni/TEMPLATE_london.md"),
    ("Scheda sessione NY", "education/enrico_stucchi/sessioni/TEMPLATE_ny.md"),
    ("Diario trade", "journal/journal_swing/README.md"),
]
RESEARCH_DOCS = [
    ("Journal degli ingest", "mc/docs/ingest_journal.md"),
    ("MOC — scheda di ricerca", "ideas/MOC_ricerca.md"),
    ("GEX / Freddy", "ideas/NOTES_gex_freddy.md"),
    ("Morpheus — modelli intraday 1-5", "education/morpheus/ANALISI_modelli_intraday_1-5.md"),
    ("Unger — i due PDF", "education/unger/NOTES_unger_pdf.md"),
    ("SSRN — i tre paper scartati", "ideas/NOTES_ssrn_batch.md"),
    ("Elder — Vivere di trading", "education/books/NOTES_elder.md"),
    ("Palmquist — candlestick", "education/books/NOTES_palmquist_candlestick.md"),
]
ARCHIVE_DOCS = [
    ("Fase 2 — testing", "mql5/docs/fase2_testing.md"),
    ("Protocollo IVB / ORB", "mql5/docs/protocols/ivb_orb.md"),
    ("Protocollo ORB breakout", "mql5/docs/protocols/orb_breakout.md"),
    ("Protocollo Turtle", "mql5/docs/protocols/turtle_breakout.md"),
]
# Strategie con una cartella ma senza riga in pipeline_status.json (idee, note).
EXTRA_STRATEGIES = [
    {"name": "Quant VWAP", "family": "idea", "instrument": "", "path": "mc/strategies/Quant_VWAP"},
]
# Ordine dei documenti dentro la pagina di una strategia.
STRATEGY_FILES = ["SPEC.md", "CHECKLIST*.md", "README*.md", "NOTES*.md"]
DOC_LABEL = {"SPEC": "Spec", "CHECKLIST": "Checklist", "README": "Readme", "NOTES": "Note"}

LABEL = {"pass": "passato", "waiver": "passato per override registrato",
         "active": "in corso", "blocked": "bloccato",
         "fail": "fallito", "pending": "da fare", "na": "n/a"}
SYMBOL = {"pass": "✓", "waiver": "!", "active": "●", "blocked": "■", "fail": "✕",
          "pending": "·", "na": "—"}
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def esc(s):
    return html.escape(str(s))


def slug(path):
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")


def inline(text):
    """Grassetto, corsivo e `code` dentro una stringa che arriva dal JSON."""
    out = esc(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)   # prima il doppio asterisco
    out = re.sub(r"\*(.+?)\*", r"<em>\1</em>", out)      # poi quello singolo
    out = re.sub(r"`(.+?)`", r"<code>\1</code>", out)
    return out


def exists(rel):
    return os.path.exists(os.path.join(ROOT, rel))


# ---------------------------------------------------------------- markdown
def render_md(text):
    # ~~barrato~~ non è nel markdown di base: lo traduciamo prima.
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    return markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        output_format="html5")


def rewrite_links(body, src_rel, by_path):
    """I link fra documenti diventano ancore interne; gli altri restano file."""
    def repl(m):
        href = m.group(1)
        if href.startswith(("#", "http://", "https://", "mailto:")):
            return m.group(0)
        target, _, frag = href.partition("#")
        if not target:
            return m.group(0)
        resolved = os.path.normpath(
            os.path.join(os.path.dirname(src_rel), target))
        if resolved in by_path:
            return 'href="#%s"' % by_path[resolved]
        return 'href="%s" class="ext" title="file nel repo: %s"' % (
            esc(href), esc(resolved))
    return re.sub(r'href="([^"]+)"', repl, body)


def headings(body, doc_id):
    """Numera gli h2/h3 e restituisce (body con id, indice)."""
    items = []
    n = [0]

    def repl(m):
        level, attrs, text = m.group(1), m.group(2), m.group(3)
        n[0] += 1
        hid = "%s-h%d" % (doc_id, n[0])
        plain = re.sub(r"<[^>]+>", "", text).strip()
        items.append((level, hid, plain))
        return '<h%s id="%s"%s>%s</h%s>' % (level, hid, attrs, text, level)

    body = re.sub(r"<h([23])([^>]*)>(.*?)</h\1>", repl, body, flags=re.S)
    return body, items


def doc_body(rel, by_path, demote=False):
    """Markdown del repo -> HTML con link interni e tabelle scorrevoli."""
    with open(os.path.join(ROOT, rel), encoding="utf8") as f:
        body = render_md(f.read())
    body = rewrite_links(body, rel, by_path)
    # immagini: il percorso nel markdown è relativo al documento, il sito sta in mc/docs
    body = re.sub(r'src="(?!https?:|data:|/)([^"]+)"',
                  lambda m: 'src="%s"' % os.path.relpath(os.path.join(ROOT, os.path.dirname(rel), m.group(1)), HERE),
                  body)
    # tabelle in un contenitore scorrevole: su schermo stretto una tabella
    # larga farebbe scorrere l'intera pagina, tagliando il testo a sinistra
    body = body.replace("<table>", '<div class="scroll"><table>')
    body = body.replace("</table>", "</table></div>")
    if demote:  # documento dentro la pagina di una strategia: h1 -> h3, h2 -> h3, h3 -> h4
        body = re.sub(r"<(/?)h3([ >])", r"<\1h4\2", body)
        body = re.sub(r"<(/?)h[12]([ >])", r"<\1h3\2", body)
    return body


# ---------------------------------------------------------------- pipeline
def is_dead(s):
    return "fail" in (s.get("stages") or {}).values()


def strategy_id(name):
    return "strategia-" + slug(name)


def board(st, link=True):
    rows = []
    for s in st["strategies"]:
        if not s.get("stages"):
            continue
        cells = []
        for g in st["stages"]:
            v = s["stages"].get(str(g["id"]), "na")
            cells.append(
                '<td><span class="chip %s" title="%s: %s">%s</span></td>'
                % (v, esc(g["name"]), LABEL.get(v, v), SYMBOL.get(v, "?")))
        name = esc(s["name"]) + (" †" if is_dead(s) else "")
        if link and s.get("path"):
            name = '<a href="#%s">%s</a>' % (strategy_id(s["name"]), name)
        rows.append('<tr><th>%s<span class="sub">%s</span></th>%s</tr>'
                    % (name, esc(s.get("instrument", "")), "".join(cells)))
    head = "".join('<th title="%s"><span>%s</span></th>'
                   % (esc(g["gate"]), esc(g["short"])) for g in st["stages"])
    return """
<div class="scroll">
 <table class="board"><thead><tr><th></th>%s</tr></thead><tbody>%s</tbody></table>
</div>
<p class="legend">
  <span class="chip pass">✓</span> passato
  <span class="chip waiver">!</span> override
  <span class="chip active">●</span> in corso
  <span class="chip blocked">■</span> bloccato
  <span class="chip fail">✕</span> fallito
  <span class="chip pending">·</span> da fare
  &nbsp;· † nel cimitero
</p>""" % (head, "".join(rows))


def todo_groups(td, groups=None):
    gs = td["groups"] if groups is None else groups
    return "".join(
        '<div class="tg"><h3>%s%s</h3><ul>%s</ul></div>'
        % (esc(g["title"]),
           ' <span class="note">%s</span>' % esc(g["note"]) if g.get("note") else "",
           "".join("<li>%s</li>" % inline(i) for i in g["items"]))
        for g in gs)


def log_items(entries):
    return "".join('<li><time>%s</time><div>%s</div></li>' % (esc(e["date"]), inline(e["text"]))
                   for e in entries)


def pipeline_page(st):
    td = st.get("todo") or {"groups": []}
    blockers = "".join("<li>%s</li>" % inline(b) for b in st.get("blockers", []))
    return """
<header class="hero"><p class="eyebrow">Prop · aggiornato al %s</p><h1>Pipeline prop</h1>
<p class="goal">%s</p></header>
<h2>Board</h2>%s
<h2>Prossimo passo <span class="note">memo del %s</span></h2>
<section class="todo">%s<p class="more-links"><a href="#prossimi-passi">Tutti i prossimi passi →</a></p></section>
<section class="cols">
  <div><h2>Profilo cercato</h2><p>%s</p><h2>Conto</h2><p>%s</p></div>
  <div><h2>Blocchi aperti</h2><ul class="blockers">%s</ul></div>
</section>
<p class="more-links"><a href="#prossimi-passi">Prossimi passi →</a> · <a href="#diario">Diario di bordo →</a>
 · <a href="#%s">Il protocollo →</a></p>
""" % (esc(st["updated"]), esc(st["goal"]), board(st), esc(td.get("updated", "")), todo_groups(td, td["groups"][:1]),
       inline(st.get("profile", "")),
       inline(st.get("prop", "")), blockers, slug("mc/docs/pipeline_prop.md"))


def todo_page(st):
    td = st.get("todo") or {"groups": []}
    return ('<header class="hero"><p class="eyebrow">Prop · memo del %s</p><h1>Prossimi passi</h1></header>'
            '<section class="todo">%s</section>' % (esc(td.get("updated", "")), todo_groups(td)))


def diary_page(st):
    return ('<header class="hero"><p class="eyebrow">Prop · %d voci</p><h1>Diario di bordo</h1></header>'
            '<ol class="log">%s</ol>' % (len(st.get("log", [])), log_items(st.get("log", []))))


def strategy_docs(path):
    seen, out = set(), []
    for pat in STRATEGY_FILES:
        for f in sorted(glob.glob(os.path.join(ROOT, path, pat))):
            rel = os.path.relpath(f, ROOT)
            if rel not in seen:
                seen.add(rel)
                out.append(rel)
    return out


def strategy_page(s, st, by_path):
    """Stato dalla pipeline + tutti i markdown della cartella della strategia."""
    pid = strategy_id(s["name"])
    parts = ['<header class="hero"><p class="eyebrow">Strategia%s%s</p><h1>%s%s</h1></header>'
             % (" · " + esc(s["family"]) if s.get("family") else "",
                " · " + esc(s["instrument"]) if s.get("instrument") else "",
                esc(s["name"]), ' <span class="tag dead">cimitero</span>' if is_dead(s) else "")]
    toc = []
    if s.get("stages"):
        chips = "".join(
            '<span class="stage"><span class="chip %s" title="%s">%s</span><small>%s</small></span>'
            % (s["stages"].get(str(g["id"]), "na"), esc(g["gate"]),
               SYMBOL.get(s["stages"].get(str(g["id"]), "na"), "?"), esc(g["short"]))
            for g in st["stages"])
        parts.append('<div class="stages">%s</div>' % chips)
    if s.get("note"):
        parts.append("<p>%s</p>" % inline(s["note"]))
    if s.get("next"):
        parts.append('<blockquote><b>Prossimo:</b> %s</blockquote>' % inline(s["next"]))
    if s.get("metrics"):
        rows = "".join("<tr><th>%s</th><td>%s</td></tr>" % (esc(k), inline(v)) for k, v in s["metrics"].items())
        parts.append('<div class="scroll"><table class="kv">%s</table></div>' % rows)
    if s.get("log"):
        hid = pid + "-log"
        toc.append(("2", hid, "Diario della strategia"))
        parts.append('<h2 id="%s">Diario della strategia</h2><ol class="log">%s</ol>' % (hid, log_items(s["log"])))
    for rel in strategy_docs(s["path"]):
        base = os.path.basename(rel).split("_")[0].split(".")[0].upper()
        title = DOC_LABEL.get(base, os.path.basename(rel))
        did = slug(rel)
        body, items = headings(doc_body(rel, by_path, demote=True), did)
        toc.append(("2", did, title))
        toc += [("3", hid, txt) for lvl, hid, txt in items if lvl == "3"]
        parts.append('<h2 id="%s">%s <span class="note"><code>%s</code></span></h2>%s' % (did, esc(title), esc(rel), body))
    return pid, "".join(parts), toc


# ---------------------------------------------------------------- contesto
def context_card():
    """Il contesto di sessione calcolato da quantlake, o (None, motivo)."""
    py = os.path.join(QL, ".venv", "bin", "python")
    if not os.path.exists(py):
        return None, "python di quantlake non trovato (%s)" % py
    code = "import json; from quantlake.context_card import card; print(json.dumps(card(), default=str))"
    try:
        r = subprocess.run([py, "-c", code], cwd=QL, capture_output=True, text=True, timeout=120)
    except Exception as e:
        return None, str(e)
    if r.returncode != 0:
        lines = r.stderr.strip().splitlines()
        return None, lines[-1] if lines else "errore sconosciuto"
    return json.loads(r.stdout), None


def num(x, d=0):
    if x is None:
        return "–"
    s = "{:,.{}f}".format(x, d)
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x):
    return "–" if x is None else "%d%%" % round(x * 100)


def when(iso, day=False):
    if not iso:
        return "–"
    t = datetime.fromisoformat(iso)
    if ROME is not None and t.tzinfo is not None:
        t = t.astimezone(ROME)
    return t.strftime("%d/%m %H:%M" if day else "%H:%M")


IT = {"low": "bassa", "high": "alta", "up": "su", "down": "giù", "positive": "positivo", "negative": "negativo"}


def it(x):
    return "–" if x is None else IT.get(x, x)


def stat(label, value, sub="", warn=False):
    return ('<div class="stat%s"><small>%s</small><b>%s</b><span>%s</span></div>'
            % (" warn" if warn else "", esc(label), esc(value), esc(sub)))


def big(label, value, unit="pt", sub="", accent=False):
    return ('<div class="big%s"><small>%s</small><b>%s<i>%s</i></b><span>%s</span></div>'
            % (" accent" if accent else "", esc(label), esc(value), esc(unit), sub))


def rows(items):
    return '<dl class="rows">%s</dl>' % "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (esc(k), esc(v)) for k, v in items)


def range_bar(q):
    if not q or any(v is None for v in q):
        return ""
    p25, p50, p75 = q
    top = p75 * 1.25
    w = lambda x: "%.1f%%" % (x / top * 100)
    return ('<div class="rbar"><small>Range Londra atteso (punti)</small>'
            '<div class="track"><div class="band" style="left:%s;width:calc(%s - %s)"></div>'
            '<div class="mid" style="left:%s"></div></div>'
            '<div class="ticks"><span>p25 %s</span><span><b>mediana %s</b></span><span>p75 %s</span></div></div>'
            % (w(p25), w(p75), w(p25), w(p50), num(p25), num(p50), num(p75)))


def context_page(c, err):
    if c is None:
        return ('<header class="hero"><p class="eyebrow">Oggi</p><h1>Contesto sessione</h1></header>'
                '<div class="warn">Contesto non disponibile: %s. Si genera con quantlake '
                '(<code>python/quantlake/applications/contesto.py</code>).</div>' % esc(err))
    d = datetime.fromisoformat(c["session_date"])
    g, inst, e = c["regime"], c["instruments"], c["em_0dte"]
    out = ['<header class="hero"><p class="eyebrow">Oggi · calcolato alle %s</p><h1>%s %d %s</h1>'
           '<p class="goal">I numeri della sezione 0 delle schede di sessione. Si aggiornano con '
           '<code>nuova_sessione.sh</code> e a ogni avvio di <code>start_frontends.sh</code>.</p></header>'
           % (when(c["generated_at"], day=True), GIORNI[d.weekday()].capitalize(), d.day, MESI[d.month - 1]),
           '<div class="warn stale" data-generated="%s" hidden>Questi numeri hanno più di 12 ore: '
           'aggiornali con <code>nuova_sessione.sh</code>.</div>' % esc(c["generated_at"])]
    out += ['<div class="warn">%s</div>' % esc(w) for w in c["warnings"]]
    stress = (g["term_9d"] or 0) > 1
    out.append('<div class="stats">%s%s%s%s</div>' % (
        stat("Volatilità", it(g["vol_regime"]), "%s dell'anno" % pct(g["iv_pct"])),
        stat("Trend 20 giorni", it(g["trend20"]), "quadrante %s" % (g["quadrant"] or "–")),
        stat("GEX", "BASSO" if g["gex_low"] else it(g["gex_regime"]), "%s dell'anno" % pct(g["gex_pct"]), g["gex_low"]),
        stat("VIX9D / VIX", num(g["term_9d"], 2), "stress a breve" if stress else "struttura normale", stress)))
    if g["gex_low"]:
        out.append('<div class="alert">GEX basso: i trend day sono %s contro %s. Londra: interruttore trend day '
                   'con un solo segnale. NY: trend più probabile, ma il setup C resta legato all\'accettazione '
                   'fuori IB.</div>' % (pct(g["trend_rate_gex_low"]), pct(g["trend_rate_gex_high"])))

    out.append('<h2 id="ctx-london">Londra · 09:00</h2><div class="cards">')
    for s in ("ES", "NQ"):
        x = inst[s]
        out.append('<section class="card"><h4>%s</h4><div class="bigs">%s%s</div>%s%s</section>' % (
            s,
            big("EM giornaliero", num(x["em"]), sub="IV %s (%s), %s dell'anno"
                % (num(x["iv"], 1), "VIX" if s == "ES" else "VXN", pct(x["iv_pct"]))),
            big("Mercato fermo se stop >", num(x["stop_max"], 1), sub="oltre: si guarda e basta", accent=True),
            range_bar(x["london_range_q"]),
            rows([("Ieri RTH high", num(x["prev_high"], 2)), ("Ieri RTH low", num(x["prev_low"], 2)),
                  ("Ieri RTH close", num(x["prev_close"], 2)),
                  ("Asia high / low", "%s / %s" % (num(x["asia_high"], 2), num(x["asia_low"], 2))),
                  ("Range asiatico", "%s pt" % num(x["asia_range"], 2)), ("Prezzo", num(x["price"], 2))])))
    out.append('</div><ul class="notes"><li>Mercato fermo (§1.3): in un quarto delle mattine Londra fa meno del '
               'p25. Se il tuo stop supera la soglia, l\'oscillazione attesa non arriva a 2× lo stop.</li>'
               '<li>Il regime della mattina (rotazionale o direzionale) non si prevede da questi numeri: si legge '
               'live dall\'accettazione.</li></ul>')

    out.append('<h2 id="ctx-ny">New York · 15:30</h2><div class="cards">')
    for s in ("ES", "NQ"):
        x = inst[s]
        f = x["gap_fill"]
        band = ""
        if f:
            band = ("gap %s–%s EM" % (num(f["lo"], 2), num(f["hi"], 2)) if f["hi"] else "gap > %s EM" % num(f["lo"], 2))
            band += ", %d giorni" % f["days"]
        em0 = x["em_0dte"]
        out.append('<section class="card"><h4>%s</h4><div class="bigs">%s%s</div>%s</section>' % (
            s,
            big("EM 0DTE" + (" (stima)" if x["em_0dte_estimated"] else ""), num(em0, 1), accent=True,
                sub=("dall'open ±%s / ±%s / ±%s" % (num(em0), num(1.5 * em0), num(2 * em0))) if em0 is not None
                else "nessuna foto di oggi"),
            big("Gap si chiude in RTH", pct(f["rate"]) if f else "–", unit="", sub=esc(band)),
            rows([("Gap vs chiusura ieri", "%s pt (%s EM)" % (num(x["gap"], 2), num(x["gap_em"], 2))),
                  ("Ieri RTH close", num(x["prev_close"], 2)), ("Prezzo", num(x["price"], 2)),
                  ("Range Londra", "%s pt (%s EM)" % (num(x["london_range"], 2), num(x["london_range_em"], 2))),
                  ("Londra high / low", "%s / %s" % (num(x["london_high"], 2), num(x["london_low"], 2))),
                  ("EM giornaliero (VIX/VXN)", "%s pt" % num(x["em"]))])))
    stats = c["stucchi_em_stats"]
    em_note = ("EM 0DTE = straddle ATM SPX dalla foto delle %s, %s l'apertura cash (%s minuti alla chiusura). "
               "Per NQ è scalato con VXN/VIX." % (when(e["timestamp"], day=True), "prima del" if e["pre_open"] else "dopo",
                                                 num(e["minutes_to_close"])) if e else
               "Nessuna foto 0DTE di oggi: la scatta il job Railway o <code>nuova_sessione.sh ny</code>.")
    out.append('</div><ul class="notes"><li>%s</li><li>Statistica Stucchi, verificata su ES: ±1 EM toccato nel ~%s '
               'delle sessioni, oltre ±2 EM nel ~%s, chiusura entro ±2 EM nel ~%s.</li><li>Il GEX da solo non '
               'accende il setup C: serve accettazione fuori IB con CVD concorde (§5.1).</li></ul>'
               % (em_note, pct(stats["touch_1"]), pct(stats["beyond_2"]), pct(stats["close_within_2"])))
    toc = [("2", "ctx-london", "Londra · 09:00"), ("2", "ctx-ny", "New York · 15:30")]
    return "".join(out), toc


# ---------------------------------------------------------------- pagina
CSS = """
/* Stile allineato alla dashboard di quantlake: terminale scuro, accento ambra,
   Inter + JetBrains Mono (se installati; altrimenti font di sistema: il sito
   resta senza rete). Scuro di default, chiaro col pulsante ◐. */
:root{
  color-scheme:dark;
  --bg:#0a0a0b; --panel:#111113; --elev:#16161a; --ink:#e4e4e7; --muted:#8b8b94; --dim:#52525b;
  --line:#1f1f23; --line-strong:#2a2a30;
  --accent:#f59e0b; --accent-hover:#fbbf24; --accent-soft:rgba(245,158,11,.10); --code:#16161a;
  --pass:#22c55e; --fail:#f87171; --active:#f59e0b; --blocked:#a1a1aa;
  --pending:#52525b; --waiver:#fbbf24;
  --sans:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
:root[data-theme="light"]{
  color-scheme:light;
  --bg:#fafafa; --panel:#ffffff; --elev:#f4f4f5; --ink:#18181b; --muted:#52525b; --dim:#a1a1aa;
  --line:#e4e4e7; --line-strong:#d4d4d8;
  --accent:#b45309; --accent-hover:#92400e; --accent-soft:#fef3c7; --code:#f4f4f5;
  --pass:#15803d; --fail:#dc2626; --active:#b45309; --blocked:#52525b;
  --pending:#a1a1aa; --waiver:#a16207;
}
::selection{background:rgba(245,158,11,.3)}
*{scrollbar-width:thin; scrollbar-color:var(--line-strong) transparent}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font:15px/1.65 var(--sans);
}
a{color:var(--accent); text-decoration:none; border-bottom:1px solid transparent}
a:hover{border-bottom-color:currentColor}
code,pre,kbd{font-family:var(--mono)}
code{background:var(--code); padding:.1em .35em; border-radius:3px; font-size:.84em; border:1px solid var(--line)}
pre{background:var(--code); padding:14px 16px; border-radius:4px; overflow:auto;
    font-size:.84em; line-height:1.5; border:1px solid var(--line)}
pre code{background:none; padding:0; font-size:1em}

.layout{display:flex; min-height:100vh}

/* ---- barra laterale ---- */
aside{
  width:272px; flex:0 0 272px; background:var(--panel);
  border-right:1px solid var(--line); position:sticky; top:0; height:100vh;
  overflow-y:auto; padding:18px 0 40px;
}
.brand{padding:0 20px 14px; display:flex; flex-direction:column; gap:2px}
.brand b{font-family:var(--mono); font-size:.9rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase}
.brand b a{color:var(--ink)!important}
.brand b::before{content:"◆ "; color:var(--accent)}
.brand span{font-size:.72rem; color:var(--muted); font-family:var(--mono)}
.search{padding:0 16px 12px}
.search input{
  width:100%; padding:8px 11px; border:1px solid var(--line-strong); border-radius:4px;
  background:var(--bg); color:var(--ink); font:inherit; font-family:var(--mono); font-size:.78rem;
}
.search input:focus{outline:none; border-color:var(--accent)}
nav h3{
  margin:16px 0 4px; padding:0 20px; font-size:.68rem; letter-spacing:.09em;
  text-transform:uppercase; color:var(--accent); font-family:var(--mono); font-weight:600;
}
nav a{
  display:block; padding:5px 20px 5px 20px; font-size:.87rem; color:var(--ink);
  border-bottom:none; border-left:2px solid transparent; line-height:1.35;
}
nav a:hover{background:var(--elev)}
nav a.on{border-left-color:var(--accent); background:var(--elev); color:var(--accent)}
nav a .hit{color:var(--muted); font-size:.74rem; font-family:var(--mono)}
nav.filtering h3{display:none}

/* ---- contenuto ---- */
main{flex:1; min-width:0; display:flex; justify-content:center; padding:0 0 120px}
article{display:none; width:100%; max-width:760px; padding:40px 32px; scroll-margin-top:56px}
h2,h3{scroll-margin-top:56px}
article.on{display:block}
article>*:first-child{margin-top:0}
h1{font-size:1.85rem; line-height:1.2; letter-spacing:-.02em; margin:0 0 .5em; font-weight:600}
h2{font-size:1.25rem; margin:2.2em 0 .5em; letter-spacing:-.01em; font-weight:600;
   padding-bottom:.25em; border-bottom:1px solid var(--line-strong)}
h3{font-size:1.06rem; margin:1.8em 0 .4em}
h4{font-size:.95rem; margin:1.5em 0 .3em; color:var(--muted)}
p,li{overflow-wrap:break-word}
blockquote{
  margin:1.4em 0; padding:.6em 0 .6em 18px; border-left:3px solid var(--accent);
  color:var(--muted); background:var(--accent-soft); border-radius:0 4px 4px 0;
  padding-right:16px;
}
blockquote p:first-child{margin-top:0} blockquote p:last-child{margin-bottom:0}
table{border-collapse:collapse; width:100%; margin:1.3em 0; font-size:.88rem;
      font-family:var(--sans)}
th,td{border:1px solid var(--line); padding:7px 10px; text-align:left; vertical-align:top}
th{background:var(--elev); font-weight:600; font-family:var(--mono); font-size:.92em; letter-spacing:.02em}
tbody tr:nth-child(even){background:color-mix(in srgb,var(--panel) 60%,transparent)}
hr{border:none; border-top:1px solid var(--line); margin:2.4em 0}
img{max-width:100%; height:auto; border-radius:4px; border:1px solid var(--line)}
del{color:var(--muted)}
.ext{border-bottom:1px dotted currentColor; opacity:.75}
.scroll{overflow-x:auto; -webkit-overflow-scrolling:touch; max-width:100%}
.scroll table{margin:1.3em 0}
main{overflow-x:hidden}

/* ---- indice a destra ---- */
.toc{
  position:sticky; top:0; align-self:flex-start; width:210px; flex:0 0 210px;
  padding:48px 20px 40px; font-size:.8rem; max-height:100vh; overflow-y:auto;
  font-family:var(--sans);
}
.toc b{display:block; font-size:.68rem; letter-spacing:.09em; text-transform:uppercase;
       color:var(--muted); margin-bottom:8px; font-weight:600}
.toc a{display:block; padding:3px 0 3px 10px; color:var(--muted);
       border-left:2px solid var(--line); line-height:1.35}
.toc a.l3{padding-left:22px; font-size:.95em}
.toc a:hover{color:var(--accent); border-left-color:var(--accent)}
.toc:empty{display:none}

/* ---- dashboard ---- */
.hero{margin-bottom:2em}
.eyebrow{font-size:.7rem; letter-spacing:.1em; text-transform:uppercase;
         color:var(--accent); margin:0 0 .4em; font-family:var(--mono); font-weight:600}
.goal{font-size:1.1rem; color:var(--muted); margin:0}
.board{font-size:.82rem}
.board th:first-child{width:11.5em}
.board tbody th{text-align:left; font-weight:600; background:var(--panel)}
.board .sub{display:block; font-weight:400; font-size:.86em; color:var(--muted)}
.board td{text-align:center; padding:4px}
.chip{
  display:inline-flex; align-items:center; justify-content:center;
  width:22px; height:22px; border-radius:3px; font-size:.75rem; font-weight:700; font-family:var(--mono);
  background:var(--elev); color:var(--pending); border:1px solid var(--line); cursor:default;
}
.chip.pass{background:color-mix(in srgb,var(--pass) 16%,transparent); color:var(--pass); border-color:color-mix(in srgb,var(--pass) 50%,transparent)}
.chip.fail{background:color-mix(in srgb,var(--fail) 16%,transparent); color:var(--fail); border-color:color-mix(in srgb,var(--fail) 50%,transparent)}
.chip.active{background:color-mix(in srgb,var(--active) 16%,transparent); color:var(--active); border-color:color-mix(in srgb,var(--active) 50%,transparent)}
.chip.blocked{background:color-mix(in srgb,var(--blocked) 16%,transparent); color:var(--blocked); border-color:color-mix(in srgb,var(--blocked) 50%,transparent)}
.chip.waiver{background:color-mix(in srgb,var(--waiver) 16%,transparent); color:var(--waiver); border:1px dashed var(--waiver)}
.chip.pending{color:var(--pending)}
.legend{font-size:.76rem; color:var(--muted); display:flex; align-items:center;
        gap:6px; flex-wrap:wrap; font-family:var(--sans)}
.legend .chip{width:19px; height:19px; font-size:.7rem}
.cols{display:grid; grid-template-columns:1fr 1fr; gap:0 36px}
.blockers{padding-left:1.1em} .blockers li{margin:.5em 0}
.log{list-style:none; padding:0; margin:0}
.log li{display:flex; gap:14px; padding:12px 0; border-top:1px solid var(--line)}
.log time{flex:0 0 5.4em; color:var(--muted); font-size:.74rem;
          font-family:var(--mono); padding-top:.28em}
.log div{min-width:0}
.todo{border:1px solid var(--line); border-left:3px solid var(--accent);
      border-radius:0 4px 4px 0; padding:4px 22px 18px; background:var(--panel)}
.todo h2{border:none; margin-top:1.1em; padding-bottom:0}
.todo h3{font-size:.95rem; margin:1.3em 0 .3em;
         font-family:var(--sans)}
.todo ul{margin:.3em 0; padding-left:1.15em}
.todo li{margin:.32em 0}
.todo .tg:first-of-type{margin-top:-.4em}
.note{font-weight:400; font-size:.76rem; color:var(--muted); letter-spacing:0;
      font-family:var(--sans); text-transform:none}
.more{margin-top:14px}
.more summary{cursor:pointer; color:var(--accent); font-size:.85rem;
              font-family:var(--sans)}
.more .log{margin-top:6px}

/* ---- barra superiore mobile ---- */
.topbar{display:none; position:sticky; top:0; z-index:20; background:var(--panel);
        border-bottom:1px solid var(--line); padding:9px 14px; align-items:center; gap:10px}
.topbar button{background:none; border:1px solid var(--line-strong); border-radius:4px;
               color:var(--ink); font:inherit; font-size:.8rem; padding:5px 10px; cursor:pointer}
.topbar b{font-size:.9rem; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}

@media (max-width:1180px){ .toc{display:none} }
@media (max-width:860px){
  .topbar{display:flex}
  .layout{display:block}
  aside{position:fixed; z-index:30; left:0; top:0; height:100vh; transform:translateX(-100%);
        transition:transform .2s ease; box-shadow:0 0 40px rgba(0,0,0,.18); width:86vw; max-width:300px}
  body.nav-open aside{transform:none}
  article{padding:22px 16px 60px}
  .cols{grid-template-columns:1fr}
  h1{font-size:1.6rem}
}
@media print{
  aside,.toc,.topbar{display:none}
  article{display:block !important; max-width:none; page-break-after:always}
}

/* ---- navigazione a gruppi ---- */
nav details{margin:10px 0 0}
nav summary{
  cursor:pointer; list-style:none; padding:4px 20px; font-size:.68rem; letter-spacing:.09em;
  text-transform:uppercase; color:var(--muted); font-family:var(--mono); font-weight:600;
}
nav summary::-webkit-details-marker{display:none}
nav summary::before{content:"▸ "; color:var(--dim)}
nav details[open] summary::before{content:"▾ "}
nav details.sub summary{text-transform:none; letter-spacing:0; font-size:.8rem; font-family:var(--sans); font-weight:400}
nav details.sub a{padding-left:32px; color:var(--muted)}
nav.filtering summary{display:none}
nav a.main{font-size:.95rem; font-weight:600; padding:8px 20px}
nav details.altro{margin-top:18px; border-top:1px solid var(--line); padding-top:8px}
nav details.altro h4{margin:12px 0 2px; padding:0 20px; font-size:.64rem; letter-spacing:.09em;
  text-transform:uppercase; color:var(--dim); font-family:var(--mono); font-weight:600}
nav details.altro a{font-size:.84rem; color:var(--muted)}
nav.filtering h4{display:none}

/* ---- pagine: panoramica, contesto, strategie ---- */
.tiles{display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; margin:0 0 1em}
.tile{display:block; background:var(--panel); border:1px solid var(--line); border-radius:4px;
      padding:14px 16px; color:var(--ink)!important; border-bottom:1px solid var(--line)}
a.tile:hover{border-color:var(--accent)}
.tile small,.stat small,.big small,.rbar small{display:block; font-family:var(--mono); font-size:.66rem;
      letter-spacing:.09em; text-transform:uppercase; color:var(--muted)}
.tile h4{margin:.3em 0 .5em; font-size:1rem; color:var(--accent)}
.tile p{margin:.25em 0; font-size:.86rem}
.tile-num b{font-family:var(--mono)}
.more-links{font-size:.86rem; margin-top:.8em}
.warn,.alert{border:1px solid color-mix(in srgb,var(--active) 55%,transparent); background:var(--accent-soft);
      border-radius:4px; padding:9px 13px; margin:8px 0; font-size:.88rem}
.alert{border-color:color-mix(in srgb,var(--fail) 60%,transparent); background:color-mix(in srgb,var(--fail) 10%,transparent)}
.warn::before{content:"⚠ "; color:var(--accent)}
.stats{display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:14px 0}
.stat{background:var(--panel); border:1px solid var(--line); border-radius:4px; padding:10px 14px}
.stat b{display:block; font-size:1.15rem; margin:.15em 0}
.stat span{font-size:.78rem; color:var(--muted)}
.stat.warn{border-color:color-mix(in srgb,var(--fail) 60%,transparent)} .stat.warn::before{content:none}
.stat.warn b{color:var(--fail)}
.cards{display:grid; grid-template-columns:1fr 1fr; gap:12px}
.card{background:var(--panel); border:1px solid var(--line); border-radius:4px; padding:16px 18px}
.card h4{margin:0 0 12px; font-family:var(--mono); color:var(--accent); letter-spacing:.06em}
.bigs{display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px}
.big b{display:block; font-family:var(--mono); font-size:1.9rem; font-weight:600; line-height:1.2; margin:.15em 0}
.big b i{font-style:normal; font-size:.9rem; color:var(--muted); margin-left:4px; font-weight:400}
.big.accent b{color:var(--accent)}
.big span{font-size:.76rem; color:var(--muted)}
.rbar{margin:4px 0 14px}
.rbar .track{position:relative; height:8px; background:var(--elev); border-radius:4px; margin-top:8px}
.rbar .band{position:absolute; top:0; bottom:0; background:color-mix(in srgb,var(--accent) 35%,transparent); border-radius:4px}
.rbar .mid{position:absolute; top:-3px; bottom:-3px; width:2px; background:var(--accent)}
.rbar .ticks{display:flex; justify-content:space-between; font-family:var(--mono); font-size:.74rem; color:var(--muted); margin-top:5px}
.rbar .ticks b{color:var(--ink); font-weight:500}
.rows{margin:0; border-top:1px solid var(--line); font-size:.86rem}
.rows div{display:flex; justify-content:space-between; gap:12px; padding:5px 0; border-bottom:1px solid var(--line)}
.rows dt{color:var(--muted)} .rows dd{margin:0; font-family:var(--mono); text-align:right}
.notes{font-size:.86rem; color:var(--muted); background:var(--panel); border:1px solid var(--line);
       border-radius:4px; padding:10px 14px 10px 30px; margin:12px 0}
.notes li{margin:.25em 0}
.stages{display:flex; flex-wrap:wrap; gap:6px; margin:0 0 1.2em}
.stage{display:flex; flex-direction:column; align-items:center; gap:3px}
.stage small{font-family:var(--mono); font-size:.62rem; color:var(--muted)}
.tag{font-family:var(--mono); font-size:.7rem; letter-spacing:.06em; text-transform:uppercase; vertical-align:middle;
     padding:2px 7px; border-radius:3px; border:1px solid var(--line-strong); color:var(--muted)}
.tag.dead{color:var(--fail); border-color:color-mix(in srgb,var(--fail) 50%,transparent)}
.kv th{width:30%}
@media (max-width:860px){ .stats{grid-template-columns:1fr 1fr} .cards{grid-template-columns:1fr} }
"""

JS = """
(function(){
  var arts = document.querySelectorAll('article');
  var links = document.querySelectorAll('nav a');
  var toc = document.getElementById('toc');
  var tocs = window.__TOCS__;

  function show(id){
    var found = false;
    arts.forEach(function(a){
      var on = a.id === id;
      a.classList.toggle('on', on);
      if(on) found = true;
    });
    if(!found){ show('home'); return; }
    links.forEach(function(l){ l.classList.toggle('on', l.getAttribute('href') === '#'+id); });
    var t = document.querySelector('nav a.on');
    if(t && t.closest('details')) t.closest('details').open = true;
    document.getElementById('crumb').textContent = t ? t.textContent : 'Banco di lavoro';
    toc.innerHTML = '';
    var items = tocs[id] || [];
    if(items.length > 2){
      var h = document.createElement('b'); h.textContent = 'In questa pagina'; toc.appendChild(h);
      items.forEach(function(it){
        var a = document.createElement('a');
        a.href = '#' + it[1]; a.textContent = it[2];
        if(it[0] === '3') a.className = 'l3';
        a.addEventListener('click', function(e){
          e.preventDefault();
          var el = document.getElementById(it[1]);
          if(el) el.scrollIntoView({behavior:'smooth', block:'start'});
        });
        toc.appendChild(a);
      });
    }
    document.body.classList.remove('nav-open');
    window.scrollTo(0, 0);
  }

  function route(){
    var h = location.hash.replace(/^#/, '');
    if(!h){ show('home'); return; }
    var el = document.getElementById(h);
    if(el && el.tagName === 'ARTICLE'){ show(h); return; }
    if(el){                       // ancora dentro un documento
      var art = el.closest('article');
      if(art){ show(art.id); el.scrollIntoView({block:'start'}); }
      return;
    }
    show('home');
  }
  window.addEventListener('hashchange', route);
  route();

  // ricerca: filtra la navigazione per titolo e per testo del documento
  var box = document.getElementById('q');
  var nav = document.querySelector('nav');
  var text = window.__TEXT__;
  box.addEventListener('input', function(){
    var q = box.value.trim().toLowerCase();
    nav.classList.toggle('filtering', q.length > 0);
    if(q) nav.querySelectorAll('details').forEach(function(d){ d.open = true; });
    links.forEach(function(l){
      var id = l.getAttribute('href').slice(1);
      var title = l.dataset.title.toLowerCase();
      var hit = l.querySelector('.hit');
      if(hit) hit.remove();
      if(!q){ l.style.display = ''; return; }
      var inTitle = title.indexOf(q) >= 0;
      var body = text[id] || '';
      var n = 0, i = body.indexOf(q);
      while(i >= 0){ n++; i = body.indexOf(q, i + q.length); }
      l.style.display = (inTitle || n) ? '' : 'none';
      if(n){
        var s = document.createElement('span');
        s.className = 'hit'; s.textContent = '  ' + n;
        l.appendChild(s);
      }
    });
  });
  document.addEventListener('keydown', function(e){
    if(e.key === '/' && document.activeElement !== box){ e.preventDefault(); box.focus(); }
    if(e.key === 'Escape'){ box.value = ''; box.dispatchEvent(new Event('input')); box.blur(); }
  });

  document.getElementById('menu').addEventListener('click', function(){
    document.body.classList.toggle('nav-open');
  });
  document.querySelectorAll('[data-generated]').forEach(function(el){
    var t0 = Date.parse(el.dataset.generated.replace(' ', 'T'));
    if(t0 && Date.now() - t0 > 12 * 3600 * 1000) el.hidden = false;
  });
  var t = document.getElementById('theme');
  t.addEventListener('click', function(){
    var cur = document.documentElement.getAttribute('data-theme');
    var next = cur === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    try{ localStorage.setItem('theme', next); }catch(e){}
  });
  try{
    var saved = localStorage.getItem('theme');
    if(saved) document.documentElement.setAttribute('data-theme', saved);
  }catch(e){}
})();
"""


def nav_link(pid, title):
    return '<a href="#%s" data-title="%s">%s</a>' % (pid, esc(title), esc(title))


def build():
    with open(STATUS, encoding="utf8") as f:
        st = json.load(f)
    c, err = context_card()

    sections = [("Prop", PROP_DOCS), ("Discrezionale", DISCR_DOCS),
                ("Ricerca", RESEARCH_DOCS), ("Archivio MQL5", ARCHIVE_DOCS)]
    docs = {sec: [(t, rel) for t, rel in lst if exists(rel)] for sec, lst in sections}
    missing = [rel for _, lst in sections for _, rel in lst if not exists(rel)]
    strategies = [s for s in st["strategies"] if s.get("path") and exists(s["path"])]
    strategies += [s for s in EXTRA_STRATEGIES if exists(s["path"])]

    # ogni markdown -> l'ancora che lo mostra (pagina propria, o sezione della strategia)
    by_path = {rel: slug(rel) for lst in docs.values() for _, rel in lst}
    for s in strategies:
        for rel in strategy_docs(s["path"]):
            by_path[rel] = slug(rel)

    # le due pagine principali: pipeline (si apre per prima) e contesto di sessione
    ctx_html, ctx_toc = context_page(c, err)
    pages = [("home", pipeline_page(st), []), ("contesto", ctx_html, ctx_toc),
             ("prossimi-passi", todo_page(st), []), ("diario", diary_page(st), [])]
    for sec, lst in docs.items():
        for title, rel in lst:
            body, items = headings(doc_body(rel, by_path), slug(rel))
            pages.append((slug(rel), '<p class="eyebrow">%s · <code>%s</code></p>%s' % (esc(sec), esc(rel), body), items))
    for s in strategies:
        pages.append(strategy_page(s, st, by_path))

    alive = [s for s in strategies if not is_dead(s)]
    dead = [s for s in strategies if is_dead(s)]
    nav = ['<a class="main" href="#home" data-title="Pipeline prop">Pipeline prop</a>',
           '<a class="main" href="#contesto" data-title="Contesto sessione">Contesto sessione</a>']
    # tutto il resto in un solo gruppo richiudibile
    altro = ["<h4>Prop</h4>", nav_link("prossimi-passi", "Prossimi passi"), nav_link("diario", "Diario di bordo")]
    altro += [nav_link(slug(rel), t) for t, rel in docs["Prop"]]
    altro.append("<h4>Strategie</h4>")
    altro += [nav_link(strategy_id(s["name"]), s["name"]) for s in alive]
    altro += [nav_link(strategy_id(s["name"]), s["name"] + " †") for s in dead]
    for sec in ("Discrezionale", "Ricerca", "Archivio MQL5"):
        if docs[sec]:
            altro.append("<h4>%s</h4>" % sec)
            altro += [nav_link(slug(rel), t) for t, rel in docs[sec]]
    nav.append('<details class="altro"><summary>Altro</summary>%s</details>' % "".join(altro))

    articles = "".join('<article id="%s"%s>%s</article>' % (pid, ' class="on"' if pid == "home" else "", body)
                       for pid, body, _ in pages)
    tocs = {pid: toc for pid, _, toc in pages}
    texts = {pid: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).lower() for pid, body, _ in pages}

    page = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Banco di lavoro</title>
<style>%s</style>
</head>
<body>
<div class="topbar">
  <button id="menu">☰</button><b id="crumb">Banco di lavoro</b>
  <button id="theme">◐</button>
</div>
<div class="layout">
  <aside>
    <div class="brand"><b><a href="#home" style="color:inherit">Banco di lavoro</a></b>
      <span>%s</span></div>
    <div class="search"><input id="q" type="search" placeholder="Cerca  (/)" autocomplete="off"></div>
    <nav>%s</nav>
  </aside>
  <main>%s</main>
  <div class="toc" id="toc"></div>
</div>
<script>
window.__TOCS__ = %s;
window.__TEXT__ = %s;
%s
</script>
</body>
</html>
""" % (CSS, esc(st["updated"]), "".join(nav), articles,
       json.dumps(tocs, ensure_ascii=False), json.dumps(texts, ensure_ascii=False), JS)

    with open(OUT, "w", encoding="utf8") as f:
        f.write(page)

    kb = os.path.getsize(OUT) / 1024
    print("scritto %s  (%d pagine, %.0f KB)" % (OUT, len(pages), kb))
    if c is None:
        print("  ! contesto di sessione non disponibile: %s" % err)
    for m in missing:
        print("  ! mancante, saltato: %s" % m)


if __name__ == "__main__":
    build()
