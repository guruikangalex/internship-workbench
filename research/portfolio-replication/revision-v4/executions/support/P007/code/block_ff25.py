#!/usr/bin/env python3
"""P007 FF25 daily 20-trading-day blocking demonstration.

Read-only on the downloaded Ken French CSV. Demonstrates two documentable
readings of the paper's "one-day buffer" and the resulting block calendars.
NO portfolio SR/IR/regression target is computed; only structural blocking
and operator-level invariants are logged.

Readings:
  A STRICT_21_STEP : for prediction start a, signal = days a-21..a-2,
                     buffer day a-1, target = a..a+19; holding starts are
                     21 trading days apart (a->a+21). This is a DERIVED
                     candidate, not confirmed author calendar.
  B ADJACENT_20_STEP: signal = a-20..a-1, target = a..a+19 (third-party
                     skip=2 leaves a one-day gap but adjacent 20-day blocks);
                     holding starts are 20 trading days apart.

Both use COMPOUND 20-day returns prod(1+r)-1 and cross-sectional rank/N
demeaning. The paper's phrase "extra one-day buffer between the last day in
the training sample and the first day in the forecast window" does NOT by
itself force reading A for every holding start.

Run: python block_ff25.py > ../logs/block_ff25.stdout.log 2> ../logs/block_ff25.stderr.log
"""
import csv
import hashlib
import io
import json
import math
import os

try:
    import numpy as np
except ImportError:
    np = None

SUPPORT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(SUPPORT, "data")
P25 = os.path.join(DATA, "25_Portfolios_5x5_Daily.csv")
PAPER_START, PAPER_END = 19630701, 20191231
N = 20


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def parse_vw(path):
    with open(path, "r", encoding="latin-1", errors="replace") as f:
        lines = f.read().splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith(",") and "SMALL LoBM" in ln:
            start = i
            break
    if start is None:
        raise RuntimeError("no VW daily section header")
    header = [c.strip() for c in lines[start].split(",")[1:]]
    rows = []
    for ln in lines[start + 1:]:
        s = ln.strip()
        if not s or len(s) < 9 or not s[:8].isdigit():
            break
        vals = [float(x.strip()) for x in s.split(",")[1:]]
        if len(vals) != len(header):
            continue
        rows.append((int(s[:8]), vals))
    return header, rows


def comp20(block):
    """compound a list of 25-vectors of percent returns -> 25-vector decimal."""
    if np is not None:
        a = np.asarray(block, dtype=float) / 100.0
        return np.prod(1.0 + a, axis=0) - 1.0
    out = [1.0] * len(block[0])
    for row in block:
        for j, v in enumerate(row):
            out[j] *= (1.0 + v / 100.0)
    return [x - 1.0 for x in out]


def rank_demean(vec):
    """cross-sectional rank/N - mean (ties averaged)."""
    n = len(vec)
    order = sorted(range(n), key=lambda j: vec[j])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and vec[order[j + 1]] == vec[order[i]]:
            j += 1
        avg = (i + j) / 2.0 / n
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    mean = sum(ranks) / n
    return [r - mean for r in ranks]


def build_blocks(dates, vals, reading):
    """Return list of dicts: signal window [start,end] indices, buffer, target window."""
    blocks = []
    if reading == "A":
        step = 21
        # first prediction start a such that a-21 >= 0 and a+19 < len
        a = 21
        while a + N <= len(dates):
            blocks.append({
                "signal": [a - 21, a - 2], "buffer": [a - 1],
                "target": [a, a + N - 1], "start": a,
            })
            a += step
    elif reading == "B":
        step = 20
        a = N
        while a + N <= len(dates):
            blocks.append({
                "signal": [a - N, a - 1], "buffer": [],
                "target": [a, a + N - 1], "start": a,
            })
            a += step
    return blocks


def pi_hat(blocks, dates, vals, k, n_train=120):
    """Pi = (1/n_train) sum_{tau=k-n_train}^{k-1} R_{tau+1} S_tau' using blocks."""
    if k < n_train or k >= len(blocks):
        return None
    s_list, r_list = [], []
    for tau in range(k - n_train, k):
        sg = blocks[tau]["signal"]
        tg = blocks[tau + 1]["target"]
        s = rank_demean(comp20(vals[sg[0]:sg[1] + 1]))
        r = comp20(vals[tg[0]:tg[1] + 1])
        s_list.append(s); r_list.append(r)
    if np is not None:
        S = np.asarray(s_list); R = np.asarray(r_list)
        assert np.isfinite(S).all() and np.isfinite(R).all(), "non-finite block input"
        with np.errstate(all="ignore"):
            P = (R.T @ S) / n_train
        assert np.isfinite(P).all(), "non-finite Pi_hat"
        return P
    m = len(s_list[0])
    P = [[0.0] * m for _ in range(m)]
    for s, r in zip(s_list, r_list):
        for i in range(m):
            for j in range(m):
                P[i][j] += r[i] * s[j] / n_train
    return P


def fmt(v):
    return round(float(v), 6)


