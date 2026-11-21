"""Rolling-window estimation engine and benchmark engines.

`run_rolling_window` is a slimmed, paper-faithful port of the original
`rolling_window/run_for_rolling_window.py::run_for_rolling_window_final`.
It keeps ONLY the objects consumed by figures in the paper:

  opt_port, opt_port_z, z_grid_weights, best_z, eigenvalues (shrinkage curves),
  pc_perf {variance, sharpe}, weights, betas_insample_sec.

The two beta flavors used only by non-paper tables (`betas`, `betas_insample`)
are intentionally omitted to avoid confusion.
"""
import os
# Pin BLAS to one thread per worker (spawned workers re-import this module before
# numpy loads) so parallel windows don't oversubscribe cores.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.model_selection import KFold

from src.upsa import UPSA
from src.shrinkage import do_lw, pca_cv
from src.lasso import lasso_cv, lasso_pca_cv_kns
from src.data import align_to_common_index
from src.metrics import sharpe


_W = {}


def _init_window(X, FF5, z_grid, rolling_window, lambdas, max_pcs):
    _W.update(X=X, FF5=FF5, z=z_grid, rw=rolling_window, lam=lambdas, max_pcs=max_pcs)


def _window_one(i):
    """All per-window quantities for OOS window i (windows are independent)."""
    X, FF5, z_grid, rw = _W["X"], _W["FF5"], _W["z"], _W["rw"]
    lambdas, max_pcs = _W["lam"], _W["max_pcs"]
    f_ins, f_oos = X[i:rw + i], X[rw + i]
    ff5_ins, ff5_oos = FF5[i:rw + i], FF5[rw + i]

    upsa = UPSA(z_list=z_grid).fit(returns=f_ins)
    b_weights = np.linalg.solve(np.cov(ff5_ins, rowvar=False), ff5_ins.mean(axis=0))

    w_upsa, upsa_scale = upsa.get_upsa_weights(output_scale=True)
    w_ridge, ridge_scale = upsa.get_ridge_weights(output_scale=True)
    w_lw, _ = do_lw(returns=f_ins, eigenvalues=upsa.eigenvalues, eigenvectors=upsa.eigenvectors)
    w = {"UPSA": w_upsa, "Ridge": w_ridge, "LW": w_lw, "PCA": pca_cv(f_ins, k_folds=rw)[0]}

    eig = {"UPSA": np.array([1 / (upsa.upsa @ (1 / (gl + upsa.z_list))) for gl in lambdas]) / upsa_scale,
           "Ridge": (lambdas + upsa.z_list[upsa.best_z]) / ridge_scale}

    ins_means = f_ins.mean(axis=0)
    ins_sec = f_ins.T @ f_ins / len(f_ins)
    opt = {"FF5": ff5_oos @ b_weights}
    bsec = {}
    for c_ in ("UPSA", "Ridge", "LW", "PCA"):
        wv = w[c_]
        opt[c_] = f_oos @ wv
        Sigma_w_sec = ins_sec @ wv
        bsec[c_] = Sigma_w_sec / (wv @ Sigma_w_sec)
    capm_ret = ff5_ins[:, 0]
    bsec["CAPM"] = (f_ins.T @ capm_ret / rw - ins_means * capm_ret.mean()) / np.var(capm_ret)
    ff5_port_ins = ff5_ins @ b_weights
    bsec["FF5"] = ((f_ins.T @ ff5_port_ins / rw - ins_means * ff5_port_ins.mean())
                   / np.var(ff5_port_ins))

    pc_full_ins = f_ins @ upsa.eigenvectors
    pc_full_oos = f_oos @ upsa.eigenvectors
    ssi = np.argsort(np.abs(np.mean(pc_full_ins, axis=0)))
    inv = {"UPSA": upsa.get_inv_eigenvalues_upsa(), "Ridge": upsa.get_inv_eigenvalues_ridge()}

    pcv = {"UPSA": np.empty(max_pcs), "Ridge": np.empty(max_pcs)}
    pcs = {"UPSA": np.empty(max_pcs), "Ridge": np.empty(max_pcs)}
    for k, pc_num in enumerate(range(1, max_pcs + 1)):
        pri, pro = pc_full_ins[:, -pc_num:], pc_full_oos[-pc_num:]
        pri_sr, pro_sr = pc_full_ins[:, ssi[-pc_num:]], pc_full_oos[ssi[-pc_num:]]
        for c_ in ("UPSA", "Ridge"):
            pcv[c_][k] = (np.mean(pri, axis=0) * inv[c_][-pc_num:]) @ pro
            pcs[c_][k] = (np.mean(pri_sr, axis=0) * inv[c_][ssi[-pc_num:]]) @ pro_sr

    return i, {"opt": opt, "w": w, "opt_z": f_oos @ upsa.eff_port, "zgw": upsa.upsa,
               "bz": upsa.best_z, "eig": eig, "bsec": bsec, "pcv": pcv, "pcs": pcs}


