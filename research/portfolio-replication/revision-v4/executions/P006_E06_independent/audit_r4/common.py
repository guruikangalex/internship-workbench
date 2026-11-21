#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P006-E06 R4 audit shared helpers. READ-ONLY w.r.t. all inputs; only writes
into the P006_E06_independent/ tree. All numbers come from real in-process runs.
"""
import os
import sys
import json
import hashlib
import importlib.util

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))            # .../P006_E06_independent/audit_r4
OWNER = os.path.dirname(HERE)                                 # .../P006_E06_independent
RESULTS = os.path.join(OWNER, "results")
PKG = "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/CO-REP-20261120-02/evidence/P006_package"
RUN_ID = "P006-E06-R4-AUDIT-001"
Z = np.logspace(-10, -1, 10)
T_WIN = 120

# load independent module (source of B0/B1 functions) without triggering main()
_spec = importlib.util.spec_from_file_location("indep_upsa", os.path.join(OWNER, "independent_upsa.py"))
indep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(indep)

sys.path.insert(0, PKG)
from src.upsa import UPSA  # noqa: E402


def load_panels():
    p = os.path.join(PKG, "data", "processed_inputs")
    f = pd.read_csv(os.path.join(p, "factors_main.csv"), index_col=0,
                    parse_dates=True, float_precision="round_trip")
    b = pd.read_csv(os.path.join(p, "benchmark.csv"), index_col=0,
                    parse_dates=True, float_precision="round_trip")
    return f, b


def first_X(panels=None):
    if panels is None:
        panels, _ = load_panels()
    return panels.iloc[:T_WIN].to_numpy(dtype=float)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dump(name, obj):
    path = os.path.join(RESULTS, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)
    print("[audit] WROTE", path)
    return path


def err(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    den = max(float(np.linalg.norm(np.asarray(b, float))), 1e-300)
    return {
        "maxabs": float(np.max(np.abs(d))),
        "meanabs": float(np.mean(np.abs(d))),
        "fro": float(np.linalg.norm(d)),
        "relative_fro": float(np.linalg.norm(d) / den),
        "corr": (float(np.corrcoef(np.asarray(a, float).ravel(), np.asarray(b, float).ravel())[0, 1])
                 if np.std(a) > 0 and np.std(b) > 0 else None),
    }


def author_parts(X, z_list=Z):
    """Return the author's internal objects for the SAME first-window X and z-grid.
    Everything computed explicitly from src/upsa.py formulas (no E06 helpers)."""
    T, P = X.shape
    eig, V = UPSA.smart_eigenvalue_decomposition_covariance(X)   # eig of XX'/T, V=(P,T)
    mu = np.mean(X, axis=0)                                       # (P,)
    proj = V.T @ X.T                                              # (T,T) = U'R'
    proj_mu = V.T @ mu                                            # (T,)
    w_adj = (X @ X.T - proj.T @ proj) / T                         # (T,T) roundoff when P>T
    l_adj = mu - V @ proj_mu                                      # (P,) roundoff when P>T
    return {
        "T": T, "P": P, "eig": eig, "V": V, "mu": mu,
        "proj": proj, "proj_mu": proj_mu, "w_adj": w_adj, "l_adj": l_adj,
    }


def author_eff_port(ap, z_list=Z):
    """Author ridge_eff_portfolios[:,j] = V diag(1/(eig+z)) U'mu + l_adj/z  (P x L)."""
    eig, V, proj_mu, l_adj = ap["eig"], ap["V"], ap["proj_mu"], ap["l_adj"]
    cols = [(V * (1.0 / (eig.reshape(1, -1) + z))) @ proj_mu + l_adj / z for z in z_list]
    return np.array(cols).T


def author_smoother(ap, z_list=Z):
    """Author ridge_smoothers W_z (T x T) = proj' diag(1/(eig+z)) proj / T + w_adj/z."""
    eig, proj, w_adj = ap["eig"], ap["proj"], ap["w_adj"]
    return [proj.T @ ((1.0 / (eig.reshape(-1, 1) + z)) * proj) / ap["T"] + w_adj / z
            for z in z_list]


def author_loo_from_smoothers(Ws):
    """Author calculate_loo_returns: (rowsum - diag)/(1 - diag)."""
    out = []
    for W in Ws:
        wb = np.sum(W, axis=1)
        wd = np.diag(W)
        out.append((wb - wd) / (1.0 - wd))
    return np.array(out).T  # (T x L)


def env_info():
    import platform
    import numpy as np
    import scipy
    import cvxopt
    import pandas as pd
    return {
        "run_id": RUN_ID,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "cvxopt": cvxopt.__version__,
        "pandas": pd.__version__,
        "package_sha256": {
            "upsa.py": sha256(os.path.join(PKG, "src", "upsa.py")),
            "portfolios.py": sha256(os.path.join(PKG, "src", "portfolios.py")),
            "factors_main.csv": sha256(os.path.join(PKG, "data", "processed_inputs", "factors_main.csv")),
        },
    }
