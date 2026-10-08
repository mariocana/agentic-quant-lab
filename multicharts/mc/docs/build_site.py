#!/usr/bin/env python3
"""Costruisce un sito statico in un solo file con tutto il lavoro del repo.

Uso:  python3 mc/docs/build_site.py   ->  scrive mc/docs/index.html

Un unico HTML autonomo: nessuna rete, nessun CDN, si apre con doppio clic e
funziona anche da chiavetta. Dentro ci sono la dashboard della pipeline (da
pipeline_status.json), tutti i documenti markdown del repo convertiti, la ricerca
full-text e un indice per documento.

Dipendenza: `markdown` (pip3 install --user markdown).
"""
import html
import json
import os
import re
import sys

try:
    import markdown
except ImportError:
    sys.exit("Manca il pacchetto markdown.  pip3 install --user markdown")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "index.html")
STATUS = os.path.join(HERE, "pipeline_status.json")

# ---------------------------------------------------------------- documenti
# (sezione, titolo, percorso relativo alla radice del repo)
# L'ordine qui è l'ordine nella barra laterale: è la mappa del lavoro, non un
# elenco alfabetico.
DOCS = [
    ("Pipeline", "Il protocollo prop", "mc/docs/pipeline_prop.md"),
    ("Pipeline", "Digest del corso", "mc/docs/institutional_protocol_digest.md"),
    ("Pipeline", "Protocollo di test MC", "mc/docs/protocollo_test_mc.md"),
    ("Pipeline", "Setup TradeStation", "mc/docs/setup_tradestation.md"),

    ("Strategie", "NQ First5 — spec", "mc/strategies/NQ_First5/SPEC.md"),
    ("Strategie", "NQ First5 — checklist Stage 1", "mc/strategies/NQ_First5/CHECKLIST_Stage1.md"),
    ("Strategie", "NQ First5 — readme", "mc/strategies/NQ_First5/README_F5.md"),
    ("Strategie", "ORB Breakout — spec †", "mc/strategies/ORB_Breakout/SPEC.md"),
    ("Strategie", "ORB Breakout — readme †", "mc/strategies/ORB_Breakout/README_ORB.md"),
    ("Strategie", "VaultBreak — spec †", "mc/strategies/VaultBreak/SPEC.md"),
    ("Strategie", "VaultBreak — readme †", "mc/strategies/VaultBreak/README_VB.md"),
    ("Strategie", "VWAP Pullback — spec", "mc/strategies/VWAP_Pullback/SPEC.md"),
    ("Strategie", "VWAP Pullback — readme", "mc/strategies/VWAP_Pullback/README_VWAP.md"),
    ("Strategie", "Gold Asian Range — spec", "mc/strategies/GoldAsianRange/SPEC.md"),
    ("Strategie", "Gold Asian Range — readme", "mc/strategies/GoldAsianRange/README_GAR.md"),
    ("Strategie", "DriftPullback — spec", "mc/strategies/DriftPullback/SPEC.md"),
    ("Strategie", "DriftPullback — readme", "mc/strategies/DriftPullback/README_DPB.md"),
    ("Strategie", "Quant VWAP — note", "mc/strategies/Quant_VWAP/NOTES.md"),

    ("Ricerca e ingest", "Journal degli ingest", "mc/docs/ingest_journal.md"),
    ("Ricerca e ingest", "Morpheus — modelli intraday 1-5", "education/morpheus/ANALISI_modelli_intraday_1-5.md"),
    ("Ricerca e ingest", "Unger — i due PDF", "education/unger/NOTES_unger_pdf.md"),
    ("Ricerca e ingest", "SSRN — i tre paper scartati", "ideas/NOTES_ssrn_batch.md"),
    ("Ricerca e ingest", "GEX / Freddy", "ideas/NOTES_gex_freddy.md"),
    ("Ricerca e ingest", "MOC — scheda di ricerca", "ideas/MOC_ricerca.md"),
    ("Ricerca e ingest", "Elder — Vivere di trading", "education/books/NOTES_elder.md"),
    ("Ricerca e ingest", "Palmquist — candlestick", "education/books/NOTES_palmquist_candlestick.md"),

    ("Discrezionale", "Playbook orderflow Londra", "education/enrico_stucchi/PLAYBOOK.md"),
    ("Discrezionale", "Calibrazione del contesto", "education/enrico_stucchi/CALIBRAZIONE_contesto.md"),
    ("Discrezionale", "Template sessione Londra", "education/enrico_stucchi/sessioni/TEMPLATE_london.md"),
    ("Discrezionale", "Template sessione NY", "education/enrico_stucchi/sessioni/TEMPLATE_ny.md"),
    ("Discrezionale", "Diario trade", "journal/journal_swing/README.md"),

    ("Archivio MQL5", "Fase 2 — testing", "mql5/docs/fase2_testing.md"),
    ("Archivio MQL5", "Protocollo IVB / ORB", "mql5/docs/protocols/ivb_orb.md"),
    ("Archivio MQL5", "Protocollo ORB breakout", "mql5/docs/protocols/orb_breakout.md"),
    ("Archivio MQL5", "Protocollo Turtle", "mql5/docs/protocols/turtle_breakout.md"),
]

LABEL = {"pass": "passato", "waiver": "passato per override registrato",
         "active": "in corso", "blocked": "bloccato",
         "fail": "fallito", "pending": "da fare", "na": "n/a"}
