#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P006-E06: three-path comparison (A author bundle vs B0/B1 independent).

Reads A's main_bundle.p READ-ONLY from P006_E01_author. Writes only into
P006_E06_independent/results/.
"""
import os
import json
import pickle
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
A_BUNDLE = ("/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/internship-workbench/"
            "research/portfolio-replication/revision-v3/executions/"
            "P006_E01_author/outputs/computed/main_bundle.p")


def diff_stats(x, y):
    d = x - y
    return {
        "maxabs": float(np.max(np.abs(d))),
        "meanabs": float(np.mean(np.abs(d))),
        "fro": float(np.linalg.norm(d)),
        "relative_fro": float(np.linalg.norm(d) / max(np.linalg.norm(y), 1e-300)),
        "corr": float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 0 and np.std(y) > 0 else None,
    }


def sharpe(r):
    return float(np.sqrt(12) * np.mean(r) / np.std(r))


def turnover(w):
    gross = np.abs(w).sum(axis=1)
    t = np.zeros(len(w))
    t[1:] = 0.5 * np.abs(np.diff(w, axis=0)).sum(axis=1) / gross[:-1]
    return float(100 * np.mean(t))


def main():
    with open(A_BUNDLE, "rb") as f:
        A = pickle.load(f)
    a_ret = A["opt_port"]["UPSA"].astype(float)
    a_w = A["weights"]["UPSA"].astype(float)
    b0_ret = pd.read_csv(os.path.join(RESULTS, "returns_B0.csv"), parse_dates=["date"]).set_index("date")["return"]
    b1_ret = pd.read_csv(os.path.join(RESULTS, "returns_B1.csv"), parse_dates=["date"]).set_index("date")["return"]
    b0_w = pd.read_csv(os.path.join(RESULTS, "weights_B0.csv"), index_col=0, parse_dates=True)
    b1_w = pd.read_csv(os.path.join(RESULTS, "weights_B1.csv"), index_col=0, parse_dates=True)
    dates = a_ret.index.intersection(b0_ret.index).intersection(b1_ret.index)
    dates = dates.sort_values()
    a_r = a_ret.loc[dates].to_numpy(float)
    r0 = b0_ret.loc[dates].to_numpy(float)
    r1 = b1_ret.loc[dates].to_numpy(float)
    a_m = a_w.loc[dates].to_numpy(float)
    w0 = b0_w.loc[dates].to_numpy(float)
    w1 = b1_w.loc[dates].to_numpy(float)

    out = {
        "run_id": "P006-E06-INDEP-20261121-01",
        "source_A": "P006_E01_author/outputs/computed/main_bundle.p (read-only)",
        "source_B": "P006_E06_independent/results/returns_B*.csv + weights_B*.csv",
        "n_aligned_months": len(dates),
        "first": str(dates[0].date()), "last": str(dates[-1].date()),
        "finite_A_returns": bool(np.isfinite(a_r).all()),
        "finite_B0_returns": bool(np.isfinite(r0).all()),
        "finite_B1_returns": bool(np.isfinite(r1).all()),
        "sharpe": {"A": sharpe(a_r), "B0": sharpe(r0), "B1": sharpe(r1)},
        "mean_monthly": {"A": float(np.mean(a_r)), "B0": float(np.mean(r0)), "B1": float(np.mean(r1))},
        "turnover_pct": {"A": turnover(a_m), "B0": turnover(w0), "B1": turnover(w1)},
        "returns": {
            "A_vs_B0": diff_stats(a_r, r0),
            "A_vs_B1": diff_stats(a_r, r1),
            "B0_vs_B1": diff_stats(r0, r1),
        },
        "weights": {
            "A_vs_B0": diff_stats(a_m, w0),
            "A_vs_B1": diff_stats(a_m, w1),
            "B0_vs_B1": diff_stats(w0, w1),
        },
        "interpretation": {
            "A_vs_B0": "A author path (divisor-T smoother, w_adj/z roundoff) vs B0 stable expression (c=T). Differences are numerical-implementation level; both target the same divisor-T math.",
            "A_vs_B1": "A author path vs paper T-1 leave-one-out. Combines numerical-implementation and divisor-convention differences.",
            "B0_vs_B1": "Isolates the T vs T-1 leave-one-out normalization difference with identical stable implementation.",
        },
    }
    with open(os.path.join(RESULTS, "three_path_comparison.json"), "w") as f:
        json.dump(out, f, indent=2)
    pd.DataFrame({"date": dates, "A_UPSA": a_r, "B0_UPSA": r0, "B1_UPSA": r1,
                  "A_minus_B0": a_r - r0, "A_minus_B1": a_r - r1,
                  "B0_minus_B1": r0 - r1}).to_csv(
        os.path.join(RESULTS, "returns_three_path.csv"), index=False)
    print(json.dumps(out, indent=2))
    print("WROTE results/three_path_comparison.json, results/returns_three_path.csv")


if __name__ == "__main__":
    main()
