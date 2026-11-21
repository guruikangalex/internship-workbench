"""Draw the main-text empirical figures from the computed engine bundle."""
import os
import sys
import pickle
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from src.data import load_panel
from src import plotting as P
from src import pricing
from src import themes
from src import tables
from src.constants import JKP_CLUSTERS

Z_GRID = np.logspace(-10, -1, 10)


def plot_main(bundle, factors, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    s = save_dir.rstrip("/") + "/"
    opt = bundle["opt_port"]

    P.plot_corr_matrix(bundle["opt_port_z"], save_folder=s + "cor_z.jpg")
    P.plot_sharpe_ratios_bar(opt, save_fig=s + "sharpe_bar.jpg")
    P.cumulative_returns_plot(opt, savefolder=s, agg_type="log")
    P.plot_alpha_bar(opt, save_fig=s + "alpha_bar.jpg")

    realized, predicted = pricing.sdf_predicted_realized(opt, factors, scaling=True)
    P.pe_scatter_plot(realized, predicted, savefolder=s + "fac_")

    P.combined_surface_with_time_overlay(bundle["z_grid_weights"], Z_GRID,
                                         bundle["best_z"], save_folder=s + "z_plot_comb.jpg")
    P.dist_plot(bundle["best_z"], bundle["z_grid_weights"], Z_GRID, save_folder=s + "dist_upsa_vs_ridge.jpg")
    P.turnover_rolling_plot(bundle["weights"], save_fig=s + "turnover_rolling_12m.jpg")

    # Shared y-axis across var- and sharpe-sorted PC panels (matches original).
    from src.metrics import sharpe
    all_sr = np.concatenate([sharpe(bundle["pc_perf"][k][c]).values
                             for k in ("variance", "sharpe")
                             for c in bundle["pc_perf"][k]])
    sr_min, sr_max = np.nanmin(all_sr), np.nanmax(all_sr)
    sr_buffer = 0.05 * (sr_max - sr_min) if sr_max != sr_min else 0.1
    pc_ylim = (max(1.0, sr_min - sr_buffer), sr_max + sr_buffer)

    P.plot_pc_sharpe(bundle["pc_perf"]["variance"], save_folder=s + "var_pc_plot.jpg", ylim=pc_ylim)
    P.plot_corr_sparse_oracle_joint(bundle["pc_perf"]["variance"], save_folder=s + "corr_sparse_oracle_max.jpg")
    bundle["_pc_ylim"] = pc_ylim   # share with appendix plotter
    P.nls_function_plot(bundle["eigenvalues"], save_folder=s + "nls_eigenvalues.jpg")

    themes.theme_allocation_panel_plot(bundle["weights"], factors, JKP_CLUSTERS,
                                       save_folder=s + "theme_allocation_panel.jpg")
    themes.theme_shapley_plot(bundle["weights"], factors, JKP_CLUSTERS,
                              save_folder=s + "theme_shapley.jpg")

    P.plot_is_vs_oos(bundle["is_vs_oos"], save_fig=s + "is_vs_oos.jpg")
    tables.write_r2_theme_table(opt, factors, save_dir)
    print(f"main figures written to {save_dir}")


if __name__ == "__main__":
    with open(HERE + "/outputs/computed/main_bundle.p", "rb") as f:
        bundle = pickle.load(f)
    factors = load_panel("factors_main")
    plot_main(bundle, factors, HERE + "/outputs/figures")
