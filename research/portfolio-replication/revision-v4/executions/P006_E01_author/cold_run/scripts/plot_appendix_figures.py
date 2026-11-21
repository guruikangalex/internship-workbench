"""Draw appendix figures. PC-Sharpe-sorted, beta-pricing and recession panels
come from the main engine bundle; the robustness bars, lasso figures and
benchmark bar are drawn when their (heavy, --compute) bundles are present."""
import os
import sys
import pickle

import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from src.data import load_panel
from src import plotting as P
from src import pricing
from src import tables

SIZE_KEYS = ["robust_mega", "robust_large", "robust_small"]
RW_KEYS = ["robust_rw60", "robust_rw240", "robust_rw360"]


def plot_appendix(appx, factors, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    s = save_dir.rstrip("/") + "/"
    main = appx["main"]
    opt = main["opt_port"]

    # PC performance, Sharpe-sorted (Fig. pc-sharpe-sr).
    # Use the shared y-axis range computed in plot_main so var/sharpe-sorted
    # panels are directly comparable (matches the original figure styling).
    pc_ylim = main.get("_pc_ylim")
    if pc_ylim is None:
        import numpy as np
        from src.metrics import sharpe
        all_sr = np.concatenate([sharpe(main["pc_perf"][k][c]).values
                                 for k in ("variance", "sharpe")
                                 for c in main["pc_perf"][k]])
        sr_min, sr_max = np.nanmin(all_sr), np.nanmax(all_sr)
        sr_buffer = 0.05 * (sr_max - sr_min) if sr_max != sr_min else 0.1
        pc_ylim = (max(1.0, sr_min - sr_buffer), sr_max + sr_buffer)
    P.plot_pc_sharpe(main["pc_perf"]["sharpe"], save_folder=s + "sr_pc_plot.jpg", ylim=pc_ylim)
    P.plot_corr_sparse_oracle_joint(main["pc_perf"]["sharpe"],
                                    save_folder=s + "corr_sparse_oracle_sr_max.jpg")

    # Beta-based pricing accuracy (Fig. beta-scatter) + R^2 table
    realized, predicted = pricing.beta_predicted_realized(opt, main["betas_insample_sec"], factors)
    P.pe_scatter_plot_beta(realized, predicted, savefolder=s + "beta_ins_sec_")
    tables.write_r2_beta_sec_table(opt, main["betas_insample_sec"], factors, save_dir)

    # Business-cycle panels (Fig. recession-panels)
    P.plot_recession_panels(opt, save_folder=s)

    # Robustness bars (only if computed)
    rob = appx.get("robustness", {})
    # FF5 and CAPM are NOT re-estimated within size groups — they remain the
    # full-market benchmarks (identical across mega/large/small). Showing them
    # next to the size-specific UPSA/Ridge/LW/PCA bars would be misleading, so
    # drop them from the size-group figures (Fig. sharpe-size / alpha-size).
    # The rolling-window robustness figures use the full universe, where FF5
    # and CAPM are valid, so they keep all methods.
    SIZE_DROP = ["FF5", "CAPM"]
    for key in SIZE_KEYS + RW_KEYS:
        b = rob.get(key)
        if b is None:
            continue
        tag = key.replace("robust_", "")
        op = b["opt_port"]
        if key in SIZE_KEYS:
            op = op.drop(columns=[c for c in SIZE_DROP if c in op.columns])
        P.plot_sharpe_ratios_full_sample(op, save_fig=s + f"sharpe_full_sample_{tag}.jpg")
        P.plot_alpha_full_sample(op, save_fig=s + f"alpha_full_sample_{tag}.jpg")

    # Lasso figures (Fig. lasso-comparison-bar, non-zero-pcs)
    lasso = appx.get("lasso")
    if lasso is not None:
        P.plot_lasso_comparison_bar(opt, lasso["opt_port"], save_fig=s + "lasso_comparison_bar.jpg")
        P.plot_non_zero_pcs(lasso["non_zero_pcs"], save_fig=s + "non_zero_pcs_ts.jpg")
        P.plot_lasso_turnover(main["weights"], lasso["weights"], save_dir)

    # Grid-size sensitivity (Fig. grid-size, grid-turnover)
    grid = appx.get("grid_size")
    if grid is not None:
        P.plot_grid_size(grid["fixed"], save_fig=s + "grid_size_fixed.jpg")
        P.plot_grid_size(grid["eig"], save_fig=s + "grid_size_eig.jpg")
        P.plot_grid_turnover(grid["fixed"], save_fig=s + "grid_turnover_fixed.jpg")
        P.plot_grid_turnover(grid["eig"], save_fig=s + "grid_turnover_eig.jpg")

    # Other benchmarks bar (Fig. sharpe-bench): UPSA + KNS + PCA SR
    ob = appx.get("other_benchmarks")
    if ob is not None:
        idx = opt.index.intersection(ob["opt_port"].index)
        combined = pd.DataFrame(index=idx)
        combined["UPSA"] = opt.loc[idx, "UPSA"]
        for c in ob["opt_port"].columns:
            combined[c] = ob["opt_port"].loc[idx, c]
        P.plot_sharpe_ratios_bar(combined, save_fig=s + "sharpe_other_benchmarks.jpg")

    missing = [k for k in SIZE_KEYS + RW_KEYS if rob.get(k) is None]
    missing += [k for k in ["lasso", "other_benchmarks"] if appx.get(k) is None]
    if missing:
        print(f"[appendix] not cached: {', '.join(missing)} — run "
              f"`python run_all.py --appendix --compute` to generate.")
    print(f"appendix figures written to {save_dir}")


if __name__ == "__main__":
    from scripts.compute_appendix_figures import compute_appendix
    appx = compute_appendix(force=False)
    plot_appendix(appx, load_panel("factors_main"), HERE + "/outputs/figures")
