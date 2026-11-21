"""Simulation DGPs and estimators behind the simulation figures.

Faithful to simulation/ridge vs upsa.py and upsa_grid_robustness.py, with two
deliberate choices:

* The UPSA ensemble uses the CONSTRAINED (non-negative) loadings everywhere.
  The original sim *code* had drifted to the unconstrained loadings, which go
  negative in ~2% of seeds and make the implied shrinkage curve heavy-tailed
  (14x rougher) — that is the source of the "jitter". The published figure is
  smooth, i.e. it used the constrained loadings, which also match the empirical
  pipeline. So we use `get_upsa_weights()` / `self.upsa` (constrained).

* Seeds are embarrassingly parallel, so the heavy "from scratch" runs use a
  process pool (n_jobs). Each seed sets its own RNG, so results are independent
  of n_jobs.
"""
import os
# Limit BLAS threads per worker (spawned workers re-import this module, so these
# take effect before numpy is imported there) to avoid CPU oversubscription.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.upsa import UPSA
from src.shrinkage import do_lw, do_lw_linear

CURVE_COLS = ["Empirical", "UPSA", "LW", "Ridge Statistical", "Ridge Economic"]


def sim_sharpe(ret):
    """Second-moment Sharpe: mean / sqrt(mean of squares).

    Used by the *time-varying* simulation (Fig. 16 / tv_*), faithful to
    ``time_varying_server.py::sharpe_scalar``.
    """
    return np.mean(ret, axis=0) / np.sqrt(np.mean(ret ** 2, axis=0))


def sim_sharpe_std(ret):
    """Standard Sharpe: mean / std.

    Used by the *cross-sim* and grid-robustness studies (Fig. 14-15 / sim_*),
    faithful to ``simulation_server.py::sharpe_scalar`` and
    ``upsa_grid_robustness.py``. The two simulation families deliberately use
    different Sharpe conventions in the paper; mixing them up shifts the
    cross-sim averages down by ~0.02 (mean/RMS <= mean/std).
    """
    s = np.std(ret, axis=0)
    return np.mean(ret, axis=0) / np.where(s > 0, s, np.nan)


def trim_eigs(eigenvalues, perct=0):
    return eigenvalues[int(perct * len(eigenvalues)):int((1 - perct) * len(eigenvalues))]


def default_dgp(p_=150):
    """Three-regime eigenvalue spectrum and mean vector from 'ridge vs upsa.py'."""
    frac, frac_2 = 0.1, 0.8
    psis = np.array([0.1, 1, 10])
    psi_eig = np.append(psis[0] * np.ones(int(p_ * frac)), psis[1] * np.ones(int(p_ * frac_2)))
    psi_eig = np.append(psi_eig, psis[2] * np.ones(int(p_ * (1 - frac - frac_2))))
    mu = np.array([0.5, 0, 1])
    lam = np.append(mu[0] * np.ones(int(p_ * frac)), mu[1] * np.ones(int(p_ * frac_2)))
    lam = np.append(lam, mu[2] * np.ones(int(p_ * (1 - frac - frac_2))))
    lam = lam / np.sqrt(p_)
    if len(psi_eig) != p_:
        psi_eig = np.append(psi_eig, [psis[2]] * (p_ - len(psi_eig)))
        lam = np.append(lam, [mu[2]] * (p_ - len(lam)))
    return psi_eig, lam, psis, mu


def simulate(psi_eig, lam, t_=600, seed=0, p_=150):
    np.random.seed(seed)
    noise = (psi_eig.reshape(1, -1) ** 0.5) * np.random.randn(t_, p_)
    return lam.reshape(1, -1) + noise


