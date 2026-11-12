# Factory trading — progetto

**02/11/2026.** Costruita: `/lab` (`.claude/skills/lab/SKILL.md`), gli agenti `lab-coder` e
`lab-judge` (`.claude/agents/`), le regole in `docs/lab.py`. Si apre una sessione Claude Code nel
repo e si scrive `/lab`.

Una sessione Claude Code con cui parli (il **desk**) e due subagent: il **coder** scrive, il
**judge** giudica. Tu giri i test in MultiCharts. Vale solo per questo repo: skill e agenti in
`.claude/`, niente plugin.

```
tu ⇄ desk  (/lab, la sessione con cui parli)
       ├─► coder : idea → SPEC.md pre-registrata (commit) → codice EasyLanguage
       │            … tu giri il test, l'xlsx va in strategies/<X>/reports/ …
       └─► judge : SPEC + report → check_report.py / gate_marginale.py → verdetto + registro
```

## 1. I tre ruoli

| | cosa fa | cosa vede | cosa non può fare |
|---|---|---|---|
| **desk** (sessione principale) | discute le idee con te, ti contesta, spiega i verdetti, tiene lo stato, decide chi chiamare | tutto | scrivere codice, dare verdetti, ribaltare un verdetto |
| **coder** (Opus) | scrive `SPEC.md` con ipotesi, soglie, attesa e kill, la committa; **dopo** scrive il codice e la checklist dello Stage 1 | l'idea, i documenti della pipeline, il protocollo | leggere `reports/` e i verdetti di altre strategie; eseguire gli script di verifica |
| **judge** (Opus) | lancia lo script della fase, controlla i preliminari, confronta con la SPEC, scrive il verdetto | SPEC, report, output degli script, registro delle varianti | modificare SPEC, soglie, script o codice; vedere la conversazione con te |

**Il verdetto lo dà lo script, non l'agente.** Il judge controlla che lo script sia stato lanciato
con la fase e i parametri giusti, legge i controlli preliminari, verifica le regole della §3 e
scrive il perché. Se lo script dice NON PASSA, il judge non può scrivere PASSA.

**Il desk non ribalta il judge.** Ne discute con te, te lo spiega. Se non sei d'accordo la strada
è una **variante nuova, pre-registrata**, che entra nel conteggio k. Mai rigirare lo stesso test.

## 2. Il percorso di una strategia (catena prop)

Sono le cinque domande di `pipeline_semplice.md`. Ogni passaggio "tu" è uno stato di attesa: il
desk si ferma e ti dice cosa girare, con quali impostazioni e su quale periodo.

| stato | chi | cosa | esce verso |
|---|---|---|---|
| `idea` | tu + desk | ne parlate; il desk ti dice se è già nel cimitero o in coda | `spec` o niente |
| `spec` | coder | `SPEC.md`: ipotesi, perché, chi perde, IS/OOS, **soglie e attesa**, varianti pre-registrate. Commit | `codice` |
| `codice` | coder | `.txt` EasyLanguage + checklist Stage 1 | `attesa_S1` |
| `attesa_S1` | **tu** | 100 giorni in MC | `verdetto_S1` |
| `verdetto_S1` | judge | il codice fa quello che dice la SPEC? (trade dove previsto, flat la sera) | `attesa_IS` · `codice` (bug, non è un kill) |
| `attesa_IS` | **tu** | IS 2020-2024 | `verdetto_IS` |
| `verdetto_IS` | judge | `check_report.py --fase 2` (via A) o `t > soglia k` (via B) | `attesa_OOS` · `cimitero` |
| `attesa_OOS` | **tu** | OOS 2025→oggi, **una volta** | `verdetto_OOS` |
| `verdetto_OOS` | judge | `check_report.py --fase 3 --dd-is <DD IS>` | `gate_book` · `cimitero` (definitivo) |
| `gate_book` | judge | `gate_marginale.py` contro il book live | `paper` · `cimitero` |
| `paper` → `eval` | tu + desk | una settimana di paper, poi un tentativo col budget dichiarato | `live` · `spenta` |

