"""Compute and cache simulation outputs: the structured-spectrum cross-sim
(scatter + shrinkage curves) and the grid-robustness sweep."""
import os
import sys
import pickle

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from src.simulations import run_cross_sim, run_grid_robustness, run_time_varying

CACHE = os.path.join(HERE, "outputs", "computed", "sim_bundle.p")


def compute_simulations(force=False, sims_cross=10000, sims_grid=500, sims_tv=10000):
    if os.path.exists(CACHE) and not force:
        print(f"[sim] using cache {CACHE}")
        with open(CACHE, "rb") as f:
            return pickle.load(f)
    print(f"[sim] cross-sim ({sims_cross}) + grid robustness ({sims_grid}) + "
          f"time-varying ({sims_tv})...")
    perf, eigs = run_cross_sim(sims=sims_cross)
    grid = run_grid_robustness(sims=sims_grid)
    tv = run_time_varying(sims=sims_tv, rolling_window=300)   # paper spec: 10,000 seeds, rw=300
    out = {"perf": perf, "eigenvalues_all": eigs, "grid": grid, "tv": tv}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "wb") as f:
        pickle.dump(out, f, protocol=4)
    print(f"[sim] cached -> {CACHE}")
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--compute", action="store_true")
    ap.add_argument("--sims", type=int, default=10000)
    a = ap.parse_args()
    compute_simulations(force=a.compute, sims_cross=a.sims)
