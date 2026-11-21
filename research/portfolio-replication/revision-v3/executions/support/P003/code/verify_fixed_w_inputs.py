#!/usr/bin/env python3
"""P003 fixed-w subexperiment input preflight (read-only, NO backtest).

Scope: prepare the FIXED-w (in-sample shrinkage w) subexperiment for
Equity 1 (monthly, 60-month risk window). The OOS w-grid gap is explicitly
NOT allowed to block this preparation. All output metrics are NOT_RUN.

The Ken French 49-industry CSV downloaded here is an explicit SUBSTITUTE
snapshot (vintage 202609), labelled APPROXIMATE_VALIDATION. Original
empirical vintage is NOT recovered; FIZ 2024-12 / CIZ 2026-09 frozen
snapshots referenced in v2 protocol are NOT present in this workbench.

Run: python verify_fixed_w_inputs.py > ../results/fixed_w_input_audit.json
"""
import csv
import hashlib
import io
import json
import os
import zipfile

SUPPORT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(SUPPORT, "data")
ZIP = os.path.join(DATA, "ind49_current.zip")
SENTINELS = {-99.99, -999.0, -999.0}


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def parse_value_weighted_monthly():
    with zipfile.ZipFile(ZIP) as z:
        member = "49_Industry_Portfolios.csv"
        raw = z.read(member)
        rows = list(csv.reader(io.StringIO(raw.decode("latin-1"))))
    hdr_idx = None
    for i, r in enumerate(rows):
        if r and r[0] == "" and any("Agric" in c for c in r):
            hdr_idx = i
            break
    header = [c.strip() for c in rows[hdr_idx][1:]]  # 49 industry names
    data = []
    for r in rows[hdr_idx + 1:]:
        if not r or len(r) < 2:
            break
        ym = r[0].strip()
        if len(ym) != 6 or not ym.isdigit():
            break
        vals = []
        for c in r[1:]:
            c = c.strip()
            vals.append(None if c in ("", "-99.99", "-999") else float(c))
        data.append((ym, vals))
    return {
        "member": member,
        "member_bytes": len(raw),
        "member_sha256": sha256_bytes(raw),
        "n_industries": len(header),
        "industries": header,
        "n_months": len(data),
        "first_month": data[0][0],
        "last_month": data[-1][0],
        "sentinel_cells": sum(
            1 for _, vals in data for v in vals if v is None
        ),
        "industries_with_any_sentinel": sorted(
            {header[j] for _, vals in data for j, v in enumerate(vals) if v is None}
        ),
        "first_year_data": data[0][0],
        # counts restricted to paper window 1942-01..2018-12 (Table 5 target)
        "paper_window_months": sum(1 for ym, _ in data if "194201" <= ym <= "201812"),
    }


def main():
    zip_bytes = os.path.getsize(ZIP)
    zip_sha = hashlib.sha256(open(ZIP, "rb").read()).hexdigest()
    parsed = parse_value_weighted_monthly()
    man = {
        "batch": "CO-REP-20261120-02",
        "paper": "P003",
        "subexperiment": "fixed-w (in-sample shrinkage of w), Equity 1",
        "purpose": "preflight inputs/config ONLY; no returns, weights, SR or grid search computed",
        "data_snapshot": {
            "status": "APPROXIMATE_VALIDATION",
            "label": "Ken French 49 Industry Portfolios, value-weighted monthly, vintage 202609 CRSP",
            "url": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_CSV.zip",
            "zip_bytes": zip_bytes,
            "zip_sha256": zip_sha,
            "archive_probe": "202412/202609 FIZ-CIZ frozen snapshots from v2 protocol NOT present in this workbench; URL probes for Data_Library_202412 returned HTTP 404; original empirical vintage NOT recovered",
            **parsed,
        },
        "fixed_w_definition": {
            "source": "v2 protocol P003 Eq(19)(20), Table 5; paper pp.134-137,142",
            "display_w_grid": [0.0, 0.10, 0.25, 0.50, 0.75, 0.90, 0.99, 1.0],
            "grid_status": "DISPLAY_ONLY_INSAMPLE_STRESS_RANGE",
            "oos_grid_status": "UNKNOWN (paper discloses only 'limited grid, monthly selection, extended sample' without actual grid/tie/min-history); NOT blocking fixed-w preparation",
            "shrinkage_formula": "Sigma_tilde=0.95*Sigma_raw+0.05*diag(Sigma_raw); Sigma_w=(1-w)*Sigma_tilde+w*diag(Sigma_raw)",
            "optimization": "max s'x - gamma/2 x'Sigma_w x, no budget/box constraints; gamma=1 scaling; solve gamma*Sigma_w*x=s",
            "cumulative_return": "monthly x_t' r_{t+1,excess}; gross Sharpe=mean/std*sqrt(12); NO execution costs",
            "signal": "XSMOM/INDMOM: 12-month cumulative industry excess return, cross-sectionally demeaned, normalized +sum=1 / -abs-sum=1",
            "equity1_risk_window": "60 MONTHLY industry excess returns ending at decision time t (past 60 months, demeaned by sample mean, denominator K-1, time t-1..t-60)",
            "sample": "input from 1927-01; Table 5 target 1942-01..2018-12; >=15y initial history; 60-month risk window means earliest evaluable month later than raw start",
            "industry_eligibility": "ex-ante: complete 12-month signal history AND complete 60-month risk window AND no realized-return lookahead; late-entering industries (Soda,Hlth,FabPr,Guns,Gold,Softw) excluded until sentinel-free; per-period pool changes recorded",
            "missing_handling": "sentinel -99.99/-999 treated as MISSING, never as 0; no post-hoc performance-based filtering",
        },
        "status": {
            "fixed_w_config": "PREPARED",
            "industry_eligibility_rule": "PREPARED_EX_ANTE",
            "input_snapshot": "APPROXIMATE_VALIDATION",
            "oos_w_grid": "UNKNOWN_NOT_BLOCKING",
            "any_backtest_or_returns": "NOT_RUN",
            "any_target_value": "NOT_ASSESSED",
            "author_code": "NOT_FOUND",
        },
    }
    out = os.path.join(SUPPORT, "results", "fixed_w_input_audit.json")
    json.dump(man, open(out, "w"), indent=2, ensure_ascii=False)
    print(json.dumps(man, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
