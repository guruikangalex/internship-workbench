#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R3 deliverable validation: CSV/JSON parse, enums, key uniqueness, evidence coverage."""
import csv, json, os, sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
errs = []

def chk(cond, msg):
    if not cond:
        errs.append(msg)

# --- CSV parse ---
for fn in ["master_table.csv", "target_alignment.csv", "evidence_index.csv",
           "issue_closure_r3.csv", "coverage_matrix.csv"]:
    p = os.path.join(BASE, fn)
    if not os.path.exists(p):
        errs.append(f"missing {fn}"); continue
    try:
        rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
        print(f"{fn}: {len(rows)} rows, {len(rows[0]) if rows else 0} cols")
    except Exception as e:
        errs.append(f"cannot parse {fn}: {e}")

# --- JSON parse ---
for fn in ["record_master.json", "reviewer_queue.json"]:
    p = os.path.join(BASE, fn)
    if not os.path.exists(p):
        errs.append(f"missing {fn}"); continue
    try:
        d = json.load(open(p, encoding="utf-8")); print(f"{fn}: OK")
    except Exception as e:
        errs.append(f"cannot parse {fn}: {e}")

# --- target alignment key uniqueness + P006-E01=115 ---
ta = os.path.join(BASE, "target_alignment.csv")
if os.path.exists(ta):
    rows = list(csv.DictReader(open(ta, encoding="utf-8-sig")))
    keys = [(r["paper_id"], r["canonical_version_id"], r["experiment_id"], r["result_id"]) for r in rows]
    chk(len(keys) == len(set(keys)), "target_alignment duplicate keys")
    n = sum(1 for r in rows if r["experiment_id"] == "P006-E01")
    chk(n == 115, f"P006-E01 targets {n} != 115")
    print("target keys unique:", len(keys) == len(set(keys)), "| P006-E01:", n)

# --- evidence coverage ---
recs = json.load(open(os.path.join(BASE, "record_master.json"), encoding="utf-8"))
ei = list(csv.DictReader(open(os.path.join(BASE, "evidence_index.csv"), encoding="utf-8-sig")))
covered = {r["evidence_id"] for r in ei}
crit = set()
for r in recs:
    crit |= set(r.get("critical_evidence_ids") or [])
chk(crit <= covered, f"critical evidence uncovered: {len(crit - covered)}")
print(f"critical evidence covered: {len(crit & covered)}/{len(crit)}")

# --- reproduction_type enum only 4 ---
TA = {"AUTHOR_CODE_RERUN", "INDEPENDENT_FAITHFUL", "APPROXIMATE_VALIDATION", "RESEARCH_EXTENSION"}
q = json.load(open(os.path.join(BASE, "reviewer_queue.json"), encoding="utf-8"))["records"]
bad = {(r.get("paper_id"), r.get("experiment_id"), r.get("reproduction_type"))
       for r in q if r.get("reproduction_type") and r["reproduction_type"] not in TA}
chk(not bad, f"bad reproduction types: {bad}")
auth = [(r["paper_id"], r["experiment_id"]) for r in q if r.get("execution_authorized")]
chk(len(auth) == 5, f"authorized count {len(auth)} != 5")
print("authorized:", auth)

if errs:
    print("VALIDATION FAILED:")
    for e in errs: print("  -", e)
    sys.exit(1)
print("VALIDATION PASSED")
