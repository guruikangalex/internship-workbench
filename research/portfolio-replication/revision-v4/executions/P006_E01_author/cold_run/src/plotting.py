"""Figure drawing. Faithful ports of the relevant functions in
helpers/plot_functions.py (paper figures only). Each function consumes already
-computed objects and writes one figure.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import statsmodels.api as sm

from src.style import METHOD_COLORS, get_method_color, save
from src.metrics import sharpe


# ───────────────────────────── Sharpe / alpha bars ─────────────────────────────
def plot_sharpe_ratios_full_sample(opt_port, save_fig=None, labels=None):
    labels = opt_port.columns if labels is None else labels
    sv = sharpe(opt_port)
    plot_values = np.maximum(sv.values, 0)
    colors = [METHOD_COLORS.get(str(l), "#999999") for l in labels]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, plot_values, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_ylabel("Sharpe Ratio", fontsize=14)
    ax.tick_params(axis="x", rotation=0, labelsize=12)
    ax.tick_params(axis="y", labelsize=12)
    ax.set_ylim(0, sv.max() * 1.15)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    for bar, val in zip(bars, sv.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.03,
                f"{val:.2f}", ha="center", va="bottom", fontsize=11)
    fig.tight_layout()
    save(save_fig)


def plot_sharpe_ratios_bar(opt_port, save_fig=None, periods=None, labels=None):
    periods = periods or [(None, None), (None, "2000"), ("2000", None)]
    labels = opt_port.columns if labels is None else labels
    period_names = ["Full Sample", "Before 2000", "After 2000"]
    data, global_max = {}, 0
    for i, (start, end) in enumerate(periods):
        if start is None and end is not None:
            sv = sharpe(opt_port[:end])
        elif start is not None and end is None:
            sv = sharpe(opt_port[start:])
        else:
            sv = sharpe(opt_port)
        data[period_names[i] if i < len(period_names) else f"Period {i+1}"] = sv
        global_max = max(global_max, sv.max())
    fig, axes = plt.subplots(1, len(data), figsize=(4.5 * len(data), 5), sharey=True)
    if len(data) == 1:
        axes = [axes]
    y_limit = global_max * 1.15
    for i, (pname, sv) in enumerate(data.items()):
        colors = [METHOD_COLORS.get(str(l), "#999999") for l in labels]
        bars = axes[i].bar(labels, np.maximum(sv.values, 0), color=colors,
                           edgecolor="white", linewidth=0.5)
        axes[i].set_title(pname, fontsize=14, fontweight="bold")
        axes[i].tick_params(axis="x", rotation=0, labelsize=12)
        axes[i].tick_params(axis="y", labelsize=12)
        axes[i].set_ylim(0, y_limit)
        axes[i].grid(axis="y", alpha=0.3, linestyle="--")
        axes[i].set_axisbelow(True)
        for bar, val in zip(bars, sv.values):
            axes[i].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.03,
                         f"{val:.2f}", ha="center", va="bottom", fontsize=11)
        if i == 0:
            axes[i].set_ylabel("Sharpe Ratio", fontsize=14)
    fig.tight_layout(pad=1)
    fig.subplots_adjust(left=0.05, right=0.98, top=0.9, bottom=0.1)
    save(save_fig)


def _alpha_one(y, X, annual_vol):
    y = y * annual_vol / np.std(np.sqrt(12) * y)
    X = X * annual_vol / np.std(np.sqrt(12) * X)
    model = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    alpha = model.params["const"] * 12 * 100
    ci = model.conf_int().loc["const"] * 12 * 100
    return alpha, alpha - ci[0], ci[1] - alpha, model.tvalues["const"]


def plot_alpha_full_sample(opt_port, save_fig=None, labels=None, annual_vol=0.1):
    if opt_port.columns[0].lower() != "upsa":
        raise ValueError("first column must be 'upsa'")
    y = opt_port.iloc[:, 0]
    indep = opt_port.columns[1:]
    alphas, lo, hi, valid = [], [], [], []
    for col in indep:
        a, l, h, _ = _alpha_one(y.copy(), opt_port[[col]].copy(), annual_vol)
        alphas.append(a); lo.append(l); hi.append(h); valid.append(col)
    x = np.arange(len(valid))
    colors = [METHOD_COLORS.get(str(l), "#999999") for l in valid]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x, alphas, color=colors, edgecolor="white", linewidth=0.5)
    ax.errorbar(x, alphas, yerr=[lo, hi], fmt="none", color="black", capsize=5)
    ax.set_ylabel(r"$\alpha$ (annualized %)", fontsize=14)
    ax.set_xticks(x); ax.set_xticklabels(valid, fontsize=12)
    ax.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax.grid(axis="y", alpha=0.3, linestyle="--"); ax.set_axisbelow(True)
    fig.tight_layout()
    save(save_fig)


def plot_alpha_bar(opt_port, save_fig=None, periods=None, labels=None, annual_vol=0.1):
    if opt_port.columns[0].lower() != "upsa":
        raise ValueError("first column must be 'upsa'")
    indep = opt_port.columns[1:]
    periods = periods or [(None, None), (None, "2000"), ("2000", None)]
    period_names = ["Full Sample", "Before 2000", "After 2000"]
    results, global_a = {}, []
    for i, (start, end) in enumerate(periods):
        dp = opt_port.loc[:end] if (start is None and end) else (
            opt_port.loc[start:] if start else opt_port)
        rows = []
        for col in indep:
            a, l, h, t = _alpha_one(dp.iloc[:, 0].copy(), dp[[col]].copy(), annual_vol)
            rows.append({"regressor": col, "alpha": a, "lo": l, "hi": h, "t": t})
            global_a += [a + h, a - l]
        results[period_names[i] if i < len(period_names) else f"Period {i+1}"] = rows
    if global_a:
        lo_, hi_ = min(global_a), max(global_a)
        buf = 0.1 * (hi_ - lo_) if hi_ != lo_ else 0.1
        ylim = (lo_ - buf, hi_ + buf)
    else:
        ylim = (-1, 1)
    fig, axes = plt.subplots(1, len(results), figsize=(4.5 * len(results), 5), sharey=True)
    if len(results) == 1:
        axes = [axes]
    for i, (pname, rows) in enumerate(results.items()):
        ax = axes[i]
        rl = [r["regressor"] for r in rows]
        xp = np.arange(len(rl))
        colors = [METHOD_COLORS.get(str(l), "#999999") for l in rl]
        ax.bar(xp, [r["alpha"] for r in rows], color=colors, edgecolor="white", linewidth=0.5)
        ax.errorbar(xp, [r["alpha"] for r in rows],
                    yerr=[[r["lo"] for r in rows], [r["hi"] for r in rows]],
                    fmt="none", color="black", capsize=5)
        ax.set_title(pname, fontsize=14, fontweight="bold")
        ax.set_xticks(xp); ax.set_xticklabels(rl, fontsize=12)
        ax.set_ylim(ylim)
        ax.grid(axis="y", alpha=0.3, linestyle="--"); ax.set_axisbelow(True)
        if i == 0:
            ax.set_ylabel(r"$\alpha$ (%)", fontsize=14)
    fig.tight_layout(pad=2.0)
    fig.subplots_adjust(left=0.05, right=0.98, top=0.88, bottom=0.1)
    save(save_fig)


# ───────────────────────────── pricing scatters ─────────────────────────────
def pe_scatter_plot_beta(realized, predicted, savefolder=None):
    """Beta-based realized vs predicted Sharpe scatter, one per method."""
    from sklearn.metrics import r2_score
    for c_ in predicted:
        x, y = predicted[c_], realized
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(x, y, color=get_method_color(c_), alpha=0.7, edgecolor="black", s=20)
        lo, hi = min(min(x), min(y)), max(max(x), max(y))
        ax.plot([lo, hi], [lo, hi], color="gray", linestyle="--", linewidth=1.5)
        ax.text(0.05, 0.95, fr"$R^2$ = {r2_score(y, x):.2f}", transform=ax.transAxes,
                fontsize=12, va="top",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="lightgray"))
        ax.set_xlabel("Realized Sharpe Ratio", fontsize=14)
        ax.set_ylabel("Predicted Sharpe Ratio", fontsize=14)
        ax.tick_params(axis="both", labelsize=12)
        ax.grid(alpha=0.3, linestyle="--")
        save(savefolder + f"{c_}_scatter_plot.jpg" if savefolder else None)


def turnover_rolling_plot(weights, save_fig=None, roll_window=12):
    """12-month rolling average turnover, UPSA vs Ridge (Fig. turnover-rolling)."""
    from src.metrics import turnover_fun
    ts, _ = turnover_fun(weights)
    ts = pd.DataFrame(ts)
    raw_u, raw_r = ts["UPSA"], ts["Ridge"]
    tu = raw_u.rolling(roll_window).mean().dropna()
    tr = raw_r.rolling(roll_window).mean().dropna()
    cidx = tu.index.intersection(tr.index)
    tu, tr = tu.loc[cidx], tr.loc[cidx]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(tu.index, tu.values, color=METHOD_COLORS["UPSA"],
            label=f"UPSA (mean: {raw_u.mean():.1f}%)", linewidth=2.5, alpha=0.85)
    ax.plot(tr.index, tr.values, color=METHOD_COLORS["Ridge"],
            label=f"Ridge (mean: {raw_r.mean():.1f}%)", linewidth=2.5, alpha=0.85)
    ax.fill_between(cidx, tu.values, tr.values, where=(tr.values > tu.values), alpha=0.18, color="green")
    ax.fill_between(cidx, tu.values, tr.values, where=(tr.values <= tu.values), alpha=0.18, color="red")
    ax.set_ylabel("12-Month Rolling Average Turnover (%)", fontsize=14)
    ax.tick_params(axis="both", labelsize=12)
    ax.legend(fontsize=12, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.12), framealpha=0.9)
    ax.grid(alpha=0.3, linestyle="--")
    plt.tight_layout(); plt.subplots_adjust(top=0.88)
    save(save_fig)


def pe_scatter_plot(realized, predicted, savefolder=None):
    """One scatter per method: realized vs SDF-predicted Sharpe + R^2."""
    from sklearn.metrics import r2_score
    for c_ in predicted:
        x, y = predicted[c_], realized
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(x, y, color=METHOD_COLORS.get(c_, "#999999"), alpha=0.7,
                   edgecolor="black", linewidth=0.3)
        lo, hi = min(min(x), min(y)), max(max(x), max(y))
        ax.plot([lo, hi], [lo, hi], color="gray", linestyle="--")
        ax.text(0.05, 0.95, fr"$R^2$ = {r2_score(y, x):.2f}", transform=ax.transAxes,
                fontsize=16, va="top", bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
        ax.set_xlabel("Realized Sharpe Ratio", fontsize=16)
        ax.set_ylabel("Predicted Sharpe Ratio", fontsize=16)
        ax.tick_params(axis="both", labelsize=14)
        save(savefolder + f"{c_}_scatter_plot.jpg" if savefolder else None)


# ───────────────────────────── PC diagnostics ─────────────────────────────
def plot_pc_sharpe(pcs, save_folder=None, name="Number of PCs (K)", scale=None, ylim=None):
    fig, ax = plt.subplots(figsize=(8, 5))
    for l in pcs:
        ax.plot(pcs[l].columns, sharpe(pcs[l]), label=l, color=get_method_color(l), linewidth=2.5)
    ax.set_ylabel("Sharpe Ratio", fontsize=14)
    ax.set_xlabel(name, fontsize=14)
    ax.tick_params(labelsize=12)
    ax.legend(loc="upper right", fontsize=12, framealpha=0.9)
    ax.grid(alpha=0.3, linestyle="--")
    if scale is not None:
        ax.set_xscale("log")
    if ylim is None:
        all_sr = [v for l in pcs for v in sharpe(pcs[l]).values]
        ax.set_ylim(max(0, min(all_sr) - 0.1), None)
    else:
        ax.set_ylim(ylim)
    plt.tight_layout()
    save(save_folder)


def plot_corr_sparse_oracle_joint(pcs, save_folder=None):
    methods = [m for m in ["UPSA", "Ridge"] if m in pcs]
    best_sr, oracle_ret = -np.inf, None
    for m in methods:
        sr = sharpe(pcs[m])
        k = np.argmax(sr)
        if sr[k] > best_sr:
            best_sr, oracle_ret = sr[k], pcs[m][pcs[m].columns[k]].values
    fig, ax = plt.subplots(figsize=(8, 5))
    for m in methods:
        corrs = [np.corrcoef(oracle_ret, pcs[m][K].values)[0, 1] for K in pcs[m].columns]
        ax.plot(pcs[m].columns, corrs, linewidth=2.5, label=m, color=get_method_color(m))
    ax.set_xlabel("Number of PCs (K)", fontsize=14)
    ax.set_ylabel("Correlation with Global Sparse Oracle", fontsize=14)
    ax.set_ylim(0.5, 1.02)
    ax.tick_params(labelsize=12)
    ax.legend(loc="upper right", fontsize=12, framealpha=0.9)
    ax.grid(alpha=0.3, linestyle="--")
    plt.tight_layout()
    save(save_folder)


# ───────────────────────────── shrinkage / correlation ─────────────────────────────
def nls_function_plot(eigenvalues, save_folder=None):
    fig, ax = plt.subplots(figsize=(8, 5))
    x_vals = None
    for l in eigenvalues:
        ev = eigenvalues[l]
        if x_vals is None:
            x_vals = np.array(ev.columns, dtype=float)
        ax.plot(x_vals, np.mean(ev, axis=0), label=l, color=get_method_color(l), linewidth=2.5)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.invert_xaxis()
    ax.set_ylabel(r"$f^{-1}(\bar{\lambda})$", fontsize=14)
    ax.set_xlabel(r"$\bar{\lambda}$", fontsize=14)
    ax.legend(loc="upper right", fontsize=12, framealpha=0.9)
    ax.tick_params(labelsize=12)
    ax.grid(alpha=0.3, linestyle="--")
    fig.tight_layout()
    save(save_folder)


def plot_corr_matrix(ports, save_folder=None):
    cov = np.cov(ports, rowvar=False)
    stds = np.sqrt(np.diag(cov))
    corr = cov / np.outer(stds, stds)
    n = corr.shape[0]
    labels = [f"{float(c):g}" if float(c) >= 0.01 else f"{float(c):.0e}" for c in ports.columns]
    fig, ax = plt.subplots(figsize=(8, 7))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, cmap="RdBu_r", vmin=-0.2, vmax=1.0, center=0.5, ax=ax,
                square=True, linewidths=0.5, linecolor="white",
                xticklabels=labels, yticklabels=labels,
                cbar_kws={"label": "Correlation", "shrink": 0.8})
    for i in range(n):
        for j in range(i + 1):
            v = corr[i, j]
            ax.text(j + 0.5, i + 0.5, f"{v:.2f}", ha="center", va="center",
                    fontsize=10, color="white" if (v > 0.75 or v < 0.1) else "black")
    ax.set_xlabel("Shrinkage Level ($z$)", fontsize=14)
    ax.set_ylabel("Shrinkage Level ($z$)", fontsize=14)
    ax.tick_params(axis="x", rotation=45, labelsize=12)
    ax.tick_params(axis="y", rotation=0, labelsize=12)
    plt.tight_layout()
    save(save_folder)


# ───────────────────────────── time-series figures ─────────────────────────────
def cumulative_returns_plot(returns, savefolder, annual_vol=0.1, agg_type="log"):
    if agg_type == "log":
        cum = np.log(1 + annual_vol * returns / np.std(np.sqrt(12) * returns)).cumsum()
    else:
        norm = annual_vol * returns / np.std(np.sqrt(12) * returns)
        cum = np.cumprod(norm + 1) - 1
    fig, ax = plt.subplots(figsize=(8, 5))
    for col in cum.columns:
        ax.plot(cum.index, cum[col], color=METHOD_COLORS.get(col, "#999999"),
                linewidth=2.5, label=col)
    ax.set_ylabel("Cumulative Log Returns", fontsize=14)
    ax.tick_params(axis="both", labelsize=12)
    ax.legend(fontsize=12, loc="upper left", framealpha=0.9)
    ax.grid(alpha=0.3, linestyle="--")
    plt.tight_layout()
    plt.savefig(savefolder + f"cumulative_returns_{agg_type}.jpg", dpi=300, bbox_inches="tight")
    plt.close()


def dist_plot(best_z, cupsa, z_grid, save_folder, legend=None):
    probs = best_z.value_counts() / len(best_z)
    for i in range(len(z_grid)):
        if i not in probs.index:
            probs.loc[i] = 0
    probs = probs.sort_index()
    probs.index = z_grid
    cupsa = cupsa / cupsa.sum(axis=1).values.reshape(-1, 1)
    cupsa_avg = np.mean(cupsa, axis=0)
    labels = [f"{z:g}" if z >= 0.01 else f"{z:.0e}" for z in z_grid]
    x = np.arange(len(z_grid)); width = 0.35
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - width / 2, cupsa_avg, width, label="UPSA",
           color=METHOD_COLORS["UPSA"], edgecolor="white", linewidth=0.5)
    ax.bar(x + width / 2, probs.values, width, label="Ridge",
           color=METHOD_COLORS["Ridge"], edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Shrinkage Level ($z$)", fontsize=14)
    ax.set_ylabel("Weight", fontsize=14)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=12)
    ax.tick_params(axis="y", labelsize=12)
    ax.legend(fontsize=12, loc="upper left", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3, linestyle="--"); ax.set_axisbelow(True)
    plt.tight_layout()
    save(save_folder)


def combined_surface_with_time_overlay(df, z_grid, best_z, save_folder=None, log_scale=True):
    from matplotlib.colors import LinearSegmentedColormap
    df = df.copy(); df.index = pd.to_datetime(df.index)
    df = df.div(df.sum(axis=1), axis=0)
    best_z = best_z.copy(); best_z.index = pd.to_datetime(best_z.index)
    W = df.apply(pd.to_numeric).values
    z_vals = df.columns.astype(float).values
    z_best_values = np.array([z_grid[int(best_z.iloc[i])] for i in range(len(best_z))])
    fig, ax = plt.subplots(figsize=(14, 6))
    W_smooth = pd.DataFrame(W, index=df.index).rolling(3, min_periods=1, center=True).mean().values
    cmap = LinearSegmentedColormap.from_list("white_blue",
            ["#FFFFFF", "#C8DFEF", "#6AAED6", "#006BA4", "#003050"])
    n_z = len(z_vals)
    im = ax.imshow(W_smooth.T, aspect="auto", origin="lower", cmap=cmap, interpolation="bilinear",
                   extent=[mdates.date2num(df.index[0]), mdates.date2num(df.index[-1]), -0.5, n_z - 0.5],
                   vmin=0, vmax=np.percentile(W_smooth, 98))
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    z_best_idx = np.array([np.argmin(np.abs(z_vals - zb)) for zb in z_best_values])
    dates_num = mdates.date2num(best_z.index)
    ax.step(dates_num, z_best_idx, where="post", color="white", linewidth=4, alpha=0.7)
    ax.step(dates_num, z_best_idx, where="post", color=METHOD_COLORS["Ridge"], linewidth=2.2, label="Ridge")
    ax.set_yticks(np.arange(n_z))
    ax.set_yticklabels([f"$10^{{{int(np.log10(z))}}}$" for z in z_vals], fontsize=12)
    ax.set_ylabel("Shrinkage Level ($z$)", fontsize=14)
    ax.tick_params(axis="x", labelsize=12)
    cbar = fig.colorbar(im, ax=ax, pad=0.02, shrink=0.9)
    cbar.set_label("UPSA Ensemble Weight", fontsize=14)
    cbar.ax.tick_params(labelsize=12)
    ax.legend(fontsize=12, loc="upper center", bbox_to_anchor=(0.5, 1.10), framealpha=0.9)
    plt.tight_layout(); plt.subplots_adjust(top=0.90)
    if save_folder is not None:
        plt.savefig(save_folder, dpi=300, bbox_inches="tight"); plt.close()
    else:
        plt.show()


def plot_recession_panels(opt_port, save_folder=None):
    """Three-panel by NBER regime: Sharpe, mean return, volatility (10% vol)."""
    import matplotlib.patches as mpatches
    from src.constants import NBER_RECESSIONS
    target_vol = 0.10
    methods = [m for m in ["UPSA", "Ridge", "LW", "PCA", "FF5", "CAPM"] if m in opt_port.columns]
    scaled = pd.DataFrame(index=opt_port.index)
    for m in methods:
        scaled[m] = opt_port[m] * (target_vol / (opt_port[m].std() * np.sqrt(12)))
    mask = pd.Series(False, index=opt_port.index)
    for s, e in NBER_RECESSIONS:
        mask |= (opt_port.index >= pd.to_datetime(s)) & (opt_port.index <= pd.to_datetime(e))
    rec, exp = scaled.loc[mask], scaled.loc[~mask]
    panels = [
        {"title": "Sharpe Ratio", "ylabel": "Annualized Sharpe Ratio", "fmt": lambda h: f"{h:.2f}",
         "rec": [rec[m].mean() / rec[m].std() * np.sqrt(12) for m in methods],
         "exp": [exp[m].mean() / exp[m].std() * np.sqrt(12) for m in methods]},
        {"title": "Mean Return", "ylabel": "Annualized Mean Return (%)", "fmt": lambda h: f"{h:.1f}",
         "rec": [rec[m].mean() * 12 * 100 for m in methods],
         "exp": [exp[m].mean() * 12 * 100 for m in methods]},
        {"title": "Volatility", "ylabel": "Annualized Volatility (%)", "fmt": lambda h: f"{h:.1f}",
         "rec": [rec[m].std() * np.sqrt(12) * 100 for m in methods],
         "exp": [exp[m].std() * np.sqrt(12) * 100 for m in methods]},
    ]
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    x = np.arange(len(methods)); width = 0.38
    colors = [get_method_color(m) for m in methods]
    for ax, panel in zip(axes, panels):
        ax.bar(x - width / 2, panel["rec"], width, color=colors, edgecolor="black", linewidth=0.8, hatch="//")
        ax.bar(x + width / 2, panel["exp"], width, color=colors, edgecolor="black", linewidth=0.8)
        ax.set_title(panel["title"], fontsize=14, fontweight="bold")
        ax.set_ylabel(panel["ylabel"], fontsize=13)
        ax.set_xticks(x); ax.set_xticklabels(methods, fontsize=11)
        ax.tick_params(axis="y", labelsize=11)
        ax.grid(axis="y", alpha=0.3, linestyle="--"); ax.set_axisbelow(True)
        all_vals = panel["rec"] + panel["exp"]
        y_min, y_max = min(min(all_vals), 0), max(all_vals)
        pad = (y_max - y_min) * 0.18
        ax.set_ylim(y_min - (pad if y_min < 0 else 0), y_max + pad)
        offset = (y_max - y_min) * 0.03
        for bars in [ax.containers[0], ax.containers[1]]:
            for bar in bars:
                h = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., h + (offset if h >= 0 else -offset),
                        panel["fmt"](h), ha="center", va="bottom" if h >= 0 else "top", fontsize=9)
    rec_patch = mpatches.Patch(facecolor="gray", edgecolor="black", hatch="//", label="Recession")
    exp_patch = mpatches.Patch(facecolor="gray", edgecolor="black", label="Expansion")
    fig.legend(handles=[rec_patch, exp_patch], fontsize=12, framealpha=0.9,
               loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=2)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    save(save_folder + "recession_panels.jpg" if save_folder else None)


def plot_non_zero_pcs(non_zero_pcs, save_fig=None):
    """Time series of #non-zero PCs retained by lasso, UPSA and Ridge stacked."""
    cols = [c for c in ["UPSA", "Ridge"] if c in non_zero_pcs.columns]
    fig, axes = plt.subplots(len(cols), 1, figsize=(8, 4 * len(cols)), sharex=True)
    if len(cols) == 1:
        axes = [axes]
    for ax, col in zip(axes, cols):
        ax.plot(non_zero_pcs.index, non_zero_pcs[col].values, linewidth=2.5, color=get_method_color(col))
        ax.set_ylabel("Non-Zero PCs", fontsize=14)
        ax.set_title(col, fontsize=14)
        ax.tick_params(labelsize=12)
        ax.grid(alpha=0.3, linestyle="--")
        ax.set_ylim(0, non_zero_pcs[cols].max().max() * 1.05)
    plt.tight_layout()
    save(save_fig)


