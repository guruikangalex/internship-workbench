"""One-time bootstrap: export the processed input panels from the original
research repository into this standalone package as CSVs.

Provenance only — the reproduction pipeline reads the CSVs already shipped in
data/processed_inputs/ and never imports from the original repository, so a
replicator does NOT need to run this script.

Usage:
    python scripts/export_inputs.py SOURCE_REPO_DIR

where SOURCE_REPO_DIR is the path to the original research repository, which
contains the source pickles under data/pickle/ (bryan_monthly_vw_cap.p,
benchmark.p, mega.p, large.p, small.p).
"""
import os
import sys
import numpy as np
import pandas as pd

# {output csv name: source pickle under data/pickle/}
PANELS = {
    "factors_main": "bryan_monthly_vw_cap",   # 153 JKP factors, monthly, vw-cap
    "benchmark": "benchmark",                 # FF5 + mom + mkt
    "factors_mega": "mega",
    "factors_large": "large",
    "factors_small": "small",
}

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "data", "processed_inputs")


def main(src):
    os.makedirs(OUT, exist_ok=True)
    for out_name, pkl in PANELS.items():
        df = pd.read_pickle(os.path.join(src, "data", "pickle", f"{pkl}.p"))
        df.index.name = "date"
        path = os.path.join(OUT, f"{out_name}.csv")
        # %.17g guarantees exact float64 round-trip
        df.to_csv(path, float_format="%.17g")
        # verify lossless round-trip (float64 exact)
        back = pd.read_csv(path, index_col=0, parse_dates=True,
                           float_precision="round_trip")
        back.index.name = "date"
        a, b = df.values.astype(float), back.values.astype(float)
        shape_ok = df.shape == back.shape
        nan_ok = bool((np.isnan(a) == np.isnan(b)).all())
        finite = ~np.isnan(a)
        max_diff = float(np.abs(a[finite] - b[finite]).max()) if finite.any() else 0.0
        idx_ok = bool((df.index == back.index).all())
        ok = shape_ok and nan_ok and idx_ok and max_diff == 0.0
        print(f"{out_name:14s} {df.shape}  lossless={ok}  max|diff|={max_diff:.2e}  -> {path}")
        if not ok:
            raise SystemExit(f"Round-trip mismatch for {out_name}; CSV not safe.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/export_inputs.py SOURCE_REPO_DIR")
    main(sys.argv[1])