def run_rolling_window(factors, benchmark, rolling_window, z_grid, n_windows=None, n_jobs=None):
    """Fit UPSA on each rolling window (in parallel — windows are independent)
    and return the paper figure objects.

    n_jobs : processes to use (default os.cpu_count(); 1 = serial).
    """
    benchmark = benchmark.drop(columns=["mom"]) if "mom" in benchmark.columns else benchmark
    benchmark, factors = align_to_common_index(benchmark, factors)
    index_ = factors.index[rolling_window:]
    if n_windows is not None:
        index_ = index_[:n_windows]
    n = len(index_)

    categories = ["UPSA", "Ridge", "LW", "PCA"]
    benchmarks = ["FF5", "CAPM"]
    lambdas = np.logspace(-7, -1, 1000)
    max_pcs = min(rolling_window, factors.shape[1])
    pc_cols = np.arange(1, max_pcs + 1, 1).astype(int)

    opt_port = pd.DataFrame(index=index_, columns=categories + benchmarks, dtype=float)
    opt_port_z = pd.DataFrame(index=index_, columns=z_grid, dtype=float)
    opt_port.loc[index_, "CAPM"] = benchmark["mkt"].loc[index_]
    eigenvalues = {c: pd.DataFrame(index=index_, columns=lambdas, dtype=float) for c in ("UPSA", "Ridge")}
    weights = {c: pd.DataFrame(index=index_, columns=factors.columns, dtype=float) for c in categories}
    pc_perf = {"variance": {c: pd.DataFrame(index=index_, columns=pc_cols, dtype=float) for c in ("UPSA", "Ridge")},
               "sharpe": {c: pd.DataFrame(index=index_, columns=pc_cols, dtype=float) for c in ("UPSA", "Ridge")}}
    betas_insample_sec = {c: pd.DataFrame(index=index_, columns=factors.columns, dtype=float)
                          for c in categories + benchmarks}
    z_grid_weights = pd.DataFrame(index=index_, columns=z_grid, dtype=float)
    best_z = pd.Series(index=index_, dtype=float)

    init_args = (factors.values, benchmark.values, np.asarray(z_grid, float),
                 rolling_window, lambdas, max_pcs)
    n_jobs = n_jobs or os.cpu_count()
    desc = f"rolling window rw={rolling_window} (n_jobs={n_jobs})"
    if n_jobs == 1:
        _init_window(*init_args)
        results = [_window_one(i) for i in tqdm(range(n), desc=desc)]
    else:
        with Pool(n_jobs, initializer=_init_window, initargs=init_args) as pool:
            results = list(tqdm(pool.imap(_window_one, range(n), chunksize=8), total=n, desc=desc))

    for i, r in results:
        t = index_[i]
        for c_ in categories + ["FF5"]:
            opt_port.at[t, c_] = r["opt"][c_]
        for c_ in categories:
            weights[c_].loc[t, :] = r["w"][c_]
        for c_ in categories + benchmarks:
            betas_insample_sec[c_].loc[t, :] = r["bsec"][c_]
        opt_port_z.loc[t, :] = r["opt_z"]
        z_grid_weights.loc[t, :] = r["zgw"]
        best_z.at[t] = r["bz"]
        for c_ in ("UPSA", "Ridge"):
            eigenvalues[c_].loc[t, :] = r["eig"][c_]
            pc_perf["variance"][c_].loc[t, :] = r["pcv"][c_]
            pc_perf["sharpe"][c_].loc[t, :] = r["pcs"][c_]

    return {
        "opt_port": opt_port,
        "opt_port_z": opt_port_z,
        "z_grid_weights": z_grid_weights,
        "best_z": best_z,
        "eigenvalues": eigenvalues,
        "pc_perf": pc_perf,
        "weights": weights,
        "betas_insample_sec": betas_insample_sec,
    }