SYMBOL = {"pass": "✓", "waiver": "!", "active": "●", "blocked": "■", "fail": "✕",
          "pending": "·", "na": "—"}


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


# ---------------------------------------------------------------- dashboard
def dashboard(st):
    stages = st["stages"]
    rows = []
    for s in st["strategies"]:
        if not s.get("stages"):
            continue
        cells = []
        for g in stages:
            v = s["stages"].get(str(g["id"]), "na")
            cells.append(
                '<td><span class="chip %s" title="%s: %s">%s</span></td>'
                % (v, esc(g["name"]), LABEL.get(v, v), SYMBOL.get(v, "?")))
        rows.append(
            '<tr><th>%s<span class="sub">%s</span></th>%s</tr>'
            % (esc(s["name"]), esc(s.get("instrument", "")), "".join(cells)))

    head = "".join('<th title="%s"><span>%s</span></th>'
                   % (esc(g["gate"]), esc(g["short"])) for g in stages)

    blockers = "".join("<li>%s</li>" % inline(b) for b in st.get("blockers", []))

    td = st.get("todo")
    todo = ""
    if td:
        groups = "".join(
            '<div class="tg"><h3>%s%s</h3><ul>%s</ul></div>'
            % (esc(g["title"]),
               ' <span class="note">%s</span>' % esc(g["note"]) if g.get("note") else "",
               "".join("<li>%s</li>" % inline(i) for i in g["items"]))
            for g in td["groups"])
        todo = ('<section class="todo"><h2>Prossimi passi '
                '<span class="note">memo del %s</span></h2>%s</section>'
                % (esc(td.get("updated", "")), groups))
    entries = st.get("log", [])
    item = lambda e: ('<li><time>%s</time><div>%s</div></li>'
                      % (esc(e["date"]), inline(e["text"])))
    log = "".join(item(e) for e in entries[:10])
    rest = entries[10:]
    more = ('<details class="more"><summary>Le altre %d voci</summary>'
            '<ol class="log">%s</ol></details>'
            % (len(rest), "".join(item(e) for e in rest))) if rest else ""

    return """
<header class="hero">
  <p class="eyebrow">Aggiornato al %s</p>
  <h1>Il banco di lavoro</h1>
  <p class="goal">%s</p>
</header>

%s

<section>
  <h2>Board della pipeline</h2>
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
    &nbsp;· † strategia chiusa
  </p>
</section>

<section class="cols">
  <div>
    <h2>Profilo cercato</h2>
    <p>%s</p>
    <h2>Conto</h2>
    <p>%s</p>
  </div>
  <div>
    <h2>Blocchi aperti</h2>
    <ul class="blockers">%s</ul>
  </div>
</section>

<section>
  <h2>Diario di bordo</h2>
  <ol class="log">%s</ol>
  %s
</section>
""" % (esc(st["updated"]), esc(st["goal"]), todo, head, "".join(rows),
       inline(st.get("profile", "")), inline(st.get("prop", "")), blockers, log, more)


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


def build():
    with open(STATUS, encoding="utf8") as f:
        st = json.load(f)

    present = [(sec, title, rel) for sec, title, rel in DOCS
               if os.path.exists(os.path.join(ROOT, rel))]
    missing = [rel for _, _, rel in DOCS
               if not os.path.exists(os.path.join(ROOT, rel))]
    by_path = {rel: slug(rel) for _, _, rel in present}

    articles = ['<article id="home" class="on">%s</article>' % dashboard(st)]
    tocs = {"home": []}
    texts = {}
    nav_parts = []
    last_sec = None

    for sec, title, rel in present:
        doc_id = by_path[rel]
        with open(os.path.join(ROOT, rel), encoding="utf8") as f:
            raw = f.read()
        body = render_md(raw)
        body = rewrite_links(body, rel, by_path)
        # tabelle in un contenitore scorrevole: su schermo stretto una tabella
        # larga farebbe scorrere l'intera pagina, tagliando il testo a sinistra
        body = body.replace("<table>", '<div class="scroll"><table>')
        body = body.replace("</table>", "</table></div>")
        body, items = headings(body, doc_id)
        tocs[doc_id] = items
        texts[doc_id] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).lower()

        articles.append(
            '<article id="%s"><p class="eyebrow">%s · <code>%s</code></p>%s</article>'
            % (doc_id, esc(sec), esc(rel), body))

        if sec != last_sec:
            nav_parts.append("<h3>%s</h3>" % esc(sec))
            last_sec = sec
        nav_parts.append('<a href="#%s" data-title="%s">%s</a>'
                         % (doc_id, esc(title), esc(title)))

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
    <nav><a href="#home" data-title="Dashboard">Dashboard</a>%s</nav>
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
""" % (CSS, esc(st["updated"]), "".join(nav_parts), "".join(articles),
       json.dumps(tocs, ensure_ascii=False), json.dumps(texts, ensure_ascii=False), JS)

    with open(OUT, "w", encoding="utf8") as f:
        f.write(page)

    kb = os.path.getsize(OUT) / 1024
    print("scritto %s  (%d documenti, %.0f KB)" % (OUT, len(present), kb))
    for m in missing:
        print("  ! mancante, saltato: %s" % m)


if __name__ == "__main__":
    build()
