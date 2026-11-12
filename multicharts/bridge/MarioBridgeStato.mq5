//+------------------------------------------------------------------+
//| MarioBridgeStato: copia su MT5 la POSIZIONE delle strategie MC.   |
//| Un file per strategia nella cartella Common, scritto              |
//| dall'indicatore Mario_BridgeStato:                                |
//|   strategia;strumento;posizione_in_micro;stop_emergenza;FINE      |
//| Agisce solo quando la posizione voluta CAMBIA: allinea MT5 a      |
//| mercato. Se lo stop d'emergenza chiude la posizione, NON la       |
//| riapre finche' MC non cambia di nuovo. Una strategia = un magic   |
//| (Magic + posizione nella lista). Vedi bridge/SPEC.md, v2.         |
//+------------------------------------------------------------------+
#property version "2.00"
#include <Trade/Trade.mqh>

input string Strategie     = "DPB,OBO,GAR";   // file mario_stato_<NOME>.csv; NON cambiare l'ordine con posizioni aperte
input string FileFill      = "mario_stato_fill.csv";
input string SimboloNQ     = "US100.cash";
input string SimboloGC     = "XAUUSD";
input double PuntoMicroNQ  = 2.0;     // $ al punto di 1 MNQ
input double PuntoMicroGC  = 10.0;    // $ al punto di 1 MGC
input double MaxLotti      = 5.0;     // rete di sicurezza: sopra, l'ordine non parte
input int    Slippage      = 20;      // deviazione massima in punti del broker
input int    MaxTentativi  = 5;       // poi si ferma finche' MC non cambia
input long   Magic         = 20261109;

CTrade trade;
string nomi[];
string strum[];
int    voluto[];       // posizione voluta da MC, in micro con segno
double stopEm[];
bool   visto[];        // letto almeno una volta
bool   daAllineare[];
int    tentativi[];

int OnInit()
{
   int n = StringSplit(Strategie, ',', nomi);
   if(n <= 0) return INIT_PARAMETERS_INCORRECT;
   ArrayResize(strum, n); ArrayResize(voluto, n); ArrayResize(stopEm, n);
   ArrayResize(visto, n); ArrayResize(daAllineare, n); ArrayResize(tentativi, n);
   for(int i = 0; i < n; i++)
   {
      StringTrimLeft(nomi[i]); StringTrimRight(nomi[i]);
      strum[i] = ""; voluto[i] = 0; stopEm[i] = 0;
      visto[i] = false; daAllineare[i] = false; tentativi[i] = 0;
   }
   trade.SetDeviationInPoints(Slippage);
   EventSetTimer(1);
   PrintFormat("MarioBridgeStato pronto: %s. Valuta conto: %s, margine: %s", Strategie,
               AccountInfoString(ACCOUNT_CURRENCY),
               AccountInfoInteger(ACCOUNT_MARGIN_MODE) == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING ? "hedging" : "NON hedging");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) { EventKillTimer(); }

string Simbolo(string s) { return s == "NQ" ? SimboloNQ : (s == "GC" ? SimboloGC : ""); }
double Punto(string s)   { return s == "NQ" ? PuntoMicroNQ : PuntoMicroGC; }
long   MagicDi(int i)    { return Magic + i; }

bool Leggi(string nome, string &st, int &pos, double &em)
{
   int h = FileOpen("mario_stato_" + nome + ".csv", FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE);
   if(h == INVALID_HANDLE) return false;          // MC lo sta riscrivendo: si rilegge fra un secondo
   string riga = FileReadString(h);
   FileClose(h);
   string c[];
   if(StringSplit(riga, ';', c) != 5 || StringFind(c[4], "FINE") != 0 || c[0] != nome) return false;
   st = c[1];
   pos = (int)StringToInteger(c[2]);
   em = StringToDouble(c[3]);
   return true;
}

