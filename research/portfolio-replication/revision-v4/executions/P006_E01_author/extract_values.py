#!/usr/bin/env python3
"""Read-only extraction of published target values from an author main_bundle.p.

Uses the author's OWN functions/constants (imported from --pkg) so the evaluator
formulas are identical to the plotting pipeline. Does not modify author code.
"""
import argparse, json, os, pickle, sys
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score


def load_bundle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def extract(pkg, bundle_path):
    sys.path.insert(0, pkg)
    from src.data import load_panel
    from src import pricing, plotting, tables
    from src.constants import JKP_CLUSTERS
    from src.metrics import sharpe, turnover_fun

    b = load_bundle(bundle_path)
    opt = b["opt_port"]
    factors = load_panel("factors_main")

    out = {"bundle_path": bundle_path, "oos_start": str(opt.index.min()),
           "oos_end": str(opt.index.max()), "oos_months": int(len(opt)),
           "models": list(opt.columns)}

    # ---- Table 1: R^2 by theme (full precision, SDF-based) ----
    r2 = pricing.r_2_table_gen(opt, factors, JKP_CLUSTERS)   # index=theme rows? -> columns are themes
    # r_2_table_gen returns DataFrame indexed by opt columns? check: all_r_2[cluster][c_] -> columns=themes, index=methods
    r2_dict = {}
    for method in r2.index:
        r2_dict[str(method)] = {str(k): (None if pd.isna(v) else float(v)) for k, v in r2.loc[method].items()}
    out["table1_r2"] = r2_dict

    # ---- Fig 3: Sharpe full / before-2000 / after-2000 ----
    periods = [(None, None), (None, "2000"), ("2000", None)]
    names = ["FULL", "BEFORE-2000", "AFTER-2000"]
    f3 = {}
    for name, (start, end) in zip(names, periods):
        if start is None and end is not None:
            sub = opt[:end]
        elif start is not None and end is None:
            sub = opt[start:]
        else:
            sub = opt
        sv = sharpe(sub)
        f3[name] = {str(k): (None if pd.isna(v) else float(v)) for k, v in sv.items()}
        f3[name + "_WINDOW"] = {"start": str(sub.index.min()), "end": str(sub.index.max()), "n": int(len(sub))}
    out["fig3_sharpe"] = f3

    # ---- Fig 5: alpha of UPSA vs each other col, HAC(5), annual_vol=0.1 ----
    f5 = {}
    y = opt.iloc[:, 0].copy()  # UPSA
    for col in opt.columns[1:]:
        a, lo, hi, t = plotting._alpha_one(y.copy(), opt[[col]].copy(), 0.1)
        f5[str(col)] = {"alpha": float(a), "ci_lo_margin": float(lo), "ci_hi_margin": float(hi),
                        "tstat": float(t)}
    out["fig5_alpha"] = f5

    # ---- Fig 8: monthly turnover (%) raw mean + 12m rolling series ----
    ts, cs = turnover_fun(b["weights"])
    ts = pd.DataFrame(ts)
    f8 = {}
    for m in ("UPSA", "Ridge"):
        raw = ts[m]
        rolling = raw.rolling(12).mean().dropna()
        f8[m] = {"mean_monthly_pct": float(raw.mean()),
                 "rolling_first_date": str(rolling.index.min()),
                 "rolling_last_date": str(rolling.index.max()),
                 "rolling_n": int(len(rolling)),
                 "rolling_values": [float(v) for v in rolling.values]}
    out["fig8_turnover"] = f8

    # ---- Fig 6: SDF predicted vs realized Sharpe per factor + R^2 ----
    realized, predicted = pricing.sdf_predicted_realized(opt, factors, scaling=True)
    f6 = {"realized": {str(k): (None if pd.isna(v) else float(v)) for k, v in realized.items()}}
    for m in predicted:
        p = predicted[m]
        f6[m] = {"predicted": {str(k): (None if pd.isna(v) else float(v)) for k, v in p.items()},
                 "r2": float(r2_score(realized, p))}
    out["fig6_pricingacc"] = f6

    # ---- NaN / inf diagnostics on opt_port ----
    out["opt_nan_count"] = int(opt.isna().sum().sum())
    out["opt_inf_count"] = int(np.isinf(opt.values).sum())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", required=True)
    ap.add_argument("--bundles", nargs="+", required=True, help="name=path pairs")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = {}
    for spec in args.bundles:
        name, path = spec.split("=", 1)
        result[name] = extract(args.pkg, path)
        print(f"extracted {name}: oos {result[name]['oos_start']}..{result[name]['oos_end']} "
              f"n={result[name]['oos_months']} nan={result[name]['opt_nan_count']} inf={result[name]['opt_inf_count']}")
    with open(args.out, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
