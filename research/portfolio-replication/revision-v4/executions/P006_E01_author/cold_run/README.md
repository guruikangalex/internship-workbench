# Replication Package for "Universal Portfolio Shrinkage"

Review of Financial Studies, MS 20240297.
Authors: Bryan Kelly, Semyon Malamud, Mo Pourmohammadi, and Fabio Trojani.
Corresponding author: Mo Pourmohammadi (mopour97@gmail.com).

This README follows the Social Science Data Editors template
(<https://social-science-data-editors.github.io/template_README/>).

## Overview

This package reproduces every figure and the two $R^2$-by-theme tables in the
paper from the processed factor-return panels in `data/processed_inputs/`. A
single entry point, `run_all.py`, supports two workflows:

- **Default (verification):** `python run_all.py --all` redraws all figures and
  tables from the numerical bundles shipped in `outputs/computed/`. This is the
  fast path to check that the outputs match the paper.
- **Full recomputation:** `python run_all.py --all --compute` recomputes every
  numerical object — estimators (UPSA, ridge, Ledoit–Wolf, PCA, KNS, lasso),
  portfolio returns, Sharpe ratios, alphas, turnover, PC diagnostics, theme
  decompositions, and the three simulation studies — from the input CSVs, and
  then draws the figures and tables.

Both workflows write all 59 figures and 2 LaTeX tables to a single folder,
`outputs/figures/`, with filenames in paper order (`fig_01_…`, …, `fig_A17_…`,
`tab_01_…`, `tab_A01_…`). A full recomputation takes **≈ 25–35 minutes on a
12-core machine** (longer on fewer cores).

## Data Availability and Provenance Statements

### Statement about rights

The package contains only processed factor-return series from public sources
and no proprietary raw micro-data. The included series are derived returns, not
the underlying micro-data, and are redistributed in accordance with the terms of
their original public sources (listed below).

### License for the data and code

The package (code and included processed data) is released under the
**BSD 3-Clause License** (see `LICENSE`).

### Summary of availability

All data used in this package are publicly available and are included in
`data/processed_inputs/` as CSV files, so the code can be run directly without
obtaining any additional data.

### Details on each data source

1. **JKP factor returns** — `data/processed_inputs/factors_main.csv`
   (153 factors, monthly, value-weighted, cap universe; 1971-11 to 2022-12).
   Source: the Global Factor Data of Jensen, Kelly, and Pedersen,
   <https://jkpfactors.com>. Publicly available; provided here as the processed
   monthly factor-return panel.
   Citation: Jensen, Theis Ingerslev, Bryan Kelly, and Lasse Heje Pedersen. 2023.
   "Is There a Replication Crisis in Finance?" *Journal of Finance* 78(5):
   2465–2518. <https://doi.org/10.1111/jofi.13249>. Accessed 2023-06-30.

2. **Fama–French 5 factors + momentum + market** —
   `data/processed_inputs/benchmark.csv` (1963-07 to 2024-12).
   Source: Kenneth R. French Data Library,
   <https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html>.
   Publicly available; provided here as the processed benchmark-factor panel.

3. **Within-size-group factors** — `data/processed_inputs/factors_{mega,large,small}.csv`
   (monthly, 1971-11 to 2022-12). Constructed by the authors from the JKP
   characteristic/return data (source 1), split into size groups. Provided here
   as the processed within-size factor-return panels; the raw CRSP/Compustat
   micro-data are neither redistributed nor required. See the paper's Online
   Appendix, "Data and Replication Details," for the construction.

The CSVs were exported with `%.17g` formatting and are read back with pandas
`float_precision="round_trip"`, so the values are bit-for-bit identical to the
source series (`scripts/export_inputs.py`).

### Dataset list

| Data file | Source | Provided | Notes |
|---|---|---|---|
| `data/processed_inputs/factors_main.csv` | JKP (jkpfactors.com) | Yes | 153 factors, vw-cap, monthly |
| `data/processed_inputs/benchmark.csv` | Ken French Data Library | Yes | FF5 + mom + mkt |
| `data/processed_inputs/factors_mega.csv` | Authors (from JKP) | Yes | mega-cap size group |
| `data/processed_inputs/factors_large.csv` | Authors (from JKP) | Yes | large-cap size group |
| `data/processed_inputs/factors_small.csv` | Authors (from JKP) | Yes | small-cap size group |

## Computational requirements

### Software

- **Python 3.9.6.**
- Python packages (exact versions in `requirements.txt`): numpy 2.0.2,
  pandas 2.3.3, scipy 1.13.1, scikit-learn 1.6.1, statsmodels 0.14.6,
  cvxopt 1.3.3, matplotlib 3.9.4, seaborn 0.13.2, tqdm 4.67.3.
- Install: `python -m pip install -r requirements.txt`.

### Controlled randomness

All randomness is seeded, so results are deterministic and independent of the
number of CPU cores used:

- The rolling-window estimation engine and the lasso / KNS / PCA benchmarks are
  fully deterministic (no RNG; `sklearn.KFold(shuffle=False)`).
- In/OOS complexity figure (`src/portfolios.py::run_is_vs_oos`): `np.random.seed(0)`.
- Simulations (`src/simulations.py`): each draw sets `np.random.seed(seed)` with
  `seed` equal to its index (`0 … sims-1`).

### Memory, runtime, and storage

- Tested on macOS (Apple Silicon, 12 cores), Python 3.9.6.
- Peak memory: ≈ 2–4 GB (the appendix step runs several estimation jobs in
  parallel).
- Runtime for `python run_all.py --all --compute` on 12 cores: **≈ 25–35 min**
  (main engine ≈ 80 s; simulations ≈ 4 min; appendix estimators ≈ 15–25 min;
  in/OOS sweep ≈ 20 s). Scales with the number of cores.
- Storage: ≈ 10 MB code + data; running the code writes caches to
  `outputs/computed/` (≈ 100 MB) and figures/tables to `outputs/figures/`
  (≈ 15 MB).

## Description of programs/code

```
run_all.py             entry point: --main / --appendix / --simulations / --all, --compute
requirements.txt       pinned dependencies
manifest.csv           one row per figure / table panel: paper number -> output filename
data/processed_inputs/ the five input CSV panels
src/
  data.py        load the processed panels (float-exact CSV read)
  upsa.py        UPSA estimator (one class, used by every figure; needs cvxopt)
  shrinkage.py   Ledoit-Wolf nonlinear & linear, PCA cross-validation
  lasso.py       PC-lasso and KNS elastic-net selection
  portfolios.py  rolling-window engine (parallel); benchmark engines; in/OOS sweep
  metrics.py     Sharpe, turnover, SDF rescaling
  pricing.py     HJ pricing errors, R^2-by-theme, theme PCs
  themes.py      thematic allocation and Shapley decomposition
  simulations.py three DGPs (structured-spectrum, grid-robustness, Markov time-varying)
  plotting.py    figure drawing
  tables.py      R^2-by-theme LaTeX tables
  style.py       method colors / save helper
  constants.py   JKP cluster map, NBER dates, pricing-error enum
scripts/
  export_inputs.py            one-time provenance: how the CSVs were exported
  compute_*_figures.py        compute + cache the numerical objects
  plot_*_figures.py           draw the figures/tables
  finalize_outputs.py         rename outputs to paper-ordered names + write manifest.csv
outputs/computed/  numerical bundles (shipped manuscript-era caches; also written by --compute)
outputs/figures/   all figures (.jpg) + tables (.tex), paper-ordered
```

## Instructions to replicators

### Where to find the outputs

All figures and tables land as single files in `outputs/figures/`, named in
paper order:

```
outputs/figures/
  fig_01_is_vs_oos.jpg           <- Figure 1
  fig_02_cor_z.jpg               <- Figure 2
  ...
  fig_06a_pricingacc_UPSA.jpg    <- Figure 6, panel (a)
  ...
  fig_A17_tv_dist_by_regime.jpg  <- Appendix Figure A.17
  tab_01_r2_theme.tex            <- Table 1
  tab_A01_r2_theme_beta_insample_sec.tex  <- Appendix Table A.1
```

A directory listing sorts in paper order. `manifest.csv` at the repo root is the
canonical `paper_id → filename` index (61 entries).

### Default run (redraw from shipped bundles)

```bash
python -m pip install -r requirements.txt
python run_all.py --all
```

Redraws all figures and tables from the shipped bundles
`outputs/computed/main_bundle.p` and `sim_bundle.p`, and writes
`outputs/figures/` in paper order. This reproduces the manuscript figures and
tables.

### Full recomputation from inputs

```bash
python -m pip install -r requirements.txt
python run_all.py --all --compute
```

Recomputes every numerical object from `data/processed_inputs/`, then draws the
figures and tables. The recomputed main-engine bundle is written to
`outputs/computed/main_bundle_regen.p` (the shipped manuscript-era bundle is
preserved as `main_bundle.p`). See the **Reproducibility note** below.

To run a subset: `python run_all.py --main`, `--appendix`, or `--simulations`
(append `--compute` to recompute that subset). Every form finalises the
paper-ordered `outputs/figures/`.

## List of figures and tables

`manifest.csv` is the canonical index: one row per paper panel (61 rows =
16 main figures + 17 appendix figures + 2 tables, expanded across multi-panel
subfigures), with columns `paper_id, kind, number, panel, label, slot, file`.
The `file` column gives the paper-ordered filename under `outputs/figures/`.
Representative entries:

| Paper item | Output filename | Computed by | Drawn by |
|---|---|---|---|
| Figure 1 (in/OOS Sharpe) | `fig_01_is_vs_oos.jpg` | `portfolios.run_is_vs_oos` | `plotting.plot_is_vs_oos` |
| Figure 3 (Sharpe bars) | `fig_03_sharpe_bar.jpg` | `portfolios.run_rolling_window` | `plotting.plot_sharpe_ratios_bar` |
| Figure 6 (pricing-acc panels) | `fig_06{a..f}_pricingacc_*.jpg` | `pricing.sdf_predicted_realized` | `plotting.pe_scatter_plot` |
| Table 1 (SDF $R^2$) | `tab_01_r2_theme.tex` | `pricing.r_2_table_gen` | `tables.write_r2_theme_table` |
| Figures 14–15 (cross-sim) | `fig_14{a,b}_*.jpg`, `fig_15{a,b}_*.jpg` | `simulations.run_cross_sim` | `scripts/plot_simulations.py` |
| Figure 16 (time-varying) | `fig_16{a,b}_tv_scatter_*.jpg` | `simulations.run_time_varying` | `scripts/plot_simulations.py` |
| Appendix Figures A.15–A.17 (TV diagnostics) | `fig_A15_*`, `fig_A16_*`, `fig_A17_*` | `simulations.run_time_varying` | `scripts/plot_simulations.py` |

## Reproducibility note

The default `python run_all.py --all` redraws every figure and table from the
shipped manuscript-era bundles (`outputs/computed/main_bundle.p` and
`sim_bundle.p`) and reproduces the manuscript outputs.

`python run_all.py --all --compute` instead recomputes every numerical object
from `data/processed_inputs/`. The recomputed results match the manuscript up to
numerical precision for Ridge, PCA, FF5, CAPM, and all simulations. A small
library-version sensitivity remains in the Ledoit–Wolf benchmark and in a few
rounding-boundary UPSA cells of the pricing-accuracy tables (Table 1 and
Appendix Table A.1): the LW cells move by at most ~0.1–0.2 in $R^2$, and, for
example, the Table 1 "All"-row UPSA $R^2$ recomputes to 0.6649 (rounds to 0.66)
versus 0.6652 (rounds to 0.67) in the manuscript. No sign, ranking, or
conclusion changes. For this reason the shipped `main_bundle.p` is the
manuscript-era bundle (so the default run reproduces these tables exactly), and
the recomputed bundle is shipped alongside as `main_bundle_regen.p` for direct
comparison.

The size-group figures (Figures 24 and 25) omit the FF5 and CAPM bars, which are
not re-estimated within size groups and are therefore not comparable to the
size-specific UPSA/Ridge/LW/PCA results.

## Acknowledgements

Semyon Malamud gratefully acknowledges the financial support of the Swiss
National Science Foundation (Grant 100018-228042) and the Swiss Finance
Institute. AQR Capital Management is a global investment management firm that
may or may not apply similar investment techniques or methods of analysis as
described herein. The views expressed here are those of the authors and not
necessarily those of AQR.

## References

- Jensen, Theis Ingerslev, Bryan Kelly, and Lasse Heje Pedersen. 2023. "Is There
  a Replication Crisis in Finance?" *Journal of Finance* 78(5): 2465–2518.
  <https://doi.org/10.1111/jofi.13249>.
- Fama, Eugene F., and Kenneth R. French. Factor data from the Kenneth R. French
  Data Library, Tuck School of Business, Dartmouth College.
