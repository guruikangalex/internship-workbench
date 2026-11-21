#!/usr/bin/env python3
"""Build discrepancy_analysis.csv for the 25 itemized FAIL/PARTIAL rows.

Pulls numbers from target_comparison_r4.csv (R4 regenerated) with the R3 verdict
from the preserved target_comparison.csv alongside, so no old record is lost.
"""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))

r4 = list(csv.DictReader(open(os.path.join(HERE, "target_comparison_r4.csv"), encoding="utf-8-sig")))
r3 = {r["result_id"]: r["numerical_verdict"] for r in
      csv.DictReader(open(os.path.join(HERE, "target_comparison.csv"), encoding="utf-8-sig"))}

fields = ["result_id", "paper_value", "author_cache_value", "cold_run_value",
          "absolute_error", "tolerance", "verdict_r3", "verdict_r4", "verdict_changed",
          "suspected_cause", "confirming_test"]
out = []
for r in r4:
    v4 = r["numerical_verdict"]
    v3 = r3.get(r["result_id"], "UNKNOWN")
    if v4 in ("FAIL", "PARTIAL", "NOT_ASSESSED") or v3 in ("FAIL", "PARTIAL"):
        out.append({
            "result_id": r["result_id"],
            "paper_value": r["paper_value"],
            "author_cache_value": r["author_cache_value"],
            "cold_run_value": r["cold_run_value"],
            "absolute_error": r["absolute_error"],
            "tolerance": r["tolerance_rule"],
            "verdict_r3": v3,
            "verdict_r4": v4,
            "verdict_changed": "YES" if v3 != v4 else "NO",
            "suspected_cause": r["suspected_cause"],
            "confirming_test": r["confirming_test"],
        })

fp = os.path.join(HERE, "discrepancy_analysis.csv")
with open(fp, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for row in out:
        w.writerow(row)
from collections import Counter
print("rows:", len(out), "R4 verdicts:", Counter(r["verdict_r4"] for r in out))
print("changed:", sum(1 for r in out if r["verdict_changed"] == "YES"))
for r in out:
    if r["verdict_changed"] == "YES":
        print("  CHANGED", r["result_id"], r["verdict_r3"], "->", r["verdict_r4"])
print("wrote", fp)
