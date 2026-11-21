#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK F: reinterpret the 24 FAILs. Produces target_comparison_r4.csv
(42 rows preserved, R3 backup kept) and summary_r4.md. All R4 verdicts are
DIAGNOSTIC_ONLY unless explicitly approved (none are)."""
import os
import sys
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import r2_score

from common import (RESULTS, OWNER, RUN_ID, load_panels, dump, env_info)

PAPER_DIR = "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/CO-REP-20261120-02/evidence/P006_package"
sys.path.insert(0, PAPER_DIR)
from src.constants import JKP_CLUSTERS  # noqa: E402


def sharpe(r):
    return float(np.sqrt(12) * np.mean(r) / np.std(r))


def alpha_one(y, x, annual_vol=0.1):
    ys = y * annual_vol / np.std(np.sqrt(12) * y)
    xs = x * annual_vol / np.std(np.sqrt(12) * x)
    mod = sm.OLS(ys, sm.add_constant(xs)).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    return float(np.asarray(mod.params)[0] * 12 * 100), float(np.asarray(mod.tvalues)[0])


def turnover(w):
    gross = np.abs(w).sum(axis=1)
    t = np.zeros(len(w))
    t[1:] = 0.5 * np.abs(np.diff(w, axis=0)).sum(axis=1) / gross[:-1]
    return float(100 * np.mean(t))


def pricing_r2(r, panels, dates):
    F = panels.reindex(dates).to_numpy(float)
    cols = list(panels.columns)
    scale = np.mean(r) / np.mean(r ** 2)
    sdfs = scale * r
    fsr_all = np.sqrt(12) * F / np.std(F, axis=0, ddof=1)
    realized = np.mean(fsr_all, axis=0)
    pred = np.sum(fsr_all * sdfs[:, None], axis=0) / len(sdfs)
    out = {"All": float(r2_score(realized.reshape(-1, 1), pred.reshape(-1, 1)))}
    for theme, names in JKP_CLUSTERS.items():
        ids = [cols.index(n) for n in names if n in cols]
        if not ids:
            out[theme] = None
            continue
        fs = F[:, ids]
        fsr = np.sqrt(12) * fs / np.std(fs)
        sr = np.mean(fsr, axis=0)
        px = np.sum(fsr * sdfs[:, None], axis=0) / len(sdfs)
        out[theme] = float(r2_score(sr.reshape(-1, 1), px.reshape(-1, 1)))
    return out


def corrected_metrics():
    panels, bench = load_panels()
    d0 = pd.read_csv(os.path.join(RESULTS, "audit_A_corrected_returns_B0.csv"))
    d1 = pd.read_csv(os.path.join(RESULTS, "audit_A_corrected_returns_B1.csv"))
    dates = pd.DatetimeIndex(d0["date"])
    r0, r1 = d0["return"].to_numpy(float), d1["return"].to_numpy(float)
    g0 = pd.read_csv(os.path.join(RESULTS, "audit_A_corrected_ridge_B0.csv"))["return"].to_numpy(float)
    g1 = pd.read_csv(os.path.join(RESULTS, "audit_A_corrected_ridge_B1.csv"))["return"].to_numpy(float)
    w0 = pd.read_csv(os.path.join(RESULTS, "audit_A_corrected_weights_B0.csv"), index_col=0).to_numpy(float)
    w1 = pd.read_csv(os.path.join(RESULTS, "audit_A_corrected_weights_B1.csv"), index_col=0).to_numpy(float)
    r2_0, r2_1 = pricing_r2(r0, panels, dates), pricing_r2(r1, panels, dates)
    out = {}
    for tag, r, g, w, r2 in (("B0", r0, g0, w0, r2_0), ("B1", r1, g1, w1, r2_1)):
        a, t = alpha_one(r, g)
        out[tag] = {
            "sharpe": sharpe(r), "alpha_vs_ridge_pp": a, "hac5_t": t,
            "turnover_pct": turnover(w), "pricing_R2": r2,
        }
    return out


def main():
    df = pd.read_csv(os.path.join(OWNER, "target_comparison_v3_backup.csv"))
    cm = corrected_metrics()

    def categorize(rid, verdict):
        if verdict == "NOT_ASSESSED":
            return "未纳入 R4 重判（子样本/模拟等原文未数字化）", "NOT_APPLICABLE", ""
        if verdict == "PASS":
            return "发表结果匹配 PASS（R3 判定，R4 未推翻）", "UNCHANGED_R3", ""
        # FAIL -> always a comparison of B0/B1 replication value vs published paper value
        if "ALPHA" in rid:
            return ("发表结果匹配 FAIL：alpha pp 复现值 vs 论文值超容差",
                    "DIAGNOSTIC_ONLY", "trace 缩放 bug 已定位并修正; 修正值见 r4_corrected_value; 未获批准改判")
        if "TSTAT" in rid:
            return ("发表结果匹配 FAIL：HAC t 复现值 vs 论文值超容差",
                    "DIAGNOSTIC_ONLY", "trace 缩放 bug 已定位并修正; 修正值见 r4_corrected_value; 未获批准改判")
        if "F08" in rid:
            return ("发表结果匹配 FAIL：换手 pp 复现值 vs 论文值超容差",
                    "DIAGNOSTIC_ONLY", "trace 缩放 bug 已定位并修正; 修正值见 r4_corrected_value; 未获批准改判")
        if "T01" in rid:
            return ("发表结果匹配 FAIL：主题定价 R² 复现值 vs 论文值超容差",
                    "DIAGNOSTIC_ONLY", "library-version / 实现敏感; 修正值见 r4_corrected_value; 未获批准改判")
        return "发表结果匹配 FAIL（其他）", "DIAGNOSTIC_ONLY", ""

    def corrected_value(rid, tag):
        if tag is None or tag not in cm:
            return None
        c = cm[tag]
        if "F03" in rid or "FULL-SAMPLE-UPSA" in rid:
            return c["sharpe"]
        if "ALPHA" in rid:
            return c["alpha_vs_ridge_pp"]
        if "TSTAT" in rid:
            return c["hac5_t"]
        if "F08" in rid:
            return c["turnover_pct"]
        if "T01" in rid:
            theme_map = {
                "SKEWNESS": "Skewness", "PROFITABILITY": "Profitability",
                "LOW-RISK": "Low Risk", "VALUE": "Value", "INVESTMENT": "Investment",
                "SEASONALITY": "Seasonality", "DEBT-ISSUANCE": "Debt Issuance",
                "SIZE": "Size", "ACCRUALS": "Accruals", "LOW-LEVERAGE": "Low Leverage",
                "PROFIT-GROWTH": "Profit Growth", "MOMENTUM": "Momentum",
                "QUALITY": "Quality", "ALL": "All",
            }
            for k, v in theme_map.items():
                if k in rid:
                    return c["pricing_R2"].get(v)
        return None

    rows = []
    for _, r in df.iterrows():
        rid = str(r["result_id"])
        tag = "B0" if rid.endswith("-B0") else ("B1" if rid.endswith("-B1") else None)
        cat, status, note = categorize(rid, str(r["numerical_verdict"]))
        cv = corrected_value(rid, tag)
        pv = r["paper_value"]
        try:
            ae = abs(float(cv) - float(pv)) if cv is not None else None
        except (TypeError, ValueError):
            ae = None
        new = r.to_dict()
        new.update({
            "r4_category": cat,
            "r4_status": status,
            "r4_corrected_value": cv,
            "r4_corrected_abs_error_vs_paper": ae,
            "r4_note": note,
            "r4_evidence": ("audit_A_eigen_trace.json; audit_A_corrected_*.json; "
                            "audit_B_decomposition.json; audit_C_leakage.json; qp_highprecision.json"
                            if status == "DIAGNOSTIC_ONLY" else ""),
            "r4_run_id": RUN_ID,
        })
        rows.append(new)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OWNER, "target_comparison_r4.csv"), index=False)

    # counts by r4 category for summary
    fail = out[out.numerical_verdict == "FAIL"]
    cat_counts = fail["r4_category"].value_counts().to_dict()
    dump("audit_F_r4_summary.json", {
        "run_id": RUN_ID, "n_rows": len(out),
        "numerical_verdict_counts": out["numerical_verdict"].value_counts().to_dict(),
        "r4_status_counts": out["r4_status"].value_counts().to_dict(),
        "fail_category_counts": cat_counts,
        "corrected_metrics": cm,
        "environment": env_info(),
    })
    print("r4 status", out["r4_status"].value_counts().to_dict())
    print("fail categories", cat_counts)
    print("corrected B0", json.dumps(cm["B0"], indent=1)[:600])
    print("WROTE target_comparison_r4.csv")


if __name__ == "__main__":
    main()
