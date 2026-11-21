#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R3 issue closure table: F01-F05 + reviewer-boundary issues + execution handoff."""
import csv, os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIELDS = ["issue_id", "category", "paper_id", "question", "change", "evidence",
          "closure_status", "independent_review", "remaining"]

rows = [
    ["R3-F01", "HANDOFF", "ALL", "Corrupted global target_alignment.csv (360061B, SHA dba11b13)",
     "Regenerated UTF-8 CSV 779 rows/25 cols from canonical records + intact local tables; unique keys; P006-E01 exactly 115",
     "target_alignment.csv; metadata/build_target_alignment.py; history/P006_OUTSIDE_PILOT_excluded.csv",
     "CONFIRMED", "Parsed with csv.DictReader; 779 unique (paper,version,exp,result); P006-E01=115", "None"],
    ["R3-F02", "HANDOFF", "ALL", "Missing real execution materials (source/config/env/logs/trajectories)",
     "Execution agents deliver self-authored code/config/env/logs/results with per-experiment run_id; large inputs via stable URL+hash",
     "executions/*/ (per-agent); execution_index_r3.csv; evidence_index.csv",
     "IN_PROGRESS", "Total-control verifies each experiment folder on agent return", "Depends on execution agents completing"],
    ["R3-F03", "HANDOFF", "ALL", "Evidence index only 6 rows vs 180 canonical / 84 critical ids",
     "Built 186-row evidence_index.csv: 53 resolved from source cards, 127 explicit DETAILS_NOT_IN_FROZEN_PACKAGE with recovery path, 6 legacy",
     "evidence_index.csv; metadata/build_evidence_index.py",
     "CONFIRMED", "84/84 critical ids covered; no fabricated URLs", "127 historical ids need source-card recovery for full detail"],
    ["R3-F04", "CONSISTENCY", "P006", "125 targets / two version aliases in queue",
     "P006-E01 narrowed to 115 PROPOSED; aliases canonicalized; E06 added with approval source; OUTSIDE_PILOT to history",
     "reviewer_queue.json; target_alignment.csv; history/P006_OUTSIDE_PILOT_excluded.csv",
     "CONFIRMED", "115 unique targets verified", "None"],
    ["R3-F04b", "CONSISTENCY", "P004/P002/P010", "Version/experiment mapping and empty TRACE targets",
     "P004 QF/arXiv/code map in support; P002 E01 superseded-by E21; P010-E03 got 4 explicit result ids",
     "reviewer_queue.json; executions/support/*",
     "CONFIRMED", "Queue shows P010-E03 result_ids non-empty; P002-E01 superseded_by set", "P004 formal-version horizon still under review (REV2-P004-02 stays OPEN)"],
    ["R3-F05", "CONSISTENCY", "P001/P003/P007/P008/P009/P010", "Stale instructions in current records",
     "Current-state corrections applied; old values moved to versioned history",
     "record_master.json; history/F05_superseded_current_fields.json; metadata/r3_baseline.md",
     "CONFIRMED", "5 superseded fields recorded with old values and reasons", "None"],
    ["R3-APPR-01", "APPROVAL", "P001/P006/P008", "Five experiments authorized in review 104aecf",
     "execution_authorized=true for P001-E01, P006-E01, P006-E06, P008-E01, P008-E03; approval_record_id set",
     "reviewer_queue.json; metadata/build_canonical_r3.py",
     "CONFIRMED", "5 entries verified in queue", "Execution results pending from agents"],
    ["R3-APPR-02", "APPROVAL", "P006-E05/P010-E01/P002-E21", "HOLD/REQUEST_EVIDENCE scopes not auto-upgraded",
     "P006-E05 kept HOLD and retired from current request; P010-E01 HOLD; P002-E21 REQUEST_EVIDENCE",
     "reviewer_queue.json", "CONFIRMED", "No unauthorized scope flagged as execution_authorized", "None"],
    ["R3-ATTACH", "BASELINE", "ALL", "Review attachments not provided",
     "Recorded non-availability; proceeded from task text + frozen commit + original sources; no claim of reading attachments",
     "metadata/r3_baseline.md", "CONFIRMED", "Baseline documents exact state", "Attachments can be supplied later for cross-check"],
]

out = os.path.join(BASE, "issue_closure_r3.csv")
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(FIELDS); w.writerows(rows)
print("wrote", out, "rows:", len(rows))
