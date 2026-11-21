"""Compute the main-config engine bundle (UPSA + benchmarks, rolling window 120)
and cache it to outputs/computed/main_bundle.p."""
import os
import sys
import pickle
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from src.data import load_panel
from src.portfolios import run_rolling_window, run_is_vs_oos

CACHE = os.path.join(HERE, "outputs", "computed", "main_bundle.p")
IS_OOS_CACHE = os.path.join(HERE, "outputs", "computed", "is_vs_oos.p")
Z_GRID = np.logspace(-10, -1, 10)


def _is_vs_oos(force):
    if os.path.exists(IS_OOS_CACHE) and not force:
        with open(IS_OOS_CACHE, "rb") as f:
            return pickle.load(f)
    print("[main] computing in/OOS complexity sweep...")
    perf = run_is_vs_oos(load_panel("factors_main"))
    with open(IS_OOS_CACHE, "wb") as f:
        pickle.dump(perf, f, protocol=4)
    return perf


def compute_main(force=False):
    if os.path.exists(CACHE) and not force:
        print(f"[main] using cache {CACHE}")
        with open(CACHE, "rb") as f:
            res = pickle.load(f)
    else:
        print("[main] computing rolling-window engine (bryan_monthly_vw_cap, rw=120)...")
        res = run_rolling_window(load_panel("factors_main"), load_panel("benchmark"), 120, Z_GRID)
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "wb") as f:
            pickle.dump(res, f, protocol=4)
        print(f"[main] cached -> {CACHE}")
    res["is_vs_oos"] = _is_vs_oos(force)
    return res


if __name__ == "__main__":
    compute_main(force="--compute" in sys.argv)
