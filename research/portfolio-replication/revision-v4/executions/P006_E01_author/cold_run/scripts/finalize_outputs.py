"""Rename every figure and table in `outputs/figures/` from its internal
semantic name to the paper-ordered name (e.g. `is_vs_oos.jpg` →
`fig_01_is_vs_oos.jpg`), and refresh `manifest.csv` accordingly.

The plotting code keeps writing semantic names so it stays readable; this
script runs at the end of `run_all.py` to produce a single, reviewer-friendly
`outputs/figures/` folder with files in paper order.

Idempotent: re-running on an already-renamed folder is a no-op.
"""
import os
import csv
import shutil

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS = os.path.join(PKG, "outputs", "figures")
MANIFEST = os.path.join(PKG, "manifest.csv")

# (paper_num, kind, short_label, [(letter, semantic_file, slot_desc)])
ORDER = [
    # MAIN FIGURES
    ("1",  "fig", "is_vs_oos",                 [("", "is_vs_oos.jpg", "")]),
    ("2",  "fig", "cor_z",                     [("", "cor_z.jpg", "")]),
    ("3",  "fig", "sharpe_bar",                [("", "sharpe_bar.jpg", "")]),
    ("4",  "fig", "cumulative_returns_log",    [("", "cumulative_returns_log.jpg", "")]),
    ("5",  "fig", "alpha_bar",                 [("", "alpha_bar.jpg", "")]),
    ("6",  "fig", "pricingacc", [
        ("a", "fac_UPSA_scatter_plot.jpg",  "UPSA"),
        ("b", "fac_Ridge_scatter_plot.jpg", "Ridge"),
        ("c", "fac_LW_scatter_plot.jpg",    "LW"),
        ("d", "fac_PCA_scatter_plot.jpg",   "PCA"),
        ("e", "fac_FF5_scatter_plot.jpg",   "FF5"),
        ("f", "fac_CAPM_scatter_plot.jpg",  "CAPM"),
    ]),
    ("7",  "fig", "surface_bestz",             [("", "z_plot_comb.jpg", "")]),
    ("8",  "fig", "turnover_rolling",          [("", "turnover_rolling_12m.jpg", "")]),
    ("9",  "fig", "cv_prob",                   [("", "dist_upsa_vs_ridge.jpg", "")]),
    ("10", "fig", "pc_sharpe", [
        ("a", "var_pc_plot.jpg",            "Sharpe_by_PC"),
        ("b", "corr_sparse_oracle_max.jpg", "corr_oracle"),
    ]),
    ("11", "fig", "shrinkage_mechanism",       [("", "nls_eigenvalues.jpg", "")]),
    ("12", "fig", "theme_panel",               [("", "theme_allocation_panel.jpg", "")]),
    ("13", "fig", "theme_shapley",             [("", "theme_shapley.jpg", "")]),
    ("14", "fig", "ridge_vs_lw", [
        ("a", "sim_econstat_eigs.jpg",    "eigs"),
        ("b", "sim_econstat_scatter.jpg", "scatter"),
    ]),
    ("15", "fig", "sim_upsa_ridge", [
        ("a", "sim_upsaridge_eigs.jpg",    "eigs"),
        ("b", "sim_upsaridge_scatter.jpg", "scatter"),
    ]),
    ("16", "fig", "tv_scatter", [
        ("a", "tv_scatter_sr.jpg",       "Sharpe"),
        ("b", "tv_scatter_turnover.jpg", "Turnover"),
    ]),
    # APPENDIX FIGURES
    ("A1",  "fig", "grid_size", [
        ("a", "grid_size_fixed.jpg", "fixed"),
        ("b", "grid_size_eig.jpg",   "eig"),
    ]),
    ("A2",  "fig", "grid_turnover", [
        ("a", "grid_turnover_fixed.jpg", "fixed"),
        ("b", "grid_turnover_eig.jpg",   "eig"),
    ]),
    ("A3",  "fig", "lasso_comparison_bar",     [("", "lasso_comparison_bar.jpg", "")]),
    ("A4",  "fig", "non_zero_pcs",             [("", "non_zero_pcs_ts.jpg", "")]),
    ("A5",  "fig", "lasso_turnover", [
        ("a", "turnover_lasso_vs_vanilla_upsa.jpg",  "vs_UPSA"),
        ("b", "turnover_lasso_vs_vanilla_ridge.jpg", "vs_Ridge"),
    ]),
    ("A6",  "fig", "pc_sharpe_sr", [
        ("a", "sr_pc_plot.jpg",                "Sharpe_by_PC"),
        ("b", "corr_sparse_oracle_sr_max.jpg", "corr_oracle"),
    ]),
    ("A7",  "fig", "sharpe_other_benchmarks",  [("", "sharpe_other_benchmarks.jpg", "")]),
    ("A8",  "fig", "sharpe_size", [
        ("a", "sharpe_full_sample_mega.jpg",  "mega"),
        ("b", "sharpe_full_sample_large.jpg", "large"),
        ("c", "sharpe_full_sample_small.jpg", "small"),
    ]),
    ("A9",  "fig", "alpha_size", [
        ("a", "alpha_full_sample_mega.jpg",  "mega"),
        ("b", "alpha_full_sample_large.jpg", "large"),
        ("c", "alpha_full_sample_small.jpg", "small"),
    ]),
    ("A10", "fig", "sharpe_rolling", [
        ("a", "sharpe_full_sample_rw60.jpg",  "rw60"),
        ("b", "sharpe_full_sample_rw240.jpg", "rw240"),
        ("c", "sharpe_full_sample_rw360.jpg", "rw360"),
    ]),
    ("A11", "fig", "alpha_rolling", [
        ("a", "alpha_full_sample_rw60.jpg",  "rw60"),
        ("b", "alpha_full_sample_rw240.jpg", "rw240"),
        ("c", "alpha_full_sample_rw360.jpg", "rw360"),
    ]),
    ("A12", "fig", "beta_scatter", [
        ("a", "beta_ins_sec_UPSA_scatter_plot.jpg",  "UPSA"),
        ("b", "beta_ins_sec_Ridge_scatter_plot.jpg", "Ridge"),
        ("c", "beta_ins_sec_LW_scatter_plot.jpg",    "LW"),
        ("d", "beta_ins_sec_PCA_scatter_plot.jpg",   "PCA"),
        ("e", "beta_ins_sec_FF5_scatter_plot.jpg",   "FF5"),
        ("f", "beta_ins_sec_CAPM_scatter_plot.jpg",  "CAPM"),
    ]),
    ("A13", "fig", "recession_panels",         [("", "recession_panels.jpg", "")]),
    ("A14", "fig", "grid_robustness",          [("", "grid_robustness.jpg", "")]),
    ("A15", "fig", "tv_heatmap",               [("", "tv_heatmap.jpg", "")]),
    ("A16", "fig", "tv_turnover",              [("", "tv_turnover.jpg", "")]),
    ("A17", "fig", "tv_dist_by_regime",        [("", "tv_dist_by_regime.jpg", "")]),
    # TABLES
    ("1",   "tab", "r2_theme",                 [("", "r_2_theme.tex", "")]),
    ("A1",  "tab", "r2_theme_beta_insample_sec", [("", "r_2_theme_beta_insample_sec.tex", "")]),
]


