"""Compute objects for appendix figures.

Cheap appendix figures (PC-Sharpe-sorted, beta-pricing, recession panels) reuse
the main engine bundle. The heavy ones (size/rolling-window robustness, lasso,
KNS/PCA-SR benchmarks) each rerun an engine; they are generated only on
--compute and run in parallel at config level (one process per job, BLAS pinned
to one thread per worker).
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import sys
import pickle
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from scripts.compute_main_figures import compute_main

COMPUTED = os.path.join(HERE, "outputs", "computed")
Z_GRID = np.logspace(-10, -1, 10)

# job key -> (engine, panel, rolling_window)
JOBS = {
    "robust_mega": ("rw", "factors_mega", 120),
    "robust_large": ("rw", "factors_large", 120),
    "robust_small": ("rw", "factors_small", 120),
    "robust_rw60": ("rw", "factors_main", 60),
    "robust_rw240": ("rw", "factors_main", 240),
    "robust_rw360": ("rw", "factors_main", 360),
    "lasso": ("lasso", "factors_main", 120),
    "other_benchmarks": ("kns", "factors_main", 120),
}


def _job_path(job):
    return os.path.join(COMPUTED, f"appx_{job}.p")


def _run_job(job):
    from src.data import load_panel
    from src.portfolios import run_rolling_window, run_lasso, run_other_benchmarks
    engine, panel, rw = JOBS[job]
    bench = load_panel("benchmark")
    factors = load_panel(panel)
    if engine == "rw":
        # n_jobs=1: this job is already one worker in the config-level pool
        # (daemonic workers cannot spawn their own pool).
        res = run_rolling_window(factors, bench, rw, Z_GRID, n_jobs=1)
    elif engine == "lasso":
        res = run_lasso(factors, bench, rw, Z_GRID)
    else:
        res = run_other_benchmarks(factors, bench, rw, Z_GRID)
    with open(_job_path(job), "wb") as f:
        pickle.dump(res, f, protocol=4)
    return job


def compute_appendix(force=False, n_jobs=None):
    # Main bundle is a dependency; reuse its cache (don't re-force it here).
    main = compute_main(force=False)
    if force:
        todo = list(JOBS)
        n_jobs = n_jobs or min(len(todo), os.cpu_count())
        print(f"[appendix] computing {len(todo)} engine jobs on {n_jobs} workers "
              f"(this is the heavy step)...")
        with Pool(n_jobs) as pool:
            for done in pool.imap_unordered(_run_job, todo):
                print(f"[appendix]   done: {done}", flush=True)
        # grid-size sweep (parallel internally; run after the job pool closes)
        from src.data import load_panel
        from src.portfolios import run_grid_size
        grid = run_grid_size(load_panel("factors_main"), load_panel("benchmark"), window=120)
        with open(os.path.join(COMPUTED, "grid_size.p"), "wb") as f:
            pickle.dump(grid, f, protocol=4)

    def load(job):
        p = _job_path(job)
        if not os.path.exists(p):
            return None
        with open(p, "rb") as f:
            return pickle.load(f)

    def load_named(name):
        p = os.path.join(COMPUTED, f"{name}.p")
        if not os.path.exists(p):
            return None
        with open(p, "rb") as f:
            return pickle.load(f)

    robustness = {k: load(k) for k in JOBS if k.startswith("robust_")}
    return {"main": main, "robustness": robustness,
            "lasso": load("lasso"), "other_benchmarks": load("other_benchmarks"),
            "grid_size": load_named("grid_size")}


if __name__ == "__main__":
    compute_appendix(force="--compute" in sys.argv)
