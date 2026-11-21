#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P008-E03: author workbook input layer -> Table 4 two 'Average excess return' means.
Fresh independent download from the AQR URL during this run, hash-verified,
then recomputed from the raw XLSX XML (no pandas/openpyxl available).

P008-R10 = Table 4 Panel A / G / Average excess return   (paper 7.84%)
P008-R11 = Table 4 Panel B / G / Average excess return   (paper 3.01%)

Method is frozen in config.json before inspecting outputs: supplier U column
(G5-G1), 674 monthly returns 1963-02..2019-03, decimal returns, arithmetic
mean * 12 * 100, no RF subtraction, no month filtering.

Reviewer high-precision values are ALSO registered, as REVIEWER_CALCULATION
reference evidence (performed_by=reviewer, original_run_acceptance=NOT_ASSESSED).
"""
import csv
import hashlib
import json
import os
import statistics
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
    CFG = json.load(f)
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
LOG = []

def log(msg=""):
    s = str(msg)
    print(s)
    LOG.append(s)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def colnum(ref):
    s = "".join(c for c in ref if c.isalpha())
    n = 0
    for c in s:
        n = n * 26 + (ord(c) - 64)
    return n

def sheet_paths(z):
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    relmap = {r.get("Id"): r.get("Target") for r in rels}
    RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    out = {}
    for sh in wb.iter(NS + "sheet"):
        tgt = relmap[sh.get(RNS)]
        if tgt.startswith("/"):
            tgt = tgt.lstrip("/")
        elif not tgt.startswith("xl/"):
            tgt = "xl/" + tgt
        out[sh.get("name")] = tgt
    return out

def read_sheet(z, path, ss):
    rows = {}
    for row in ET.fromstring(z.read(path)).iter(NS + "row"):
        cells = {}
        for c in row.findall(NS + "c"):
            v = c.find(NS + "v")
            if v is None or v.text is None:
                continue
            cells[colnum(c.get("r"))] = ss[int(v.text)] if c.get("t") == "s" else float(v.text)
        rows[int(row.get("r"))] = cells
    return rows

def excel_date(serial):
    return (datetime(1899, 12, 30) + timedelta(days=float(serial))).strftime("%Y-%m-%d")

def main():
    log("P008-E03 INDEPENDENT WORKBOOK RECOMPUTE | run_id=%s | %s" %
        (CFG["run_id"], datetime.now(timezone.utc).isoformat()))
    tol = CFG["tolerances"]["average_excess_return_absolute_pp"]
    log("tolerance +/-%.3f percentage points frozen at %s before result inspection" %
        (tol, CFG["tolerance_frozen_at_utc"]))

    path = os.path.join(HERE, CFG["input"]["local_download_path"])
    h = sha256_file(path)
    size = os.path.getsize(path)
    ok_hash = h == CFG["input"]["expected_sha256"]
    ok_size = size == CFG["input"]["expected_size_bytes"]
    log("downloaded xlsx: size=%d hash=%s" % (size, h))
    log("hash matches expected %s ; size matches %s" % (ok_hash, ok_size))
    log("source URL: %s" % CFG["input"]["url"])

    z = zipfile.ZipFile(path)
    ss = ["".join(t.text or "" for t in si.iter(NS + "t"))
          for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(NS + "si")]
    paths = sheet_paths(z)
    log("sheets: %s" % list(paths.keys()))

    U_COL = 21  # supplier column U = G5-G1 (A=1 ... U=21)
    results_by_panel = {}
    manifest_by_panel = {}
    for panel, sheet_name in [("PanelA", "Equal-weighted excess returns"),
                              ("PanelB", "Value-weighted excess returns")]:
        rows = read_sheet(z, paths[sheet_name], ss)
        maxc = max((max(v.keys()) for v in rows.values() if v), default=0)
        # date column: the column with the most Excel-serial dates in 20000..60000
        dcol = max(range(1, maxc + 1),
                   key=lambda c: sum(1 for v in rows.values()
                                     if isinstance(v.get(c), float) and 20000 <= v[c] <= 60000))
        recs = []
        for r, v in rows.items():
            d = v.get(dcol)
            if isinstance(d, float) and 20000 <= d <= 60000:
                recs.append((d, v))
        recs.sort()
        dates = [excel_date(d) for d, _ in recs]
        # continuity check: month index increments by exactly 1
        def ym(s):
            return int(s[:4]) * 12 + int(s[5:7])
        contiguous = all(ym(dates[i + 1]) - ym(dates[i]) == 1 for i in range(len(dates) - 1))
        unique = len(set(dates)) == len(dates)
        vals = [v[U_COL] for _, v in recs if isinstance(v.get(U_COL), float)]
        # header sanity: locate the G5-G1 label and its column
        header_hits = [(r, c) for r, cells in rows.items() for c, val in cells.items()
                       if isinstance(val, str) and "G5-G1" in val]
        header_ok = any(c == U_COL for _, c in header_hits)
        mean_m = statistics.fmean(vals)
        mean_ann_pct = mean_m * 12.0 * 100.0
        # audit: U vs T-P row-level discrepancy (T=20, P=16)
        tp_diffs = [abs(v[U_COL] - (v.get(20, float("nan")) - v.get(16, float("nan"))))
                    for _, v in recs if all(isinstance(v.get(c), float) for c in (16, 20, U_COL))]
        max_tp = max(tp_diffs) if tp_diffs else None
        results_by_panel[panel] = {
            "sheet": sheet_name, "date_col": dcol, "u_col": U_COL,
            "n_months": len(vals), "first": dates[0], "last": dates[-1],
            "contiguous": contiguous, "unique_dates": unique, "header_ok": header_ok,
            "header_hits": header_hits[:5],
            "mean_monthly_decimal": mean_m, "mean_annualized_pct": mean_ann_pct,
            "std_monthly_pct": statistics.stdev(vals) * 100 if len(vals) > 1 else None,
            "max_abs_U_minus_TP": max_tp,
        }
        manifest_by_panel[panel] = {"sheet": sheet_name, "n_months": len(vals),
                                    "first": dates[0], "last": dates[-1],
                                    "date_col": dcol, "u_col": U_COL}
        log("\n[%s] %s: n=%d %s..%s contiguous=%s unique=%s header_U_G5G1=%s" %
            (panel, sheet_name, len(vals), dates[0], dates[-1], contiguous, unique, header_ok))
        log("  mean monthly (decimal)=%.15g -> annualized %.15f%%" % (mean_m, mean_ann_pct))
        log("  max |U - (T-P)| row-level = %s" % max_tp)

    A = results_by_panel["PanelA"]["mean_annualized_pct"]
    B = results_by_panel["PanelB"]["mean_annualized_pct"]
    paper_A = CFG["published_targets"]["P008-R10"]["paper_value_pct"]
    paper_B = CFG["published_targets"]["P008-R11"]["paper_value_pct"]
    ref_A = CFG["reviewer_reference"]["P008-R10_pct"]
    ref_B = CFG["reviewer_reference"]["P008-R11_pct"]
    log("\n[COMPARISON]")
    log("  R10 paper %.2f%% vs recompute %.15f%% diff %.6f pp (tol %.3f)" % (paper_A, A, A - paper_A, tol))
    log("  R11 paper %.2f%% vs recompute %.15f%% diff %.6f pp (tol %.3f)" % (paper_B, B, B - paper_B, tol))
    log("  reviewer R10 %.15f%% diff %.3e ; reviewer R11 %.15f%% diff %.3e" %
        (ref_A, A - ref_A, ref_B, B - ref_B))

    checks = {
        "download_hash_matches": ok_hash,
        "download_size_matches": ok_size,
        "panelA_674_months_1963_02_to_2019_03": results_by_panel["PanelA"]["n_months"] == 674 and
            results_by_panel["PanelA"]["first"] == "1963-02-28" and results_by_panel["PanelA"]["last"] == "2019-03-31",
        "panelB_674_months_1963_02_to_2019_03": results_by_panel["PanelB"]["n_months"] == 674 and
            results_by_panel["PanelB"]["first"] == "1963-02-28" and results_by_panel["PanelB"]["last"] == "2019-03-31",
        "panelA_contiguous_unique": results_by_panel["PanelA"]["contiguous"] and results_by_panel["PanelA"]["unique_dates"],
        "panelB_contiguous_unique": results_by_panel["PanelB"]["contiguous"] and results_by_panel["PanelB"]["unique_dates"],
        "header_U_is_G5G1": results_by_panel["PanelA"]["header_ok"] and results_by_panel["PanelB"]["header_ok"],
        "R10_within_tolerance": abs(A - paper_A) <= tol,
        "R11_within_tolerance": abs(B - paper_B) <= tol,
        "R10_matches_reviewer": abs(A - ref_A) < 1e-9,
        "R11_matches_reviewer": abs(B - ref_B) < 1e-9,
    }
    all_pass = all(checks.values())
    log("\n[CHECKS] " + ", ".join("%s=%s" % (k, v) for k, v in checks.items()))

    # comparison rows
    cfg_sha = sha256_file(os.path.join(HERE, "config.json"))
    code_sha = sha256_file(os.path.abspath(__file__))
    common = {
        "reviewed_source_commit": CFG["reviewed_source_commit"], "execution_commit": "null",
        "approval_record_id": CFG["approval_record_id"], "paper_id": "P008",
        "canonical_version_id": CFG["canonical_version_id"], "experiment_id": "P008-E03",
        "reproduction_type": CFG["reproduction_type"], "experiment_purpose": CFG["experiment_purpose"],
        "execution_authorized": "true", "run_id": CFG["run_id"],
        "execution_status": "EXECUTED" if all_pass else "EXECUTED_WITH_EXCEPTIONS",
        "performed_by": "general-purpose-3",
        "input_manifest": json.dumps({
            "url": CFG["input"]["url"], "http_code": CFG["input"]["download_http_code"],
            "obtained_utc": CFG["input"]["download_utc"], "sha256": h, "size_bytes": size,
            "version": "AQR author workbook vF (labelled JFE forthcoming in file era)",
            "shape": {"PanelA": manifest_by_panel["PanelA"], "PanelB": manifest_by_panel["PanelB"]},
            "date_range": "1963-02-28..2019-03-31, 674 monthly observations, contiguous and unique",
            "column_definition": "supplier U column (G5-G1) decimal monthly total-return spread",
            "status": "FULL_REQUIRED_DATA_ACCESSED; independent fresh download + recompute",
        }, ensure_ascii=False),
        "code_commit_or_sha256": code_sha, "config_path": "config.json",
        "config_sha256": cfg_sha, "environment_path": "environment.json",
        "actual_command": "curl download; then python3 source.py > run_stdout.log 2> run_stderr.log",
        "log_paths": "run_stdout.log;run_stderr.log;download_stderr.txt",
        "tolerance_frozen_at": CFG["tolerance_frozen_at_utc"] + " (before result inspection)",
        "market_economic_verdict": "NOT_ASSESSED", "original_run_acceptance": "NOT_ASSESSED",
        "deviations_from_paper": "Method frozen from protocol: supplier U column, arithmetic monthly mean*12*100, no RF subtraction, no month filtering; no regression/t-stat layer.",
        "evidence_ids": "P008-S11;P008-B02;reviewer-workbook-recompute",
        "remaining_blockers": "P008-R12/R13 six-factor alpha/t-stats remain P008-E04 NOT_RUN (factor vintage and SE unfrozen).",
    }
    FIELDS = [
        "reviewed_source_commit", "execution_commit", "approval_record_id", "paper_id",
        "canonical_version_id", "experiment_id", "result_id", "reproduction_type",
        "experiment_purpose", "execution_authorized", "run_id", "execution_status",
        "performed_by", "input_manifest", "code_commit_or_sha256", "config_path",
        "config_sha256", "environment_path", "actual_command", "log_paths",
        "output_paths_and_hashes", "reference_kind", "source_location", "paper_value",
        "reference_value", "replication_value", "unit", "tolerance_rule",
        "tolerance_frozen_at", "absolute_error", "relative_error", "relative_error_note",
        "numerical_verdict", "theoretical_mechanism_verdict", "market_economic_verdict",
        "original_run_acceptance", "deviations_from_paper", "evidence_ids",
        "remaining_blockers",
    ]
    rows = []
    def add(result_id, ref_kind, src, paper_val, ref_val, rep_val, unit, rule, ae, re, nv, note=""):
        r = dict(common)
        r.update({
            "result_id": result_id, "reference_kind": ref_kind, "source_location": src,
            "paper_value": str(paper_val), "reference_value": str(ref_val),
            "replication_value": str(rep_val), "unit": unit, "tolerance_rule": rule,
            "absolute_error": ("" if ae is None else str(ae)),
            "relative_error": ("" if re is None else str(re)), "relative_error_note": note,
            "numerical_verdict": nv, "theoretical_mechanism_verdict": "NOT_APPLICABLE(input-layer mean)",
        })
        rows.append(r)

    for rid, panel, paper, ref, val in [("P008-R10", "PanelA", paper_A, ref_A, A),
                                        ("P008-R11", "PanelB", paper_B, ref_B, B)]:
        add(rid, "PUBLISHED_VALUE", "Table 4 %s / G / Average excess return" % panel,
            "%.2f%%" % paper, "%.2f%%" % paper, "%.15f%%" % val, "annualized percentage points",
            "+/-%.3f pp frozen before inspection" % tol, abs(val - paper), abs(val - paper) / paper,
            "PASS" if abs(val - paper) <= tol else "CHECK",
            "independent fresh download + recompute from author workbook")
        add(rid, "REVIEWER_CALCULATION",
            "reviewer recompute of same workbook (registered evidence; performed_by=reviewer)",
            "%.2f%%" % paper, "%.15f%%" % ref, "%.15f%%" % val, "annualized percentage points",
            "agreement with reviewer reference within 1e-9 pp", abs(val - ref), None,
            "PASS" if abs(val - ref) < 1e-9 else "CHECK",
            "reviewer original_run_acceptance=NOT_ASSESSED; this run independently reproduced the same number")
    add("P008-R10", "PUBLISHED_VALUE", "input workbook sha256 (fresh download)",
        CFG["input"]["expected_sha256"], CFG["input"]["expected_sha256"], h,
        "sha256", "exact", None, None, "PASS" if ok_hash else "CHECK", "HTTP 200, 215209 bytes")
    add("P008-R11", "PUBLISHED_VALUE", "input workbook date/sample shape",
        "674 months 1963-02-28..2019-03-31", "674 months 1963-02-28..2019-03-31",
        "%d months %s..%s" % (results_by_panel["PanelB"]["n_months"],
                              results_by_panel["PanelB"]["first"], results_by_panel["PanelB"]["last"]),
        "months", "exact count and endpoints", None, None,
        "PASS" if checks["panelB_674_months_1963_02_to_2019_03"] else "CHECK", "")

    results = {
        "metadata": {
            "run_id": CFG["run_id"], "generated_utc": datetime.now(timezone.utc).isoformat(),
            "python": sys.version.split()[0], "source_sha256": code_sha, "config_sha256": cfg_sha,
            "purpose": CFG["experiment_purpose"], "all_checks_pass": all_pass,
            "download_url": CFG["input"]["url"], "downloaded_sha256": h, "downloaded_size": size,
        },
        "input_manifest": common["input_manifest"],
        "panels": results_by_panel,
        "comparison": {
            "P008-R10": {"paper_pct": paper_A, "recompute_pct": A, "reviewer_pct": ref_A,
                         "diff_paper_pp": A - paper_A, "diff_reviewer_pp": A - ref_A},
            "P008-R11": {"paper_pct": paper_B, "recompute_pct": B, "reviewer_pct": ref_B,
                         "diff_paper_pp": B - paper_B, "diff_reviewer_pp": B - ref_B},
        },
        "checks": checks, "comparison_rows": rows,
    }
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(HERE, "target_comparison.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    with open(os.path.join(HERE, "run_internal.log"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(LOG) + "\n")
    log("\nWROTE results.json, target_comparison.csv, run_internal.log")
    log("ALL CHECKS PASS = %s" % all_pass)

if __name__ == "__main__":
    main()
