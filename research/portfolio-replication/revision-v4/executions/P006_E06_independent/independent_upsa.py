#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P006-E06 INDEPENDENT_FAITHFUL implementation (IMPLEMENTATION_AUDIT).

Independent implementation of the paper's UPSA pipeline with:
  B0 : stable LOO expression with c = T      (author divisor convention)
  B1 : stable LOO expression with c = T - 1  (paper T-1 leave-one-out)

Core identity implemented and cross-checked against direct delete-row refit:
    K = X X'                       (T x T)
    G_c = (K + c z I)^(-1)
    a_t = 1 - (G_c 1)_t / diag(G_c)_t         (T-vector per z)

Full-window ridge basis (eff_port) keeps the ORIGINAL T for both B0 and B1,
as required by the approval. Author src/upsa.py is imported ONLY as a
first-window A-reference (never used to produce B0/B1 outputs).

Run modes:
    python independent_upsa.py --first-window
    python independent_upsa.py --full
    python independent_upsa.py --all
"""
import os
import sys
import json
import time
import hashlib
import platform
import argparse

import numpy as np
import pandas as pd
from cvxopt import matrix, solvers

solvers.options["show_progress"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/CO-REP-20261120-02/evidence/P006_package"
Z = np.logspace(-10, -1, 10)
T_WIN = 120
L = len(Z)
RESULTS = os.path.join(HERE, "results")
os.makedirs(RESULTS, exist_ok=True)


# --------------------------------------------------------------------------- io
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_inputs():
    p = os.path.join(PKG, "data", "processed_inputs")
    f = pd.read_csv(os.path.join(p, "factors_main.csv"), index_col=0,
                    parse_dates=True, float_precision="round_trip")
    b = pd.read_csv(os.path.join(p, "benchmark.csv"), index_col=0,
                    parse_dates=True, float_precision="round_trip")
    return f, b


# ---------------------------------------------------------- core math (indep.)
def eig_K(X):
    """K = X X' (T x T), symmetric PSD; eigh and clip tiny negative eigenvalues."""
    K = X @ X.T
    lam, V = np.linalg.eigh(K)
    lam = np.clip(lam, 0.0, None)
    return lam, V


def prepare_full_basis(X, lam, V):
    """eff_port[:,j] = X' (K + T*z_j I)^(-1) 1  (original-T ridge basis).

    Also returns V'1 used by every stable-LOO evaluation.
    """
    T = X.shape[0]
    Vt1 = V.T @ np.ones(T)
    invT = 1.0 / (lam[:, None] + T * Z[None, :])   # T x L
    g1 = V @ (Vt1[:, None] * invT)                 # T x L = (K+T z I)^-1 1
    eff_port = X.T @ g1                            # P x L
    return eff_port, Vt1


def stable_loo(V, Vt1, lam, c):
    """A[t,j] = 1 - (G_c 1)_t / diag(G_c)_t, G_c = (K + c*z*I)^(-1).

    Returns A (T x L), diagG (T x L), cond (L,) analytic condition numbers.
    """
    inv = 1.0 / (lam[:, None] + c * Z[None, :])    # T x L
    g1 = V @ (Vt1[:, None] * inv)                  # T x L
    dg = (V ** 2) @ inv                            # T x L = diag(G_c)
    A = 1.0 - g1 / dg
    cond = (lam[-1] + c * Z) / (lam[0] + c * Z)
    return A, dg, cond


def direct_refit_loo(X, rows, d):
    """Truly independent direct delete-row refit with divisor d.

    For each left-out row t: S_(-t)=X_(-t)'X_(-t)/d, m_(-t)=X_(-t)'1/d,
    p_j=(S_(-t)+z_j I)^(-1) m_(-t), A[t,j]=X[t] p_j.
    Returns A (len(rows) x L), cond (len(rows) x L).
    """
    T, P = X.shape
    XtX = X.T @ X
    Xt1 = X.sum(axis=0)
    eye = np.eye(P)
    A = np.empty((len(rows), L))
    cond = np.empty_like(A)
    for i, t in enumerate(rows):
        Sm = (XtX - np.outer(X[t], X[t])) / d
        mm = (Xt1 - X[t]) / d
        for j, z in enumerate(Z):
            M = Sm + z * eye
            p = np.linalg.solve(M, mm)
            A[i, j] = X[t] @ p
            cond[i, j] = np.linalg.cond(M)
    return A, cond