# ───────────────────────────── cross-sim (parallel) ─────────────────────────────
def _cross_one(seed, psi_eig, lam, z, t_, p_, train_frac):
    factors = simulate(psi_eig, lam, t_=t_, seed=seed, p_=p_)
    n = int(factors.shape[0] * train_frac)
    f_train, f_test = factors[:n, :], factors[n:, :]
    u = UPSA(z_list=z.copy()).fit(returns=f_train)
    eig = u.eigenvalues

    lw_w, lw_eig = do_lw(returns=f_train, eigenvalues=eig, eigenvectors=u.eigenvectors)
    lwl_w, lwl_eig = do_lw_linear(returns=f_train, eigenvalues=eig, eigenvectors=u.eigenvectors)

    # Cross-sim uses the standard Sharpe (mean/std), matching simulation_server.py.
    perf = {
        "UPSA": sim_sharpe_std(f_test @ u.get_upsa_weights()),            # constrained
        "Ridge Economic": sim_sharpe_std(f_test @ u.get_ridge_weights()),
        "LW": sim_sharpe_std(f_test @ lw_w),
        "Ridge Statistical": sim_sharpe_std(f_test @ lwl_w),
    }

    def resc(c):
        return c * np.sum(eig) / np.sum(c)

    curves = {
        "Empirical": eig,
        "LW": resc(lw_eig),
        "Ridge Statistical": resc(lwl_eig),
        "Ridge Economic": resc(eig + z[u.best_z]),
        "UPSA": resc(1 / (u.upsa @ (1 / (eig + z.reshape(-1, 1))))),  # constrained loadings
    }
    return perf, curves


def run_cross_sim(sims=10000, t_=600, p_=150, train_frac=0.5, n_jobs=None):
    """Per-seed OOS Sharpe (UPSA/Ridge Economic/LW/Ridge Statistical) and the
    average implied shrinkage curves. Returns (perf, eigenvalues_all)."""
    psi_eig, lam, _, _ = default_dgp(p_)
    z = np.logspace(-4, 4, 9)   # FIGURE_L = 9 (simulation_server.py), not 2
    n_jobs = n_jobs or os.cpu_count()
    n_eig = min(p_, int(t_ * train_frac))
    work = partial(_cross_one, psi_eig=psi_eig, lam=lam, z=z, t_=t_, p_=p_, train_frac=train_frac)

    perf_rows = []
    curve_sum = {c: np.zeros(n_eig) for c in CURVE_COLS}
    with Pool(n_jobs) as pool:
        for perf, curves in tqdm(pool.imap(work, range(sims), chunksize=20),
                                 total=sims, desc=f"cross sim (n_jobs={n_jobs})"):
            perf_rows.append(perf)
            for c in CURVE_COLS:
                curve_sum[c] += curves[c]
    perf = pd.DataFrame(perf_rows)
    eigenvalues_all = pd.DataFrame({c: curve_sum[c] / sims for c in CURVE_COLS},
                                   index=np.arange(1, n_eig + 1))
    return perf, eigenvalues_all


# ───────────────────────────── grid robustness (parallel) ─────────────────────────────
def _grid_one(seed, psi_eig, lam, t_, p_, train_frac, grid_sizes, eig_range):
    factors = simulate(psi_eig, lam, t_=t_, seed=seed, p_=p_)
    n = int(factors.shape[0] * train_frac)
    f_train, f_test = factors[:n, :], factors[n:, :]
    ref_eigs = UPSA(z_list=np.logspace(-10, -1, 10)).fit(returns=f_train).eigenvalues
    out = {"Fixed": {}, "Eigenvalue-based": {}}
    for L in grid_sizes:
        grids = {"Fixed": np.logspace(-4, 4, int(L)),
                 "Eigenvalue-based": np.logspace(np.log10(np.min(ref_eigs) / eig_range),
                                                 np.log10(eig_range * np.max(ref_eigs)), int(L))}
        for name, zg in grids.items():
            w = UPSA(z_list=zg).fit(returns=f_train).get_upsa_weights()  # constrained
            r = f_test @ w
            out[name][L] = np.mean(r) / np.std(r) if np.std(r) > 0 else 0.0
    return out