def plot_lasso_comparison_bar(opt_port_base, opt_port_lasso, save_fig):
    methods = [m for m in ["UPSA", "Ridge"]
               if m in opt_port_base.columns and m in opt_port_lasso.columns]
    idx = opt_port_base.index.intersection(opt_port_lasso.index)
    base, lasso = opt_port_base.loc[idx], opt_port_lasso.loc[idx]
    bl, bv, bc, bh = [], [], [], []
    for m in methods:
        c = get_method_color(m)
        bl.append(m); bv.append(sharpe(base[[m]]).values[0]); bc.append(c); bh.append("")
        bl.append(f"{m}+Lasso"); bv.append(sharpe(lasso[[m]]).values[0]); bc.append(c); bh.append("//")
    x = np.arange(len(bl))
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(x, bv, edgecolor="black", linewidth=0.8)
    for bar, c, h in zip(bars, bc, bh):
        bar.set_facecolor(c)
        if h:
            bar.set_hatch(h); bar.set_alpha(0.7)
    for bar, val in zip(bars, bv):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{val:.2f}", ha="center", va="bottom", fontsize=11)
    ax.set_ylabel("Annualized Sharpe Ratio", fontsize=14)
    ax.set_xticks(x); ax.set_xticklabels(bl, fontsize=12)
    ax.set_ylim(0, max(bv) * 1.15)
    ax.grid(alpha=0.3, linestyle="--", axis="y"); ax.set_axisbelow(True)
    fig.tight_layout()
    save(save_fig)


