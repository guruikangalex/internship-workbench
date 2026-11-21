"""Draw the simulation figures from cached simulation outputs.
Ported from simulation/ridge vs upsa.py and upsa_grid_robustness.py."""
import os
import sys
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from src.simulations import trim_eigs
from src.style import get_method_color

# (x_name, y_name, x_label, y_label, stem). Matches the paper's two cross-sim
# panels exactly (simulation_plot_all.py::merge_static figure_pairs).
PAIRS = [
    ("Ridge Economic", "Ridge Statistical", None, None, "sim_econstat"),    # Fig. 14
    ("UPSA", "Ridge Economic", None, "Ridge", "sim_upsaridge"),             # Fig. 15
]


def _scatter_sim(x, y, x_label, y_label, path):
    """Exact port of helpers.plot_functions.scatter_plot_sim — the single
    scatter style used by every simulation scatter in the paper (cross-sim
    Figs 14-15 and time-varying Fig 16). Grey markers (alpha 0.15, s 10),
    black dashed 45-degree line, equal box aspect, dashed grid, framed legend,
    white round-box stats with a light-grey edge."""
    x, y = np.asarray(x), np.asarray(y)
    avg_x, avg_y = x.mean(), y.mean()
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(x, y, color="grey", marker="o", edgecolor="none", alpha=0.15, s=10)
    lims = [min(x.min(), y.min()), max(x.max(), y.max())]
    ax.plot(lims, lims, color="black", linewidth=1.5, linestyle="--", label="45-degree line")
    ax.set_xlabel(x_label, fontsize=14)
    ax.set_ylabel(y_label, fontsize=14)
    ax.tick_params(labelsize=12)
    ax.grid(alpha=0.3, linestyle="--")
    ax.set_aspect("equal", adjustable="box")
    ax.text(0.05, 0.95, f"Avg {x_label}: {avg_x:.2f}\nAvg {y_label}: {avg_y:.2f}",
            transform=ax.transAxes, fontsize=12, verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="lightgray"))
    ax.legend(loc="lower right", fontsize=12, framealpha=0.9)
    fig.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _scatter(perf, x_name, y_name, x_label, y_label, path):
    """Cross-sim scatter (Figs 14-15)."""
    _scatter_sim(perf[x_name].values, perf[y_name].values,
                 x_label or x_name, y_label or y_name, path)


