"""Thematic decomposition of SDF loadings (paper figures only):
  * theme_allocation_panel_plot  -> Fig. theme-panel
  * theme_shapley_plot           -> Fig. theme-shapley

Both recompute the theme-level numerical objects (allocation shares; exact
Shapley decomposition of the Delta Sharpe ratio over all 2^K theme subsets)
before drawing. Ported from helpers/plot_functions.py.
"""
import numpy as np
import pandas as pd

from src.style import METHOD_COLORS, save


def _rescale_and_map(weights, factor_returns, jkp_clusters, target_vol):
    """Common preprocessing: target-vol rescale + factor->theme map + theme list."""
    w_upsa = weights["UPSA"].copy()
    w_ridge = weights["Ridge"].copy()
    factors = w_upsa.columns.tolist()
    fr = factor_returns.reindex(index=w_upsa.index, columns=factors)

    ret_upsa = (w_upsa * fr).sum(axis=1)
    ret_ridge = (w_ridge * fr).sum(axis=1)
    w_upsa = w_upsa * (target_vol / (ret_upsa.std() * np.sqrt(12)))
    w_ridge = w_ridge * (target_vol / (ret_ridge.std() * np.sqrt(12)))

    factor_to_theme = {}
    for theme, members in jkp_clusters.items():
        for fac in members:
            if fac in factors:
                factor_to_theme[fac] = theme
    for f in factors:
        factor_to_theme.setdefault(f, "Other")

    themes = list(jkp_clusters.keys())
    if any(f not in sum(jkp_clusters.values(), []) for f in factors):
        themes.append("Other")
    return w_upsa, w_ridge, fr, factors, factor_to_theme, themes


def theme_allocation_panel_plot(weights, factor_returns, jkp_clusters, save_folder=None,
                                target_vol=0.10):
    """Two-panel thematic allocation: levels (UPSA vs Ridge) and difference."""
    import matplotlib.pyplot as plt
    w_upsa, w_ridge, fr, factors, factor_to_theme, themes = _rescale_and_map(
        weights, factor_returns, jkp_clusters, target_vol)

    w_upsa_norm = w_upsa.abs().div(w_upsa.abs().sum(axis=1), axis=0)
    w_ridge_norm = w_ridge.abs().div(w_ridge.abs().sum(axis=1), axis=0)

    share_upsa, share_ridge = {}, {}
    for t in themes:
        cols = [f for f in factors if factor_to_theme.get(f) == t]
        share_upsa[t] = w_upsa_norm[cols].sum(axis=1).mean()
        share_ridge[t] = w_ridge_norm[cols].sum(axis=1).mean()

    theme_df = pd.DataFrame({"UPSA": share_upsa, "Ridge": share_ridge})
    theme_df["diff"] = theme_df["UPSA"] - theme_df["Ridge"]
    theme_df = theme_df.sort_values("diff", ascending=True)

    COLOR_UPSA, COLOR_RIDGE = METHOD_COLORS["UPSA"], METHOD_COLORS["Ridge"]
    COLOR_POS, COLOR_NEG = "#2ca02c", "#d62728"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5),
                                   gridspec_kw={"width_ratios": [3, 2]}, sharey=True)
    y = np.arange(len(theme_df))
    h = 0.35
    ax1.barh(y + h / 2, theme_df["UPSA"] * 100, height=h, color=COLOR_UPSA, label="UPSA", zorder=3)
    ax1.barh(y - h / 2, theme_df["Ridge"] * 100, height=h, color=COLOR_RIDGE, label="Ridge", zorder=3)
    ax1.set_yticks(y)
    ax1.set_yticklabels(theme_df.index, fontsize=11)
    ax1.set_xlabel(r"$s$ (%)", fontsize=12)
    ax1.legend(fontsize=11, loc="lower right", framealpha=0.9)
    ax1.grid(axis="x", alpha=0.3, linestyle="--", zorder=0)
    ax1.set_axisbelow(True)
    for sp in ("top", "right"):
        ax1.spines[sp].set_visible(False)

    diff_vals = theme_df["diff"] * 100
    colors = [COLOR_POS if v > 0 else COLOR_NEG for v in diff_vals.values]
    ax2.barh(y, diff_vals.values, color=colors, zorder=3)
    ax2.set_xlabel(r"$\Delta s$ (%)", fontsize=12)
    ax2.axvline(0, color="black", linewidth=0.8)
    ax2.grid(axis="x", alpha=0.3, linestyle="--", zorder=0)
    ax2.set_axisbelow(True)
    for sp in ("top", "right"):
        ax2.spines[sp].set_visible(False)

    plt.tight_layout()
    save(save_folder)


def theme_shapley_plot(weights, factor_returns, jkp_clusters, save_folder=None,
                       target_vol=0.10):
    """Exact Shapley decomposition of Delta Sharpe ratio into theme contributions."""
    import matplotlib.pyplot as plt
    from itertools import combinations
    from math import factorial

    w_upsa, w_ridge, fr, factors, factor_to_theme, themes = _rescale_and_map(
        weights, factor_returns, jkp_clusters, target_vol)
    K = len(themes)

    upsa_arr = np.column_stack([
        (w_upsa[[f for f in factors if factor_to_theme.get(f) == t]]
         * fr[[f for f in factors if factor_to_theme.get(f) == t]]).sum(axis=1).values
        for t in themes])
    ridge_arr = np.column_stack([
        (w_ridge[[f for f in factors if factor_to_theme.get(f) == t]]
         * fr[[f for f in factors if factor_to_theme.get(f) == t]]).sum(axis=1).values
        for t in themes])

    def subset_delta_sr(mask):
        if not mask.any():
            return 0.0
        r_u = upsa_arr[:, mask].sum(axis=1)
        r_r = ridge_arr[:, mask].sum(axis=1)
        sr_u = r_u.mean() / r_u.std() * np.sqrt(12) if r_u.std() > 0 else 0.0
        sr_r = r_r.mean() / r_r.std() * np.sqrt(12) if r_r.std() > 0 else 0.0
        return sr_u - sr_r

    delta_sr_cache = {}
    for bits in range(2 ** K):
        mask = np.array([(bits >> i) & 1 for i in range(K)], dtype=bool)
        delta_sr_cache[bits] = subset_delta_sr(mask)

    shapley = {}
    for k_idx, t in enumerate(themes):
        phi = 0.0
        other = [i for i in range(K) if i != k_idx]
        for s_size in range(K):
            coeff = factorial(s_size) * factorial(K - s_size - 1) / factorial(K)
            for combo in combinations(other, s_size):
                bits_s = sum(1 << i for i in combo)
                phi += coeff * (delta_sr_cache[bits_s | (1 << k_idx)] - delta_sr_cache[bits_s])
        shapley[t] = phi

    shapley_s = pd.Series(shapley).sort_values()
    COLOR_POS, COLOR_NEG = "#2ca02c", "#d62728"

    fig, ax = plt.subplots(figsize=(7, 5.5))
    y = np.arange(len(shapley_s))
    colors = [COLOR_POS if v > 0 else COLOR_NEG for v in shapley_s.values]
    ax.barh(y, shapley_s.values, color=colors, zorder=3, edgecolor="white", linewidth=0.3)
    ax.set_yticks(y)
    ax.set_yticklabels(shapley_s.index, fontsize=11)
    ax.set_xlabel(r"Shapley $\Delta$ Sharpe Ratio", fontsize=12)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.grid(axis="x", alpha=0.3, linestyle="--", zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    plt.tight_layout()
    save(save_folder)