def plot_grid_size(grid_one, save_fig=None):
    """OOS Sharpe (UPSA & Ridge) vs number of grid points, one grid type.
    Matches the manuscript: 'Sharpe Ratio' / 'Number of Grid Points' (no $L$),
    integer x-ticks at every other point."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(grid_one["n"], grid_one["sharpe_upsa"], label="UPSA",
            color=get_method_color("UPSA"), linewidth=2.5, marker="o", markersize=4)
    ax.plot(grid_one["n"], grid_one["sharpe_ridge"], label="Ridge",
            color=get_method_color("Ridge"), linewidth=2.5, marker="s", markersize=4)
    ax.set_xlabel("Number of Grid Points", fontsize=14)
    ax.set_ylabel("Sharpe Ratio", fontsize=14)
    ax.set_xticks(list(grid_one["n"])[::2])
    ax.tick_params(labelsize=12)
    ax.legend(fontsize=12, framealpha=0.9)
    ax.grid(alpha=0.3, linestyle="--")
    plt.tight_layout()
    save(save_fig)


def plot_grid_turnover(grid_one, save_fig=None):
    """Mean turnover (%) (UPSA & Ridge) vs number of grid points, one grid type.
    Matches the manuscript: 'Turnover (%)' / 'Number of Grid Points' (no $L$),
    integer x-ticks at every other point."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(grid_one["n"], grid_one["turnover_upsa"], label="UPSA",
            color=get_method_color("UPSA"), linewidth=2.5, marker="o", markersize=4)
    ax.plot(grid_one["n"], grid_one["turnover_ridge"], label="Ridge",
            color=get_method_color("Ridge"), linewidth=2.5, marker="s", markersize=4)
    ax.set_xlabel("Number of Grid Points", fontsize=14)
    ax.set_ylabel("Turnover (%)", fontsize=14)
    ax.set_xticks(list(grid_one["n"])[::2])
    ax.tick_params(labelsize=12)
    ax.legend(fontsize=12, framealpha=0.9)
    ax.grid(alpha=0.3, linestyle="--")
    plt.tight_layout()
    save(save_fig)