def run_grid_robustness(sims=500, t_=600, p_=150, train_frac=0.5, eig_range=10, n_jobs=None):
    """Mean OOS UPSA Sharpe vs number of grid points, for a wide fixed grid and an
    eigenvalue-based grid. Returns {name: Series indexed by grid size}."""
    psi_eig, lam, _, _ = default_dgp(p_)
    grid_sizes = np.arange(1, 21, 1).astype(int)
    n_jobs = n_jobs or os.cpu_count()
    work = partial(_grid_one, psi_eig=psi_eig, lam=lam, t_=t_, p_=p_, train_frac=train_frac,
                   grid_sizes=grid_sizes, eig_range=eig_range)
    acc = {"Fixed": np.zeros(len(grid_sizes)), "Eigenvalue-based": np.zeros(len(grid_sizes))}
    with Pool(n_jobs) as pool:
        for out in tqdm(pool.imap(work, range(sims), chunksize=5),
                        total=sims, desc=f"grid robustness (n_jobs={n_jobs})"):
            for name in acc:
                acc[name] += np.array([out[name][L] for L in grid_sizes])
    return {name: pd.Series(acc[name] / sims, index=grid_sizes) for name in acc}


# ════════════════════════════ time-varying (Markov) simulation ════════════════════════════
# Paper spec, Markov switching (p_switch=0.05): UPSA adapts its ensemble each
# window while Ridge commits to one z. Faithful to simulation/time_varying_server.py.
TV_FRACS = (0.10, 0.80, 0.10)
TV_PSIS = (0.1, 1.0, 10.0)
TV_MU1 = (0.5, 0.0, 1.0)
TV_MU2 = (0.5, 0.0, 5.0)
TV_T, TV_P, TV_PSWITCH = 600, 150, 0.05
TV_REP_SEED = 8301              # paper's hand-picked representative seed (single-path figures)
_TV = {}


def simulate_time_varying(seed, t_=TV_T, p_=TV_P, p_switch=TV_PSWITCH):
    np.random.seed(seed)
    group_sizes = [int(f * p_) for f in TV_FRACS[:-1]]
    group_sizes.append(p_ - sum(group_sizes))

    def _vec(vals):
        return np.concatenate([v * np.ones(n) for v, n in zip(vals, group_sizes)])

    psi = _vec(TV_PSIS)
    lam = np.zeros((2, p_))
    lam[0] = _vec(TV_MU1) / np.sqrt(p_)
    lam[1] = _vec(TV_MU2) / np.sqrt(p_)
    states = np.zeros(t_, dtype=int)
    for t in range(1, t_):
        states[t] = 1 - states[t - 1] if np.random.rand() < p_switch else states[t - 1]
    noise = np.random.randn(t_, p_)
    factors = lam[states, :] + np.sqrt(np.stack([psi, psi])[states, :]) * noise
    return factors, states


def run_tv_rolling(factors, rolling_window, z_grid):
    """Rolling UPSA/Ridge over the time-varying path (constrained loadings)."""
    t_, p_ = factors.shape
    index_ = np.arange(rolling_window, t_)
    u_ret, r_ret, zw, bz, uw, rw_, z_out = [], [], [], [], [], [], None
    for t in range(rolling_window, t_):
        f_train = factors[t - rolling_window:t, :]
        upsa = UPSA(z_list=z_grid if isinstance(z_grid, np.ndarray) else z_grid).fit(returns=f_train)
        if z_out is None:
            z_out = upsa.z_list.copy()
        w_u, w_r = upsa.get_upsa_weights(), upsa.get_ridge_weights()
        f_oos = factors[t, :]
        u_ret.append(f_oos @ w_u); r_ret.append(f_oos @ w_r)
        zw.append(upsa.upsa.copy()); bz.append(upsa.best_z)
        uw.append(w_u); rw_.append(w_r)
    opt_port = pd.DataFrame({"UPSA": u_ret, "Ridge": r_ret}, index=index_)
    z_grid_weights = pd.DataFrame(np.array(zw), index=index_, columns=z_out)
    best_z = pd.Series(bz, index=index_)
    weights = {"UPSA": pd.DataFrame(np.array(uw), index=index_),
               "Ridge": pd.DataFrame(np.array(rw_), index=index_)}
    return opt_port, z_grid_weights, best_z, z_out, weights