def _eigs(eig, x_name, y_name, x_label, y_label, path):
    """Cross-sim shrinkage curves + eigenvalue histograms — faithful to
    simulation_plot_all.py::plot_eigenvalues: dashed grid on the curve axis,
    light empirical/theoretical histograms (alpha 0.2/0.3, grey edges), and a
    framed 4-column legend box above the plot."""
    empirical = trim_eigs(eig["Empirical"])
    fig, ax1 = plt.subplots(figsize=(7, 7))
    ax1.plot(empirical, trim_eigs(eig[y_name]), label=y_label or y_name,
             linewidth=2.5, color=get_method_color(y_name))
    ax1.plot(empirical, trim_eigs(eig[x_name]), label=x_label or x_name,
             linewidth=2.5, color=get_method_color(x_name))
    ax1.set_xlabel(r"$\bar{\lambda}_i$", fontsize=14)
    ax1.set_ylabel(r"$f^{-1}(\bar{\lambda}_i)$", fontsize=14)
    ax1.tick_params(labelsize=12)
    ax1.grid(alpha=0.3, linestyle="--")

    ax2 = ax1.twinx()
    ax2.hist(empirical, bins=30, alpha=0.2, color="lightcoral",
             edgecolor="grey", linewidth=0.3, density=True, label="Empirical")
    theo = []
    for ev, prop in zip(sorted([0.1, 1, 10]), [0.10, 0.80, 0.10]):
        theo.extend([ev] * int(1000 * prop))
    ax2.hist(theo, bins=30, alpha=0.3, color="steelblue",
             edgecolor="grey", linewidth=0.3, density=True, label="Theoretical")
    ax2.set_ylabel("Eigenvalue Density", fontsize=14)
    ax2.tick_params(labelsize=12)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc="lower center", bbox_to_anchor=(0.5, 1.05),
               ncol=4, fontsize=11, framealpha=0.9)
    fig.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _grid(grid, path):
    """Cross-sim grid robustness panel matching the manuscript: truncate to
    L ≤ 10 (the plateau begins at L=2 — extra points add no information),
    show markers on each line, integer x-ticks at every grid point, and
    label the fixed grid with its explicit range."""
    DISPLAY_LMAX = 10
    GRID_COLORS = {"Fixed": "#006BA4", "Eigenvalue-based": "#C85200"}
    GRID_LABELS = {"Fixed": r"Fixed ($10^{-4}$ to $10^{4}$)",
                   "Eigenvalue-based": "Eigenvalue-based"}
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, series in grid.items():
        s = series.loc[series.index <= DISPLAY_LMAX]
        ax.plot(s.index, s.values, label=GRID_LABELS.get(name, name),
                linewidth=2.5, color=GRID_COLORS.get(name), marker="o", markersize=5)
    ax.set_xlabel("Number of Grid Points ($L$)", fontsize=14)
    ax.set_ylabel("Out-of-Sample Sharpe Ratio", fontsize=14)
    ax.tick_params(labelsize=12)
    ax.legend(fontsize=12, loc="lower right", framealpha=0.9)
    ticks = [L for L in list(grid.values())[0].index if L <= DISPLAY_LMAX]
    ax.set_xticks(ticks)
    ax.grid(alpha=0.3, linestyle="--")
    fig.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_simulations(sim, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    s = save_dir.rstrip("/") + "/"
    perf, eig = sim["perf"], sim["eigenvalues_all"]
    for x_name, y_name, x_label, y_label, stem in PAIRS:
        _scatter(perf, x_name, y_name, x_label, y_label, s + stem + "_scatter.jpg")
        _eigs(eig, x_name, y_name, x_label, y_label, s + stem + "_eigs.jpg")
    _grid(sim["grid"], s + "grid_robustness.jpg")
    if sim.get("tv") is not None:
        plot_time_varying(sim["tv"], save_dir)
    print(f"simulation figures written to {save_dir}")


if __name__ == "__main__":
    with open(HERE + "/outputs/computed/sim_bundle.p", "rb") as f:
        sim = pickle.load(f)
    plot_simulations(sim, HERE + "/outputs/figures")


# ───────────────────────────── time-varying (Markov) figures ─────────────────────────────
from matplotlib.colors import LinearSegmentedColormap
COLOR_UPSA, COLOR_RIDGE = get_method_color("UPSA"), get_method_color("Ridge")


def _shade_regimes(ax, states, rolling_window):
    oos = states[rolling_window:]
    idx = np.arange(rolling_window, rolling_window + len(oos))
    chg = np.diff((oos == 1).astype(int), prepend=0, append=0)
    for s, e in zip(idx[np.where(chg[:-1] == 1)[0]], idx[np.where(chg[1:] == -1)[0]]):
        ax.axvspan(s, e, alpha=0.08, color="red", zorder=0)


def _tv_scatter(df, metric, path):
    """Time-varying Ridge-vs-UPSA scatter (Fig 16) — same scatter_plot_sim
    style as the cross-sim panels (x=Ridge, y=UPSA, labels '<m> Sharpe Ratio'
    / '<m> Turnover (%)', both averages printed to 2 decimals)."""
    _scatter_sim(df["Ridge"].values, df["UPSA"].values,
                 f"Ridge {metric}", f"UPSA {metric}", path)


def _tv_heatmap(best, path):
    """UPSA ensemble-weight heatmap + Ridge best-z overlay — exact port of
    helpers.plot_functions.heatmap_plot (wide 14x6 panel, no x-label,
    upper-centre framed Ridge legend)."""
    zgw, best_z, z_grid = best["z_grid_weights"], best["best_z"], best["z_grid"]
    rw, states = best["rolling_window"], best["states"]
    zw_norm = zgw.div(zgw.sum(axis=1), axis=0)        # row-normalised ensemble shares
    W, idx = zw_norm.values, zw_norm.index.values
    cmap = LinearSegmentedColormap.from_list(
        "white_blue", ["#FFFFFF", "#C8DFEF", "#6AAED6", "#006BA4", "#003050"])
    n_z = len(z_grid)
    fig, ax = plt.subplots(figsize=(14, 6))
    W_smooth = pd.DataFrame(W, index=zw_norm.index).rolling(3, min_periods=1, center=True).mean().values
    im = ax.imshow(W_smooth.T, aspect="auto", origin="lower", cmap=cmap, interpolation="bilinear",
                   extent=[idx[0], idx[-1], -0.5, n_z - 0.5], vmin=0, vmax=np.percentile(W_smooth, 98))
    z_best_idx = np.array([np.argmin(np.abs(z_grid - z_grid[int(bz)])) for bz in best_z.values])
    ax.step(best_z.index.values, z_best_idx, where="post", color="white", linewidth=4, alpha=0.7)
    ax.step(best_z.index.values, z_best_idx, where="post",
            color=get_method_color("Ridge"), linewidth=2.2, label="Ridge")
    _shade_regimes(ax, states, rw)
    ax.set_yticks(np.arange(n_z))
    z_labels = []
    for z in z_grid:
        exp = np.log10(z)
        z_labels.append(f"$10^{{{int(round(exp))}}}$" if abs(exp - round(exp)) < 0.01 else f"{z:.1e}")
    ax.set_yticklabels(z_labels, fontsize=12)
    ax.set_ylabel("Shrinkage Level ($z$)", fontsize=14)
    ax.set_xlabel("")
    ax.tick_params(axis="x", labelsize=12)
    cbar = fig.colorbar(im, ax=ax, pad=0.02, shrink=0.9)
    cbar.set_label("UPSA Ensemble Weight", fontsize=14)
    cbar.ax.tick_params(labelsize=12)
    ax.legend(fontsize=12, loc="upper center", ncol=1, bbox_to_anchor=(0.5, 1.10), framealpha=0.9)
    plt.tight_layout(); plt.subplots_adjust(top=0.90)
    plt.savefig(path, dpi=300, bbox_inches="tight"); plt.close(fig)


def _tv_turnover(best, path, roll_window=12):
    """Rolling turnover (%) panel — exact port of
    helpers.plot_functions.turnover_comparison_plot. Simple
    `w.diff().abs().sum()` turnover (NO drift adjustment), '<method> (mean:
    X.X%)' legend labels, upper-centre framed legend, green/red fill."""
    weights, states, rw = best["weights"], best["states"], best["rolling_window"]
    ts_turnover = {}
    for method, w in weights.items():
        gross = w.abs().sum(axis=1)
        diff_abs_sum = w.diff().abs().sum(axis=1)
        turnover_ts = 0.5 * diff_abs_sum / gross.shift()
        turnover_ts.iloc[0] = 0.0
        ts_turnover[method] = 100 * turnover_ts
    ts_turnover = pd.DataFrame(ts_turnover)
    ts_turnover = ts_turnover.clip(upper=ts_turnover.quantile(0.99).max())
    turn_upsa = ts_turnover["UPSA"].rolling(roll_window).mean().dropna()
    turn_ridge = ts_turnover["Ridge"].rolling(roll_window).mean().dropna()
    cidx = turn_upsa.index.intersection(turn_ridge.index)
    turn_upsa, turn_ridge = turn_upsa.loc[cidx], turn_ridge.loc[cidx]
    lbl_u = f"UPSA (mean: {ts_turnover['UPSA'].mean():.1f}%)"
    lbl_r = f"Ridge (mean: {ts_turnover['Ridge'].mean():.1f}%)"
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(turn_upsa.index, turn_upsa.values, color=COLOR_UPSA, label=lbl_u, linewidth=2.5, alpha=0.85)
    ax.plot(turn_ridge.index, turn_ridge.values, color=COLOR_RIDGE, label=lbl_r, linewidth=2.5, alpha=0.85)
    ax.fill_between(cidx, turn_upsa.values, turn_ridge.values,
                    where=(turn_ridge.values > turn_upsa.values), alpha=0.18, color="green")
    ax.fill_between(cidx, turn_upsa.values, turn_ridge.values,
                    where=(turn_ridge.values <= turn_upsa.values), alpha=0.18, color="red")
    _shade_regimes(ax, states, rw)
    ax.set_xlabel("")
    ax.set_ylabel("12-Month Rolling Average Turnover (%)", fontsize=14)
    ax.tick_params(axis="both", labelsize=12)
    ax.legend(fontsize=12, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.12), framealpha=0.9)
    ax.grid(alpha=0.3, linestyle="--")
    plt.tight_layout(); plt.subplots_adjust(top=0.88)
    plt.savefig(path, dpi=300, bbox_inches="tight"); plt.close(fig)


