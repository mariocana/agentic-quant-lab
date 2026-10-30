#!/usr/bin/env python3
"""Verifica PtnBaseSA: ricalcola i pattern 1-40 dal log di PtnBaseSA_Check e li confronta.

Il log ha una riga per sessione:
    PTN 1260810  1600 0101...(40 cifre) O= 7840.25 H= 7861.00 L= 7830.75 C= 7850.50
Con le righe in ordine, la sessione i ha "oggi" = riga i, "ieri" = riga i-1, ...,
"5 giorni fa" = riga i-5. Si ricalcolano i 40 pattern con le stesse formule della
funzione (stesso ordine delle operazioni) e si confrontano con le cifre stampate.

Le prime 5 sessioni del log non hanno abbastanza storia e si saltano. Una sessione
che manca nel log (festività, chart che parte a metà) sposta gli indici: lo script
segnala i salti di data di più di 4 giorni.

Uso:  python3 check_ptn.py log.txt
Solo libreria standard.
"""
import re
import sys
from datetime import date

ROW = re.compile(r"PTN\s+(\d{7})\s+(\d+)\s+([01]{40})\s+O=\s*([-\d.]+)\s+H=\s*([-\d.]+)\s+L=\s*([-\d.]+)\s+C=\s*([-\d.]+)")


def mc_date(s):
    """Data MultiCharts YYYMMDD (anno - 1900) -> date."""
    return date(1900 + int(s[:3]), int(s[3:5]), int(s[5:7]))


def patterns(o, h, l, c):
    """o, h, l, c: liste indicizzate come nella funzione (0 = oggi, 5 = 5 sessioni fa)."""
    p = {}
    p[1] = abs(o[1] - c[1]) < 0.5 * (h[1] - l[1])
    p[2] = abs(o[1] - c[5]) < 0.5 * (h[5] - c[1])
    p[3] = abs(o[5] - c[1]) < 0.5 * (max(h[1:6]) - min(l[1:6]))
    p[4] = (h[0] - o[0]) > (h[1] - o[1]) * 1
    p[5] = (h[0] - o[0]) > (h[1] - o[1]) * 1.5
    p[6] = (o[0] - l[0]) > (o[1] - l[1]) * 1
    p[7] = (o[0] - l[0]) > (o[1] - l[1]) * 1.5
    p[8] = c[1] > c[2] and c[2] > c[3] and c[3] > c[4]
    p[9] = c[1] < c[2] and c[2] < c[3] and c[3] < c[4]
    p[10] = h[1] > h[2] and l[1] > l[2]
    p[11] = h[1] < h[2] and l[1] < l[2]
    p[12] = h[0] > l[0] + l[0] * 0.75 / 100
    p[13] = h[0] < l[0] + l[0] * 0.75 / 100
    p[14] = c[1] > c[2]
    p[15] = c[1] < c[2]
    p[16] = c[1] < o[1]
    p[17] = c[1] > o[1]
    p[18] = c[1] < c[2] - c[2] * 0.5 / 100
    p[19] = c[1] > c[2] + c[2] * 0.5 / 100
    p[20] = h[0] > h[1]
    p[21] = h[1] > h[5]
    p[22] = l[0] < l[1]
    p[23] = l[1] < l[5]
    p[24] = h[1] > h[2] and h[1] > h[3] and h[1] > h[4]
    p[25] = h[1] < h[2] and h[1] < h[3] and h[1] < h[4]
    p[26] = l[1] < l[2] and l[1] < l[3] and l[1] < l[4]
    p[27] = l[1] > l[2] and l[1] > l[3] and l[1] > l[4]
    p[28] = c[1] > c[2] and c[2] > c[3] and o[0] > c[1]
    p[29] = c[1] < c[2] and c[2] < c[3] and o[0] < c[1]
    p[30] = (h[1] - c[1]) < 0.20 * (h[1] - l[1])
    p[31] = (c[1] - l[1]) < 0.20 * (h[1] - l[1])
    p[32] = o[0] < l[1] or o[0] > h[1]
    p[33] = o[0] < c[1] - c[1] * 0.5 / 100
    p[34] = o[0] > c[1] + c[1] * 0.5 / 100
    p[35] = h[0] < h[1] and l[0] > l[1]
    p[36] = (h[1] - l[1]) < ((h[2] - l[2]) + (h[3] - l[3])) / 3
    p[37] = (h[1] - l[1]) < (h[2] - l[2]) and (h[2] - l[2]) < (h[3] - l[3])
    p[38] = h[2] > h[1] and l[2] < l[1]
    p[39] = h[1] < h[2] or l[1] > l[2]
    p[40] = h[2] < h[1] and l[2] > l[1]
    return p


def main(path):
    rows = []
    for line in open(path, encoding="utf8", errors="replace"):
        m = ROW.search(line)
        if m:
            d, t, bits, *ohlc = m.groups()
            rows.append((mc_date(d), t, bits, [float(x) for x in ohlc]))
    if len(rows) < 6:
        raise SystemExit(f"{path}: {len(rows)} righe PTN, ne servono almeno 6")

    for (d0, *_), (d1, *_) in zip(rows, rows[1:]):
        if (d1 - d0).days > 4:
            print(f"ATTENZIONE: salto di {(d1 - d0).days} giorni fra {d0} e {d1} (sessioni mancanti?)")

    mismatch = {}
    checked = 0
    for i in range(5, len(rows)):
        win = [rows[i - k][3] for k in range(6)]          # 0 = oggi ... 5 = 5 sessioni fa
        o, h, l, c = ([w[j] for w in win] for j in range(4))
        p = patterns(o, h, l, c)
        bits = rows[i][2]
        checked += 1
        for k in range(1, 41):
            if (bits[k - 1] == "1") != p[k]:
                mismatch.setdefault(k, []).append(rows[i][0])

    print(f"sessioni nel log: {len(rows)}, confrontate: {checked} (le prime 5 non hanno storia)")
    freq = {k: sum(r[2][k - 1] == "1" for r in rows[5:]) for k in range(1, 41)}
    print("frequenza (vero / confrontate):", " ".join(f"{k}:{freq[k]}" for k in range(1, 41)))
    if not mismatch:
        print(f"OK: tutti i 40 pattern coincidono su {checked} sessioni")
        return 0
    for k, ds in sorted(mismatch.items()):
        print(f"pattern {k:2d}: {len(ds)} differenze, prime: {', '.join(map(str, ds[:5]))}")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1]))
