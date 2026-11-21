#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build target_comparison.csv from E06 results.

Template fields follow target_alignment.csv plus the approval-mandated fields
(reviewed_source_commit, canonical_version_id, reproduction_type,
experiment_purpose, execution_authorized, run_id, execution_status,
reference_kind). Paper values are the published values registered in the
P006-E01 rows of target_alignment.csv for the same canonical version; E06 has
no pre-registered rows of its own, so reference_kind is explicit.
"""
import os
import csv
import json

HERE = os.path.dirname(os.path.abspath(__file__))
MET = json.load(open(os.path.join(HERE, "results", "metrics.json")))
COMMIT = "104aecfcad4c308e1044a3d15483fe2320619597"
RUN_ID = "P006-E06-INDEP-20261121-01"

COLS = [
    "reviewed_source_commit", "paper_id", "version_id", "canonical_version_id",
    "experiment_id", "reproduction_type", "experiment_purpose",
    "execution_authorized", "run_id", "execution_status", "reference_kind",
    "result_id", "target_cell_or_series", "source_location", "input",
    "entrypoint", "config", "unit", "paper_value", "reference_file",
    "tolerance", "rerun_value", "absolute_error", "relative_error",
    "numerical_verdict", "economic_verdict", "difference_explanation",
    "result_status", "scope_status",
]

HALF_UNIT = {
    "F03-FULL-SAMPLE-UPSA": 0.005,
    "F05-FULL-RIDGE-ALPHA": 0.005,
    "F05-FULL-RIDGE-TSTAT": 0.005,
    "F08-UPSA-MEAN": 0.05,
}
PAPER = [
    ("P006-F03-FULL-SAMPLE-UPSA", "Full Sample / UPSA / annualized Sharpe",
     "§3.3 figure 3 and descriptive values", "annualized Sharpe", 1.92),
    ("P006-F05-FULL-RIDGE-ALPHA", "Full Sample / UPSA vs Ridge / annualized alpha percentage points",
     "§3.3 Figure 5 and descriptive values", "annualized alpha percentage points", 4.46),
    ("P006-F05-FULL-RIDGE-TSTAT", "Full Sample / UPSA vs Ridge / HAC(5) t-statistic",
     "§3.3 Figure 5 and descriptive values", "HAC(5) t-statistic", 3.72),
    ("P006-F08-UPSA-MEAN", "Full Sample / UPSA / mean monthly turnover percentage points",
     "§4.2 Figure 8 and Appendix D.3 summary", "mean monthly turnover percentage points", 12.4),
    ("P006-T01-SKEWNESS-UPSA", "Skewness / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.69),
    ("P006-T01-PROFITABILITY-UPSA", "Profitability / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.53),
    ("P006-T01-LOW-RISK-UPSA", "Low Risk / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.77),
    ("P006-T01-VALUE-UPSA", "Value / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.73),
    ("P006-T01-INVESTMENT-UPSA", "Investment / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.67),
    ("P006-T01-SEASONALITY-UPSA", "Seasonality / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.58),
    ("P006-T01-DEBT-ISSUANCE-UPSA", "Debt Issuance / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.49),
    ("P006-T01-SIZE-UPSA", "Size / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.70),
    ("P006-T01-ACCRUALS-UPSA", "Accruals / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.50),
    ("P006-T01-LOW-LEVERAGE-UPSA", "Low Leverage / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.30),
    ("P006-T01-PROFIT-GROWTH-UPSA", "Profit Growth / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.60),
    ("P006-T01-MOMENTUM-UPSA", "Momentum / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.17),
    ("P006-T01-QUALITY-UPSA", "Quality / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", -0.40),
    ("P006-T01-ALL-UPSA", "All / UPSA / pricing R-squared", "§3.4 Table 1", "pricing R-squared", 0.67),
]

NOT_RUN = [
    ("P006-F03-BEFORE-AFTER-2000", "Fig.3 before/after 2000 UPSA sub-sample Sharpe (12 cells)",
     "§3.3 Figure 3", "annualized Sharpe", ""),
    ("P006-F05-SUBSAMPLE-ALPHA", "Fig.5 sub-sample alpha intervals (15 combos)",
     "§3.3 Figure 5", "annualized alpha percentage points", ""),
    ("P006-F06-SCATTER", "Fig.6 153-factor scatter R-squared panels",
     "§3.3 Figure 6", "R-squared", ""),
    ("P006-T01-ALL-RIDGE-AND-OTHERS", "Table 1 non-UPSA columns (Ridge/LW/PCA and other themes)",
     "§3.4 Table 1", "pricing R-squared", ""),
    ("P006-T-E1-APPENDIX", "Appendix Table E.1 84 cells",
     "Appendix E", "pricing R-squared", ""),
    ("P006-SIMULATIONS", "Simulation figures (DGP-based)",
     "§5 / Appendix F", "various", ""),
]


def rerun_for(rid, path):
    if rid.endswith("F03-FULL-SAMPLE-UPSA"):
        return MET["strategy"][path]["sharpe"]
    if rid.endswith("F05-FULL-RIDGE-ALPHA"):
        return MET["strategy"][path]["alpha_vs_ridge_pp"]
    if rid.endswith("F05-FULL-RIDGE-TSTAT"):
        return MET["strategy"][path]["alpha_vs_ridge_hac5_t"]
    if rid.endswith("F08-UPSA-MEAN"):
        return MET["strategy"][path]["turnover_pct"]
    theme = rid.replace("P006-T01-", "").replace("-UPSA", "").replace("-", " ").title()
    # map back to exact key names used in metrics.json
    key_map = {k.lower(): k for k in MET["strategy"][path]["pricing_R2"]}
    return MET["strategy"][path]["pricing_R2"][key_map[theme.lower()]]


def tol_text(rid):
    for k, v in HALF_UNIT.items():
        if rid.endswith(k):
            return f"Absolute half unit {v}; apply original displayed rounding"
    return "Absolute half unit 0.005; apply original displayed rounding"


def main():
    rows = []
    for path in ("B0", "B1"):
        for rid, cell, loc, unit, paper in PAPER:
            rerun = rerun_for(rid, path)
            abs_err = abs(rerun - paper)
            half = HALF_UNIT.get(rid, 0.005)
            num_verdict = "MATCH" if abs_err <= half else "NUMERIC_DIFFERENCE"
            eco = ("SAME_DISPLAYED_VALUE" if num_verdict == "MATCH"
                   else "IMPLEMENTATION_DEPENDENT_DIFFERENCE")
            if path == "B0":
                expl = ("Independent c=T stable LOO; same divisor-T math as author A but without "
                        "A's 1/z-amplified roundoff in w_adj/z and l_adj/z. First-window A-vs-B0 "
                        "LOO maxabs 0.219 at z<=1e-8, 3.3e-9 at z>=1e-6.")
            else:
                expl = ("Independent paper T-1 leave-one-out (c=T-1); full-window ridge basis keeps "
                        "original T. Isolates T-vs-T-1 divisor effect vs B0 (monthly-return maxabs "
                        "0.00874, corr 0.9999975); also inherits the A-vs-B0 implementation gap.")
            rows.append({
                "reviewed_source_commit": COMMIT,
                "paper_id": "P006", "version_id": "P006-RFS-20261119",
                "canonical_version_id": "P006-RFS-20261119", "experiment_id": "P006-E06",
                "reproduction_type": "INDEPENDENT_FAITHFUL",
                "experiment_purpose": "IMPLEMENTATION_AUDIT",
                "execution_authorized": "true", "run_id": RUN_ID,
                "execution_status": "COMPLETED",
                "reference_kind": "paper_published_value_from_P006_E01_target_row",
                "result_id": rid + "-" + path,
                "target_cell_or_series": cell,
                "source_location": "https://doi.org/10.1093/rfs/hhag084; " + loc,
                "input": "data/processed_inputs/factors_main.csv; data/processed_inputs/benchmark.csv",
                "entrypoint": "python independent_upsa.py --all; python compare_paths.py",
                "config": ("T=120; Z=10**[-10..-1]; OOS 1981-11..2022-12 (494 months); "
                           "B0 c=T, B1 c=T-1; eff_port/full basis original T; trace scale "
                           "sum(1/inv_eigs)/sum(eig); A bundle read-only"),
                "unit": unit, "paper_value": paper,
                "reference_file": "target_alignment.csv E01 row (paper value)",
                "tolerance": tol_text(rid),
                "rerun_value": round(rerun, 10),
                "absolute_error": round(abs_err, 10),
                "relative_error": round(abs_err / abs(paper), 10) if paper else "",
                "numerical_verdict": num_verdict,
                "economic_verdict": eco,
                "difference_explanation": expl,
                "result_status": "RUN",
                "scope_status": "E06_AD_HOC_PAPER_VALUE_MAP",
            })
    for rid, cell, loc, unit, paper in NOT_RUN:
        rows.append({
            "reviewed_source_commit": COMMIT, "paper_id": "P006",
            "version_id": "P006-RFS-20261119",
            "canonical_version_id": "P006-RFS-20261119", "experiment_id": "P006-E06",
            "reproduction_type": "INDEPENDENT_FAITHFUL",
            "experiment_purpose": "IMPLEMENTATION_AUDIT",
            "execution_authorized": "true", "run_id": RUN_ID,
            "execution_status": "COMPLETED",
            "reference_kind": "paper_value_not_independently_digitized_for_E06",
            "result_id": rid, "target_cell_or_series": cell,
            "source_location": "https://doi.org/10.1093/rfs/hhag084; " + loc,
            "input": "", "entrypoint": "", "config": "", "unit": unit,
            "paper_value": paper, "reference_file": "target_alignment.csv (no E06 row)",
            "tolerance": "", "rerun_value": "", "absolute_error": "",
            "relative_error": "", "numerical_verdict": "NOT_ASSESSED",
            "economic_verdict": "NOT_ASSESSED",
            "difference_explanation": "E06 scope is the T-1 LOO formula audit; this target cell was not digitized or pre-registered for E06.",
            "result_status": "NOT_RUN", "scope_status": "E06_OUT_OF_SCOPE",
        })
    out = os.path.join(HERE, "target_comparison.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"WROTE {out}: {len(rows)} rows ({sum(r['result_status']=='RUN' for r in rows)} RUN, "
          f"{sum(r['result_status']=='NOT_RUN' for r in rows)} NOT_RUN)")


if __name__ == "__main__":
    main()
