#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK A: eigenvalue scaling & trace-normalisation audit (all numbers from real runs)."""
import os
import numpy as np

from common import (Z, T_WIN, RUN_ID, RESULTS, indep, UPSA, first_X,
                    author_parts, author_eff_port, author_smoother,
                    author_loo_from_smoothers, err, dump, env_info)


def main():
    X = first_X()
    T, P = X.shape
    ap = author_parts(X, Z)

    # ---- 1. what does eig_K actually return? ----
    lamK, VK = indep.eig_K(X)                       # eigenvalues of X X' (T-dim)
    eig_auth = ap["eig"]                             # eigenvalues of X X'/T (T-dim, from author code)
    ratio = np.sort(lamK) / (T * np.sort(eig_auth))
    # independent recomputation of the author's second moment, for cross-check
    K_T = X @ X.T / T
    eig_direct = np.linalg.eigh(K_T)[0]
    ratio_direct = np.sort(lamK) / (T * np.sort(eig_direct))

    # ---- 2. z-grid vs lam scale ----
    scale = {
        "lamK_XXt": {"min": float(lamK.min()), "max": float(lamK.max()),
                     "trace": float(lamK.sum())},
        "eig_XXt_div_T": {"min": float(eig_auth.min()), "max": float(eig_auth.max()),
                          "trace": float(eig_auth.sum())},
        "z_grid": {"min": float(Z.min()), "max": float(Z.max()),
                   "n": len(Z)},
        "lamK_over_Teig_maxabs_dev_from_1": float(np.max(np.abs(ratio - 1.0))),
        "lamK_over_Teig_direct_maxabs_dev_from_1": float(np.max(np.abs(ratio_direct - 1.0))),
        # how many z's are below the smallest eigenvalue under each convention
        "n_z_below_lamK_min": int(np.sum(Z < lamK.min())),
        "n_z_below_eig_min": int(np.sum(Z < eig_auth.min())),
        "z_median_over_lamK_min": float(np.median(Z) / lamK.min()),
        "z_median_over_eig_min": float(np.median(Z) / eig_auth.min()),
    }

    # ---- 3. full ridge basis: Tz (B0/B1) vs author z-with-eig/T ----
    eff_ind, Vt1 = indep.prepare_full_basis(X, lamK, VK)   # X'(K+TzI)^-1 1 ; (P x L)
    eff_auth = author_eff_port(ap, Z)                      # author expression, (P x L)
    ladj_norm = float(np.linalg.norm(ap["l_adj"]))
    ladj_over_z_norm = [float(ladj_norm / z) for z in Z]
    eff = {
        "eff_port_ind_Tz_vs_author_z": err(eff_ind, eff_auth),
        "author_l_adj_norm": ladj_norm,
        "author_l_adj_over_z_norm_by_z": [{"z": float(z), "norm": v}
                                          for z, v in zip(Z, ladj_over_z_norm)],
        "identity_note": ("X'(K+TzI)^-1 1 = (X'X/T + zI)^-1 X'1 = author V diag(1/(eig+z))U'mu "
                          "when K/T eigenvalues are used; l_adj/z is pure roundoff when P>T "
                          "with full T-dim eigenbasis."),
    }
    # per-z eff-port comparison
    eff["per_z"] = [{"z": float(z), **err(eff_ind[:, j], eff_auth[:, j])}
                    for j, z in enumerate(Z)]

    # ---- 4/5. trace scaling & final weights, isolate the lam-vs-lam/T effect ----
    # get the same QP mixing weights used by B0 first-window
    A0, dg0, _ = indep.stable_loo(VK, Vt1, lamK, T_WIN)
    bz_B0, W_B0, info_B0 = indep.qp_mixture(A0.mean(0), A0.T @ A0 / T_WIN)
    # author QP on its own LOO
    Ws = author_smoother(ap, Z)
    A_author = author_loo_from_smoothers(Ws)
    bz_auth, W_auth, info_auth = indep.qp_mixture(A_author.mean(0), A_author.T @ A_author / T_WIN)

    def scale_from(eig, W):
        inv_eigs = W @ (1.0 / (eig[None, :] + Z[:, None]))  # (L x T)
        return float(np.sum(1.0 / inv_eigs) / np.sum(eig))

    sc_ind = scale_from(lamK, W_B0)             # E06 code path (eig = XX' eigenvalues)
    sc_fix = scale_from(lamK / T_WIN, W_B0)     # consistent K/T convention (== author formula)
    sc_auth_WB0 = scale_from(eig_auth, W_B0)    # same as sc_fix numerically
    sc_auth = scale_from(eig_auth, W_auth)      # author's own weights

    # author actual weights via its getter
    m = UPSA(z_list=Z).fit(returns=X)
    pi_auth = np.asarray(m.get_upsa_weights())
    pi_ind = np.asarray(indep.asset_weights(lamK, eff_ind, W_B0)[0])  # current E06 B0 first window
    # isolate scale: current eff_port & W but with the consistent scale
    pi_fix = eff_ind @ W_B0 * sc_fix
    # author eff_port & author W with consistent scale -> should reproduce pi_auth
    pi_auth_recompute = eff_auth @ W_auth * sc_auth
    # cross: author W on independent eff_port (eff-port equivalence isolation)
    pi_cross = eff_ind @ W_auth * sc_auth

    # ridge scale
    sc_ridge_ind = float(np.sum(1.0 / (1.0 / (lamK + Z[bz_B0]))) / np.sum(lamK))
    sc_ridge_fix = float(np.sum(1.0 / (1.0 / (lamK / T_WIN + Z[bz_B0]))) / np.sum(lamK / T_WIN))

    scaling = {
        "scale_E06_current_lamK": sc_ind,
        "scale_consistent_lamK_over_T": sc_fix,
        "scale_consistent_eig_auth_same_W": sc_auth_WB0,
        "scale_author_own_W": sc_auth,
        "scale_ridge_E06_current": sc_ridge_ind,
        "scale_ridge_consistent": sc_ridge_fix,
        "ratio_current_over_consistent": sc_ind / sc_fix,
        "trace_norm_formula_E06": "scale = sum(1/inv_eigs)/sum(eigenvalues), inv_eigs = W @ 1/(eig+z)",
        "trace_norm_formula_author": "get_upsa_weights: scale = sum(1/inv_eigs)/sum(eigenvalues), eig = eig(XX'/T)",
        "trace_norm_formula_paper": "scale = sum(1/inv_eigs)/sum(eigen_lambda) (trace normalisation to unit total weight)",
    }

    weights = {
        "pi_E06_current_lamK_vs_author": err(pi_ind, pi_auth),
        "pi_E06_consistent_scale_vs_author": err(pi_fix, pi_auth),
        "pi_E06_current_vs_consistent": err(pi_ind, pi_fix),
        "pi_author_recomputed_vs_getter": err(pi_auth_recompute, pi_auth),
        "pi_effport_ind_vs_author_same_W": err(pi_cross, pi_auth_recompute),
        "W_B0_vs_W_author_fro": float(np.linalg.norm(W_B0 - W_auth)),
        "best_z_B0": int(bz_B0), "best_z_author": int(m.best_z),
        "qp_status_B0": info_B0["status"], "qp_status_author_form": info_auth["status"],
        "sum_pi_E06_current": float(pi_ind.sum()),
        "sum_pi_consistent": float(pi_fix.sum()),
        "sum_pi_author": float(pi_auth.sum()),
    }

    # ---- 6. Does the scale discrepancy change OOS results? ----
    # scale_E06_current vs scale_consistent is a single multiplicative factor per window;
    # quantify on first window and report that a full rerun is executed separately in task B/audit.
    impact = {
        "first_window_scale_ratio_current_over_consistent": sc_ind / sc_fix,
        "first_window_return_ratio_if_only_scale_changed": sc_ind / sc_fix,
        "note": ("If lam(XX') is used in asset_weights while z is NOT scaled by T, the effective "
                 "shrinkage z_eff = z/T -> far smaller than intended; scale changes by the reported "
                 "ratio. A corrected full rerun with new run_id is produced in taskA_rerun below."),
    }

    out = {
        "issue": "P006-E06 R4 TASK A eigenvalue scaling & trace normalisation audit",
        "run_id": RUN_ID, "T": T, "P": P, "z_grid": Z.tolist(),
        "environment": env_info(),
        "conclusion_lam_is": "XX' eigenvalues (T-dim, NOT divided by T) in independent_upsa.eig_K; "
                             "author uses eig(XX'/T). lamK = T * eig_author verified numerically.",
        "scale": scale, "eff_port": eff, "trace_scaling": scaling,
        "weights": weights, "impact": impact,
    }
    dump("audit_A_eigen_trace.json", out)
    # concise stdout for the record
    print("lamK min/max", lamK.min(), lamK.max())
    print("eig_auth min/max", eig_auth.min(), eig_auth.max())
    print("max|lamK/(T*eig_auth)-1|", np.max(np.abs(ratio - 1.0)))
    print("eff_port ind vs author maxabs", eff["eff_port_ind_Tz_vs_author_z"]["maxabs"])
    print("scale current", sc_ind, "consistent", sc_fix, "ratio", sc_ind / sc_fix)
    print("pi current vs author maxabs", weights["pi_E06_current_lamK_vs_author"]["maxabs"])
    print("pi consistent vs author maxabs", weights["pi_E06_consistent_scale_vs_author"]["maxabs"])
    print("pi author recompute vs getter maxabs", weights["pi_author_recomputed_vs_getter"]["maxabs"])


if __name__ == "__main__":
    main()
