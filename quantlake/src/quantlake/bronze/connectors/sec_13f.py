"""SEC EDGAR 13F-HR (institutional holdings) -> bronze/sec_13f_holdings.

    submissions  https://data.sec.gov/submissions/CIK##########.json
                 the fund's recent filings: 13F-HR with accession, filing date
                 and period of report (quarter end)
    index        https://www.sec.gov/Archives/edgar/data/<cik>/<accession>/index.json
                 files of the filing: the information table is the .xml that
                 is not primary_doc.xml
    info table   one <infoTable> per position: issuer, class, CUSIP, value,
                 shares (or principal), put/call

Only original 13F-HR are used (13F-HR/A amendments skipped): one filing per
fund and quarter. Value is in dollars for filings since 2023-01-03 and in
thousands before (converted here). Uses SECClient (SEC_USER_AGENT, <= 8 req/s).
"""
import re
import xml.etree.ElementTree as ET
from datetime import date

from quantlake.bronze.connectors.sec_form4 import ARCHIVES, SECClient

DOLLAR_VALUES_SINCE = date(2023, 1, 3)


def filings(client: SECClient, cik: int, n: int = 3) -> list[dict]:
    """The last n original 13F-HR, newest first, one per period of report."""
    r = client.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    if r is None:
        return []
    d = r.json()
    rec = d["filings"]["recent"]
    out, periods = [], set()
    for form, acc, filed, period in zip(rec["form"], rec["accessionNumber"], rec["filingDate"], rec["reportDate"]):
        if form != "13F-HR" or period in periods:
            continue
        periods.add(period)
        out.append({"cik": cik, "fund_name": d.get("name"), "accession": acc,
                    "filed_date": date.fromisoformat(filed), "period": date.fromisoformat(period)})
        if len(out) == n:
            break
    return out


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(el, name: str):
    for c in el:
        if _local(c.tag) == name:
            return c
    return None


def _text(el, *path: str) -> str | None:
    for name in path:
        el = _child(el, name) if el is not None else None
    return el.text.strip() if el is not None and el.text else None


def info_table(client: SECClient, filing: dict) -> list[dict]:
    cik, acc = filing["cik"], filing["accession"]
    base = f"{ARCHIVES}/edgar/data/{cik}/{acc.replace('-', '')}"
    idx = client.get(f"{base}/index.json")
    if idx is None:
        return []
    names = [i["name"] for i in idx.json().get("directory", {}).get("item", [])]
    xmls = [n for n in names if n.lower().endswith(".xml") and n.lower() != "primary_doc.xml"]
    if not xmls:
        return []
    r = client.get(f"{base}/{xmls[0]}")
    if r is None:
        return []
    text = re.sub(r"^\s*<\?xml[^>]*>", "", r.text)
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    mult = 1.0 if filing["filed_date"] >= DOLLAR_VALUES_SINCE else 1000.0
    rows = []
    for t in root.iter():
        if _local(t.tag) != "infoTable":
            continue
        value = _text(t, "value")
        shares = _text(t, "shrsOrPrnAmt", "sshPrnamt")
        rows.append({
            "issuer": _text(t, "nameOfIssuer"),
            "title_class": _text(t, "titleOfClass"),
            "cusip": (_text(t, "cusip") or "").upper(),
            "value_usd": float(value.replace(",", "")) * mult if value else None,
            "shares": float(shares.replace(",", "")) if shares else None,
            "share_type": _text(t, "shrsOrPrnAmt", "sshPrnamtType"),
            "put_call": (_text(t, "putCall") or "").upper() or None,
        })
    return rows