def run_lasso(factors, benchmark, rolling_window, z_grid, alpha_list=None, k_fold=None):
    """Lasso-augmented UPSA/Ridge PC regressions (appendix lasso figures).
    Port of run_for_rolling_window.py::run_lasso_for_rolling_window, called as in
    run_upsa_lasso.py with alpha_list = z_grid and k_fold = rolling_window."""
    if alpha_list is None:
        alpha_list = z_grid
    if k_fold is None:
        k_fold = rolling_window
    benchmark = benchmark.drop(columns=["mom"]) if "mom" in benchmark.columns else benchmark
    benchmark, factors = align_to_common_index(benchmark, factors)
    index_ = factors.index[rolling_window:]
    categories = ["UPSA", "Ridge"]
    max_pcs = min(rolling_window, factors.shape[1])
    pc_cols = np.arange(1, max_pcs + 1, 1).astype(int)

    opt_port = pd.DataFrame(index=index_, columns=categories, dtype=float)
    weights = {c: pd.DataFrame(index=index_, columns=factors.columns, dtype=float) for c in categories}
    non_zero_pcs = {c: pd.Series(index=index_, dtype=float) for c in categories}
    pc_selection = {c: pd.DataFrame(index=index_, columns=pc_cols, dtype=float) for c in categories}

    for i in tqdm(range(len(index_)), desc=f"lasso rw={rolling_window}"):
        f_ins = factors.iloc[i:rolling_window + i, :].values
        f_oos = factors.iloc[rolling_window + i, :].values
        upsa = UPSA(z_list=z_grid).fit(returns=f_ins)
        inv_eigs = {"UPSA": upsa.get_inv_eigenvalues_upsa(),
                    "Ridge": upsa.get_inv_eigenvalues_ridge()}
        lasso_weights, _ = lasso_cv(returns=f_ins, eigenvectors=upsa.eigenvectors,
                                    shrunk_inv_eigenvalues=inv_eigs, alpha_list=alpha_list,
                                    k_fold=k_fold, z_grid=z_grid)
        for c_ in categories:
            w_factor = upsa.eigenvectors @ lasso_weights[c_]
            weights[c_].loc[index_[i], :] = w_factor
            non_zero_pcs[c_].loc[index_[i]] = int(np.sum(lasso_weights[c_] != 0))
            pc_selection[c_].loc[index_[i], :] = (lasso_weights[c_] != 0).astype(int)
            opt_port.loc[index_[i], c_] = f_oos @ w_factor

    return {"opt_port": opt_port, "weights": weights,
            "non_zero_pcs": pd.DataFrame(non_zero_pcs), "pc_selection": pc_selection}


def run_other_benchmarks(factors, benchmark, rolling_window, z_grid):
    """KNS (elastic-net) and PCA-SR (Sharpe-sorted PCA-CV) benchmarks
    (appendix sharpe-bench). Port of other_benchmarks.py."""
    benchmark = benchmark.drop(columns=["mom"]) if "mom" in benchmark.columns else benchmark
    benchmark, factors = align_to_common_index(benchmark, factors)
    index_ = factors.index[rolling_window:]
    categories = ["KNS", "PCA SR"]
    alpha_list = z_grid
    k_fold = rolling_window

    opt_port = pd.DataFrame(index=index_, columns=categories, dtype=float)
    weights = {c: pd.DataFrame(index=index_, columns=factors.columns, dtype=float) for c in categories}
    kf = KFold(n_splits=k_fold, shuffle=False)

    for i in tqdm(range(len(index_)), desc=f"other benchmarks rw={rolling_window}"):
        f_ins = factors.iloc[i:rolling_window + i, :].values
        f_oos = factors.iloc[rolling_window + i, :].values
        upsa = UPSA(z_list=z_grid).fit(returns=f_ins)
        eig_full = (upsa.eigenvalues, upsa.eigenvectors)
        eig_folds = [UPSA.smart_eigenvalue_decomposition_covariance(f_ins[tr])
                     for tr, _ in kf.split(f_ins)]
        w_pca, _ = pca_cv(f_ins, k_folds=k_fold, sort_by="sharpe",
                          eig_folds=eig_folds, eig_full=eig_full)
        weights["PCA SR"].loc[index_[i], :] = w_pca
        opt_port.loc[index_[i], "PCA SR"] = f_oos @ w_pca
        w_kns = lasso_pca_cv_kns(returns=f_ins, eigenvectors=upsa.eigenvectors,
                                 eigenvalues=upsa.eigenvalues, alpha_list=alpha_list,
                                 z_grid=z_grid, k_fold=k_fold, eig_folds=eig_folds)
        weights["KNS"].loc[index_[i], :] = upsa.eigenvectors @ w_kns
        opt_port.loc[index_[i], "KNS"] = f_oos @ upsa.eigenvectors @ w_kns

    return {"opt_port": opt_port, "weights": weights}


