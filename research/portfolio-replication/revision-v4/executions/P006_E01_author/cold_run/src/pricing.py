"""SDF- and beta-based out-of-sample pricing accuracy by JKP theme.
Ported from helpers/plot_functions.py (r_2_table_gen, get_first_pcs,
pe scatter inputs) and rolling_window/plot_stuff.py (calculate_pe).

These recompute the numerical objects behind the pricing-accuracy figures
(Fig. pricingacc / beta-scatter) and the R^2 theme tables.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from src.constants import PricingErrors


# ----------------------------------------------- SDF-based predicted/realized SR
def sdf_predicted_realized(opt_port, factors, scaling=True):
    """Realized vs SDF-predicted annualized Sharpe ratios for each test factor.
    Returns (realized: Series over factors, predicted: dict[method] -> Series)."""
    factors_sub = factors.loc[opt_port.index]
    factors_sr = np.sqrt(12) * factors_sub / np.std(factors_sub)
    realized = np.mean(factors_sr, axis=0)
    if scaling:
        scale = np.mean(opt_port, axis=0) / np.mean(opt_port ** 2, axis=0)
        sdfs = scale * opt_port
    else:
        sdfs = opt_port
    predicted = {c_: factors_sr.T @ sdfs[c_] / len(sdfs) for c_ in opt_port.columns}
    return realized, predicted


def r_2_table_gen(opt_port, factors, jkp, scaling=True):
    """R^2 (fit to the 45-degree line) of SDF-predicted vs realized Sharpe,
    per JKP theme plus 'All'.

    Faithful to the published table (helpers/plot_functions.py): WITHIN each
    theme the factors are normalised by a SINGLE pooled standard deviation of
    the theme block (``np.std`` over the 2-D array), whereas the 'All' row uses
    per-column normalisation (each factor by its own vol, identical to the
    pricing-accuracy scatter). The two scalings are deliberately different in
    the paper, so the per-theme rows must use the pooled std to reproduce it.
    """
    if scaling:
        scale = np.mean(opt_port, axis=0) / np.mean(opt_port ** 2, axis=0)
        sdfs = scale * opt_port
    else:
        sdfs = opt_port
    all_r_2 = {}
    for cluster in jkp:
        all_r_2[cluster] = {}
        names = [c for c in jkp[cluster] if c in factors.columns]
        if len(names) == 0:
            for c_ in opt_port.columns:
                all_r_2[cluster][c_] = np.nan
            continue
        # per theme: ONE pooled std over the whole theme block (2-D -> scalar)
        fsub = factors.loc[opt_port.index, names].values
        fsr = np.sqrt(12) * fsub / np.std(fsub)
        sharpes = np.mean(fsr, axis=0)
        for c_ in opt_port.columns:
            x = fsr.T @ sdfs[c_].values / len(sdfs)
            all_r_2[cluster][c_] = r2_score(sharpes, x)
    # 'All' row: per-column normalisation over the full 153-factor panel
    realized, predicted = sdf_predicted_realized(opt_port, factors, scaling)
    all_r_2["All"] = {c_: r2_score(realized, predicted[c_]) for c_ in opt_port.columns}
    return pd.DataFrame(all_r_2)


def get_first_pcs(factors, opt_sub, jkp):
    """First principal component (time series) of each theme's factor block."""
    first_pcs = []
    for cluster in jkp:
        names = [c for c in jkp[cluster] if c in factors.columns]
        ret_clus = factors.loc[opt_sub.index, names].values
        eigvec = np.linalg.eigh(ret_clus @ ret_clus.T)[1]
        first_pcs.append(pd.Series(eigvec[:, -1], index=opt_sub.index, name=cluster))
    return pd.DataFrame(first_pcs).T


# ---------------------------------------------------- beta-based predicted SR
def beta_predicted_realized(opt_port, beta_ins, factors):
    """Realized vs in-sample-beta-predicted Sharpe ratios per factor.

    Faithful to the published table: the realized per-factor Sharpe is
    calibrated on the OOS-aligned slice of the panel (`factors.loc[opt_port.index]`),
    not the full panel that includes the rolling-window warmup. The original
    pipeline did this via `align_to_common_index(opt_port, factors)` before
    calling this function; we replicate that here so callers don't have to.
    """
    factors_oos = factors.loc[opt_port.index]
    fac_scale = factors_oos.std() / np.sqrt(12)
    realized = np.mean(factors_oos, axis=0) / fac_scale
    predicted = {c_: (opt_port[c_].T @ beta_ins[c_] / len(opt_port[c_])) / fac_scale
                 for c_ in beta_ins}
    return realized, predicted


def r_2_table_gen_beta(opt_port, beta_ins, factors, jkp):
    realized, predicted = beta_predicted_realized(opt_port, beta_ins, factors)
    all_r_2 = {}
    for cluster in jkp:
        all_r_2[cluster] = {}
        names = [c for c in jkp[cluster] if c in factors.columns]
        if len(names) == 0:
            for c_ in beta_ins:
                all_r_2[cluster][c_] = np.nan
            continue
        for c_ in beta_ins:
            all_r_2[cluster][c_] = r2_score(realized[names], predicted[c_][names])
    all_r_2["All"] = {c_: r2_score(realized, predicted[c_]) for c_ in beta_ins}
    return pd.DataFrame(all_r_2)


# ------------------------------------------------- HJ-distance pricing errors
def calculate_pe(opt_sub, factors, jkp, type=PricingErrors.Covariance, benchmark="UPSA"):
    """Relative HJ-distance pricing errors per theme, normalized by UPSA."""
    pes = {c_: {} for c_ in opt_sub.columns}
    for cluster in jkp:
        names = [c for c in jkp[cluster] if c in factors.columns]
        ret_clus = factors.loc[opt_sub.index, names].values
        if type == PricingErrors.Covariance:
            cov_fac = np.linalg.pinv(ret_clus.T @ ret_clus / ret_clus.shape[0])
        elif type == PricingErrors.Variance:
            cov_fac = np.diag(1 / np.mean(ret_clus ** 2, axis=0))
        else:  # Identity
            cov_fac = np.eye(ret_clus.shape[1])
        factor_scale_matrix = ret_clus @ cov_fac @ ret_clus.T
        for c_ in opt_sub.columns:
            scal = np.mean(opt_sub[c_]) / np.mean(opt_sub[c_] ** 2)
            sdf = 1 - scal * opt_sub[c_]
            pes[c_][cluster] = sdf.T @ factor_scale_matrix @ sdf / (ret_clus.shape[0] ** 2)
    for c_ in opt_sub.columns:
        if c_ != benchmark:
            for cluster in jkp:
                pes[c_][cluster] = pes[c_][cluster] / pes[benchmark][cluster]
    pes.pop(benchmark)
    return pes
