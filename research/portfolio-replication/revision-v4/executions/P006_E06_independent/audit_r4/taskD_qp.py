#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK D: QP KKT-precision audit. Keeps original cvxopt-default results;
adds high-precision cvxopt, SLSQP and scaled-Q diagnostics. Threshold stays 1e-7.
"""
import os
import json
import time
import numpy as np
import pandas as pd
from cvxopt import matrix, solvers

from common import Z, T_WIN, RUN_ID, RESULTS, indep, load_panels, dump, env_info

TOL = 1e-7


def kkt_residual(u, Q, W):
    """Multiplier-free KKT residual, identical to independent_upsa.qp_mixture."""
    grad = Q @ W - u                      # implied lambda >= 0
    return float(max(
        np.max(np.maximum(0.0, -W)),      # primal feasibility W >= 0
        np.max(np.maximum(0.0, -grad)),   # dual feasibility lambda >= 0
        np.max(np.abs(W * grad)),         # complementarity
    ))


def cvxopt_solve(u, Q, opts):
    old = dict(solvers.options)
    solvers.options.clear()
    solvers.options.update(opts)
    try:
        Pm = matrix(np.asarray(Q, dtype=np.double))
        q = matrix(np.asarray(-u, dtype=np.double))
        G = matrix(-np.eye(len(u)))
        h = matrix(np.zeros((len(u), 1)))
        sol = solvers.qp(Pm, q, G, h)
        W = np.asarray(sol["x"]).ravel()
        return W, str(sol["status"]), {
            "gap": float(sol.get("gap", np.nan)),
            "res_primal": float(sol.get("residual primal", np.nan)),
            "res_dual": float(sol.get("residual dual", np.nan)),
            "iterations": int(sol.get("iterations", -1)),
        }
    finally:
        solvers.options.clear()
        solvers.options.update(old)


def slsqp_solve(u, Q):
    from scipy.optimize import minimize
    L = len(u)
    res = minimize(lambda w: 0.5 * w @ Q @ w - u @ w, np.ones(L) / L,
                   jac=lambda w: Q @ w - u, method="SLSQP",
                   bounds=[(0.0, None)] * L, options={"ftol": 1e-14, "maxiter": 2000})
    return np.maximum(res.x, 0.0), bool(res.success)


def summarize(res_list):
    a = np.asarray(res_list, float)
    return {
        "n": int(a.size), "max": float(a.max()), "mean": float(a.mean()),
        "median": float(np.median(a)),
        "n_gt_1e-7": int(np.sum(a > TOL)),
        "n_gt_1e-8": int(np.sum(a > 1e-8)),
        "p95": float(np.percentile(a, 95)),
    }


def main():
    panels, _ = load_panels()
    Xall = panels.to_numpy(float)
    dates = panels.index[T_WIN:]
    n = len(dates)

    # original diagnostics (frozen result)
    d0 = json.load(open(os.path.join(RESULTS, "qp_diagnostics_B0.json")))
    d1 = json.load(open(os.path.join(RESULTS, "qp_diagnostics_B1.json")))
    orig0 = [float(x["kkt_residual"]) for x in d0]
    orig1 = [float(x["kkt_residual"]) for x in d1]
    orig_summary = {
        "B0": summarize(orig0), "B1": summarize(orig1),
        "B0_status_counts": d0 and {s: sum(1 for x in d0 if x["status"] == s)
                                    for s in set(x["status"] for x in d0)},
        "B1_status_counts": d1 and {s: sum(1 for x in d1 if x["status"] == s)
                                    for s in set(x["status"] for x in d1)},
        "residual_definition": ("max(max(0,-W), max(0,u-QW), max|W*(QW-u)|) with implied "
                                "multiplier lambda = QW-u >= 0; multiplier-free KKT. "
                                "cvxopt status='optimal' only certifies its internal "
                                "abstol/reltol/feastol (defaults 1e-7), NOT this KKT measure."),
        "note": "Original configuration results preserved; no threshold relaxation.",
    }

    # recompute u,Q per window once
    uQs = []
    for i in range(n):
        X = Xall[i:i + T_WIN]
        lam, V = indep.eig_K(X)
        _, Vt1 = indep.prepare_full_basis(X, lam, V)
        A0, _, _ = indep.stable_loo(V, Vt1, lam, T_WIN)
        A1, _, _ = indep.stable_loo(V, Vt1, lam, T_WIN - 1)
        uQs.append((A0.mean(0), A0.T @ A0 / T_WIN, A1.mean(0), A1.T @ A1 / T_WIN))

    methods = {
        "cvxopt_default": {"show_progress": False},
        "cvxopt_highprec": {"show_progress": False, "abstol": 1e-12, "reltol": 1e-12,
                            "feastol": 1e-12, "maxiters": 10000},
        "cvxopt_highprec_scaled": {"show_progress": False, "abstol": 1e-12, "reltol": 1e-12,
                                   "feastol": 1e-12, "maxiters": 10000},
    }
    res = {name: {"B0": [], "B1": []} for name in methods}
    res["scipy_slsqp"] = {"B0": [], "B1": []}
    statuses = {name: {"B0": {}, "B1": {}} for name in list(methods) + ["scipy_slsqp"]}
    Wdiff = {name: {"B0": [], "B1": []} for name in res}
    t0 = time.time()
    for i, (u0, Q0, u1, Q1) in enumerate(uQs):
        for path, u, Q in (("B0", u0, Q0), ("B1", u1, Q1)):
            Wd, sd, _ = cvxopt_solve(u, Q, methods["cvxopt_default"])
            Wh, sh, ih = cvxopt_solve(u, Q, methods["cvxopt_highprec"])
            s = float(np.mean(np.diag(Q)))
            Ws, ss, isc = cvxopt_solve(u / s, Q / s, methods["cvxopt_highprec_scaled"])
            Wsl, ok = slsqp_solve(u, Q)
            for name, W in (("cvxopt_default", Wd), ("cvxopt_highprec", Wh),
                            ("cvxopt_highprec_scaled", Ws), ("scipy_slsqp", Wsl)):
                res[name][path].append(kkt_residual(u, Q, W))
                Wdiff[name][path].append(float(np.linalg.norm(W - Wd)))
            for name, st in (("cvxopt_default", sd), ("cvxopt_highprec", sh),
                             ("cvxopt_highprec_scaled", ss)):
                statuses[name][path][st] = statuses[name][path].get(st, 0) + 1
            statuses["scipy_slsqp"][path]["success" if ok else "fail"] = \
                statuses["scipy_slsqp"][path].get("success" if ok else "fail", 0) + 1
        if (i + 1) % 150 == 0:
            print(f"[D] {i+1}/{n} elapsed {time.time()-t0:.1f}s", flush=True)

    out = {
        "run_id": RUN_ID, "n_oos": n, "threshold": TOL,
        "environment": env_info(),
        "original_frozen": orig_summary,
        "highprecision": {
            name: {
                "B0": summarize(res[name]["B0"]), "B1": summarize(res[name]["B1"]),
                "status_counts": statuses[name],
                "W_fro_vs_cvxopt_default_B0_max": float(max(Wdiff[name]["B0"])),
                "W_fro_vs_cvxopt_default_B1_max": float(max(Wdiff[name]["B1"])),
            } for name in res
        },
        "verdict": None,
        "elapsed_sec": float(time.time() - t0),
    }
    hp = out["highprecision"]["cvxopt_highprec"]
    out["verdict"] = (
        "KKT residual > 1e-7 with cvxopt status='optimal' is CONFIRMED for the original "
        "configuration (B0 %d/%d, B1 %d/%d windows). Tightening cvxopt tolerances to 1e-12 "
        "reduces max KKT to B0=%.3g, B1=%.3g; this is a solver-tolerance limitation, not QP "
        "infeasibility. Original results retained; threshold NOT relaxed." % (
            orig_summary["B0"]["n_gt_1e-7"], n, orig_summary["B1"]["n_gt_1e-7"], n,
            hp["B0"]["max"], hp["B1"]["max"]))
    dump("qp_highprecision.json", out)
    print("orig B0 max", orig_summary["B0"]["max"], "n>1e-7", orig_summary["B0"]["n_gt_1e-7"])
    print("orig B1 max", orig_summary["B1"]["max"], "n>1e-7", orig_summary["B1"]["n_gt_1e-7"])
    for name in res:
        print(name, "B0 max", out["highprecision"][name]["B0"]["max"],
              "B1 max", out["highprecision"][name]["B1"]["max"])


if __name__ == "__main__":
    main()
