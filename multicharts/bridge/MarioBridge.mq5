//+------------------------------------------------------------------+
//| MarioBridge: esegue su MT5 i segnali scritti da MultiCharts.      |
//| Legge una riga per evento dal file nella cartella Common:         |
//|   azione;id;strategia;strumento;lato;micro;stop;target;FINE       |
//|   PENDENTE;...;target;su;giu;FINE  (ordini stop OCO ai bordi)     |
//| Stop e target sono DISTANZE in punti, calcolate dal fill sul CFD. |
//| Lotti: micro x valore del punto del micro / valore del punto      |
//| per lotto, letto dalle specifiche del simbolo. Vedi bridge/SPEC.md|
//+------------------------------------------------------------------+
#property version "1.00"
#include <Trade/Trade.mqh>

input string FileSegnali   = "mario_bridge.csv";
input string FileFill      = "mario_bridge_fill.csv";
input string SimboloNQ     = "US100.cash";
input string SimboloGC     = "XAUUSD";
input double PuntoMicroNQ  = 2.0;     // $ al punto di 1 MNQ
input double PuntoMicroGC  = 10.0;    // $ al punto di 1 MGC
input double MaxLotti      = 5.0;     // rete di sicurezza: sopra, l'ordine non parte
input int    Slippage      = 20;      // deviazione massima in punti del broker
input long   Magic         = 20261104;

CTrade trade;
long   offset = 0;

int ApriFile()
{
   return FileOpen(FileSegnali, FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE);
}

int OnInit()
{
   // si parte dalla fine del file: i segnali vecchi non si eseguono mai
   int h = ApriFile();
   if(h != INVALID_HANDLE)
   {
      FileSeek(h, 0, SEEK_END);
      offset = (long)FileTell(h);
      FileClose(h);
   }
   trade.SetExpertMagicNumber(Magic);
   trade.SetDeviationInPoints(Slippage);
   EventSetTimer(1);
   PrintFormat("MarioBridge pronto, offset %I64d. Valuta conto: %s", offset, AccountInfoString(ACCOUNT_CURRENCY));
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) { EventKillTimer(); }

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

void Registra(string id, string azione, string simbolo, double lotti, double prezzo)
{
   int h = FileOpen(FileFill, FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ);
   if(h == INVALID_HANDLE) return;
   FileSeek(h, 0, SEEK_END);
   double sp = SymbolInfoDouble(simbolo, SYMBOL_ASK) - SymbolInfoDouble(simbolo, SYMBOL_BID);
   FileWriteString(h, StringFormat("%s;%s;%s;%s;%.2f;%.5f;%.5f\r\n", TimeToString(TimeTradeServer(), TIME_DATE|TIME_SECONDS),
                                   id, azione, simbolo, lotti, prezzo, sp));
   FileClose(h);
}

void Apri(string id, string simbolo, int lato, double micro, double puntoMicro, double stopPts, double tgtPts)
{
   double lotti = Lotti(simbolo, micro * puntoMicro);
   if(lotti <= 0 || lotti > MaxLotti) { PrintFormat("%s: lotti %.2f fuori limite, ordine non inviato", id, lotti); return; }
   int cifre = (int)SymbolInfoInteger(simbolo, SYMBOL_DIGITS);
   double prezzo = lato > 0 ? SymbolInfoDouble(simbolo, SYMBOL_ASK) : SymbolInfoDouble(simbolo, SYMBOL_BID);
   double sl = NormalizeDouble(prezzo - lato * stopPts, cifre);
   double tp = tgtPts > 0 ? NormalizeDouble(prezzo + lato * tgtPts, cifre) : 0;
   bool ok = lato > 0 ? trade.Buy(lotti, simbolo, 0, sl, tp, id) : trade.Sell(lotti, simbolo, 0, sl, tp, id);
   if(!ok) { PrintFormat("%s: rifiutato, %d %s", id, trade.ResultRetcode(), trade.ResultComment()); return; }
   Registra(id, "APRI", simbolo, lotti, PrezzoEseguito());
}

