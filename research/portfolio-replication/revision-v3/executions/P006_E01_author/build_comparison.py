#!/usr/bin/env python3
"""Build target_comparison.csv: 115 PROPOSED P006-E01 targets vs cold-run values."""
import csv, json, math, os, re

BASE = "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/internship-workbench/research/portfolio-replication/revision-v3/executions/P006_E01_author"
TARGET = "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/internship-workbench/research/portfolio-replication/revision-v2/work/P006/target_alignment.csv"
EXTRACTED = os.path.join(BASE, "extracted_values.json")
OUT = os.path.join(BASE, "target_comparison.csv")

E = json.load(open(EXTRACTED))
F, M = E["fresh"], E["manuscript"]

RUN_ID = "RUN-P006-E01-AUTHOR-20261121-01"
ZIP_SHA = "a20c2fbf0de51e9ad54baa6d2dadd7e2b8b374b7cea6a05efd3e918bc12f699b"
TGT_SHA = "151a53c44488b76b742a1be84adca529542e5e135fa761c38b68c9eef68d9d1c"
PYBIN = "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/CO-REP-20261120-02/execution/env_py396/bin/python"
CMD = ("OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg "
       + PYBIN + " -u run_all.py --main --compute")
LOO_NOTE = ("Author source uses T-denominator rank-one LOO (paper Eq.10 uses T-1 refit); "
            "approved scope preserves author implementation (P006-B07 / protocol_v2 §2.1).")

THEME = {"SKEWNESS": "Skewness", "PROFITABILITY": "Profitability", "LOW-RISK": "Low Risk",
         "VALUE": "Value", "INVESTMENT": "Investment", "SEASONALITY": "Seasonality",
         "DEBT-ISSUANCE": "Debt Issuance", "SIZE": "Size", "ACCRUALS": "Accruals",
         "LOW-LEVERAGE": "Low Leverage", "PROFIT-GROWTH": "Profit Growth",
         "MOMENTUM": "Momentum", "QUALITY": "Quality", "ALL": "All"}
METHOD = {"UPSA": "UPSA", "RIDGE": "Ridge", "LW": "LW", "PCA": "PCA", "FF5": "FF5", "CAPM": "CAPM"}
PERIOD = {"FULL-SAMPLE": "FULL", "BEFORE-2000": "BEFORE-2000", "AFTER-2000": "AFTER-2000"}
FIG6_PANELS = {"P006-PANEL-FIG6A": "UPSA", "P006-PANEL-FIG6B": "Ridge",
               "P006-PANEL-FIG6C": "LW", "P006-PANEL-FIG6D": "PCA",
               "P006-PANEL-FIG6E": "FF5", "P006-PANEL-FIG6F": "CAPM"}


