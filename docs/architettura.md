# Architettura del laboratorio

Un repository, quattro cartelle, una catena sola: un'idea viene proposta e scartata presto,
poi validata, poi eseguita. Gli agenti propongono e scrivono; ogni giudizio è codice, e ogni
decisione che tocca i soldi è di una persona.

Lo schema completo, con le tre vie di esecuzione, è in [desk_ricerca.md](desk_ricerca.md).

| cartella | cosa fa | chi la usa |
|---|---|---|
| `quantlake/` | i dati: connettori, bronze → silver → gold, lo storico a 1 minuto di MultiCharts | la misura, `motore`, le dashboard |
| `ricerca/` | il desk di ricerca: perimetro, registro delle idee, comandi | la skill `/ricerca` |
| `multicharts/` | strategie, SPEC, `motore`, `lab.py`, pipeline prop e live, bridge MT5 | la skill `/lab` |
| `hyperliquid-bridge/` | il connettore verso Hyperliquid: esecuzione, rischio, journal. Nessuna strategia. Fermo finché il bridge da MultiCharts non c'è | Railway |
| `fe/` | una pagina sola: dati, trading desk, COT, Equity, laboratorio | il browser |

## La catena

1. **Ricerca** (`/ricerca`, agenti `ricerca-*`): ipotesi con fonti e pagina, critica prima del
   codice, regola scritta nel motore, misura sull'in-sample. Esce un dossier.
2. **Validazione** (`/lab`, agenti `lab-coder` e `lab-judge`): SPEC pre-registrata, codice
   EasyLanguage, fasi della pipeline giudicate da `multicharts/docs/lab.py`.
3. **Esecuzione**: MultiCharts sul VPS, verso il broker futures, il bridge MT5 e, più avanti,
   il bridge verso `hyperliquid-bridge/`.

## Perché i confini cadono qui

**Il verdetto è codice, il giudizio è dell'agente.** La misura, i minimi del perimetro, il
tetto mensile e i gate della pipeline sono numeri confrontati con soglie. Il critico scrive
perché a un'idea non si dovrebbe credere, e non promuove niente.

**Ogni idea si conta.** Il registro (`ricerca/registro/trials.jsonl`) è append-only, con una
catena di hash, e tiene ogni idea dalla nascita. Senza quel conto non c'è correzione per test
multiplo: niente impedirebbe di riproporre fra due settimane un'idea già morta con altre parole.

**Il perimetro si chiude col codice, non col prompt.** `ricerca/perimetro.yaml` dice quali
orizzonti e mercati sono aperti; `ricerca idea` rifiuta il resto. Un divieto in un prompt è
una richiesta cortese, un rifiuto in un comando è un muro.

**La misura usa il motore, non un indicatore.** Stop e target risolti sul percorso a 1 minuto,
ogni trade contato, R:R realizzato al netto dei costi. È calibrata su DriftPullback.

**Chi scrive non vede i numeri.** Ricercatore, critico e coder non leggono mai una misura, un
report o un verdetto. È una regola che gli agenti seguono, non una sandbox.

**Ogni numero preso da un paper porta la pagina.** È la difesa contro un modello che
attribuisce a un autore cose che l'autore non ha scritto.

**`hyperliquid-bridge/` non importa niente dal resto.** Tiene la chiave dell'API wallet (nelle
variabili di Railway, mai nel repository) e deve poter girare con il minimo installato. Un
test sui confini di import lo verifica.

## multicharts dentro il laboratorio (dal 12/11/2026)

La catena MultiCharts sta in `multicharts/`, importata dal repository `my-codes` con la sua
storia (commit `25de898`, ramo `audit-e-gate-intervallo`). Fuori sono rimasti il materiale del
corso (`protocollo/`, `education/`) e i vecchi progetti Python.

1. **Due skill.** `/ricerca` porta un'idea fino al dossier; `/lab` la porta dalla SPEC al
   verdetto. Agenti e skill stanno in `.claude/` alla radice.
2. **`/lab` si lancia dalla radice**: `python3 multicharts/docs/lab.py ...` e
   `PYTHONPATH=multicharts python3 -m motore...`. I percorsi dentro `pipeline_status.json`
   restano relativi a `multicharts/`.
3. **Gli sha sono cambiati.** L'import ha riscritto la storia: `multicharts/docs/commit_map_unione.tsv`
   tiene la corrispondenza vecchio → nuovo, e `lab.py` la usa per le righe `registrata: <sha>`
   delle SPEC, che non sono state toccate.
4. **Due stati separati.** `pipeline_status.json` e i verdetti sono di `/lab`; il registro delle
   idee è di `/ricerca`. Passa un file solo: il dossier.
5. **Le tabelle ES/NQ di quantlake restano intatte**: `motore` le legge da `quantlake/data`.

## Cosa è stato chiuso

Il 12/11/2026 la fabbrica Hyperliquid (`alpha-quant/`, `/quant-factory`, agenti `factory-*`):
replay del ciclo del desk, gate di portafoglio, holdout. Ha giudicato una strategia,
`reversal_v1`, e l'ha bocciata; le sue tre righe restano in testa al registro. Il codice è in
git fino al commit `7cc21f9`, l'audit in [audit_2026-11-12.md](audit_2026-11-12.md).

## Il deploy

Railway deve costruire da `hyperliquid-bridge/` (Root Directory) e guardare solo
`hyperliquid-bridge/**` (watch paths): un commit nel resto del repository non fa ripartire il
servizio. La cartella si chiamava `trading-desk/` fino al 12/11/2026: le due impostazioni vanno
cambiate a mano su Railway.