def plot_is_vs_oos(perf, save_fig=None):
    """In-sample vs out-of-sample Sharpe across complexity c=N/T (Fig. is-oos)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(perf.index, perf["In-sample"], color="#C85200", linewidth=2.5, label="In-sample")
    ax.plot(perf.index, perf["Out-of-sample"], color="#006BA4", linewidth=2.5, label="Out-of-sample")
    ax.fill_between(perf.index, perf["Out-of-sample"], perf["In-sample"], alpha=0.15, color="gray")
    ax.set_ylabel("Sharpe Ratio", fontsize=14)
    ax.set_xlabel(r"$c = N / T$", fontsize=14)
    ax.tick_params(axis="both", labelsize=12)
    ax.legend(fontsize=12, loc="upper left", framealpha=0.9)
    ax.grid(alpha=0.3, linestyle="--")
    ax.set_xlim(perf.index.min(), perf.index.max())
    plt.tight_layout()
    save(save_fig)


def plot_lasso_turnover(vanilla_weights, lasso_weights, save_dir, roll_window=12):
    """12-month rolling turnover, base vs +Lasso, one panel per method
    (Fig. lasso-turnover). Saves turnover_lasso_vs_vanilla_{upsa,ridge}.jpg."""
    from src.metrics import turnover_fun
    s = save_dir.rstrip("/") + "/"
    tv = pd.DataFrame(turnover_fun(vanilla_weights)[0])
    tl = pd.DataFrame(turnover_fun(lasso_weights)[0])
    for method in ("UPSA", "Ridge"):
        color = get_method_color(method)
        rv, rl = tv[method], tl[method]
        cv = rv.rolling(roll_window).mean().dropna()
        cl = rl.rolling(roll_window).mean().dropna()
        cidx = cv.index.intersection(cl.index)
        cv, cl = cv.loc[cidx], cl.loc[cidx]
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(cidx, cv.values, color=color, linewidth=2.5, alpha=0.85,
                label=f"{method} (mean: {rv.mean():.1f}%)")
        ax.plot(cidx, cl.values, color="grey", linewidth=2.5, alpha=0.7, linestyle=":",
                label=f"{method}+Lasso (mean: {rl.mean():.1f}%)")
        ax.fill_between(cidx, cv.values, cl.values, where=(cl.values > cv.values), alpha=0.18, color="red")
        ax.fill_between(cidx, cv.values, cl.values, where=(cl.values <= cv.values), alpha=0.18, color="green")
        ax.set_ylabel("12-Month Rolling Average Turnover (%)", fontsize=14)
        ax.tick_params(axis="both", labelsize=12)
        ax.legend(fontsize=12, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.12), framealpha=0.9)
        ax.grid(alpha=0.3, linestyle="--")
        plt.tight_layout(); plt.subplots_adjust(top=0.88)
        save(s + f"turnover_lasso_vs_vanilla_{method.lower()}.jpg")
