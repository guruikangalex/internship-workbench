#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK A corrected full rerun: K/T eigenvalue convention in trace scaling.
New run_id P006-E06-R4-AUDIT-001. Original B0/B1 results left untouched.
Writes audit_A_corrected_* files only.
"""
import os
import time
import numpy as np
import pandas as pd

from common import (Z, T_WIN, RUN_ID, RESULTS, indep, load_panels, dump, err)


def asset_weights_corrected(lam, eff_port, W, T):
    """Author-consistent trace scale: eigenvalues are of K/T, z unchanged."""
    eig = lam / T
    inv_eigs = W @ (1.0 / (eig[None, :] + Z[:, None]))
    scale = float(np.sum(1.0 / inv_eigs) / np.sum(eig))
    return eff_port @ W * scale, scale


def ridge_weights_corrected(lam, eff_port, best_z, T):
    eig = lam / T
    inv_eigs = 1.0 / (eig + Z[best_z])
    scale = float(np.sum(1.0 / inv_eigs) / np.sum(eig))
    return eff_port[:, best_z] * scale, scale


def sharpe(r):
    return float(np.sqrt(12) * np.mean(r) / np.std(r))


def main():
    panels, benchmark = load_panels()
    Xall = panels.to_numpy(dtype=float)
    dates = panels.index[T_WIN:]
    P = Xall.shape[1]
    n = len(dates)
    cols = list(panels.columns)

    W0 = np.empty((n, len(Z))); W1 = np.empty((n, len(Z)))
    pi0 = np.empty((n, P)); pi1 = np.empty((n, P))
    ret0 = np.empty(n); ret1 = np.empty(n)
    rrd0 = np.empty(n); rrd1 = np.empty(n)
    sc0 = np.empty(n); sc1 = np.empty(n)
    bz0 = np.empty(n, int); bz1 = np.empty(n, int)

    # original (uncorrected) series for direct comparison (v4 results store CSVs, not npz)
    o_ret0 = pd.read_csv(os.path.join(RESULTS, "returns_B0.csv"))["return"].to_numpy(float)
    o_ret1 = pd.read_csv(os.path.join(RESULTS, "returns_B1.csv"))["return"].to_numpy(float)
    o_pi0 = pd.read_csv(os.path.join(RESULTS, "weights_B0.csv"), index_col=0).to_numpy(float)
    o_pi1 = pd.read_csv(os.path.join(RESULTS, "weights_B1.csv"), index_col=0).to_numpy(float)

    t0 = time.time()
    for i in range(n):
        X = Xall[i:i + T_WIN]
        Xo = Xall[i + T_WIN]
        lam, V = indep.eig_K(X)
        eff_port, Vt1 = indep.prepare_full_basis(X, lam, V)
        A0, _, _ = indep.stable_loo(V, Vt1, lam, T_WIN)
        A1, _, _ = indep.stable_loo(V, Vt1, lam, T_WIN - 1)
        u0, Q0 = A0.mean(0), A0.T @ A0 / T_WIN
        u1, Q1 = A1.mean(0), A1.T @ A1 / T_WIN
        bz0[i], w0, _ = indep.qp_mixture(u0, Q0)
        bz1[i], w1, _ = indep.qp_mixture(u1, Q1)
        W0[i], W1[i] = w0, w1
        pi0[i], sc0[i] = asset_weights_corrected(lam, eff_port, w0, T_WIN)
        pi1[i], sc1[i] = asset_weights_corrected(lam, eff_port, w1, T_WIN)
        ret0[i] = Xo @ pi0[i]
        ret1[i] = Xo @ pi1[i]
        rrd0[i] = Xo @ ridge_weights_corrected(lam, eff_port, bz0[i], T_WIN)[0]
        rrd1[i] = Xo @ ridge_weights_corrected(lam, eff_port, bz1[i], T_WIN)[0]
        if (i + 1) % 100 == 0:
            print(f"[rerun] {i+1}/{n} elapsed {time.time()-t0:.1f}s", flush=True)

    idx = dates
    pd.DataFrame(pi0, index=idx, columns=cols).to_csv(
        os.path.join(RESULTS, "audit_A_corrected_weights_B0.csv"))
    pd.DataFrame(pi1, index=idx, columns=cols).to_csv(
        os.path.join(RESULTS, "audit_A_corrected_weights_B1.csv"))
    pd.DataFrame({"date": idx, "return": ret0}).to_csv(
        os.path.join(RESULTS, "audit_A_corrected_returns_B0.csv"), index=False)
    pd.DataFrame({"date": idx, "return": ret1}).to_csv(
        os.path.join(RESULTS, "audit_A_corrected_returns_B1.csv"), index=False)
    pd.DataFrame({"date": idx, "return": rrd0}).to_csv(
        os.path.join(RESULTS, "audit_A_corrected_ridge_B0.csv"), index=False)
    pd.DataFrame({"date": idx, "return": rrd1}).to_csv(
        os.path.join(RESULTS, "audit_A_corrected_ridge_B1.csv"), index=False)
    np.savez_compressed(os.path.join(RESULTS, "audit_A_corrected_full_raw.npz"),
                        dates=np.array([d.strftime("%Y-%m-%d") for d in idx]),
                        ret0=ret0, ret1=ret1, ridge0=rrd0, ridge1=rrd1,
                        pi0=pi0, pi1=pi1, W0=W0, W1=W1, scale0=sc0, scale1=sc1,
                        bz0=bz0, bz1=bz1)

    out = {
        "run_id": RUN_ID, "n_oos": n,
        "convention": "trace scale uses eigenvalues of K/T (author-consistent); "
                      "eff_port K+Tz and LOO stable expression unchanged from E06",
        "sharpe": {"orig_B0": sharpe(o_ret0), "corr_B0": sharpe(ret0),
                   "orig_B1": sharpe(o_ret1), "corr_B1": sharpe(ret1)},
        "B0_orig_vs_corrected": err(o_ret0, ret0),
        "B1_orig_vs_corrected": err(o_ret1, ret1),
        "weights_B0_orig_vs_corrected": err(o_pi0, pi0),
        "weights_B1_orig_vs_corrected": err(o_pi1, pi1),
        "scale_corrected_B0_min_max": [float(sc0.min()), float(sc0.max())],
        "scale_corrected_B1_min_max": [float(sc1.min()), float(sc1.max())],
        "finite": {k: bool(np.all(np.isfinite(v))) for k, v in
                   [("ret0", ret0), ("ret1", ret1), ("pi0", pi0), ("pi1", pi1)]},
        "elapsed_sec": float(time.time() - t0),
    }
    dump("audit_A_corrected_summary.json", out)
    print("sharpe orig/corr B0", out["sharpe"]["orig_B0"], out["sharpe"]["corr_B0"])
    print("sharpe orig/corr B1", out["sharpe"]["orig_B1"], out["sharpe"]["corr_B1"])
    print("B0 return orig vs corrected maxabs", out["B0_orig_vs_corrected"]["maxabs"])


if __name__ == "__main__":
    main()
