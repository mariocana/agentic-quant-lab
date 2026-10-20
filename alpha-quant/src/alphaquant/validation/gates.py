"""The gates of the pipeline as functions: trade list in, verdict out.

Two methodologies, kept apart (mc/docs/prop_vs_live.md, 15/10/2026):

    prop  passing an eval. Active. Its checks make the verdict.
    live  own capital. FROZEN until payouts start (mc/docs/metodologia_live.md).
          Its checks are computed and printed, marked as live, and never touch
          the verdict while LiveConfig.frozen is True.

Prop gates (mc/docs/pipeline_semplice.md):
    2  IS: does the edge exist?         n, t >= 2, WR >= 55%, R:R 0.5-1
    4  improvements, IS only            split-sample, <= 3 inputs, Gate 2 again
    5  OOS, once: does it hold?         t >= 1.3, WR >= 50%, R:R 0.5-1, DD <= 1.5x IS
    6  bootstrap EV, IS + OOS           EV > 0, P(EV <= 0), CI overlap
    7  prop simulator: is it enough?    pass rate, cumulated over attempts; size is an output
The old Gate 3 (Monte Carlo drawdown against the MLL) is retired: the drawdown
enters only as the MLL inside the Stage 7 simulation.

A Check with passed=None could not be evaluated (a rule not modeled, a period
not given); it does not fail the gate, but the gate is then not `complete`.
"""
from dataclasses import dataclass, field
from datetime import date

import numpy as np

from alphaquant.validation.metrics import Metrics, measure
from alphaquant.validation.prop import LUCIDFLEX_50K, PropAccount, PropReport, cumulative, simulate
from alphaquant.validation.resampling import bootstrap_mean, dd_at_horizons
from alphaquant.validation.trades import TradeLog


@dataclass(frozen=True)
class GateConfig:
    """Prop thresholds."""
    account: PropAccount = LUCIDFLEX_50K
    micro_ratio: float = 10.0          # NQ -> MNQ
    # Gate 2
    min_trades: int = 200
    min_t: float = 2.0
    min_win_rate: float = 55.0
    rr_range: tuple[float, float] = (0.5, 1.0)
    period_slack_days: int = 31        # first/last trade this close to the declared range
    # Gate 4
    max_optimized_inputs: int = 3
    # Gate 5
    oos_min_t: float = 1.3
    oos_min_win_rate: float = 50.0
    oos_max_dd_ratio: float = 1.5
    # Gate 6
    boot_sims: int = 10_000
    boot_ci: float = 0.95
    max_p_ev_le_zero_is: float = 0.05
    max_p_ev_le_zero_oos: float = 0.10
    dd_horizons: tuple[int, ...] = (10, 20, 40)
    # Gate 7
    cost_in_report: float = 15.0       # round turn inside the report's P&L (NQ $7.50/side)
    cost_micro: float = 1.50           # MNQ round turn
    prop_sizes: tuple[int, ...] = (1, 2, 3, 4, 6, 8)
    prop_sims: int = 20_000
    prop_max_days: int = 60
    min_first_pass: float = 0.40
    min_pass_within_4: float = 0.85
    max_mean_days: float = 15.0
    max_expired: float = 0.05
    seed: int = 20261015


@dataclass(frozen=True)
class LiveConfig:
    """Own-capital thresholds, frozen on 15/10/2026 (metodologia_live.md)."""
    frozen: bool = True
    min_pf: float = 1.2
    min_avg_trade: float = 70.0        # NQ $70 (MNQ $7); GC $140
    max_year_share: float = 0.5
    early_years: tuple[int, int] = (2021, 2023)
    late_from_year: int = 2024


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool | None
    value: str
    threshold: str


