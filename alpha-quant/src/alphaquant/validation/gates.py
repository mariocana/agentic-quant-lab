"""Gates 2-7 of mc/docs/pipeline_prop.md as functions: trade list in, verdict out.

Every threshold lives in GateConfig, with the doc's values as defaults (NQ at
1 contract, LucidFlex 50k). A Check with passed=None could not be evaluated
(missing data, or a rule not modeled); it does not fail the gate, but the
gate is then not `complete` and the report says why.

Money: the input is the full-size list at 1 contract; gates divide by
`micro_ratio` where the doc says "÷ 10".
"""
from dataclasses import dataclass, field

import numpy as np

from alphaquant.validation.metrics import Metrics, measure
from alphaquant.validation.prop import LUCIDFLEX_50K, PropAccount, PropReport, cumulative, simulate
from alphaquant.validation.resampling import bootstrap_mean, dd_at_horizons, monte_carlo
from alphaquant.validation.trades import TradeLog


@dataclass(frozen=True)
class GateConfig:
    account: PropAccount = LUCIDFLEX_50K
    micro_ratio: float = 10.0          # NQ -> MNQ
    # Gate 2
    min_trades: int = 200
    min_avg_trade: float = 70.0        # NQ $70 (MNQ $7); GC $140
    min_pf: float = 1.2
    min_win_rate: float = 55.0
    rr_range: tuple[float, float] = (0.5, 1.0)
    max_dd_share_of_mll: float = 0.5   # one historical path: half the MLL as margin
    max_worst_share_of_mll: float = 0.25
    max_year_share: float = 0.5
    early_years: tuple[int, int] = (2021, 2023)
    late_from_year: int = 2024
    # Gate 3
    mc_sims: int = 1000
    max_losing_share: float = 0.10
    dd_pct: float = 95.0               # the tail already: no margin, 100% of the MLL
    # Gate 4
    max_optimized_inputs: int = 3
    # Gate 5
    oos_min_win_rate: float = 50.0
    oos_min_t: float = 1.3
    oos_min_avg_share: float = 0.5     # "same order of magnitude": OOS avg >= half the IS avg
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
class Check:
    name: str
    passed: bool | None
    value: str
    threshold: str


@dataclass(frozen=True)
class GateResult:
    stage: int
    title: str
    checks: list[Check]
    data: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(c.passed is not False for c in self.checks)

    @property
    def complete(self) -> bool:
        return all(c.passed is not None for c in self.checks)

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if c.passed is False]

    def report(self) -> str:
        mark = {True: "OK ", False: "NO ", None: "?  "}
        lines = [f"Gate {self.stage} - {self.title}"]
        lines += [f"  {mark[c.passed]} {c.name:<34} {c.value:<22} {c.threshold}" for c in self.checks]
        verdict = "PASS" if self.passed else "FAIL"
        if self.passed and not self.complete:
            verdict += " (incomplete: checks marked ? not evaluated)"
        lines.append(f"  VERDICT: {verdict}")
        return "\n".join(lines)


def _usd(x: float) -> str:
    return f"${x:,.0f}"


def gate2(log: TradeLog, cfg: GateConfig = GateConfig()) -> GateResult:
    """IS backtest, 1 contract, costs on: does the edge exist?"""
    m = measure(log)
    mll, r = cfg.account.mll, cfg.micro_ratio
    lo, hi = cfg.rr_range
    early = [v for y, v in m.by_year.items() if cfg.early_years[0] <= y <= cfg.early_years[1]]
    late = [v for y, v in m.by_year.items() if y >= cfg.late_from_year]
    stable = None if not early or not late else (sum(early) > 0) == (sum(late) > 0)
    share = m.top_year_share
    checks = [
        Check("trades IS", m.n >= cfg.min_trades, str(m.n), f">= {cfg.min_trades}"),
        Check("avg trade (net)", m.avg >= cfg.min_avg_trade, f"${m.avg:,.2f}", f">= ${cfg.min_avg_trade:,.2f}"),
        Check("profit factor", m.pf >= cfg.min_pf, f"{m.pf:.3f}", f">= {cfg.min_pf}"),
        Check("win rate", m.win_rate >= cfg.min_win_rate, f"{m.win_rate:.1f}%", f">= {cfg.min_win_rate:.0f}%"),
        Check("R:R (avg win / avg loss)", lo <= m.rr <= hi, f"{m.rr:.2f}", f"{lo}-{hi}"),
        Check("max DD / micro", m.max_dd / r <= cfg.max_dd_share_of_mll * mll,
              _usd(m.max_dd / r), f"<= {_usd(cfg.max_dd_share_of_mll * mll)}"),
        Check("worst trade / micro", -m.worst_trade / r <= cfg.max_worst_share_of_mll * mll,
              _usd(m.worst_trade / r), f">= -{_usd(cfg.max_worst_share_of_mll * mll)}"),
        Check("largest year share of net", None if share is None else share <= cfg.max_year_share,
              "n/a (net <= 0)" if share is None else f"{100 * share:.0f}%", f"<= {100 * cfg.max_year_share:.0f}%"),
        Check(f"same sign {cfg.early_years[0]}-{cfg.early_years[1] % 100} vs {cfg.late_from_year}+", stable,
              "n/a (a period is empty)" if stable is None else f"{sum(early):,.0f} / {sum(late):,.0f}", "same sign"),
    ]
    return GateResult(2, "IS backtest: does the edge exist?", checks, {"metrics": m})