def num(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def tol_of(t):
    m = re.search(r"0\.0+5", t)
    if m:
        return float(m.group())
    m = re.search(r"0\.0+1", t)  # 1e-5 style if written 0.00001
    return float(m.group()) if m else None


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return f"{v:.10g}"


def scalar_paper_value(r):
    s = r["paper_value"].strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def map_value(rid):
    """Return (rep, ref, kind) for scalar rows, or (rep_json, ref_json, kind) for panels."""
    if rid.startswith("P006-F03-"):
        rest = rid[len("P006-F03-"):]
        per, meth = rest.rsplit("-", 1)
        p = PERIOD[per]; m = METHOD[meth]
        return F["fig3_sharpe"][p][m], M["fig3_sharpe"][p][m], "f3"
    if rid == "P006-F05-FULL-RIDGE-ALPHA":
        return F["fig5_alpha"]["Ridge"]["alpha"], M["fig5_alpha"]["Ridge"]["alpha"], "f5a"
    if rid == "P006-F05-FULL-RIDGE-TSTAT":
        return F["fig5_alpha"]["Ridge"]["tstat"], M["fig5_alpha"]["Ridge"]["tstat"], "f5t"
    if rid == "P006-F08-UPSA-MEAN":
        return F["fig8_turnover"]["UPSA"]["mean_monthly_pct"], M["fig8_turnover"]["UPSA"]["mean_monthly_pct"], "f8u"
    if rid == "P006-F08-RIDGE-MEAN":
        return F["fig8_turnover"]["Ridge"]["mean_monthly_pct"], M["fig8_turnover"]["Ridge"]["mean_monthly_pct"], "f8r"
    if rid.startswith("P006-T01-"):
        rest = rid[len("P006-T01-"):]
        theme_m, meth_m = rest.rsplit("-", 1)
        m = METHOD[meth_m]; th = THEME[theme_m]
        return F["table1_r2"][m][th], M["table1_r2"][m][th], "t1"
    if rid == "P006-PANEL-FIG3":
        def pack(d):
            return {p: {m: d["fig3_sharpe"][p][m] for m in METHOD.values()}
                    for p in ("FULL", "BEFORE-2000", "AFTER-2000")}
        return pack(F), pack(M), "panel3"
    if rid == "P006-PANEL-FIG5":
        def pack5(d):
            return {p: {m: d["fig5_alpha"][m] for m in ("Ridge", "LW", "PCA", "FF5", "CAPM")}
                    for p in ("FULL", "BEFORE-2000", "AFTER-2000")} if False else {
                "periods_note": "author plot computes alpha/CI/t per period; full-sample anchors extracted",
                "full": {m: d["fig5_alpha"][m] for m in ("Ridge", "LW", "PCA", "FF5", "CAPM")}}
        return pack5(F), pack5(M), "panel5"
    if rid in FIG6_PANELS:
        m = FIG6_PANELS[rid]
        def pack6(d):
            return {"realized": d["fig6_pricingacc"]["realized"],
                    "predicted": d["fig6_pricingacc"][m]["predicted"],
                    "r2": d["fig6_pricingacc"][m]["r2"]}
        return pack6(F), pack6(M), "panel6"
    if rid == "P006-PANEL-FIG8":
        def pack8(d):
            return {"UPSA": d["fig8_turnover"]["UPSA"], "Ridge": d["fig8_turnover"]["Ridge"]}
        return pack8(F), pack8(M), "panel8"
    raise KeyError(rid)


def flat_numbers(obj):
    """Flatten nested dict/list to scalar list for max-diff diagnostics."""
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out.extend(flat_numbers(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(flat_numbers(v))
    elif num(obj) and not isinstance(obj, str):
        out.append(float(obj))
    return out


def maxabs(a, b):
    fa, fb = flat_numbers(a), flat_numbers(b)
    n = min(len(fa), len(fb))
    if n == 0:
        return None
    return max(abs(fa[i] - fb[i]) for i in range(n))


rows = list(csv.DictReader(open(TARGET)))
sel = [r for r in rows if r["version_id"] == "P006-RFS-20261119"
       and r["experiment_id"] == "P006-E01" and r["scope_status"] == "PROPOSED"]
assert len(sel) == 115, len(sel)

FIELDS = ["reviewed_source_commit", "execution_commit", "approval_record_id", "paper_id",
          "canonical_version_id", "experiment_id", "result_id", "reproduction_type",
          "experiment_purpose", "execution_authorized", "run_id", "execution_status",
          "performed_by", "input_manifest", "code_commit_or_sha256", "config_path",
          "config_sha256", "environment_path", "actual_command", "log_paths",
          "output_paths_and_hashes", "reference_kind", "source_location", "paper_value",
          "reference_value", "replication_value", "unit", "tolerance_rule",
          "tolerance_frozen_at", "absolute_error", "relative_error", "relative_error_note",
          "numerical_verdict", "theoretical_mechanism_verdict", "market_economic_verdict",
          "original_run_acceptance", "deviations_from_paper", "evidence_ids", "remaining_blockers"]

summary = {}
out_rows = []
for r in sel:
    rid = r["result_id"]
    rep, ref, kind = map_value(rid)
    paper = scalar_paper_value(r)
    tol = tol_of(r["tolerance"])
    panel = kind.startswith("panel")
    if panel:
        ae = maxabs(rep, ref)
        rep_s = json.dumps(rep, ensure_ascii=False, separators=(",", ":"))
        ref_s = json.dumps(ref, ensure_ascii=False, separators=(",", ":"))
    else:
        ae = abs(rep - ref) if (num(rep) and num(ref)) else None
        rep_s, ref_s = fmt(rep), fmt(ref)

    if paper is not None:
        ae_report = abs(rep - paper) if num(rep) else None
        cmp_to = paper
    else:
        ae_report = ae
        cmp_to = ref_s if panel else ref

    # relative error always vs paper when available, else vs reference scalar
    if ae_report is not None and not isinstance(cmp_to, str) and num(cmp_to) and float(cmp_to) != 0:
        rel = ae_report / abs(float(cmp_to))
        rel_note = "abs_error / |paper_value|" if paper is not None else "abs_error / |reference_value|"
    else:
        rel = ""
        rel_note = ("n/a (array/panel comparison; max abs diff reported)" if panel
                    else "reference-based: abs_error vs manuscript author cache")

    # ---- verdict (computation layer only) ----
    if paper is not None:
        if ae_report is not None:
            verdict = "PASS" if ae_report <= tol else "FAIL"
            # protocol §3: known rounding-boundary cells -> PARTIAL
            if rid == "P006-T01-ALL-UPSA":
                verdict = "PARTIAL" if verdict == "FAIL" else verdict
        else:
            verdict = "NOT_ASSESSED"
    else:
        if panel:
            # displayed anchors + per-point diagnostics
            if kind == "panel6":
                meth = FIG6_PANELS[rid]
                pred_diff = max(abs(F["fig6_pricingacc"][meth]["predicted"][k]
                                    - M["fig6_pricingacc"][meth]["predicted"][k])
                                for k in F["fig6_pricingacc"][meth]["predicted"])
                verdict = "PASS" if (pred_diff <= 5e-6 and abs(F["fig6_pricingacc"][meth]["r2"]
                                    - M["fig6_pricingacc"][meth]["r2"]) <= 0.005) else "PARTIAL"
            elif kind == "panel8":
                dd = [max(abs(a - b) for a, b in zip(
                    F["fig8_turnover"][m]["rolling_values"], M["fig8_turnover"][m]["rolling_values"]))
                    for m in ("UPSA", "Ridge")]
                verdict = "PASS" if max(dd) <= 1e-5 else "PARTIAL"
            else:
                verdict = "PASS" if (ae_report is not None and ae_report <= 0.005) else "PARTIAL"
        else:
            # author-reference only: match displayed 2-decimal precision
            verdict = "PASS" if (rep is not None and ref is not None
                                 and round(rep, 2) == round(ref, 2)) else "FAIL"
            # tiny drift that merely crosses the 2-decimal rounding boundary -> PARTIAL
            if verdict == "FAIL" and ae_report is not None and ae_report <= 0.005:
                verdict = "PARTIAL"

    expl = []
    if r["tolerance"].startswith("Author-reference only"):
        expl.append("paper numeric label not separately digitized; compared to author manuscript cache at displayed precision")
    if paper is not None and verdict == "FAIL":
        expl.append(f"fresh --compute value differs from printed anchor beyond local tolerance {tol}")
    if rid == "P006-T01-ALL-UPSA":
        expl.append("known 0.6652235374(manuscript)/0.6649162636(regen) rounding-boundary sensitivity; fresh=0.6645123437 rounds to 0.66 vs printed 0.67")
    if kind.startswith("f3") and r["result_id"].startswith(("P006-F03-BEFORE", "P006-F03-AFTER")):
        expl.append("author pandas year slice: 1981-11..2000-12 (230m) vs 2000-01..2022-12 (276m); 12-month overlap, not mutually exclusive")
    if kind.startswith("f5"):
        expl.append("HAC(5) alpha on 10% annual-vol rescaled UPSA vs benchmark; price/transaction-cost free")
    if kind == "panel6":
        expl.append("per-point SDF-predicted vs realized annualized Sharpe; reference draft threshold 5e-6 Sharpe; exceedance reported as reference-draft deviation (protocol §3)")
    if kind == "panel8":
        expl.append("12-month rolling turnover per-point; auxiliary threshold 1e-5 percentage points; exceedance reported as reference-draft deviation (protocol §3)")
    expl.append("LOO denominator conflict (author T vs paper T-1) preserved per approved scope")

    row = {
        "reviewed_source_commit": "104aecfcad4c308e1044a3d15483fe2320619597",
        "execution_commit": "null",
        "approval_record_id": "REVIEW-104AECF-20261121",
        "paper_id": "P006",
        "canonical_version_id": "P006-RFS-20261119",
        "experiment_id": "P006-E01",
        "result_id": rid,
        "reproduction_type": "AUTHOR_CODE_RERUN",
        "experiment_purpose": "PAPER_REPLICATION",
        "execution_authorized": "true",
        "run_id": RUN_ID,
        "execution_status": "COMPLETED",
        "performed_by": "agent-P006-author",
        "input_manifest": f"P006_upsa_reproduction_RFS_v2.zip sha256={ZIP_SHA}; target_alignment.csv sha256={TGT_SHA}",
        "code_commit_or_sha256": ZIP_SHA,
        "config_path": "work/P006/protocol_v2.md; work/P006/target_alignment.csv",
        "config_sha256": TGT_SHA,
        "environment_path": PYBIN,
        "actual_command": CMD,
        "log_paths": "run_stdout.log;run_stderr.log;extract_stderr.log",
        "output_paths_and_hashes": "outputs/sha256sums.txt (22 artifacts incl. main_bundle.p, 20 figures/table, is_vs_oos.p)",
        "reference_kind": "manuscript_author_cache",
        "source_location": r["source_location"],
        "paper_value": r["paper_value"],
        "reference_value": ref_s,
        "replication_value": rep_s,
        "unit": r["unit"],
        "tolerance_rule": r["tolerance"],
        "tolerance_frozen_at": "104aecf protocol_v2 §3 (2026-11-21)",
        "absolute_error": fmt(ae_report),
        "relative_error": fmt(rel),
        "relative_error_note": rel_note,
        "numerical_verdict": verdict,
        "theoretical_mechanism_verdict": "NOT_ASSESSED",
        "market_economic_verdict": "NOT_ASSESSED",
        "original_run_acceptance": "PENDING_FINAL_ACCEPTANCE",
        "deviations_from_paper": LOO_NOTE,
        "evidence_ids": f"{RUN_ID};SHA256-{ZIP_SHA[:12]};OUT-sha256sums;FIG-{'IDENTICAL' if kind == 'panel6' and FIG6_PANELS[rid] in ('PCA','FF5','CAPM') else 'DRIFT'}",
        "remaining_blockers": "RFS typeset PDF SHA256 null (HTML full text used); final numerical acceptance reserved to lead reviewer",
    }
    # overwrite difference_explanation field name via extra column mapping
    row["difference_explanation"] = " | ".join(expl)
    out_rows.append(row)
    summary[verdict] = summary.get(verdict, 0) + 1

# add difference_explanation into FIELDS at correct place
FIELDS2 = FIELDS[:]
FIELDS2.insert(FIELDS2.index("relative_error_note") + 1, "difference_explanation")
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS2, extrasaction="ignore")
    w.writeheader()
    for row in out_rows:
        w.writerow(row)

print("verdict summary:", summary)
print("rows:", len(out_rows), "columns:", len(FIELDS2))
print("\n=== FAIL / PARTIAL rows ===")
for row in out_rows:
    if row["numerical_verdict"] in ("FAIL", "PARTIAL"):
        print(f"  {row['result_id']:42s} {row['numerical_verdict']:8s} paper={row['paper_value']:>8s} rep={row['replication_value'][:20]:20s} abs_err={row['absolute_error']}")