def qp_mixture(u, Q):
    """Non-negative Markowitz QP: max W'u - 0.5 W'QW s.t. W >= 0.

    Returns (best_z_idx, W, info) with KKT residual computed multiplier-free.
    """
    Pm = matrix(np.asarray(Q, dtype=np.double))
    q = matrix(np.asarray(-u, dtype=np.double))
    G = matrix(-np.eye(len(u)))
    h = matrix(np.zeros((len(u), 1)))
    sol = solvers.qp(Pm, q, G, h)
    W = np.asarray(sol["x"]).ravel()
    status = str(sol["status"])
    obj = float(W @ u - 0.5 * W @ Q @ W)
    grad = Q @ W - u                       # = Lagrange multiplier lambda >= 0
    kkt = float(max(
        np.max(np.maximum(0.0, -W)),       # primal feasibility W >= 0
        np.max(np.maximum(0.0, -grad)),    # dual feasibility lambda >= 0
        np.max(np.abs(W * grad)),          # complementarity
    ))
    best_z = int(np.argmax(u / np.sqrt(np.diag(Q))))
    info = {
        "status": status,
        "objective": obj,
        "kkt_residual": kkt,
        "cvxopt_gap": float(sol.get("gap", np.nan)),
        "cvxopt_res_primal": float(sol.get("residual primal", np.nan)),
        "cvxopt_res_dual": float(sol.get("residual dual", np.nan)),
        "cvxopt_iterations": int(sol.get("iterations", -1)),
        "sum_W": float(W.sum()),
    }
    return best_z, W, info


def qp_slsqp_crosscheck(u, Q):
    """Independent scipy crosscheck on first window (not used for outputs)."""
    from scipy.optimize import minimize
    Ln = len(u)
    f = lambda w: 0.5 * w @ Q @ w - u @ w
    g = lambda w: Q @ w - u
    res = minimize(f, np.ones(Ln) / Ln, jac=g, method="SLSQP",
                   bounds=[(0.0, None)] * Ln,
                   options={"ftol": 1e-12, "maxiter": 1000})
    return res


def asset_weights(lam, eff_port, W):
    """pi = eff_port @ W * scale ; scale = sum(1/inv_eigs)/sum(eigenvalues)."""
    inv_eigs = W @ (1.0 / (lam[None, :] + Z[:, None]))   # L x T -> T
    scale = float(np.sum(1.0 / inv_eigs) / np.sum(lam))
    pi = eff_port @ W * scale
    return pi, scale, inv_eigs


def ridge_weights(lam, eff_port, best_z):
    inv_eigs = 1.0 / (lam + Z[best_z])
    scale = float(np.sum(1.0 / inv_eigs) / np.sum(lam))
    return eff_port[:, best_z] * scale, scale


def errors(stable, direct):
    d = stable - direct
    maxabs = float(np.max(np.abs(d)))
    fro = float(np.linalg.norm(d))
    denom = max(float(np.linalg.norm(direct)), 1e-300)
    rel = fro / denom
    return {"maxabs": maxabs, "fro": fro, "relative_error": rel}