# ───────────────────────────── grid-size sensitivity ─────────────────────────────
def _grid_sweep_one(task, X, window, eig_range):
    """One (grid_type, n) sweep over the real panel: returns OOS UPSA/Ridge mean
    turnover and Sharpe for that grid specification."""
    grid_type, n = task
    z = int(n) if grid_type == "eig" else np.logspace(-10, -1, int(n))
    T = X.shape[0]
    ru = np.empty(T - window)
    rr = np.empty(T - window)
    wu = np.empty((T - window, X.shape[1]))
    wr = np.empty((T - window, X.shape[1]))
    for t in range(T - window):
        f_ins, f_oos = X[t:t + window], X[t + window]
        u = UPSA(z_list=z).fit(returns=f_ins, eig_range=eig_range)
        a, b = u.get_upsa_weights(), u.get_ridge_weights()
        ru[t], rr[t] = f_oos @ a, f_oos @ b
        wu[t], wr[t] = a, b

    def _sharpe(r):
        return np.sqrt(12) * r.mean() / r.std()

    def _turn(w):
        dw = np.abs(np.diff(w, axis=0)).sum(axis=1)
        denom = np.abs(w[:-1]).sum(axis=1)
        return 100 * np.mean(0.5 * dw / denom)

    return grid_type, int(n), _sharpe(ru), _sharpe(rr), _turn(wu), _turn(wr)


def run_grid_size(factors, benchmark, window=120, points=range(2, 21), eig_range=10, n_jobs=None):
    """Sweep UPSA/Ridge OOS Sharpe and turnover vs number & placement of grid
    points (fixed log-grid vs eigenvalue-based). Parallel over (type, n)."""
    benchmark = benchmark.drop(columns=["mom"]) if "mom" in benchmark.columns else benchmark
    benchmark, factors = align_to_common_index(benchmark, factors)
    X = factors.values
    tasks = [(g, n) for g in ("fixed", "eig") for n in points]
    n_jobs = n_jobs or min(len(tasks), os.cpu_count())
    work = partial(_grid_sweep_one, X=X, window=window, eig_range=eig_range)
    out = {g: {"n": [], "sharpe_upsa": [], "sharpe_ridge": [],
               "turnover_upsa": [], "turnover_ridge": []} for g in ("fixed", "eig")}
    with Pool(n_jobs) as pool:
        results = list(tqdm(pool.imap_unordered(work, tasks), total=len(tasks), desc="grid size"))
    for g, n, su, sr, tu, tr in sorted(results, key=lambda r: (r[0], r[1])):
        out[g]["n"].append(n)
        out[g]["sharpe_upsa"].append(su)
        out[g]["sharpe_ridge"].append(sr)
        out[g]["turnover_upsa"].append(tu)
        out[g]["turnover_ridge"].append(tr)
    return out


# ───────────────────────────── in-sample vs out-of-sample (complexity) ─────────────────────────────
def _markowitz(f):
    return f.mean() @ np.linalg.inv(f.cov())


def run_is_vs_oos(factors, n_sims=100, k_fold=5, seed=0):
    """In-sample vs K-fold out-of-sample Markowitz Sharpe as portfolio complexity
    c=N/T grows (random factor subsets). Port of ins_vs_oos.py. Fig. is-oos."""
    np.random.seed(seed)
    cols = factors.columns
    voc_grid = np.linspace(1, len(cols), 20).astype(int)
    perf = pd.DataFrame(0.0, index=voc_grid, columns=["In-sample", "Out-of-sample"])
    kf = KFold(n_splits=k_fold)
    f_is = None
    for p_ in tqdm(voc_grid, desc="is vs oos"):
        is_sim, oos_sim = [], []
        for _ in range(n_sims):
            f_sub = factors[np.random.choice(cols, p_, replace=False)]
            is_sim.append(sharpe(f_sub @ _markowitz(f_sub)))
            oos = 0.0
            for tr, te in kf.split(f_sub):
                f_oos, f_is = f_sub.iloc[tr], f_sub.iloc[te]
                oos += sharpe(f_oos @ _markowitz(f_is)) / k_fold
            oos_sim.append(oos)
        perf.loc[p_, "In-sample"] = np.mean(is_sim)
        perf.loc[p_, "Out-of-sample"] = np.mean(oos_sim)
    perf.index = perf.index / f_is.shape[0]   # c = N / T (fold size), as in the paper
    return perf