@dataclass(frozen=True)
class GateResult:
    stage: int
    title: str
    checks: list[Check]                               # prop: these make the verdict
    live: list[Check] = field(default_factory=list)   # own capital: frozen, informative
    live_frozen: bool = True
    data: dict = field(default_factory=dict)

    def _verdict_checks(self) -> list[Check]:
        return self.checks if self.live_frozen else self.checks + self.live

    @property
    def passed(self) -> bool:
        return all(c.passed is not False for c in self._verdict_checks())

    @property
    def complete(self) -> bool:
        return all(c.passed is not None for c in self._verdict_checks())

    @property
    def failures(self) -> list[Check]:
        return [c for c in self._verdict_checks() if c.passed is False]

    def report(self) -> str:
        mark = {True: "OK ", False: "NO ", None: "?  "}
        row = lambda c: f"  {mark[c.passed]} {c.name:<34} {c.value:<22} {c.threshold}"
        lines = [f"Gate {self.stage} - {self.title}"] + [row(c) for c in self.checks]
        if self.live:
            state = "FROZEN, informative, not in the verdict" if self.live_frozen else "ACTIVE"
            lines += [f"  -- live criteria (own capital): {state}"] + [row(c) for c in self.live]
        verdict = "PASS" if self.passed else "FAIL"
        if self.passed and not self.complete:
            verdict += " (incomplete: checks marked ? not evaluated)"
        lines.append(f"  VERDICT: {verdict}")
        return "\n".join(lines)


def _usd(x: float) -> str:
    return f"${x:,.0f}"


def _rr(m: Metrics, cfg: GateConfig, label: str) -> Check:
    lo, hi = cfg.rr_range
    return Check(label, lo <= m.rr <= hi, f"{m.rr:.2f}", f"{lo}-{hi}")


def live_checks(m: Metrics, live: LiveConfig = LiveConfig(), long_horizon: bool = True) -> list[Check]:
    """Own-capital criteria. `long_horizon` adds those that judge years, not an eval."""
    checks = [
        Check("avg trade (net)", m.avg >= live.min_avg_trade, f"${m.avg:,.2f}", f">= ${live.min_avg_trade:,.2f}"),
    ]
    if not long_horizon:
        return checks
    share = m.top_year_share
    early = [v for y, v in m.by_year.items() if live.early_years[0] <= y <= live.early_years[1]]
    late = [v for y, v in m.by_year.items() if y >= live.late_from_year]
    stable = None if not early or not late else (sum(early) > 0) == (sum(late) > 0)
    return [
        Check("profit factor", m.pf >= live.min_pf, f"{m.pf:.3f}", f">= {live.min_pf}"),
        *checks,
        Check("largest year share of net", None if share is None else share <= live.max_year_share,
              "n/a (net <= 0)" if share is None else f"{100 * share:.0f}%", f"<= {100 * live.max_year_share:.0f}%"),
        Check(f"same sign {live.early_years[0]}-{live.early_years[1] % 100} vs {live.late_from_year}+", stable,
              "n/a (a period is empty)" if stable is None else f"{sum(early):,.0f} / {sum(late):,.0f}", "same sign"),
    ]


def gate2(
    log: TradeLog,
    cfg: GateConfig = GateConfig(),
    live: LiveConfig = LiveConfig(),
    period: tuple[date, date] | None = None,
) -> GateResult:
    """IS, 1 contract, costs on: does the edge exist? `period` is the IS range declared in SPEC.md."""
    m = measure(log)
    checks = [
        Check("trades IS", m.n >= cfg.min_trades, str(m.n), f">= {cfg.min_trades}"),
        Check("t (avg / error bar)", m.t >= cfg.min_t, f"{m.t:.2f}", f">= {cfg.min_t}"),
        Check("win rate", m.win_rate >= cfg.min_win_rate, f"{m.win_rate:.1f}%", f">= {cfg.min_win_rate:.0f}%"),
        _rr(m, cfg, "R:R (avg win / avg loss)"),
    ]
    if period is not None:
        first = log.frame["entry_time"].min().date()
        last = log.frame["entry_time"].max().date()
        slack = cfg.period_slack_days
        covered = (first - period[0]).days <= slack and (period[1] - last).days <= slack
        checks.append(Check("time range covers the declared IS", covered, f"{first} -> {last}",
                            f"{period[0]} -> {period[1]}"))
    # a number to look at, not a threshold (Live 002, 245)
    checks.append(Check("avg trade (net), to look at", True, f"${m.avg:,.2f}", "info"))
    return GateResult(2, "IS: does the edge exist?", checks, live_checks(m, live), live.frozen, {"metrics": m})