Lo Stage 4 (migliorie, solo IS, max 3 input, split-sample) è un giro `spec` → `attesa_IS` su una
variante: la variante è una strategia figlia con la sua SPEC, e conta nel k della madre.

## 3. Le regole che diventano codice

Il desk e gli agenti le seguono, ma non si fidano della memoria: le controlla uno script, `docs/lab.py`
(solo libreria standard, come `check_report.py`), che il judge lancia prima di scrivere un verdetto.

1. **Pre-registrazione.** `SPEC.md` deve essere committata **prima** che il report compaia, e non
   deve essere cambiata dal commit di pre-registrazione (`git log` / `git diff` sul file). Se è
   cambiata, quel report vale per una variante nuova.
2. **L'OOS una volta sola.** Se nel registro c'è già un verdetto OOS per quella strategia (o
   variante), `lab.py` rifiuta il secondo.
3. **Il conto delle varianti.** `lab.py` conta le varianti IS girate per la strategia e stampa la
   soglia t del massimo di k strategie a edge zero (k=2 → 0,56 · 3 → 0,85 · 4 → 1,03 · 6 → 1,27).
4. **I preliminari.** Una riga `NO` di `check_report.py` blocca il verdetto. Le righe `?`
   (slippage a zero, session template, range) il judge le gira a te come domanda, e il verdetto
   resta sospeso finché non rispondi.
5. **Il tetto del book.** Massimo 3 strategie; 2 settimane di live fra un'aggiunta e l'altra.

Il judge **non ha Write né Edit**: legge, lancia gli script e consegna il verdetto a
`lab.py verdict`, che scrive il file e aggiorna lo stato. Così non può toccare SPEC o soglie
nemmeno per sbaglio.

## 4. Dove sta lo stato

- **`docs/pipeline_status.json`** resta la fonte unica e `build_site.py` la pagina. Ogni cambio di
  stato passa da `lab.py` (`lab.py set`, `lab.py log`), mai a mano, così il JSON resta valido.
  Il campo `stages` di oggi diventa la catena prop; per la live si aggiunge un campo accanto.
- **`strategies/<X>/verdicts/<fase>.md`**: il verdetto del judge, con l'output dello script
  incollato, le regole della §3 controllate e il commit della SPEC a cui si riferisce.
- **Il registro** di `pipeline_semplice.md` (fase 3b) lo aggiorna `lab.py verdict`, non l'agente.

## 5. Comandi

| comando | cosa succede |
|---|---|
| `/lab` + testo libero | parli col desk: idee, dubbi, "perché è morta X?" |
| `/lab nuova <idea>` | il desk ne discute con te, poi manda il coder a scrivere la SPEC e il codice |
| `/lab report <strategia> <file.xlsx>` | il judge giudica il report della fase in cui è la strategia |
| `/lab variante <strategia> <cosa cambia>` | nuova SPEC figlia, conta nel k |
| `/lab book <strategia>` | gate marginale contro il book live |
| `/lab stato` | dove sta ogni strategia e cosa aspetta da te |

## 6. La catena live

Dopo. Oggi è in stand-by fino ai payout (`metodologia_live.md`). Stessa struttura, criteri diversi
(PF, avg trade, concentrazione annuale, robustezza al regime, ragione strutturale). Una strategia
avrà uno stato per catena: può passare la prop e restare ferma sul live.

## 7. Decisioni prese e punti aperti

1. **Il coder non vede i risultati delle altre strategie** (deciso): per non tarare la SPEC su
   numeri visti. Ma gli serve il cimitero per non riproporre idee morte: lo filtra il desk prima.
2. **Le righe `?` dei preliminari**: il judge verifica da solo quelle che SPEC e checklist
   permettono di verificare; le altre diventano domande per Mario, che il desk non può rispondere
   al posto suo (deciso).
3. **SESSION 1 e SESSION 2** oggi lavorano su questo repo: cosa fanno, e quale parte di questo
   prendono loro. Da guardare prima di costruire, per non duplicare.
4. **Modelli.** Coder su Opus effort alto, judge su Opus effort medio; Sonnet per il judge si può
   provare dopo i primi verdetti, confrontando.
