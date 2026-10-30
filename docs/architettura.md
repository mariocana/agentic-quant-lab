# Architettura del laboratorio

Un repository, tre pacchetti, una sola direzione di dipendenza. Gli agenti
progettano e scrivono le strategie; quello che arriva in produzione resta una
funzione Python deterministica, e il rischio resta codice che nessun prompt può
cambiare.

Tratteggiato = da costruire.

```mermaid
flowchart TB
    subgraph REPO["agentic-quant-lab"]
        direction TB

        subgraph FA["factory/ — gli agenti"]
            RIC["ricercatore<br/>ipotesi + meccanismo"]
            SPEC["spec builder<br/>StrategySpec"]
            COD["coder<br/>strategy.py + gate AST"]
            CRIT["critico<br/>dossier, nessun veto"]
            REG[("registro delle prove<br/>append-only")]
        end

        subgraph AQ["alpha-quant/ — simulazione e verdetto"]
            SIM["engine livello 2<br/>fee, funding, slippage"]
            GATE["validation/gates.py<br/>lista trade to verdetto"]
        end

        subgraph QL["quantlake/ — i dati"]
            CONN["connettori<br/>Binance UM, Capital, FRED, CFTC<br/>+ Hyperliquid"]
            MED["bronze to silver to gold<br/>Delta, letture versionate"]
            INST[("reference/instruments")]
        end

        subgraph AD["ai-desk/ — produzione"]
            LOOP["loop.py<br/>signals to risk to execution to journal"]
            RISKE["risk/engine.py<br/>9 regole, codice puro"]
            VAR[("var/<br/>journal, ledger, fill veri")]
        end
    end

    RAILWAY["Railway<br/>root ai-desk/, watch ai-desk/**<br/>qui vive la chiave dell'API wallet"]
    HL(["Hyperliquid<br/>perp cripto + HIP-3"])
    PR{{"pull request<br/>il cancello umano"}}
    SHADOW["shadow mode<br/>8-12 settimane<br/>il vero out-of-sample"]

    RIC --> SPEC --> COD
    COD -.-> SIM
    CONN --> MED --> INST
    MED -.-> SIM
    INST -. "contratto di schema" .-> SIM
    SIM -.-> GATE
    GATE -.-> CRIT
    GATE -. "ogni prova si conta" .-> REG
    REG -. "correzione per test multiplo" .-> GATE
    CRIT -.-> PR
    PR ==> SHADOW
    SHADOW ==> PR
    PR ==> LOOP
    LOOP --- RISKE
    LOOP --> VAR
    LOOP -. "snapshot giornaliero<br/>universo punto-nel-tempo" .-> MED
    VAR -. "calibrazione: il simulatore<br/>deve riprodurre i fill veri" .-> SIM
    LOOP -. "detta l'interfaccia Strategy" .-> COD
    AD --> RAILWAY
    RAILWAY <--> HL

    classDef todo stroke-dasharray:5 5
    class FA,SIM,SHADOW,REG todo
```

## Perché i confini cadono qui

**Un repo perché writer e reader di un contratto si cambiano insieme.**
`reference/instruments` è scritto da quantlake e letto in sola lettura da
alpha-quant; l'interfaccia `Strategy` è dettata da ai-desk e scritta dal coder.
In entrambi i casi lo schema non può cambiare senza il suo lettore, e in un repo
solo cambiano nello stesso commit con una sola esecuzione dei test. Una strategia
generata viene validata contro il codice del desk che la farà girare davvero, non
contro una dipendenza pinnata che può essere vecchia di una settimana.

**La direzione delle dipendenze è una regola, non un muro.** `ai-desk/` non importa
niente da `factory/`, da `alpha-quant/` o da `quantlake/`: è il sistema che tiene i
soldi e deve poter girare con il minimo installato. Separare i repo lo garantiva per
costruzione; qui va imposto da un test sui confini di import, come il desk già fa
al suo interno. La chiave dell'API wallet non sta in nessun repository: vive nelle
variabili di Railway e in `.env`, che è gitignorato.

**Il verdetto è codice, il dossier è dell'LLM.** Tutto ciò che un modello può
rilevare leggendo un report di metriche — decadimento fuori campione, dipendenza da
un singolo trade, sensibilità a parametri e costi — è calcolabile. Se è un numero si
confronta con una soglia; il critico scrive perché a quel risultato non dovresti
credere, e non ha autorità di promuovere niente.

**Ogni prova si conta.** Il registro è append-only e tiene ogni ipotesi mai nata con
l'hash della sua spec e la versione dei dati. Senza un conteggio permanente dei
tentativi non esiste correzione per test multiplo, e il caveau out-of-sample non è
difendibile: niente impedirebbe di riproporre fra due settimane un'ipotesi già
bruciata con parole diverse.

**Il cancello è limitato dal calendario, non dal calcolo.** Lo storico serve a
scartare le ipotesi morte; la promozione la decide il tempo in avanti, perché è
l'unico campione su cui nessuno può sbirciare. Per questo la capacità produttiva
della fabbrica è irrilevante e può girare lenta.

**Il desk produce i dati, il laboratorio li consuma.** Un solo client Hyperliquid,
quello che opera davvero: se il simulatore leggesse le barre per una strada diversa
da quella del desk, la divergenza fra simulato e reale sarebbe garantita e
introvabile. Per lo stesso motivo il simulatore va calibrato contro `var/`, cioè
contro fill, slippage e fee di cicli realmente eseguiti: se non riproduce il passato
che abbiamo tradato, la sua opinione su una strategia mai tradata non vale niente.

## Il deploy

Railway costruisce da `ai-desk/` (Root Directory) e guarda solo `ai-desk/**`
(watch paths). Senza i watch path, un commit nella fabbrica farebbe ripartire il
servizio che opera: è lo stesso difetto che aveva il deploy da my-codes, dove un
commit su MultiCharts poteva ridistribuire il desk.