def split_sample(base: TradeLog, variant: TradeLog) -> Check:
    """Stage 4: an addition must raise the avg trade in both halves of the IS."""
    b1, b2 = (measure(h).avg for h in base.halves())
    v1, v2 = (measure(h).avg for h in variant.halves())
    return Check("split-sample avg trade", v1 > b1 and v2 > b2,
                 f"{v1 - b1:+,.2f} / {v2 - b2:+,.2f}", "better in both halves")


def gate4(base: TradeLog, variant: TradeLog, optimized_inputs: int, cfg: GateConfig = GateConfig(),
          live: LiveConfig = LiveConfig()) -> GateResult:
    """Improvements, IS only: split-sample, few inputs, then Gate 2 again on the variant."""
    g2 = gate2(variant, cfg, live)
    checks = [
        split_sample(base, variant),
        Check("optimized inputs", optimized_inputs <= cfg.max_optimized_inputs,
              str(optimized_inputs), f"<= {cfg.max_optimized_inputs}"),
        Check("Gate 2 on the variant", g2.passed, ", ".join(c.name for c in g2.failures) or "all ok", "pass"),
        Check("rules simple and explainable", None, "judged by a person", ""),
    ]
    return GateResult(4, "Improvements (IS only)", checks, live_frozen=live.frozen, data={"gate2": g2})


def gate5(is_log: TradeLog, oos_log: TradeLog, cfg: GateConfig = GateConfig(),
          live: LiveConfig = LiveConfig()) -> GateResult:
    """OOS, parameters frozen, once. A fail goes to the cemetery: there is no second try."""
    mi, mo = measure(is_log), measure(oos_log)
    checks = [
        Check("t OOS", mo.t >= cfg.oos_min_t, f"{mo.t:.2f} (IS {mi.t:.2f})", f">= {cfg.oos_min_t}"),
        Check("win rate OOS", mo.win_rate >= cfg.oos_min_win_rate, f"{mo.win_rate:.1f}% (IS {mi.win_rate:.1f}%)",
              f">= {cfg.oos_min_win_rate:.0f}%"),
        _rr(mo, cfg, "R:R OOS"),
        Check("DD OOS vs IS", mo.max_dd <= cfg.oos_max_dd_ratio * mi.max_dd,
              f"{_usd(mo.max_dd)} vs {_usd(mi.max_dd)}", f"<= {cfg.oos_max_dd_ratio}x IS"),
        Check("avg trade OOS, to look at", True, f"${mo.avg:,.2f} (IS ${mi.avg:,.2f})", "info"),
    ]
    return GateResult(5, "Out-of-sample (once)", checks, live_checks(mo, live, long_horizon=False), live.frozen,
                      {"is": mi, "oos": mo})