def main():
    out = {
        "batch": "CO-REP-20261120-02", "paper": "P007",
        "task": "20-trading-day blocking + buffer-reading demonstration",
        "data": {
            "file": P25, "sha256": sha256(P25),
            "bytes": os.path.getsize(P25),
            "url": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/25_Portfolios_5x5_Daily_CSV.zip",
            "vintage_note": "first line of CSV carried 202609 CRSP database; downloaded fresh 2026-11-21",
        },
        "paper_window": [PAPER_START, PAPER_END],
        "readings": {},
        "invariants": {},
        "status": "UNKNOWN",
    }
    header, rows = parse_vw(P25)
    out["data"]["n_assets"] = len(header)
    out["data"]["assets"] = header
    out["data"]["total_daily_rows"] = len(rows)
    out["data"]["first_last_daily"] = [rows[0][0], rows[-1][0]]
    paper = [(d, v) for d, v in rows if PAPER_START <= d <= PAPER_END]
    dates = [d for d, _ in paper]
    vals = [v for _, v in paper]
    out["paper_window_days"] = len(paper)
    out["paper_first_last"] = [dates[0], dates[-1]]
    print("paper window", len(paper), dates[0], dates[-1])

    for reading, label in [("A", "STRICT_21_STEP"), ("B", "ADJACENT_20_STEP")]:
        blocks = build_blocks(dates, vals, reading)
        rec = {
            "label": label,
            "n_blocks": len(blocks),
            "step_trading_days": 21 if reading == "A" else 20,
            "unused_tail_days": len(dates) - (blocks[-1]["target"][1] + 1) if blocks else None,
            "first": {
                "signal_dates": [dates[blocks[0]["signal"][0]], dates[blocks[0]["signal"][1]]],
                "buffer_dates": [dates[i] for i in blocks[0]["buffer"]],
                "target_dates": [dates[blocks[0]["target"][0]], dates[blocks[0]["target"][1]]],
            },
            "last": {
                "signal_dates": [dates[blocks[-1]["signal"][0]], dates[blocks[-1]["signal"][1]]],
                "target_dates": [dates[blocks[-1]["target"][0]], dates[blocks[-1]["target"][1]]],
            },
            "min_blocks_before_first_oos": 121,
            "max_oos_evaluations": max(0, len(blocks) - 121),
        }
        out["readings"][reading] = rec
        print(label, "n_blocks", rec["n_blocks"], "step", rec["step_trading_days"],
              "first target", rec["first"]["target_dates"])

    # Operator-level invariants at a common demonstrative block index k.
    k = 130
    PA = pi_hat(build_blocks(dates, vals, "A"), dates, vals, k)
    PB = pi_hat(build_blocks(dates, vals, "B"), dates, vals, k)
    inv = {"k": k, "n_train_pairs": 120, "note": "Pi_hat differs by reading; compare operator invariants"}
    if np is not None and PA is not None and PB is not None:
        inv["PA_shape"] = list(PA.shape)
        inv["PB_shape"] = list(PB.shape)
        inv["PA_fro"] = fmt(np.linalg.norm(PA))
        inv["PB_fro"] = fmt(np.linalg.norm(PB))
        inv["relative_operator_diff_fro"] = fmt(np.linalg.norm(PA - PB) / np.linalg.norm(PA))
        ua, da, vta = np.linalg.svd(PA)
        ub, db, vtb = np.linalg.svd(PB)
        inv["singular_values_A_top5"] = [fmt(x) for x in da[:5]]
        inv["singular_values_B_top5"] = [fmt(x) for x in db[:5]]
        # sign invariance: reconstruct operator with flipped singular-vector signs
        da_flip = da.copy(); vta_flip = vta.copy()
        ua[:, 0] *= -1; vta[0, :] *= -1
        with np.errstate(all="ignore"):
            PA_flip = (ua * da) @ vta
        inv["sign_flip_operator_reconstruction_max_abs_diff"] = fmt(np.max(np.abs(PA - PA_flip)))
        # symmetric/antisymmetric spectral invariants (phase-free outer product)
        sym = (PA + PA.T) / 2
        asym = (PA - PA.T) / 2
        wa, Va = np.linalg.eigh(sym)
        # antisymmetric operator norm is phase-invariant under x->-x,y->-y jointly
        inv["sym_eigs_top5_abs"] = [fmt(abs(x)) for x in sorted(wa, key=lambda z: -abs(z))[:5]]
        inv["antisym_fro"] = fmt(np.linalg.norm(asym))
        inv["rank_PA"] = int(np.linalg.matrix_rank(PA))
        inv["rank_PB"] = int(np.linalg.matrix_rank(PB))
        inv["interpretation"] = (
            "Differences in singular-vector signs or eigenvector complex phase do NOT "
            "by themselves constitute failure; the operator (Pi, symmetric/antisymmetric "
            "parts, singular values, outer products) is the phase-free invariant. "
            "Final portfolio returns must be checked separately."
        )
    out["invariants"] = inv
    out["status"] = "DONE_STRUCTURAL"
    out["target_results"] = {"Figure1_2_3_TableII": "NOT_RUN", "economic_conclusion": "NOT_ASSESSED"}
    path = os.path.join(SUPPORT, "results", "block_ff25_results.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("invariants", {k: v for k, v in inv.items() if k in ("relative_operator_diff_fro", "rank_PA", "rank_PB")})
    print("OVERALL", out["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