def _tv_turnover(weights, factors_df=None):
    """Simple mean turnover (%) per method (no drift adjustment), clipped at
    the 99th percentile of the per-seed time series. This matches the
    manuscript's stored simulation-turnover values exactly — the original
    block files were generated by an earlier `compute_turnover(weights)`
    call (no `factors=` arg), so the drift-adjusted variant is not what the
    paper's Figure 16 / scatter plots display. `factors_df` is accepted but
    ignored for backwards-compatibility with the surrounding plumbing."""
    out = {}
    for method, w in weights.items():
        gross = w.abs().sum(axis=1)
        diff_abs_sum = w.diff().abs().sum(axis=1)
        ts = 0.5 * diff_abs_sum / gross.shift()
        ts.iloc[0] = 0.0
        out[method] = 100 * ts.clip(upper=ts.quantile(0.99)).mean()
    return out


def _tv_init(rolling_window, z_grid):
    _TV.update(rw=rolling_window, z=z_grid)


def _tv_one(seed):
    factors, states = simulate_time_varying(seed)
    opt_port, _, _, _, weights = run_tv_rolling(factors, _TV["rw"], _TV["z"])
    fdf = pd.DataFrame(factors, columns=range(factors.shape[1])).loc[weights["UPSA"].index]
    turn = _tv_turnover(weights, fdf)
    su = sim_sharpe(opt_port["UPSA"].values)
    sr = sim_sharpe(opt_port["Ridge"].values)
    return seed, su, sr, turn["UPSA"], turn["Ridge"]


def run_time_varying(sims=2000, rolling_window=300, z_grid=None, n_jobs=None):
    """Parallel multi-seed Markov-switching scan. Returns per-seed Sharpe and
    turnover DataFrames plus the full path of the representative seed (the
    paper's hand-picked seed 8301) for the heatmap / turnover / distribution
    figures.

    Paper spec: sims=10,000, rolling_window=300, and z_grid defaults to the
    fixed log-grid logspace(-4, 4, 9) (clean 10^n shrinkage labels)."""
    if z_grid is None:
        z_grid = np.logspace(-4, 4, 9)
    n_jobs = n_jobs or os.cpu_count()
    with Pool(n_jobs, initializer=_tv_init, initargs=(rolling_window, z_grid)) as pool:
        recs = list(tqdm(pool.imap_unordered(_tv_one, range(sims), chunksize=4),
                         total=sims, desc=f"time-varying (n_jobs={n_jobs})"))
    recs.sort()
    seeds = [r[0] for r in recs]
    sharpe = pd.DataFrame({"UPSA": [r[1] for r in recs], "Ridge": [r[2] for r in recs]}, index=seeds)
    turnover = pd.DataFrame({"UPSA": [r[3] for r in recs], "Ridge": [r[4] for r in recs]}, index=seeds)

    # The paper's single-path figures use a fixed hand-picked representative seed;
    # fall back to the best-scoring seed only for small test runs without it.
    score = (turnover["Ridge"] - turnover["UPSA"]) + (sharpe["UPSA"] - sharpe["Ridge"]) * 100
    best_seed = TV_REP_SEED if TV_REP_SEED in sharpe.index else int(score.idxmax())
    factors, states = simulate_time_varying(best_seed)
    opt_port, z_grid_weights, best_z, z_out, weights = run_tv_rolling(factors, rolling_window, z_grid)
    fdf = pd.DataFrame(factors, columns=range(factors.shape[1])).loc[weights["UPSA"].index]
    best = {"seed": best_seed, "states": states, "rolling_window": rolling_window,
            "z_grid": z_out, "z_grid_weights": z_grid_weights, "best_z": best_z,
            "weights": weights, "opt_port": opt_port, "factors_df": fdf,
            "sr_upsa": sharpe.loc[best_seed, "UPSA"], "sr_ridge": sharpe.loc[best_seed, "Ridge"]}
    return {"sharpe": sharpe, "turnover": turnover, "best": best}