# ------------------------------------------------------------- first window
def first_window(panels):
    X = panels.iloc[:T_WIN].to_numpy(dtype=float)
    T, P = X.shape
    rows = [0, 59, 119]
    lam, V = eig_K(X)
    eff_port, Vt1 = prepare_full_basis(X, lam, V)

    A_T, dgT, condT = stable_loo(V, Vt1, lam, T)
    A_Tm1, dgTm1, condTm1 = stable_loo(V, Vt1, lam, T - 1)
    dT, cT = direct_refit_loo(X, rows, T)
    dTm1, cTm1 = direct_refit_loo(X, rows, T - 1)

    per_z = []
    for j, z in enumerate(Z):
        eT = errors(A_T[rows, j], dT[:, j])
        eTm1 = errors(A_Tm1[rows, j], dTm1[:, j])
        per_z.append({
            "z": float(z),
            "stable_T_vs_direct_T": eT,
            "stable_Tm1_vs_direct_Tm1": eTm1,
            "cond_K_plus_Tz": float(condT[j]),
            "cond_K_plus_Tm1z": float(condTm1[j]),
            "cond_direct_T_max": float(np.max(cT[:, j])),
            "cond_direct_Tm1_max": float(np.max(cTm1[:, j])),
            "direct_T_values": dT[:, j].tolist(),
            "direct_Tm1_values": dTm1[:, j].tolist(),
            "stable_T_values": A_T[rows, j].tolist(),
            "stable_Tm1_values": A_Tm1[rows, j].tolist(),
        })

    # QP on both paths
    out = {}
    bz_T, W_T, info_T = qp_mixture(A_T.mean(0), A_T.T @ A_T / T)
    bz_Tm1, W_Tm1, info_Tm1 = qp_mixture(A_Tm1.mean(0), A_Tm1.T @ A_Tm1 / T)
    pi_T, scale_T, _ = asset_weights(lam, eff_port, W_T)
    pi_Tm1, scale_Tm1, _ = asset_weights(lam, eff_port, W_Tm1)
    ridge_pi_T, rs_T = ridge_weights(lam, eff_port, bz_T)

    # A reference from author code (first window only)
    sys.path.insert(0, PKG)
    from src.upsa import UPSA
    m = UPSA(z_list=Z).fit(returns=X)
    A_author = m.estimated_loo_rets
    pi_author = m.get_upsa_weights()
    W_author = np.asarray(m.upsa).ravel()
    e_A_B0_loo = errors(A_T, A_author)
    e_A_B0_pi = errors(pi_T, pi_author)
    for j, z in enumerate(Z):
        per_z[j]["author_A_vs_stable_B0_loo"] = errors(A_T[:, j], A_author[:, j])
    eA_by_group = {
        "z_ge_1e-6_maxabs": float(max(p["author_A_vs_stable_B0_loo"]["maxabs"]
                                    for p in per_z if p["z"] >= 1e-6)),
        "z_eq_1e-7_maxabs": float(per_z[3]["author_A_vs_stable_B0_loo"]["maxabs"]),
        "z_le_1e-8_maxabs": float(max(p["author_A_vs_stable_B0_loo"]["maxabs"]
                                    for p in per_z if p["z"] <= 1e-8)),
        "note": "Author A uses smoother w_adj/z with w_adj = roundoff residual of "
                "(RR'-proj'proj)/T; dividing by tiny z amplifies roundoff. "
                "Stable B0 derives G from eigh(K) directly and does not carry this term.",
    }

    slsqp = qp_slsqp_crosscheck(A_T.mean(0), A_T.T @ A_T / T)
    slsqp_W = np.maximum(slsqp.x, 0.0)

    out = {
        "issue": "P006-E06 first-window independent stability check",
        "T": T, "P": P, "rows_checked": rows, "z_grid": Z.tolist(),
        "equivalence": {
            "stable_T_vs_direct_T": errors(A_T[rows], dT),
            "stable_Tm1_vs_direct_Tm1": errors(A_Tm1[rows], dTm1),
            "author_A_LOO_vs_stable_B0": e_A_B0_loo,
            "author_A_pi_vs_stable_B0": e_A_B0_pi,
            "author_A_W_vs_B0_fro": float(np.linalg.norm(W_author - W_T)),
            "scipy_slsqp_W_vs_B0_fro": float(np.linalg.norm(slsqp_W - W_T)),
            "scipy_slsqp_success": bool(slsqp.success),
        },
        "author_A_vs_B0_by_z_group": eA_by_group,
        "per_z": per_z,
        "qp": {"B0": info_T, "B1": info_Tm1},
        "best_z": {"B0": bz_T, "B1": bz_Tm1, "author": int(m.best_z)},
        "scale": {"B0": scale_T, "B1": scale_Tm1, "ridge_B0": rs_T},
        "mixture_W_B0": W_T.tolist(),
        "mixture_W_B1": W_Tm1.tolist(),
        "trace_norm_check": {
            "sum_eigenvalues": float(np.sum(lam)),
            "inv_eigs_B0_sum": float(np.sum(1.0 / (W_T @ (1.0 / (lam[None, :] + Z[:, None]))))),
        },
        "inputs": {
            "factors_main_csv_sha256": sha256(os.path.join(PKG, "data", "processed_inputs", "factors_main.csv")),
            "author_upsa_py_sha256": sha256(os.path.join(PKG, "src", "upsa.py")),
        },
        "environment": {"python": platform.python_version(), "numpy": np.__version__},
        "independence": "B0/B1 produced by this file; author UPSA imported only as A reference here.",
    }
    with open(os.path.join(RESULTS, "first_window_check.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("[first-window] equivalence summary:")
    print(json.dumps(out["equivalence"], indent=2))
    print("[first-window] per-z maxabs stable_T vs direct_T:",
          [round(p["stable_T_vs_direct_T"]["maxabs"], 10) for p in per_z])
    print("[first-window] per-z maxabs stable_Tm1 vs direct_Tm1:",
          [round(p["stable_Tm1_vs_direct_Tm1"]["maxabs"], 10) for p in per_z])
    print("[first-window] WROTE results/first_window_check.json")


# ------------------------------------------------------------------ full run
def full_run(panels, benchmark):
    Xall = panels.to_numpy(dtype=float)
    dates = panels.index[T_WIN:]
    P = Xall.shape[1]
    n = len(dates)

    W0 = np.empty((n, L)); W1 = np.empty((n, L))
    pi0 = np.empty((n, P)); pi1 = np.empty((n, P))
    ridge0 = np.empty(n); ridge1 = np.empty(n)
    ret0 = np.empty(n); ret1 = np.empty(n)
    scale0 = np.empty(n); scale1 = np.empty(n)
    bz0 = np.empty(n, int); bz1 = np.empty(n, int)
    diag_qp0 = []; diag_qp1 = []
    cond0 = np.empty((n, L)); cond1 = np.empty((n, L))
    eig_min = np.empty(n); eig_max = np.empty(n)
    t_start = time.time()

    for i in range(n):
        X = Xall[i:i + T_WIN]
        Xo = Xall[i + T_WIN]
        lam, V = eig_K(X)
        eff_port, Vt1 = prepare_full_basis(X, lam, V)
        lam0, lam1 = float(lam[0]), float(lam[-1])
        eig_min[i], eig_max[i] = lam0, lam1

        A0, _, c0 = stable_loo(V, Vt1, lam, T_WIN)
        A1, _, c1 = stable_loo(V, Vt1, lam, T_WIN - 1)
        cond0[i], cond1[i] = c0, c1

        u0, Q0 = A0.mean(0), A0.T @ A0 / T_WIN
        u1, Q1 = A1.mean(0), A1.T @ A1 / T_WIN
        bz0[i], w0, i0 = qp_mixture(u0, Q0)
        bz1[i], w1, i1 = qp_mixture(u1, Q1)
        W0[i], W1[i] = w0, w1
        diag_qp0.append({"date": str(dates[i].date()), **i0})
        diag_qp1.append({"date": str(dates[i].date()), **i1})

        pi0[i], scale0[i], _ = asset_weights(lam, eff_port, w0)
        pi1[i], scale1[i], _ = asset_weights(lam, eff_port, w1)
        ret0[i] = Xo @ pi0[i]
        ret1[i] = Xo @ pi1[i]
        rp0, _ = ridge_weights(lam, eff_port, bz0[i])
        rp1, _ = ridge_weights(lam, eff_port, bz1[i])
        ridge0[i] = Xo @ rp0
        ridge1[i] = Xo @ rp1

        if (i + 1) % 50 == 0 or i == 0:
            print(f"[full] {i+1}/{n} windows done, elapsed {time.time()-t_start:.1f}s", flush=True)

    elapsed = time.time() - t_start
    cols = list(panels.columns)
    idx = dates
    pd.DataFrame(pi0, index=idx, columns=cols).to_csv(os.path.join(RESULTS, "weights_B0.csv"))
    pd.DataFrame(pi1, index=idx, columns=cols).to_csv(os.path.join(RESULTS, "weights_B1.csv"))
    pd.DataFrame(W0, index=idx, columns=[f"z{j}" for j in range(L)]).to_csv(os.path.join(RESULTS, "mixture_B0.csv"))
    pd.DataFrame(W1, index=idx, columns=[f"z{j}" for j in range(L)]).to_csv(os.path.join(RESULTS, "mixture_B1.csv"))

    def save_series(vals, name):
        pd.DataFrame({"date": idx, "return": vals}).to_csv(os.path.join(RESULTS, name), index=False)

    save_series(ret0, "returns_B0.csv")
    save_series(ret1, "returns_B1.csv")
    save_series(ridge0, "returns_ridge_B0.csv")
    save_series(ridge1, "returns_ridge_B1.csv")
    with open(os.path.join(RESULTS, "qp_diagnostics_B0.json"), "w") as f:
        json.dump(diag_qp0, f, indent=1)
    with open(os.path.join(RESULTS, "qp_diagnostics_B1.json"), "w") as f:
        json.dump(diag_qp1, f, indent=1)
    np.savez_compressed(os.path.join(RESULTS, "full_raw_B0_B1.npz"),
                        dates=np.array([d.strftime("%Y-%m-%d") for d in idx]),
                        ret0=ret0, ret1=ret1, ridge0=ridge0, ridge1=ridge1,
                        pi0=pi0, pi1=pi1, W0=W0, W1=W1, scale0=scale0, scale1=scale1,
                        bz0=bz0, bz1=bz1, cond0=cond0, cond1=cond1,
                        eig_min=eig_min, eig_max=eig_max)

    summary = {
        "n_oos": n,
        "first_oos": str(idx[0].date()),
        "last_oos": str(idx[-1].date()),
        "elapsed_sec": elapsed,
        "finite_returns_B0": bool(np.all(np.isfinite(ret0))),
        "finite_returns_B1": bool(np.all(np.isfinite(ret1))),
        "finite_weights_B0": bool(np.all(np.isfinite(pi0))),
        "finite_weights_B1": bool(np.all(np.isfinite(pi1))),
        "scale_B0_min_max": [float(scale0.min()), float(scale0.max())],
        "scale_B1_min_max": [float(scale1.min()), float(scale1.max())],
        "qp_status_counts_B0": _status_counts(diag_qp0),
        "qp_status_counts_B1": _status_counts(diag_qp1),
        "qp_kkt_max_B0": max(d["kkt_residual"] for d in diag_qp0),
        "qp_kkt_max_B1": max(d["kkt_residual"] for d in diag_qp1),
        "cond_K_plus_Tz_max": float(cond0.max()),
        "cond_K_plus_Tm1z_max": float(cond1.max()),
    }
    with open(os.path.join(RESULTS, "full_run_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("[full] summary:", json.dumps(summary, indent=2))
    print("[full] WROTE results/full_run_summary.json and results/*B0*/*B1*")
    return summary


def _status_counts(diag):
    out = {}
    for d in diag:
        out[d["status"]] = out.get(d["status"], 0) + 1
    return out


# -------------------------------------------------------------------- metrics
def compute_metrics(panels, benchmark):
    d = np.load(os.path.join(RESULTS, "full_raw_B0_B1.npz"), allow_pickle=True)
    dates = pd.DatetimeIndex(d["dates"])
    ret0, ret1 = d["ret0"], d["ret1"]
    r0, r1 = d["ridge0"], d["ridge1"]
    pi0, pi1 = d["pi0"], d["pi1"]

    b = benchmark.copy()
    if "mom" in b.columns:
        b = b.drop(columns=["mom"])
    b = b.reindex(dates)
    ff5 = b[["mkt", "smb", "hml", "rmw", "cma"]].to_numpy(dtype=float)
    bw = np.linalg.solve(np.cov(ff5, rowvar=False), ff5.mean(axis=0))
    ff5_ret = ff5 @ bw
    capm_ret = b["mkt"].to_numpy(dtype=float)

    def sharpe(r):
        return float(np.sqrt(12) * np.mean(r) / np.std(r))

    def turnover(w):
        gross = np.abs(w).sum(axis=1)
        diff = np.abs(np.diff(w, axis=0)).sum(axis=1)
        t = np.zeros(len(w))
        t[1:] = 0.5 * diff / gross[:-1]
        return float(100 * np.mean(t))

    def alpha_one(y, x, annual_vol=0.1):
        import statsmodels.api as sm
        ys = y * annual_vol / np.std(np.sqrt(12) * y)
        xs = x * annual_vol / np.std(np.sqrt(12) * x)
        model = sm.OLS(ys, sm.add_constant(xs)).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        a = float(np.asarray(model.params)[0] * 12 * 100)
        tstat = float(np.asarray(model.tvalues)[0])
        return a, tstat

    def pricing_r2(r):
        """src/pricing.py SDF scaling using the STRATEGY RETURN SERIES."""
        from sklearn.metrics import r2_score
        sys.path.insert(0, PKG)
        from src.constants import JKP_CLUSTERS
        F = panels.reindex(dates).to_numpy(dtype=float)
        cols = list(panels.columns)
        scale = np.mean(r) / np.mean(r ** 2)
        sdfs = scale * r                         # 494-vector SDF proxy
        # All: per-column normalisation (author np.std(DataFrame) => ddof=1)
        fsr_all = np.sqrt(12) * F / np.std(F, axis=0, ddof=1)
        realized = np.mean(fsr_all, axis=0)
        pred = np.sum(fsr_all * sdfs[:, None], axis=0) / len(sdfs)
        out = {"All": float(r2_score(realized.reshape(-1, 1), pred.reshape(-1, 1)))}
        for theme, names in JKP_CLUSTERS.items():
            ids = [cols.index(n) for n in names if n in cols]
            if not ids:
                out[theme] = None
                continue
            fs = F[:, ids]
            fsr = np.sqrt(12) * fs / np.std(fs)
            sharpe_theme = np.mean(fsr, axis=0)
            px = np.sum(fsr * sdfs[:, None], axis=0) / len(sdfs)
            out[theme] = float(r2_score(sharpe_theme.reshape(-1, 1), px.reshape(-1, 1)))
        return out

    res = {
        "n_oos": len(ret0),
        "period": [str(dates[0].date()), str(dates[-1].date())],
        "strategy": {},
        "benchmark": {"CAPM_sharpe": sharpe(capm_ret), "FF5_sharpe": sharpe(ff5_ret),
                      "Ridge_B0_sharpe": sharpe(r0), "Ridge_B1_sharpe": sharpe(r1)},
        "definitions": {
            "sharpe": "sqrt(12)*mean/std (monthly)",
            "alpha": "UPSA vs single rival strategy, both scaled to 10% annual vol, OLS const+HAC(5), const*12*100 pp",
            "pricing_R2": "src/pricing.py SDF scaling; theme pooled std, All per-column std",
            "turnover": "src/metrics.py time-series turnover in percent, first month 0",
        },
    }
    for name, r, pi in (("B0", ret0, pi0), ("B1", ret1, pi1)):
        alpha_r, t_r = alpha_one(r, d[f"ridge{0 if name=='B0' else 1}"])
        res["strategy"][name] = {
            "sharpe": sharpe(r),
            "mean_monthly": float(np.mean(r)),
            "std_monthly": float(np.std(r)),
            "alpha_vs_ridge_pp": alpha_r,
            "alpha_vs_ridge_hac5_t": t_r,
            "alpha_vs_CAPM_pp": alpha_one(r, capm_ret)[0],
            "alpha_vs_FF5_pp": alpha_one(r, ff5_ret)[0],
            "turnover_pct": turnover(pi),
            "pricing_R2": pricing_r2(r),
        }
    # B0 vs B1 return-series difference
    diff = ret0 - ret1
    res["B0_vs_B1"] = {
        "mean_monthly_diff": float(np.mean(diff)),
        "std_monthly_diff": float(np.std(diff)),
        "maxabs_monthly_diff": float(np.max(np.abs(diff))),
        "corr": float(np.corrcoef(ret0, ret1)[0, 1]),
        "sharpe_B0": sharpe(ret0), "sharpe_B1": sharpe(ret1),
        "sharpe_diff": sharpe(ret0) - sharpe(ret1),
        "alpha_vs_ridge_pp_B0": res["strategy"]["B0"]["alpha_vs_ridge_pp"],
        "alpha_vs_ridge_pp_B1": res["strategy"]["B1"]["alpha_vs_ridge_pp"],
        "turnover_B0": res["strategy"]["B0"]["turnover_pct"],
        "turnover_B1": res["strategy"]["B1"]["turnover_pct"],
    }
    with open(os.path.join(RESULTS, "metrics.json"), "w") as f:
        json.dump(res, f, indent=2)
    print("[metrics]", json.dumps(res, indent=2))
    print("[metrics] WROTE results/metrics.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--first-window", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--metrics", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    do_all = args.all or not (args.first_window or args.full or args.metrics)
    panels, bench = load_inputs()
    if args.first_window or do_all:
        first_window(panels)
    if args.full or do_all:
        full_run(panels, bench)
    if args.metrics or do_all:
        compute_metrics(panels, bench)


if __name__ == "__main__":
    main()
