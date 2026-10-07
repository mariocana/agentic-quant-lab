"""Read-only market data from Hyperliquid. No key needed.

Wraps hyperliquid.info.Info and returns our schemas. Everything numeric comes back
from the API as strings; conversion happens here and nowhere else.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from hyperliquid.info import Info
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from desk.schemas import AccountState, AssetContext, Position, asset_class

INTERVAL_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}


class Candle(dict):
    """{t, o, h, l, c, v} with t in ms UTC. Kept as a dict for cheap parquet/sqlite IO."""


def _with_retries(info: Info, attempts: int = 4, timeout_s: float = 20.0) -> Info:
    """Make the SDK's HTTP session survive a dropped connection.

    One cycle makes ~30 sequential calls. Without this, a single
    "Remote end closed connection without response" kills the whole cycle: no
    orders, no journal record, a trading day lost. Seen in production.
    """
    retry = Retry(
        total=attempts, connect=attempts, read=attempts, status=attempts,
        backoff_factor=0.5,                       # 0.5s, 1s, 2s, 4s
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),   # these reads are idempotent
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=16)
    info.session.mount("https://", adapter)
    info.session.mount("http://", adapter)
    if info.timeout is None:
        info.timeout = timeout_s              # never hang a cycle on one call
    return info


class HLMarket:
    def __init__(self, base_url: str, dexs: tuple[str, ...] = ()):
        self.info = _with_retries(Info(base_url, skip_ws=True))
        self.dexs = dexs
        self._meta_cache: dict[str, dict] = {}   # asset -> {szDecimals, maxLeverage}

    # ---- universe / metadata -------------------------------------------------

    def refresh_meta(self) -> dict[str, dict]:
        meta = self.info.meta()
        self._meta_cache = {u["name"]: u for u in meta["universe"]}
        for dex in self.dexs:
            m = self.info.meta(dex=dex)
            self._meta_cache.update({u["name"]: u for u in m["universe"]})
        return self._meta_cache

    def meta(self, asset: str) -> dict:
        if asset not in self._meta_cache:
            self.refresh_meta()
        try:
            return self._meta_cache[asset]
        except KeyError:
            raise KeyError(f"{asset} is not listed on this venue "
                           f"({len(self._meta_cache)} perps available)") from None

    def contexts(self) -> dict[str, AssetContext]:
        """Funding, OI, mark, mid, 24h volume for every main-dex perp."""
        meta, ctxs = self.info.meta_and_asset_ctxs()
        out: dict[str, AssetContext] = {}
        for u, c in zip(meta["universe"], ctxs):
            if u.get("isDelisted") or c.get("midPx") is None:
                continue
            out[u["name"]] = AssetContext(
                asset=u["name"],
                mark_px=float(c["markPx"]),
                mid_px=float(c["midPx"]),
                funding_hourly=float(c["funding"]),
                open_interest=float(c["openInterest"]),
                day_volume_usd=float(c["dayNtlVlm"]),
                sz_decimals=int(u["szDecimals"]),
                max_leverage=int(u["maxLeverage"]),
            )
        return out

    def top_by_volume(self, n: int, exclude_hip3: bool = True) -> list[str]:
        ctxs = self.contexts()
        names = [a for a in ctxs if not (exclude_hip3 and asset_class(a) == "hip3")]
        names.sort(key=lambda a: ctxs[a].day_volume_usd, reverse=True)
        return names[:n]

    # ---- prices --------------------------------------------------------------

    def candles(self, asset: str, interval: str, bars: int) -> list[Candle]:
        step = INTERVAL_MS[interval]
        end = int(time.time() * 1000)
        start = end - bars * step
        raw = self.info.candles_snapshot(asset, interval, start, end)
        return [
            Candle(t=int(r["t"]), o=float(r["o"]), h=float(r["h"]), l=float(r["l"]), c=float(r["c"]), v=float(r["v"]))
            for r in raw
        ]

    def book_depth_10bps(self, asset: str) -> tuple[float, float]:
        """(mid, USD notional resting within 10 bps of mid, both sides)."""
        book = self.info.l2_snapshot(asset)
        bids, asks = book["levels"]
        if not bids or not asks:
            return 0.0, 0.0
        best_bid, best_ask = float(bids[0]["px"]), float(asks[0]["px"])
        mid = (best_bid + best_ask) / 2
        lo, hi = mid * (1 - 0.001), mid * (1 + 0.001)
        depth = sum(float(l["px"]) * float(l["sz"]) for l in bids if float(l["px"]) >= lo)
        depth += sum(float(l["px"]) * float(l["sz"]) for l in asks if float(l["px"]) <= hi)
        return mid, depth

    # ---- account (read-only, needs only the address) -------------------------

    def spot_usdc(self, address: str) -> float:
        """USDC on the spot balance. On a Unified account it backs perp margin; on a
        classic one it is money the desk cannot touch until it is moved across."""
        try:
            st = self.info.post("/info", {"type": "spotClearinghouseState", "user": address})
            return sum(float(b["total"]) for b in st.get("balances", []) if b.get("coin") == "USDC")
        except Exception:                 # noqa: BLE001 - informational
            return 0.0

    def account_state(self, address: str, unified_collateral: bool = False) -> AccountState:
        st = self.info.user_state(address)
        ms = st["marginSummary"]
        positions = []
        for ap in st.get("assetPositions", []):
            p = ap["position"]
            size = float(p["szi"])
            if size == 0:
                continue
            entry = float(p["entryPx"]) if p.get("entryPx") else 0.0
            notional = float(p["positionValue"]) * (1 if size > 0 else -1)
            mark = abs(notional / size) if size else entry
            positions.append(Position(
                asset=p["coin"], notional_usd=notional, size=size, entry_px=entry,
                mark_px=mark, unrealized_pnl_usd=float(p["unrealizedPnl"]),
            ))
        spot = self.spot_usdc(address)
        equity = float(ms["accountValue"])
        return AccountState(
            # On a Unified account the exchange lets spot USDC back perp margin, and
            # the app shows the sum as "Available to Trade". The API reports the two
            # separately and nothing in it says which mode the account is in, so this
            # is a declared setting: inferring it would mean guessing how much capital
            # the desk has, and sizing every limit off that guess.
            equity_usd=equity + spot if unified_collateral else equity,
            margin_used_usd=float(ms["totalMarginUsed"]),
            positions=positions,
            spot_usdc=spot,
            as_of=datetime.now(timezone.utc),
        )