def paper_name(num, kind, label, letter, slot, ext):
    is_app = num.startswith("A")
    n_digits = f"A{int(num[1:]):02d}" if is_app else f"{int(num):02d}"
    prefix = f"{kind}_{n_digits}"
    if letter:
        return f"{prefix}{letter}_{label}_{slot}{ext}"
    return f"{prefix}_{label}{ext}"


def finalize():
    if not os.path.isdir(FIGS):
        print(f"[finalize] {FIGS} does not exist — nothing to do.")
        return
    rows = []
    missing = []
    for num, kind, label, panels in ORDER:
        for letter, semantic, slot in panels:
            ext = os.path.splitext(semantic)[1]
            target = paper_name(num, kind, label, letter, slot, ext)
            src = os.path.join(FIGS, semantic)
            dst = os.path.join(FIGS, target)
            if os.path.exists(src) and src != dst:
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.move(src, dst)
            if not os.path.exists(dst):
                missing.append(semantic)
                continue
            is_app = num.startswith("A")
            paper_id = (f"{'Appendix ' if is_app else ''}{kind.capitalize()} "
                        f"{num}{letter}")
            rows.append({
                "paper_id": paper_id, "kind": kind, "number": num,
                "panel": letter, "label": label, "slot": slot, "file": target,
            })
    with open(MANIFEST, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["paper_id", "kind", "number",
                                          "panel", "label", "slot", "file"])
        w.writeheader()
        w.writerows(rows)
    print(f"[finalize] {len(rows)} outputs in {FIGS} (paper order)")
    print(f"[finalize] manifest -> {MANIFEST}")
    if missing:
        print(f"[finalize] WARNING: {len(missing)} expected outputs missing:")
        for m in missing:
            print(f"  {m}")


if __name__ == "__main__":
    finalize()
