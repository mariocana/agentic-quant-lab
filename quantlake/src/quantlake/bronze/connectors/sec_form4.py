"""SEC EDGAR Form 4 (insider transactions) -> bronze/sec_form4.

    daily index   https://www.sec.gov/Archives/edgar/daily-index/YYYY/QTRn/form.YYYYMMDD.idx
                  every filing of the day by form type: the Form 4 / 4/A lines
                  give the accession file (edgar/data/<cik>/<accession>.txt)
    filing        the full submission .txt, whose <XML> block is the
                  ownershipDocument: issuer, reporting owner + role, and one
                  nonDerivativeTransaction per trade of common stock

One row per non-derivative transaction. Derivative rows (options, RSU) are
left out: the signal is in open-market purchases (code P) and sales (S).

The SEC blocks automated requests without a declared contact: the User-Agent
comes from SEC_USER_AGENT in .env (e.g. "quantlake Name name@example.com").
Fair access is 10 requests/second: the client stays under 8.
"""
import os
import re
import threading
import time
import xml.etree.ElementTree as ET
from datetime import date

import httpx

from quantlake import config  # noqa: F401  (loads .env)

ARCHIVES = "https://www.sec.gov/Archives"
MAX_RPS = 8
FORMS = ("4", "4/A")


class SECClient:
    """Rate-limited GET with the declared User-Agent."""

    def __init__(self, user_agent: str | None = None, max_rps: float = MAX_RPS):
        self.user_agent = user_agent or os.getenv("SEC_USER_AGENT")
        if not self.user_agent:
            raise RuntimeError("SEC_USER_AGENT missing in python/quantlake/.env "
                               "(the SEC requires a contact, e.g. 'quantlake Name name@example.com')")
        self.interval = 1.0 / max_rps
        self._lock = threading.Lock()
        self._next = 0.0
        self._client = httpx.Client(timeout=30, headers={"User-Agent": self.user_agent,
                                                         "Accept-Encoding": "gzip, deflate"})

    def get(self, url: str, retries: int = 4) -> httpx.Response | None:
        for attempt in range(retries):
            with self._lock:
                wait = self._next - time.monotonic()
                if wait > 0:
                    time.sleep(wait)
                self._next = max(time.monotonic(), self._next) + self.interval
            try:
                r = self._client.get(url)
            except httpx.HTTPError:
                time.sleep(2 * (attempt + 1))
                continue
            if r.status_code == 404:
                return None
            if r.status_code in (429, 503):
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r
        raise RuntimeError(f"SEC: too many failures on {url}")


def daily_index_url(day: date) -> str:
    q = (day.month - 1) // 3 + 1
    return f"{ARCHIVES}/edgar/daily-index/{day.year}/QTR{q}/form.{day:%Y%m%d}.idx"


def parse_daily_index(text: str) -> list[dict]:
    """Form 4 / 4/A filings of the day, one per accession (the index lists issuer and owner)."""
    out, seen = [], set()
    for line in text.splitlines():
        m = re.match(r"^(4|4/A)\s+(.*?)\s+(\d+)\s+(\d{8}|\d{4}-\d{2}-\d{2})\s+(edgar/\S+\.txt)\s*$", line)
        if not m:
            continue
        accession = m.group(5).rsplit("/", 1)[-1].removesuffix(".txt")
        if accession in seen:
            continue
        seen.add(accession)
        out.append({"form": m.group(1), "path": m.group(5), "accession": accession})
    return out


def _t(node, path: str) -> str | None:
    el = node.find(path)
    if el is None:
        return None
    v = el.find("value")
    txt = (v.text if v is not None else el.text) or ""
    return txt.strip() or None


def _flag(v: str | None) -> bool:
    return (v or "").strip().lower() in ("1", "true")


def _num(v: str | None) -> float | None:
    try:
        return float(v.replace(",", "")) if v else None
    except ValueError:
        return None


def parse_form4(submission: str) -> list[dict]:
    """Transactions of one Form 4 submission (.txt with an <XML> block)."""
    m = re.search(r"<XML>(.*?)</XML>", submission, re.S | re.I)
    if not m:
        return []
    xml = m.group(1).strip()
    try:
        doc = ET.fromstring(xml)
    except ET.ParseError:
        return []
    issuer = doc.find("issuer")
    owners = doc.findall("reportingOwner")
    if issuer is None or not owners:
        return []
    # several joint owners: the first one names the row, all their roles count
    owner = owners[0]
    rel = [o.find("reportingOwnerRelationship") for o in owners]
    rel = [r for r in rel if r is not None]
    any_flag = lambda tag: any(_flag(_t(r, tag)) for r in rel)
    title = next((_t(r, "officerTitle") for r in rel if _t(r, "officerTitle")), None)
    base = {
        "issuer_cik": _t(issuer, "issuerCik"),
        "issuer_name": _t(issuer, "issuerName"),
        "symbol": (_t(issuer, "issuerTradingSymbol") or "").upper().strip() or None,
        "owner_cik": _t(owner, "reportingOwnerId/rptOwnerCik"),
        "owner_name": _t(owner, "reportingOwnerId/rptOwnerName"),
        "n_owners": len(owners),
        "is_director": any_flag("isDirector"),
        "is_officer": any_flag("isOfficer"),
        "is_ten_pct": any_flag("isTenPercentOwner"),
        "officer_title": title,
        "plan_10b5_1": _flag(_t(doc, "aff10b5One")),
        "period": _t(doc, "periodOfReport"),
    }
    rows = []
    for tx in doc.findall("nonDerivativeTable/nonDerivativeTransaction"):
        shares = _num(_t(tx, "transactionAmounts/transactionShares"))
        price = _num(_t(tx, "transactionAmounts/transactionPricePerShare"))
        rows.append({
            **base,
            "security": _t(tx, "securityTitle"),
            "transaction_date": _t(tx, "transactionDate"),
            "code": _t(tx, "transactionCoding/transactionCode"),
            "acquired_disposed": _t(tx, "transactionAmounts/transactionAcquiredDisposedCode"),
            "shares": shares,
            "price": price,
            "value": shares * price if shares is not None and price is not None else None,
            "shares_after": _num(_t(tx, "postTransactionAmounts/sharesOwnedFollowingTransaction")),
            "direct": (_t(tx, "ownershipNature/directOrIndirectOwnership") or "D") == "D",
        })
    return rows