double Lotti(string simbolo, double dollariAlPunto)
{
   double tv = SymbolInfoDouble(simbolo, SYMBOL_TRADE_TICK_VALUE);
   double ts = SymbolInfoDouble(simbolo, SYMBOL_TRADE_TICK_SIZE);
   double step = SymbolInfoDouble(simbolo, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(simbolo, SYMBOL_VOLUME_MIN);
   if(tv <= 0 || ts <= 0 || step <= 0) return 0;
   double esatti = dollariAlPunto / (tv / ts);
   double lotti = MathRound(esatti / step) * step;
   if(lotti < vmin) lotti = vmin;
   if(MathAbs(lotti - esatti) > 0.05 * esatti)
      PrintFormat("ATTENZIONE %s: lotti esatti %.4f, usati %.4f", simbolo, esatti, lotti);
   return lotti;
}

// prezzo del fill: su FTMO ResultPrice() torna 0 per gli ordini a mercato, il deal ha quello vero
double PrezzoEseguito()
{
   ulong deal = trade.ResultDeal();
   if(deal > 0 && HistoryDealSelect(deal)) return HistoryDealGetDouble(deal, DEAL_PRICE);
   return trade.ResultPrice();
}

void Registra(string nome, string azione, string simbolo, double lotti, double prezzo)
{
   int h = FileOpen(FileFill, FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ);
   if(h == INVALID_HANDLE) return;
   FileSeek(h, 0, SEEK_END);
   double sp = SymbolInfoDouble(simbolo, SYMBOL_ASK) - SymbolInfoDouble(simbolo, SYMBOL_BID);
   FileWriteString(h, StringFormat("%s;%s;%s;%s;%.2f;%.5f;%.5f\r\n", TimeToString(TimeTradeServer(), TIME_DATE|TIME_SECONDS),
                                   nome, azione, simbolo, lotti, prezzo, sp));
   FileClose(h);
}

// lato della posizione MT5 di questa strategia: +1, -1, 0
int LatoMT5(int i)
{
   int lato = 0;
   for(int k = PositionsTotal() - 1; k >= 0; k--)
   {
      ulong t = PositionGetTicket(k);
      if(t == 0 || PositionGetInteger(POSITION_MAGIC) != MagicDi(i)) continue;
      lato = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? 1 : -1;
   }
   return lato;
}

// chiude le posizioni della strategia che non stanno dal lato 'tieni' (0 = tutte)
bool Chiudi(int i, int tieni)
{
   bool ok = true;
   trade.SetExpertMagicNumber(MagicDi(i));
   for(int k = PositionsTotal() - 1; k >= 0; k--)
   {
      ulong t = PositionGetTicket(k);
      if(t == 0 || PositionGetInteger(POSITION_MAGIC) != MagicDi(i)) continue;
      int lato = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? 1 : -1;
      if(tieni != 0 && lato == tieni) continue;
      string sim = PositionGetString(POSITION_SYMBOL);
      double vol = PositionGetDouble(POSITION_VOLUME);
      if(trade.PositionClose(t)) Registra(nomi[i], "FLAT", sim, vol, PrezzoEseguito());
      else { ok = false; PrintFormat("%s: chiusura rifiutata, %d %s", nomi[i], trade.ResultRetcode(), trade.ResultComment()); }
   }
   return ok;
}

bool Apri(int i, string sim)
{
   int lato = voluto[i] > 0 ? 1 : -1;
   double lotti = Lotti(sim, MathAbs(voluto[i]) * Punto(strum[i]));
   if(lotti <= 0 || lotti > MaxLotti)
   {
      PrintFormat("%s: lotti %.2f fuori limite, ordine non inviato", nomi[i], lotti);
      return true;                                 // non si riprova: e' un errore di configurazione
   }
   int cifre = (int)SymbolInfoInteger(sim, SYMBOL_DIGITS);
   double prezzo = lato > 0 ? SymbolInfoDouble(sim, SYMBOL_ASK) : SymbolInfoDouble(sim, SYMBOL_BID);
   double sl = stopEm[i] > 0 ? NormalizeDouble(prezzo - lato * stopEm[i], cifre) : 0;
   trade.SetExpertMagicNumber(MagicDi(i));
   string nota = "MB-" + nomi[i];
   bool ok = lato > 0 ? trade.Buy(lotti, sim, 0, sl, 0, nota) : trade.Sell(lotti, sim, 0, sl, 0, nota);
   if(!ok)
   {
      PrintFormat("%s: apertura rifiutata, %d %s", nomi[i], trade.ResultRetcode(), trade.ResultComment());
      return false;
   }
   Registra(nomi[i], lato > 0 ? "LONG" : "SHORT", sim, lotti, PrezzoEseguito());
   return true;
}

void Allinea(int i)
{
   string sim = Simbolo(strum[i]);
   if(sim == "") { PrintFormat("%s: strumento sconosciuto %s", nomi[i], strum[i]); daAllineare[i] = false; return; }
   int lato = voluto[i] > 0 ? 1 : (voluto[i] < 0 ? -1 : 0);
   bool ok = Chiudi(i, lato);                      // via il lato sbagliato (tutto, se MC e' flat)
   if(ok && lato != 0 && LatoMT5(i) == 0) ok = Apri(i, sim);
   if(ok) { daAllineare[i] = false; tentativi[i] = 0; return; }
   if(++tentativi[i] >= MaxTentativi)
   {
      PrintFormat("%s: %d tentativi falliti, mi fermo finche' MC non cambia posizione", nomi[i], tentativi[i]);
      daAllineare[i] = false;
   }
}

void OnTimer()
{
   for(int i = 0; i < ArraySize(nomi); i++)
   {
      string st; int p; double em;
      if(!Leggi(nomi[i], st, p, em)) continue;
      if(!visto[i])
      {
         // all'avvio non si insegue niente: si aspetta il prossimo cambio di MC
         visto[i] = true; voluto[i] = p; strum[i] = st; stopEm[i] = em;
         PrintFormat("%s all'avvio: MC %d micro, MT5 lato %d%s", nomi[i], p, LatoMT5(i),
                     (p != 0 || LatoMT5(i) != 0) ? ". NON allineo: aspetto il prossimo cambio di MC" : "");
         continue;
      }
      if(p != voluto[i])
      {
         PrintFormat("%s: MC %d -> %d micro", nomi[i], voluto[i], p);
         voluto[i] = p; strum[i] = st; stopEm[i] = em;
         daAllineare[i] = true; tentativi[i] = 0;
      }
      if(daAllineare[i]) Allinea(i);
   }
}