// due ordini stop OCO: su e giu sono le distanze dei bordi dal prezzo, non i prezzi del futures
void Pendenti(string id, string simbolo, double micro, double puntoMicro, double stopPts, double tgtPts,
              double su, double giu)
{
   if(su <= 0) { Apri(id, simbolo, 1, micro, puntoMicro, stopPts, tgtPts); return; }   // gia' oltre il bordo
   if(giu <= 0) { Apri(id, simbolo, -1, micro, puntoMicro, stopPts, tgtPts); return; }
   double lotti = Lotti(simbolo, micro * puntoMicro);
   if(lotti <= 0 || lotti > MaxLotti) { PrintFormat("%s: lotti %.2f fuori limite, ordini non inviati", id, lotti); return; }
   int cifre = (int)SymbolInfoInteger(simbolo, SYMBOL_DIGITS);
   double mid = (SymbolInfoDouble(simbolo, SYMBOL_ASK) + SymbolInfoDouble(simbolo, SYMBOL_BID)) / 2;
   double alto = NormalizeDouble(mid + su, cifre), basso = NormalizeDouble(mid - giu, cifre);
   double tpL = tgtPts > 0 ? NormalizeDouble(alto + tgtPts, cifre) : 0;
   double tpS = tgtPts > 0 ? NormalizeDouble(basso - tgtPts, cifre) : 0;
   if(!trade.BuyStop(lotti, alto, simbolo, NormalizeDouble(alto - stopPts, cifre), tpL, ORDER_TIME_GTC, 0, id))
      PrintFormat("%s: buy stop rifiutato, %d %s", id, trade.ResultRetcode(), trade.ResultComment());
   if(!trade.SellStop(lotti, basso, simbolo, NormalizeDouble(basso + stopPts, cifre), tpS, ORDER_TIME_GTC, 0, id))
      PrintFormat("%s: sell stop rifiutato, %d %s", id, trade.ResultRetcode(), trade.ResultComment());
   Registra(id, "PENDENTE", simbolo, lotti, mid);
}

// OCO: con una posizione aperta su un simbolo, gli ordini pendenti su quel simbolo si cancellano
void Oco()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      string simbolo = PositionGetString(POSITION_SYMBOL);
      for(int j = OrdersTotal() - 1; j >= 0; j--)
      {
         ulong ordine = OrderGetTicket(j);
         if(ordine == 0 || OrderGetInteger(ORDER_MAGIC) != Magic || OrderGetString(ORDER_SYMBOL) != simbolo) continue;
         string id = OrderGetString(ORDER_COMMENT);
         if(trade.OrderDelete(ordine))
            Registra(id, "APRI", simbolo, PositionGetDouble(POSITION_VOLUME), PositionGetDouble(POSITION_PRICE_OPEN));
      }
   }
}

void Chiudi(string id, string simbolo)
{
   for(int j = OrdersTotal() - 1; j >= 0; j--)
   {
      ulong ordine = OrderGetTicket(j);
      if(ordine != 0 && OrderGetInteger(ORDER_MAGIC) == Magic && OrderGetString(ORDER_COMMENT) == id)
         trade.OrderDelete(ordine);
   }
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      if(PositionGetString(POSITION_COMMENT) != id) continue;
      double lotti = PositionGetDouble(POSITION_VOLUME);
      if(trade.PositionClose(ticket)) Registra(id, "CHIUDI", simbolo, lotti, PrezzoEseguito());
   }
}

void Esegui(string riga)
{
   string c[];
   int n = StringSplit(riga, ';', c);
   if(n != 9 && !(n == 11 && c[0] == "PENDENTE")) { Print("riga non valida: ", riga); return; }
   string simbolo = c[3] == "NQ" ? SimboloNQ : (c[3] == "GC" ? SimboloGC : "");
   double punto = c[3] == "NQ" ? PuntoMicroNQ : PuntoMicroGC;
   if(simbolo == "") { Print("strumento sconosciuto: ", riga); return; }
   if(c[0] == "APRI")
      Apri(c[1], simbolo, (int)StringToInteger(c[4]), StringToDouble(c[5]), punto, StringToDouble(c[6]), StringToDouble(c[7]));
   else if(c[0] == "PENDENTE")
      Pendenti(c[1], simbolo, StringToDouble(c[5]), punto, StringToDouble(c[6]), StringToDouble(c[7]),
               StringToDouble(c[8]), StringToDouble(c[9]));
   else if(c[0] == "CHIUDI")
      Chiudi(c[1], simbolo);
}

void OnTimer()
{
   Oco();
   int h = ApriFile();
   if(h == INVALID_HANDLE) return;
   FileSeek(h, offset, SEEK_SET);
   while(!FileIsEnding(h))
   {
      string riga = FileReadString(h);
      if(StringFind(riga, ";FINE") < 0) break;     // riga a meta': si rilegge al giro dopo
      offset = (long)FileTell(h);
      Esegui(riga);
   }
   FileClose(h);
}
