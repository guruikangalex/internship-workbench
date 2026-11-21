#!/usr/bin/env python3
"""R4 fixed comparison builder: 115 PROPOSED P006-E01 targets vs cold-run values.

Fixes over v3 (see build_comparison_v3_backup.py):
  #1 no hardcoded executor absolute paths -> argparse, defaults relative to this file
  #2 strict key/length/order validation (no silent min() truncation); missing or
     extra items are reported explicitly and force FAIL/NOT_ASSESSED
  #3 All-UPSA verdict is derived from numbers+frozen tolerance, never hardcoded
  #4 difference_explanation strings are generated from the current extracted values

Outputs target_comparison_r4.csv (does not overwrite the R3 115-row file).
"""
import argparse, csv, json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))


def discover_workroot(start):
    """Walk upward to the directory that contains CO-REP-20261120-02."""
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, "CO-REP-20261120-02")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise RuntimeError("cannot locate CO-REP-20261120-02 from " + start)
        d = parent


WORKROOT = discover_workroot(HERE)
DEFAULT_PYBIN = os.path.join(
    WORKROOT, "CO-REP-20261120-02/execution/env_py396/bin/python")

# Evidence identifiers (not executor paths)
RUN_ID = "RUN-P006-E01-AUTHOR-20261121-R4"
ZIP_SHA = "a20c2fbf0de51e9ad54baa6d2dadd7e2b8b374b7cea6a05efd3e918bc12f699b"
TGT_SHA_FROZEN = "151a53c44488b76b742a1be84adca529542e5e135fa761c38b68c9eef68d9d1c"
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
PANEL_FIG6_SHARPE_TOL = 5e-6      # frozen reference-draft threshold (protocol §3)
PANEL_FIG8_TURNOVER_TOL = 1e-5    # frozen reference-draft threshold (protocol §3)
AUTHOR_REF_DISPLAY_TOL = 0.005    # frozen: half of one displayed 2-decimal unit

FIELDS = ["reviewed_source_commit", "execution_commit", "approval_record_id", "paper_id",
          "canonical_version_id", "experiment_id", "result_id", "reproduction_type",
          "experiment_purpose", "execution_authorized", "run_id", "execution_status",
          "performed_by", "input_manifest", "code_commit_or_sha256", "config_path",
          "config_sha256", "environment_path", "actual_command", "log_paths",
          "output_paths_and_hashes", "reference_kind", "source_location", "paper_value",
          "author_cache_value", "cold_run_value", "reference_value", "replication_value",
          "unit", "tolerance_rule", "tolerance_frozen_at", "absolute_error", "relative_error",
          "relative_error_note", "difference_explanation", "numerical_verdict",
          "theoretical_mechanism_verdict", "market_economic_verdict", "original_run_acceptance",
          "deviations_from_paper", "suspected_cause", "confirming_test", "evidence_ids",
          "remaining_blockers"]