def gate6(is_log: TradeLog, oos_log: TradeLog, risk_per_contract: float, cfg: GateConfig = GateConfig()) -> GateResult:
    """Bootstrap of the EV in $ and in R, IS and OOS (Colab EV notebook).

    `risk_per_contract` is the average stop in $ for 1 contract; R = pnl / (contracts x risk).
    """
    if risk_per_contract <= 0:
        raise ValueError("risk_per_contract must be > 0")
    res = {}
    for name, log in (("is", is_log), ("oos", oos_log)):
        r = log.pnl / (log.frame["contracts"].to_numpy() * risk_per_contract)
        res[name] = (bootstrap_mean(log.pnl, cfg.boot_sims, cfg.boot_ci, cfg.seed),
                     bootstrap_mean(r, cfg.boot_sims, cfg.boot_ci, cfg.seed))
    (is_usd, is_r), (oos_usd, oos_r) = res["is"], res["oos"]
    p_is = max(is_usd.p_le_zero, is_r.p_le_zero)
    p_oos = max(oos_usd.p_le_zero, oos_r.p_le_zero)
    checks = [
        Check("EV IS > 0 ($ and R)", is_usd.mean > 0 and is_r.mean > 0, f"${is_usd.mean:,.2f} / {is_r.mean:.3f}R", "> 0"),
        Check("EV OOS > 0 ($ and R)", oos_usd.mean > 0 and oos_r.mean > 0,
              f"${oos_usd.mean:,.2f} / {oos_r.mean:.3f}R", "> 0"),
        Check("P(EV <= 0) IS", p_is < cfg.max_p_ev_le_zero_is, f"{p_is:.3f}", f"< {cfg.max_p_ev_le_zero_is}"),
        Check("P(EV <= 0) OOS", p_oos < cfg.max_p_ev_le_zero_oos, f"{p_oos:.3f}", f"< {cfg.max_p_ev_le_zero_oos}"),
        Check("CI IS and OOS overlap ($)", is_usd.overlaps(oos_usd),
              f"[{is_usd.lo:,.0f}, {is_usd.hi:,.0f}] [{oos_usd.lo:,.0f}, {oos_usd.hi:,.0f}]", "overlap"),
    ]
    yardstick = dd_at_horizons(np.concatenate([is_log.pnl, oos_log.pnl]), cfg.dd_horizons, seed=cfg.seed)
    return GateResult(6, "Bootstrap EV (IS + OOS)", checks, data={
        "is_usd": is_usd, "is_r": is_r, "oos_usd": oos_usd, "oos_r": oos_r, "dd_yardstick": yardstick,
    })


def gate7(oos_log: TradeLog, cfg: GateConfig = GateConfig()) -> GateResult:
    """Prop simulator, single strategy, on the OOS list (full size; converted to micro here)."""
    micro = oos_log.to_micro(cfg.micro_ratio, cfg.cost_in_report, cfg.cost_micro)
    rep: PropReport = simulate(micro, cfg.account, cfg.prop_sizes, cfg.prop_sims, cfg.prop_max_days, seed=cfg.seed)
    iid = rep.iid
    within4 = cumulative(iid.pass_rate, 4)
    days = iid.mean_days_to_pass
    checks = [
        Check(f"pass rate 1st attempt ({rep.best} micro)", iid.pass_rate >= cfg.min_first_pass,
              f"{100 * iid.pass_rate:.1f}%", f">= {100 * cfg.min_first_pass:.0f}%"),
        Check("pass within 4 attempts (iid)", within4 >= cfg.min_pass_within_4,
              f"{100 * within4:.1f}% (seq {100 * rep.sequential[min(4, len(rep.sequential) - 1)]:.1f}%)",
              f">= {100 * cfg.min_pass_within_4:.0f}%"),
        Check("mean days to pass", None if days is None else days <= cfg.max_mean_days,
              "n/a (no pass)" if days is None else f"{days:.1f}", f"<= {cfg.max_mean_days:.0f}"),
        Check(f"expired evals (> {cfg.prop_max_days} days)", iid.open_rate < cfg.max_expired,
              f"{100 * iid.open_rate:.1f}%", f"< {100 * cfg.max_expired:.0f}%"),
        Check("mean DD in attempt", iid.mean_max_dd < cfg.account.mll, _usd(iid.mean_max_dd), f"< {_usd(cfg.account.mll)}"),
        Check("size <= reliable size", rep.best <= rep.reliable, f"{rep.best} vs {rep.reliable}", "p95 loss per micro"),
        Check("FUNDED: qualification and payout", None, "not modeled", "funded rules not in the simulator"),
    ]
    return GateResult(7, f"Prop simulator, single strategy ({cfg.account.name})", checks, data={"prop": rep})
