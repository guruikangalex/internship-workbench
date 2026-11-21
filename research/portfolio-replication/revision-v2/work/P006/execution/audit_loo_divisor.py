#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REV2-P006-09 paired audit: LOO divisor convention and low-z stability.

Closes issue REV2-P006-09: run paired approved paths on the real first training
window (factors_main, T=120, P=153, 1971-11..1981-10), compare full-target
sensitivity, and PRESERVE the author implementation (do not modify author source).

Paths:
  A author   : smoother = P_r (l+z)^-1 P_r' / T + w_adj/z ; LOO=(wbar-w)/(1-w)
  B paper    : LOO penalty z -> z*(T-1)/T (smoother only); full-window basis uses original z
  C direct   : diagnostic, smoother /(T-1) and w_adj/(T-1), z unrescaled

Nature: IMPLEMENTATION_AUDIT, NOT paper replication; formal targets stay NOT_RUN.
"""
import os, sys, json, hashlib, platform
import numpy as np

# Author P006 replication package dir: override with UPSA_PACKAGE_DIR; default relative.
# Receiver downloads Dataverse DOI 10.7910/DVN/OHZFKD (file 14008244) and points here.
PKG = os.environ.get(
    "UPSA_PACKAGE_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..",
                                 "..", "evidence", "P006_package")),
)
if not os.path.isdir(PKG):
    raise SystemExit("P006 package dir not found; set UPSA_PACKAGE_DIR to the extracted "
                     "upsa_reproduction directory (Dataverse 10.7910/DVN/OHZFKD).")
sys.path.insert(0, PKG)
from src.data import load_panel
from src.upsa import UPSA

Z = np.logspace(-10, -1, 10)
T_WIN = 120

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def loo_from_smoothers(smoothers):
    """Equivalent to author calculate_loo_returns: (wbar - w_diag)/(1 - w_diag)."""
    w_diag = [np.diag(w) for w in smoothers]
    w_bar = [np.sum(w, axis=1) for w in smoothers]
    loo = [(w_bar[i] - w_diag[i]) / (1 - w_diag[i]) for i in range(len(smoothers))]
    return np.array(loo).T

def build_smoothers(returns, eigenvalues, eigenvectors, z_list, divisor, z_rescale):
    """Ridge smoothers with given divisor and z rescaling (P>T branch, author-isomorphic)."""
    proj = eigenvectors.T @ returns.T
    mu = np.mean(returns, axis=0)
    pmu = eigenvectors.T @ mu
    w_adj = (returns @ returns.T - proj.T @ proj) / divisor
    out = []
    zz = z_list * z_rescale if z_rescale else z_list
    for z in zz:
        s = proj.T @ ((1.0 / (eigenvalues.reshape(-1, 1) + z)) * proj) / divisor + w_adj / z
        out.append(s)
    return out

def qp_mixture(loo_rets):
    """Author compute_upsa equivalent. Returns (best_z_idx, W) with W in R^L (L=10)
    the ridge-basis MIXING coefficients, NOT final asset weights pi in R^N."""
    best_z, W = UPSA.compute_upsa(loo_rets)
    return int(best_z), np.asarray(W).ravel()

def main():
    panels = load_panel("factors_main")
    X = panels.iloc[:T_WIN].to_numpy(dtype=float)
    T, P = X.shape
    eigval, eigvec = UPSA.smart_eigenvalue_decomposition_covariance(X)

    model = UPSA(z_list=Z).fit(returns=X)
    smooth_A, eff_A = model.w_and_lambda(X, eigval, eigvec)
    loo_A, _ = model.calculate_loo_returns(smooth_A)

    smooth_B = build_smoothers(X, eigval, eigvec, Z, divisor=T, z_rescale=(T - 1.0) / T)
    loo_B = loo_from_smoothers(smooth_B)
    smooth_C = build_smoothers(X, eigval, eigvec, Z, divisor=T - 1, z_rescale=None)
    loo_C = loo_from_smoothers(smooth_C)

    per_z = []
    for j, z in enumerate(Z):
        lA, lB, lC = loo_A[:, j], loo_B[:, j], loo_C[:, j]
        per_z.append({"z": float(z),
                      "loo_A_vs_B_fro": float(np.linalg.norm(lA - lB)),
                      "loo_A_vs_B_maxabs": float(np.max(np.abs(lA - lB))),
                      "loo_A_vs_C_fro": float(np.linalg.norm(lA - lC)),
                      "loo_A_vs_C_maxabs": float(np.max(np.abs(lA - lC)))})

    bzA, WA = qp_mixture(loo_A)
    bzB, WB = qp_mixture(loo_B)
    bzC, WC = qp_mixture(loo_C)
    bz_author, WA_author = qp_mixture(model.estimated_loo_rets)
    author_consistency = {"pathA_best_z_eq_author": bool(bzA == bz_author == model.best_z),
                          "pathA_mixture_vs_author_L2": float(np.linalg.norm(WA - WA_author))}

    def asset_weights(mdl, loo, eff_port):
        bz, Wmix = qp_mixture(loo)
        inv_eigs = Wmix @ (1 / (mdl.eigenvalues.reshape(1, -1) + Z.reshape(-1, 1)))
        scale = np.sum(1 / inv_eigs) / np.sum(mdl.eigenvalues)
        return eff_port @ Wmix * scale

    piA = asset_weights(model, loo_A, eff_A)
    piB = asset_weights(model, loo_B, eff_A)
    piC = asset_weights(model, loo_C, eff_A)
    pi_author = model.get_upsa_weights()

    out = {
        "author_consistency": author_consistency,
        "asset_weights_check": {
            "pathA_pi_vs_author_get_upsa_weights_L2": float(np.linalg.norm(piA - pi_author)),
            "note": "pi in R^N (N=153) final asset weights; W in R^L (L=10) mixing coefficients; do not conflate."},
        "issue_id": "REV2-P006-09",
        "experiment_layer": "IMPLEMENTATION_AUDIT",
        "reproduction_type": "AUTHOR_CODE_RERUN (path A) + AUDIT VARIANTS (B,C)",
        "not_paper_replication": True,
        "environment": {"python": platform.python_version(), "numpy": np.__version__,
                        "author_code": "Dataverse 10.7910/DVN/OHZFKD file 14008244 (extracted); local path via UPSA_PACKAGE_DIR",
                        "upsa_py_sha256": sha256(os.path.join(PKG, "src", "upsa.py"))},
        "data": {"panel": "factors_main", "rows_total": len(panels), "train_window": T_WIN,
                 "P": P, "first_train_start": str(panels.index[0].date()),
                 "first_train_end": str(panels.index[T_WIN - 1].date()),
                 "factors_main_csv_sha256": sha256(os.path.join(PKG, "data", "processed_inputs", "factors_main.csv"))},
        "definitions": {
            "A_author": "author w_and_lambda: smoother /T + w_adj/z; LOO=(wbar-w)/(1-w); z unrescaled",
            "B_paper_aligned": "LOO penalty z->z*(T-1)/T in smoother; full-window basis uses original z",
            "C_direct_Tminus1": "diagnostic: smoother /(T-1), w_adj/(T-1), z unrescaled"},
        "z_grid": [float(z) for z in Z],
        "per_z": per_z,
        "full_target": {
            "W_mixture_A": WA.tolist(), "W_mixture_B": WB.tolist(), "W_mixture_C": WC.tolist(),
            "W_mixture_dim": "L=10 (ridge-basis mixing coefficients, NOT asset weights)",
            "best_z_idx_A": bzA, "best_z_idx_B": bzB, "best_z_idx_C": bzC,
            "W_mixture_A_vs_B_fro": float(np.linalg.norm(WA - WB)),
            "W_mixture_A_vs_C_fro": float(np.linalg.norm(WA - WC)),
            "asset_pi_A_vs_B_fro": float(np.linalg.norm(piA - piB)),
            "asset_pi_A_vs_C_fro": float(np.linalg.norm(piA - piC))},
        "verdict": {"path_A_preserved": True, "author_implementation_not_modified": True,
                     "numeric_sensitivity_recorded": True,
                     "claim": "Audit records divisor-convention difference and low-z stability; not paper replication, not backfilled into P006-E01."},
    }
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "audit_loo_divisor_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: out[k] for k in ("issue_id", "definitions", "full_target", "verdict")}, ensure_ascii=False, indent=2)[:4000])
    print("\nWROTE audit_loo_divisor_results.json")

if __name__ == "__main__":
    main()