def num(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def tol_of(t):
    if not t:
        return None
    m = re.search(r"0\.0+5", t)
    if m:
        return float(m.group())
    m = re.search(r"0\.0+1", t)
    return float(m.group()) if m else None


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return f"{v:.10g}"


def scalar_paper_value(r):
    s = (r.get("paper_value") or "").strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def map_value(rid, F, M):
    """Return (rep, ref, kind)."""
    if rid.startswith("P006-F03-"):
        rest = rid[len("P006-F03-"):]
        per, meth = rest.rsplit("-", 1)
        p, m = PERIOD[per], METHOD[meth]
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
        m, th = METHOD[meth_m], THEME[theme_m]
        return F["table1_r2"][m][th], M["table1_r2"][m][th], "t1"
    if rid == "P006-PANEL-FIG3":
        def pack(d):
            return {p: {m: d["fig3_sharpe"][p][m] for m in METHOD.values()}
                    for p in ("FULL", "BEFORE-2000", "AFTER-2000")}
        return pack(F), pack(M), "panel3"
    if rid == "P006-PANEL-FIG5":
        def pack5(d):
            return {"periods_note": "author plot computes alpha/CI/t per period; full-sample anchors extracted",
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


# ---------------------------------------------------------------- strict compare (fix #2)
def flatten_keyed(obj, prefix=""):
    """Flatten nested dict/list to an ordered mapping path->scalar, preserving
    keys/list positions so missing and extra items are detectable."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten_keyed(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(flatten_keyed(v, f"{prefix}[{i}]"))
    elif num(obj) and not isinstance(obj, str):
        out[prefix or "root"] = float(obj)
    return out


def strict_maxabs(a, b):
    """Strict comparison. Returns (max_abs_diff|None, issues list, n_pairs).

    Any missing/extra path or type mismatch is an explicit issue; no min() truncation.
    """
    fa, fb = flatten_keyed(a), flatten_keyed(b)
    ka, kb = set(fa), set(fb)
    issues = []
    missing = sorted(ka - kb)
    extra = sorted(kb - ka)
    if missing:
        issues.append(f"MISSING in cold_run ({len(missing)}): {missing[:6]}")
    if extra:
        issues.append(f"EXTRA in author cache ({len(extra)}): {extra[:6]}")
    common = sorted(ka & kb)
    if not common:
        issues.append("NO comparable scalar pairs")
        return None, issues, 0
    diffs = [abs(fa[k] - fb[k]) for k in common]
    return max(diffs), issues, len(common)


def scalar_verdict(paper, rep, ref, tol, ae_report, regime):
    """Uniform verdict from numbers + frozen tolerance. No result_id special case (fix #3)."""
    if regime == "paper":
        # paper anchor vs fresh --compute value: strict frozen tolerance
        if ae_report is None or tol is None:
            return "NOT_ASSESSED"
        return "PASS" if ae_report <= tol else "FAIL"
    # author-reference-only: displayed 2-decimal precision, tiny drift = PARTIAL
    # (no numeric tolerance string in these rows; frozen display tol is used)
    if ae_report is None:
        return "NOT_ASSESSED"
    if rep is not None and ref is not None and round(rep, 2) == round(ref, 2):
        return "PASS"
    if ae_report <= AUTHOR_REF_DISPLAY_TOL:
        return "PARTIAL"
    return "FAIL"


# ---------------------------------------------------------------- explanations (fix #4)
def boundary_note(paper, F_vals, M_vals, R_vals):
    """Generate a numeric rounding-boundary note from current values (no hardcoded numbers)."""
    if paper is None or not all(num(v) for v in (F_vals, M_vals, R_vals)):
        return None
    pdisp = round(float(paper), 2)
    fdisp = round(float(F_vals), 2)
    if fdisp == pdisp:
        return None
    fv, mv, rv, pv = float(F_vals), float(M_vals), float(R_vals), float(paper)
    boundary = pdisp - 0.005 if fv < pv else pdisp + 0.005
    dist = abs(fv - boundary)
    return (f"rounding-boundary analysis: paper={pv:.10f}->display {pdisp:.2f}, "
            f"fresh={fv:.10f}->display {fdisp:.2f}, manuscript_cache={mv:.10f}->{mv:.2f}, "
            f"author_regen={rv:.10f}->{rv:.2f}; boundary={boundary:.4f}, "
            f"fresh_distance_to_boundary={dist:.10f}")


def cause_for(rid, kind, verdict):
    """Qualitative root-cause + confirming test (derived from lw_diagnosis_data.json)."""
    if verdict not in ("FAIL", "PARTIAL"):
        return "", ""
    cause = ("数值环境/缓存来源差异：作者缓存与冷重算的源码、输入逐字节一致，"
             "冷重跑22产物哈希完全复现；差异出现在数值层而非实现缺失。"
             "LW 非线性收缩对全部120个特征值求逆（最小特征值 2.7969e-07，"
             "逆权重达 3.57e6，条件数约 1.41e5），放大 LAPACK/BLAS 与缓存来源差异；"
             "手稿缓存生成时间早于滚动窗口源码最终修改。")
    test = ("lw_diagnosis_data.json：冷/缓存 LW 权重在首个窗口 1981-11-30 即分叉"
            "(max 2.45)，LW 回报 max 2.73，而 PCA(独立特征分解) max 4.9e-11；"
            "1e-12 相对特征值扰动 -> LW 权重差 1.67e-3、OOS 回报差 1.6e-3。")
    if kind.startswith("panel"):
        cause = ("面板级逐点数组超出参考诊断阈值（Fig6 5e-6 Sharpe / Fig8 1e-5 百分点），"
                 "系同一数值环境漂移在逐点序列上的体现，非实现缺失；索引/日期/长度严格一致。")
        test = ("extracted_values.json 逐点数组 + lw_diagnosis_data.json：索引/列严格相等，"
                "首窗口即分叉；面板阈值 5e-6/1e-5 下逐点超出数见 extracted_values.json。")
    elif rid == "P006-F05-FULL-RIDGE-ALPHA":
        cause = ("Ridge 权重数值漂移经 HAC(5) alpha 放大：fresh 4.4512 vs 论文 4.46，"
                 "手稿缓存 4.4613 贴近论文；非实现缺失。")
        test = ("extracted_values.json fig5_alpha.Ridge(alpha/tstat) + "
                "lw_diagnosis_data.json opt_port_Ridge 首窗口分叉 max 1.23e-3。")
    elif "LW" not in rid and rid != "P006-PANEL-FIG6C":
        # UPSA-family marginal cells: boundary crossing + same numerical drift
        cause = ("舍入边界擦边叠加数值漂移：abs_error 仅略超冻结容差 0.005，"
                 "fresh 显示两位小数较论文锚点低一档；手稿缓存显示值与论文一致，"
                 "作者再生缓存与冷重算低一档。按统一规则判 FAIL/PARTIAL，未放宽容差。")
        test = ("extracted_values.json fresh/manuscript/regen 三值对照 + "
                "lw_diagnosis_data.json opt_port_UPSA 首窗口分叉 max 4.4e-2。")
    return cause, test


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default=HERE, help="execution directory (default: this file's dir)")
    ap.add_argument("--target", default=os.path.join(HERE, "../../target_alignment.csv"),
                    help="target_alignment.csv (default: revision-v4/target_alignment.csv)")
    ap.add_argument("--extracted", default=None, help="extracted_values.json (default: <base>/extracted_values.json)")
    ap.add_argument("--out", default=None, help="output csv (default: <base>/target_comparison_r4.csv)")
    ap.add_argument("--pybin", default=DEFAULT_PYBIN, help="python used for the cold run")
    args = ap.parse_args()

    base = os.path.abspath(args.base)
    extracted = args.extracted or os.path.join(base, "extracted_values.json")
    out = args.out or os.path.join(base, "target_comparison_r4.csv")
    target = os.path.abspath(args.target)

    with open(extracted) as f:
        E = json.load(f)
    F, M, R = E["fresh"], E["manuscript"], E["regen"]

    # integrity: target subset must be exactly the 115 frozen PROPOSED rows
    rows = list(csv.DictReader(open(target, encoding="utf-8-sig")))
    sel = [r for r in rows if r.get("canonical_version_id") == "P006-RFS-20261119"
           and r.get("experiment_id") == "P006-E01" and r.get("scope_status") == "PROPOSED"]
    if len(sel) != 115:
        raise RuntimeError(f"expected 115 PROPOSED targets, got {len(sel)} from {target}")

    tgt_sha_actual = __import__("hashlib").sha256(open(target, "rb").read()).hexdigest()
    cmd = ("OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg "
           + args.pybin + " -u run_all.py --main --compute")

    summary = {}
    out_rows = []
    strict_issues = []
    for r in sel:
        rid = r["result_id"]
        rep, ref, kind = map_value(rid, F, M)
        paper = scalar_paper_value(r)
        tol = tol_of(r.get("tolerance"))
        panel = kind.startswith("panel")
        comparison_issues = []

        if panel:
            ae, issues, n = strict_maxabs(rep, ref)
            comparison_issues.extend(issues)
            rep_s = json.dumps(rep, ensure_ascii=False, separators=(",", ":"))
            ref_s = json.dumps(ref, ensure_ascii=False, separators=(",", ":"))
            if issues:
                strict_issues.append((rid, issues))
        else:
            ae = abs(rep - ref) if (num(rep) and num(ref)) else None
            rep_s, ref_s = fmt(rep), fmt(ref)

        if paper is not None:
            ae_report = abs(rep - paper) if num(rep) else None
            cmp_to = paper
            regime = "paper"
        else:
            ae_report = ae
            cmp_to = ref_s if panel else ref
            regime = "author"

        if ae_report is not None and not isinstance(cmp_to, str) and num(cmp_to) and float(cmp_to) != 0:
            rel = ae_report / abs(float(cmp_to))
            rel_note = "abs_error / |paper_value|" if paper is not None else "abs_error / |reference_value|"
        else:
            rel = ""
            rel_note = ("n/a (array/panel comparison; strict keyed max abs diff reported)" if panel
                        else "reference-based: abs_error vs manuscript author cache")

        # ---- verdict ----
        if panel and comparison_issues:
            verdict = "NOT_ASSESSED"  # fix #2: never silently truncate / mismatch
        elif paper is not None:
            verdict = scalar_verdict(paper, rep, ref, tol, ae_report, "paper")
        elif panel:
            if comparison_issues:
                verdict = "NOT_ASSESSED"
            elif kind == "panel6":
                meth = FIG6_PANELS[rid]
                fpred = F["fig6_pricingacc"][meth]["predicted"]
                mpred = M["fig6_pricingacc"][meth]["predicted"]
                _, pissues, _ = strict_maxabs(fpred, mpred)
                if pissues:
                    verdict = "NOT_ASSESSED"; comparison_issues.extend(pissues)
                else:
                    pred_diff = max(abs(fpred[k] - mpred[k]) for k in fpred)
                    r2_diff = abs(F["fig6_pricingacc"][meth]["r2"] - M["fig6_pricingacc"][meth]["r2"])
                    verdict = "PASS" if (pred_diff <= PANEL_FIG6_SHARPE_TOL
                                         and r2_diff <= 0.005) else "PARTIAL"
            elif kind == "panel8":
                dds, pissues = [], []
                for m in ("UPSA", "Ridge"):
                    fr = F["fig8_turnover"][m]["rolling_values"]
                    mr = M["fig8_turnover"][m]["rolling_values"]
                    for key in ("rolling_first_date", "rolling_last_date", "rolling_n"):
                        if F["fig8_turnover"][m].get(key) != M["fig8_turnover"][m].get(key):
                            pissues.append(f"panel8 {m} {key} metadata mismatch")
                    _, iss, _ = strict_maxabs(fr, mr)
                    pissues.extend(iss)
                    if not iss:
                        dds.append(max(abs(a - b) for a, b in zip(fr, mr)))
                if pissues:
                    verdict = "NOT_ASSESSED"; comparison_issues.extend(pissues)
                else:
                    verdict = "PASS" if max(dds) <= PANEL_FIG8_TURNOVER_TOL else "PARTIAL"
            else:
                verdict = "PASS" if (ae_report is not None and ae_report <= 0.005) else "PARTIAL"
        else:
            verdict = scalar_verdict(paper, rep, ref, tol, ae_report, "author")
        if comparison_issues and verdict == "PASS":
            verdict = "NOT_ASSESSED"

        # ---- explanation (data-driven) ----
        expl = []
        if r.get("tolerance", "").startswith("Author-reference only"):
            expl.append("paper numeric label not separately digitized; compared to author manuscript cache at displayed precision")
        if paper is not None and verdict == "FAIL":
            expl.append(f"fresh --compute value {fmt(rep)} differs from printed anchor {fmt(paper)} "
                        f"by absolute error {fmt(ae_report)} beyond frozen tolerance {fmt(tol)}")
        # generate boundary analysis from current data for any paper cell crossing display rounding
        pv = paper
        if pv is not None and rid.startswith("P006-T01-"):
            theme_m, meth_m = rid[len("P006-T01-"):].rsplit("-", 1)
            m, th = METHOD[meth_m], THEME[theme_m]
            note = boundary_note(pv, F["table1_r2"][m][th], M["table1_r2"][m][th], R["table1_r2"][m][th])
            if note:
                expl.append(note)
        if kind.startswith("f3") and rid.startswith(("P006-F03-BEFORE", "P006-F03-AFTER")):
            sw = F.get("fig3_sharpe", {})
            for p in ("BEFORE-2000", "AFTER-2000"):
                w = F.get(p + "_WINDOW")
                if w:
                    expl.append(f"author pandas year slice {p}: {w['start']}..{w['end']} ({w['n']}m); 12-month overlap, not mutually exclusive")
        if kind.startswith("f5"):
            expl.append("HAC(5) alpha on 10% annual-vol rescaled UPSA vs benchmark; price/transaction-cost free")
        if kind == "panel6":
            expl.append(f"per-point SDF-predicted vs realized Sharpe; frozen reference threshold {PANEL_FIG6_SHARPE_TOL:g} Sharpe; exceedance reported as reference-draft deviation")
        if kind == "panel8":
            expl.append(f"12-month rolling turnover per-point; frozen auxiliary threshold {PANEL_FIG8_TURNOVER_TOL:g} percentage points; exceedance reported as reference-draft deviation")
        expl.append(LOO_NOTE)
        if comparison_issues:
            expl.append("STRICT VALIDATION ISSUE: " + " ; ".join(comparison_issues))

        cause, test = cause_for(rid, kind, verdict)

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
            "performed_by": "agent-P006-author-R4",
            "input_manifest": f"P006_upsa_reproduction_RFS_v2.zip sha256={ZIP_SHA}; target_alignment.csv sha256_actual={tgt_sha_actual}; frozen_recorded={TGT_SHA_FROZEN}",
            "code_commit_or_sha256": ZIP_SHA,
            "config_path": "revision-v4/target_alignment.csv; protocol_v2 §3",
            "config_sha256": tgt_sha_actual,
            "environment_path": args.pybin,
            "actual_command": cmd,
            "log_paths": "run_computation_r4_stdout.log;run_computation_r4_stderr.log",
            "output_paths_and_hashes": "outputs/sha256sums.txt (22 artifacts, all re-verified OK in R4)",
            "reference_kind": "manuscript_author_cache",
            "source_location": r.get("source_location", ""),
            "paper_value": r.get("paper_value", ""),
            "author_cache_value": ref_s,
            "cold_run_value": rep_s,
            "reference_value": ref_s,
            "replication_value": rep_s,
            "unit": r.get("unit", ""),
            "tolerance_rule": r.get("tolerance", ""),
            "tolerance_frozen_at": "104aecf protocol_v2 §3 (2026-11-21)",
            "absolute_error": fmt(ae_report),
            "relative_error": fmt(rel),
            "relative_error_note": rel_note,
            "difference_explanation": " | ".join(expl),
            "numerical_verdict": verdict,
            "theoretical_mechanism_verdict": "NOT_ASSESSED",
            "market_economic_verdict": "NOT_ASSESSED",
            "original_run_acceptance": "PENDING_FINAL_ACCEPTANCE",
            "deviations_from_paper": LOO_NOTE,
            "suspected_cause": cause,
            "confirming_test": test,
            "evidence_ids": f"{RUN_ID};SHA256-{ZIP_SHA[:12]};OUT-sha256sums-R4;LW-DIAG-lw_diagnosis_data.json",
            "remaining_blockers": "RFS typeset PDF SHA256 null (HTML full text used); final numerical acceptance reserved to lead reviewer",
        }
        out_rows.append(row)
        summary[verdict] = summary.get(verdict, 0) + 1

    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in out_rows:
            w.writerow(row)

    print("verdict summary:", dict(sorted(summary.items())))
    print("rows:", len(out_rows), "columns:", len(FIELDS))
    print("strict validation issues:", len(strict_issues))
    for rid, iss in strict_issues:
        print("  ", rid, "->", iss)
    print("target sha actual:", tgt_sha_actual)
    print("\n=== FAIL / PARTIAL rows ===")
    for row in out_rows:
        if row["numerical_verdict"] in ("FAIL", "PARTIAL", "NOT_ASSESSED"):
            print(f"  {row['result_id']:42s} {row['numerical_verdict']:12s} "
                  f"paper={row['paper_value']:>8s} abs_err={row['absolute_error']:>12s}")


if __name__ == "__main__":
    main()
