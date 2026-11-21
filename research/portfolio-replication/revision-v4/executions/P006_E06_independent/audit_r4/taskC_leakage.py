#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK C: look-ahead bias audit of the FF5 benchmark construction in
independent_upsa.py:412-419 (compute_metrics). Author code portfolios.py:49
uses ONLY in-sample FF5 for the per-window benchmark weights.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import T_WIN, RUN_ID, RESULTS, load_panels, dump, err, env_info


def sharpe(r):
    return float(np.sqrt(12) * np.mean(r) / np.std(r))


def alpha_one(y, x, annual_vol=0.1):
    ys = y * annual_vol / np.std(np.sqrt(12) * y)
    xs = x * annual_vol / np.std(np.sqrt(12) * x)
    mod = sm.OLS(ys, sm.add_constant(xs)).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    return float(np.asarray(mod.params)[0] * 12 * 100), float(np.asarray(mod.tvalues)[0])


def solve_w(ff5):
    """Author portfolios.py:49 b_weights = solve(cov(ff5_ins), mean(ff5_ins))."""
    return np.linalg.solve(np.cov(ff5, rowvar=False), np.mean(ff5, axis=0))


def main():
    panels, bench = load_panels()
    idx_all = panels.index[T_WIN:]
    n = len(idx_all)
    b = bench.drop(columns=["mom"]) if "mom" in bench.columns else bench.copy()
    # align benchmark to the FULL factor panel index (train + OOS), exactly as the
    # author's run_rolling_window does via align_to_common_index.
    b = b.reindex(panels.index)
    ff5_panel = b[["mkt", "smb", "hml", "rmw", "cma"]].to_numpy(float)
    ff5_oos_panel = ff5_panel[T_WIN:]              # the 494 OOS months used by E06

    # returns series of the three benchmark conventions
    r_full = np.empty(n)      # E06 current: one full-OOS estimate (LOOK-AHEAD)
    r_roll = np.empty(n)      # author: per-window in-sample estimate (NO look-ahead)
    r_expand = np.empty(n)    # research extension: expanding window (NO look-ahead)

    for i in range(n):
        ff5_oos = ff5_oos_panel[i]                 # month t OOS factor vector
        # (1) full OOS sample - uses ALL 494 OOS months, i.e. future months for every i
        r_full[i] = ff5_oos @ solve_w(ff5_oos_panel)
        # (2) author in-sample window - the T_WIN months preceding month i
        ins = ff5_panel[i:i + T_WIN]
        r_roll[i] = ff5_oos @ solve_w(ins)
        # (3) expanding window: starts with the T_WIN training months, then grows
        #     by one past month at a time (never uses months >= T_WIN+i)
        r_expand[i] = ff5_oos @ solve_w(ff5_panel[:T_WIN + i])

    # E06's actual FF5 series as recorded in metrics.json (should equal r_full)
    met = __import__("json").load(open(os.path.join(RESULTS, "metrics.json")))
    e06_ff5_sharpe = met["benchmark"]["FF5_sharpe"]

    # strategy returns (E06 current B0/B1) for alpha comparison
    o0 = pd.read_csv(os.path.join(RESULTS, "returns_B0.csv"))["return"].to_numpy(float)
    o1 = pd.read_csv(os.path.join(RESULTS, "returns_B1.csv"))["return"].to_numpy(float)

    bench_series = {
        "full_OOS_E06_current": r_full,
        "rolling_insample_author": r_roll,
        "expanding_no_lookahead": r_expand,
    }
    bsum = {}
    for k, v in bench_series.items():
        bsum[k] = {
            "sharpe": sharpe(v),
            "mean_monthly": float(np.mean(v)),
            "std_monthly": float(np.std(v)),
            "alpha_B0_pp": alpha_one(o0, v)[0],
            "alpha_B0_t": alpha_one(o0, v)[1],
            "alpha_B1_pp": alpha_one(o1, v)[0],
        }

    leakage = {
        "E06_code_location": "independent_upsa.py:412-419 compute_metrics",
        "E06_code": ("b = benchmark.reindex(all 494 OOS dates); ff5 = b[[mkt,smb,hml,rmw,cma]]; "
                     "bw = solve(cov(ff5), mean(ff5)); ff5_ret = ff5 @ bw  # ONE estimate over ALL OOS months"),
        "author_code_location": "src/portfolios.py:49 (_window_one)",
        "author_code": ("ff5_ins = FF5[i:rw+i]; b_weights = solve(cov(ff5_ins), mean(ff5_ins)); "
                        "opt['FF5'] = ff5_oos @ b_weights  # per-window, in-sample only"),
        "lookahead_verdict": "YES - E06 uses the entire 494-month OOS FF5 sample (including future "
                             "months relative to every date) to estimate one set of benchmark weights.",
        "is_author_comparison_convention": "NO - the author's own published FF5 benchmark is estimated "
                                            "rolling in-sample per window; E06 deviates from it.",
        "affects": ["benchmark FF5_sharpe reported in metrics.json",
                    "alpha_vs_FF5_pp (rival strategy for alpha)"],
        "does_not_affect": ["B0/B1 UPSA strategy returns and weights (they never use benchmark data)",
                            "B0/B1 Sharpe, turnover, pricing R2, alpha_vs_ridge, alpha_vs_CAPM"],
        "tradeable_as_strategy": "NO as implemented - requires all future FF5 returns; "
                                 "the rolling and expanding variants are tradeable.",
    }
    impact = {
        "E06_recorded_FF5_sharpe": e06_ff5_sharpe,
        "recomputed_full_OOS_sharpe": sharpe(r_full),
        "rolling_insample_sharpe": sharpe(r_roll),
        "expanding_sharpe": sharpe(r_expand),
        "full_vs_rolling_diff": err(r_full, r_roll),
        "full_vs_expanding_diff": err(r_full, r_expand),
        "by_convention": bsum,
        "recommendation": ("RESEARCH_EXTENSION / DIAGNOSTIC ONLY: report rolling-in-sample FF5 as the "
                           "author-comparable benchmark; keep full-OOS as a clearly-labelled look-ahead "
                           "diagnostic. Do NOT mix into the original paper reproduction verdict."),
    }
    out = {
        "run_id": RUN_ID, "n_oos": n, "T_WIN": T_WIN,
        "environment": env_info(),
        "leakage_audit": leakage, "numeric_impact": impact,
        "ff5_series": {k: v.tolist() for k, v in bench_series.items()},
    }
    dump("audit_C_leakage.json", out)
    print("E06 FF5 sharpe", e06_ff5_sharpe, "recomputed full", sharpe(r_full))
    print("rolling author sharpe", sharpe(r_roll), "expanding", sharpe(r_expand))
    print("full vs rolling maxabs", impact["full_vs_rolling_diff"]["maxabs"])
    print("alpha B0 full/rolling/expanding pp",
          bsum["full_OOS_E06_current"]["alpha_B0_pp"],
          bsum["rolling_insample_author"]["alpha_B0_pp"],
          bsum["expanding_no_lookahead"]["alpha_B0_pp"])


if __name__ == "__main__":
    main()