def _tv_dist(best, path):
    """Single panel, pooled over ALL out-of-sample periods (matches the published
    figure): UPSA average normalised ensemble weight vs Ridge best-z frequency
    per shrinkage level. Faithful to helpers/plot_functions.dist_plot."""
    zgw, best_z, z_grid = best["z_grid_weights"], best["best_z"], best["z_grid"]
    probs = best_z.value_counts() / len(best_z)                    # Ridge: freq of each z
    probs = probs.reindex(range(len(z_grid))).fillna(0).sort_index()
    cupsa = zgw.values / zgw.values.sum(axis=1, keepdims=True)     # UPSA: normalise per period
    cupsa_avg = np.mean(cupsa, axis=0)
    labels = [f"{z:g}" if z >= 0.01 else f"{z:.0e}" for z in z_grid]
    x = np.arange(len(z_grid)); width = 0.35
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - width / 2, cupsa_avg, width, label="UPSA", color=COLOR_UPSA, edgecolor="white", linewidth=0.5)
    ax.bar(x + width / 2, probs.values, width, label="Ridge", color=COLOR_RIDGE, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Shrinkage Level ($z$)", fontsize=14)
    ax.set_ylabel("Weight", fontsize=14)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=12)
    ax.tick_params(axis="y", labelsize=12)
    ax.legend(fontsize=12, loc="upper left", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3, linestyle="--"); ax.set_axisbelow(True)
    plt.tight_layout(); plt.savefig(path, dpi=300, bbox_inches="tight"); plt.close()


def plot_time_varying(tv, save_dir):
    s = save_dir.rstrip("/") + "/"
    _tv_scatter(tv["sharpe"], "Sharpe Ratio", s + "tv_scatter_sr.jpg")
    _tv_scatter(tv["turnover"], "Turnover (%)", s + "tv_scatter_turnover.jpg")
    _tv_heatmap(tv["best"], s + "tv_heatmap.jpg")
    _tv_turnover(tv["best"], s + "tv_turnover.jpg")
    _tv_dist(tv["best"], s + "tv_dist_by_regime.jpg")