def gate3(log: TradeLog, cfg: GateConfig = GateConfig()) -> GateResult:
    """Monte Carlo on the IS list.

    The drawdown tail comes from the reshuffle, as in MultiCharts. Median net and
    share of losing paths come from draws with replacement: under a pure reshuffle
    the net is the same in every path, and those two criteria would say nothing.
    """
    mc = monte_carlo(log.pnl, cfg.mc_sims, cfg.seed)
    dd = mc.dd_pct(cfg.dd_pct) / cfg.micro_ratio
    checks = [
        Check("median net (resample)", mc.median_net > 0, _usd(mc.median_net), "> $0"),
        Check("losing paths (resample)", mc.losing_share < cfg.max_losing_share,
              f"{100 * mc.losing_share:.1f}%", f"< {100 * cfg.max_losing_share:.0f}%"),
        Check(f"DD p{cfg.dd_pct:.0f} / micro (reshuffle)", dd <= cfg.account.mll, _usd(dd), f"<= {_usd(cfg.account.mll)}"),
    ]
    return GateResult(3, "Monte Carlo IS", checks, {"monte_carlo": mc})


def split_sample(base: TradeLog, variant: TradeLog) -> Check:
    """Stage 4: an addition must raise the avg trade in both halves of the IS."""
    b1, b2 = (measure(h).avg for h in base.halves())
    v1, v2 = (measure(h).avg for h in variant.halves())
    return Check("split-sample avg trade", v1 > b1 and v2 > b2,
                 f"{v1 - b1:+,.2f} / {v2 - b2:+,.2f}", "better in both halves")


def gate4(base: TradeLog, variant: TradeLog, optimized_inputs: int, cfg: GateConfig = GateConfig()) -> GateResult:
    """Improvements, IS only: split-sample, few inputs, then Gates 2 and 3 again on the variant."""
    g2, g3 = gate2(variant, cfg), gate3(variant, cfg)
    checks = [
        split_sample(base, variant),
        Check("optimized inputs", optimized_inputs <= cfg.max_optimized_inputs,
              str(optimized_inputs), f"<= {cfg.max_optimized_inputs}"),
        Check("Gate 2 on the variant", g2.passed, ", ".join(c.name for c in g2.failures) or "all ok", "pass"),
        Check("Gate 3 on the variant", g3.passed, ", ".join(c.name for c in g3.failures) or "all ok", "pass"),
        Check("rules simple and explainable", None, "judged by a person", ""),
    ]
    return GateResult(4, "Improvements (IS only)", checks, {"gate2": g2, "gate3": g3})


def gate5(is_log: TradeLog, oos_log: TradeLog, cfg: GateConfig = GateConfig()) -> GateResult:
    """OOS, parameters frozen, once. A fail goes to the cemetery: there is no second try."""
    mi, mo = measure(is_log), measure(oos_log)
    lo, hi = cfg.rr_range
    checks = [
        Check("avg trade OOS vs IS", mo.avg > 0 and mo.avg >= cfg.oos_min_avg_share * mi.avg,
              f"${mo.avg:,.2f} vs ${mi.avg:,.2f}", f">= {100 * cfg.oos_min_avg_share:.0f}% of IS"),
        Check("win rate OOS", mo.win_rate >= cfg.oos_min_win_rate, f"{mo.win_rate:.1f}%",
              f">= {cfg.oos_min_win_rate:.0f}%"),
        Check("profit factor OOS", mo.pf > 1.0, f"{mo.pf:.3f} (IS {mi.pf:.3f})", "> 1"),
        Check("R:R OOS", lo <= mo.rr <= hi, f"{mo.rr:.2f}", f"{lo}-{hi}"),
        Check("t OOS (equity drifts up)", mo.t >= cfg.oos_min_t, f"{mo.t:.2f}", f">= {cfg.oos_min_t}"),
        Check("DD OOS vs IS", mo.max_dd <= cfg.oos_max_dd_ratio * mi.max_dd,
              f"{_usd(mo.max_dd)} vs {_usd(mi.max_dd)}", f"<= {cfg.oos_max_dd_ratio}x IS"),
    ]
    return GateResult(5, "Out-of-sample (once)", checks, {"is": mi, "oos": mo})


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
    return GateResult(6, "Bootstrap EV (IS + OOS)", checks,
                      {"is_usd": is_usd, "is_r": is_r, "oos_usd": oos_usd, "oos_r": oos_r, "dd_yardstick": yardstick})


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
    return GateResult(7, f"Prop simulator, single strategy ({cfg.account.name})", checks, {"prop": rep})
