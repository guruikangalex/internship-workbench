#!/usr/bin/env python3
"""Task C numerical experiments: locate the first divergence between the
author-manuscript cache and the deterministic cold recompute, and test which
layer (inputs / eigendecomposition / LW shrinkage / weight-to-return mapping)
amplifies the LW-family discrepancy.

Read-only. Writes lw_diagnosis_data.json with all measured numbers.
"""
import hashlib, json, os, pickle, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WORKROOT = "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43"
COLD = os.path.join(HERE, "cold_run/outputs/computed/main_bundle.p")
MS = os.path.join(WORKROOT, "CO-REP-20261120-02/evidence/_stage_P006/upsa_reproduction/outputs/computed/main_bundle.p")
RG = os.path.join(WORKROOT, "CO-REP-20261120-02/evidence/_stage_P006/upsa_reproduction/outputs/computed/main_bundle_regen.p")
PKG = os.path.join(HERE, "cold_run")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def load(p):
    return pickle.load(open(p, "rb"))


def cmp_df(a, b, label, out):
    """Compare two DataFrames elementwise; record max abs diff and first mismatch cell."""
    if list(a.index) != list(b.index) or list(a.columns) != list(b.columns):
        out[label] = {"index_equal": False, "columns_equal": False,
                      "note": "label set/order mismatch -> NOT_ASSESSED"}
        return
    d = (a.values - b.values)
    ad = np.abs(d)
    mi, mj = np.unravel_index(np.argmax(ad), ad.shape)
    # first cell (row-major) that differs at all
    nz = np.argwhere(ad > 0)
    if len(nz):
        fi, fj = nz[0]
        first = {"date": str(a.index[fi]), "col": str(a.columns[fj]),
                 "cold": float(a.values[fi, fj]), "cache": float(b.values[fi, fj]),
                 "abs_diff": float(ad[fi, fj])}
    else:
        first = None
    out[label] = {
        "shape": list(a.shape), "index_equal": True, "columns_equal": True,
        "max_abs_diff": float(ad.max()), "mean_abs_diff": float(ad.mean()),
        "max_cell": {"date": str(a.index[mi]), "col": str(a.columns[mj]),
                     "cold": float(a.values[mi, mj]), "cache": float(b.values[mi, mj]),
                     "abs_diff": float(ad[mi, mj])},
        "first_nonzero_cell": first,
        "n_nonzero_cells": int(np.count_nonzero(ad)),
    }


def main():
    cold, ms, rg = load(COLD), load(MS), load(RG)
    out = {
        "experiment": "R4/P006-E01 LW family divergence localization",
        "bundle_sha256": {"cold": sha(COLD), "manuscript": sha(MS), "regen": sha(RG)},
        "bundles": {},
    }

    for name, b in (("manuscript", ms), ("regen", rg)):
        e = {}
        cmp_df(cold["opt_port"], b["opt_port"], "opt_port_all_methods", e)
        for m in ("UPSA", "Ridge", "LW", "PCA", "FF5", "CAPM"):
            cmp_df(cold["opt_port"][[m]], b["opt_port"][[m]], f"opt_port_{m}", e)
        cmp_df(cold["weights"]["LW"], b["weights"]["LW"], "weights_LW", e)
        cmp_df(cold["weights"]["UPSA"], b["weights"]["UPSA"], "weights_UPSA", e)
        cmp_df(cold["weights"]["Ridge"], b["weights"]["Ridge"], "weights_Ridge", e)
        cmp_df(cold["z_grid_weights"], b["z_grid_weights"], "z_grid_weights", e)
        cmp_df(cold["eigenvalues"]["UPSA"], b["eigenvalues"]["UPSA"], "eigcurve_UPSA", e)
        cmp_df(cold["eigenvalues"]["Ridge"], b["eigenvalues"]["Ridge"], "eigcurve_Ridge", e)
        out["bundles"][name] = e

    # ---- LW amplification experiment on one window ----
    # Rebuild window 0 exactly as the author pipeline does, then perturb the
    # eigendecomposition at increasing relative magnitudes and measure how the
    # LW weight / OOS return responds. This tests the shrinkage-amplification
    # layer without needing the author's original environment.
    sys.path.insert(0, PKG)
    from src.data import load_panel
    from src.upsa import UPSA
    from src.shrinkage import do_lw
    from src.data import align_to_common_index

    factors = load_panel("factors_main")
    bench = load_panel("benchmark")
    bench = bench.drop(columns=["mom"]) if "mom" in bench.columns else bench
    bench, factors = align_to_common_index(bench, factors)
    X = factors.values
    rw = 120
    z_grid = np.logspace(-10, -1, 10)
    f_ins, f_oos = X[0:rw], X[rw]

    upsa = UPSA(z_list=z_grid).fit(returns=f_ins)
    w_lw0, delta0 = do_lw(returns=f_ins, eigenvalues=upsa.eigenvalues,
                          eigenvectors=upsa.eigenvectors)
    r0 = float(f_oos @ w_lw0)

    amp = []
    rng = np.random.default_rng(0)
    for rel in (1e-14, 1e-12, 1e-10, 1e-8, 1e-6):
        pert_eig = upsa.eigenvalues * (1 + rel * rng.standard_normal(upsa.eigenvalues.shape))
        wl, _ = do_lw(returns=f_ins, eigenvalues=pert_eig, eigenvectors=upsa.eigenvectors)
        amp.append({
            "rel_eig_perturbation": rel,
            "lw_weight_max_abs_diff": float(np.max(np.abs(wl - w_lw0))),
            "oos_return_diff": float(f_oos @ (wl - w_lw0)),
        })
    out["lw_amplification_window0"] = {
        "T": int(f_ins.shape[0]), "P": int(f_ins.shape[1]),
        "n_eigs": int(len(upsa.eigenvalues)),
        "eig_min": float(np.min(upsa.eigenvalues)), "eig_max": float(np.max(upsa.eigenvalues)),
        "z_grid": [float(z) for z in z_grid],
        "base_lw_weight_norm": float(np.linalg.norm(w_lw0)),
        "base_oos_return": r0,
        "perturbation_results": amp,
    }

    # ---- eigenvalues used by LW (raw UPSA eigendecomposition) ----
    out["window0_raw_eigs"] = {
        "first_10": [float(x) for x in upsa.eigenvalues[:10]],
        "last_10": [float(x) for x in upsa.eigenvalues[-10:]],
        "condition_number_maxmin": float(np.max(upsa.eigenvalues) / np.maximum(np.min(upsa.eigenvalues), 1e-300)),
        "n_negative": int(np.sum(upsa.eigenvalues < 0)),
    }

    fp = os.path.join(HERE, "lw_diagnosis_data.json")
    with open(fp, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("wrote", fp)
    for name in ("manuscript", "regen"):
        print("===", name, "===")
        for key in ("opt_port_UPSA", "opt_port_Ridge", "opt_port_LW", "opt_port_PCA",
                    "weights_LW", "eigcurve_UPSA"):
            v = out["bundles"][name][key]
            if "max_abs_diff" in v:
                fc = v["first_nonzero_cell"]
                print(f"  {key:18s} max={v['max_abs_diff']:.6e} n_nonzero={v['n_nonzero_cells']}"
                      f" first={fc['date']}/{fc['col']} diff={fc['abs_diff']:.3e}" if fc else
                      f"  {key:18s} IDENTICAL")


if __name__ == "__main__":
    main()
