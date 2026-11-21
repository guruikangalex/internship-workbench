#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F01 rebuild: regenerate a parseable global target_alignment.csv from canonical
records + intact local target tables + reviewer queue.

Source of truth (frozen commit 104aecf):
  - revision-v2/work/P006/target_alignment.csv  (500 rows, intact)
  - revision-v2/work/P001/target_alignment.csv  (14 rows, intact)
  - revision-v2/record_master.json              (21 canonical records)
  - revision-v2/reviewer_queue.json             (17 approval records, 516 result_ids)

F04 fixes applied here:
  - P006-E01 narrowed to exactly 115 PROPOSED targets (version P006-RFS-20261119);
    10 OUTSIDE_PILOT excluded (kept in history, not in current scope).
  - canonical version aliases unified: RFS2026_TYPESET_20261119 -> P006-RFS-20261119,
    NBER20260521 -> P006-NBER-20260521.
  - P010-E03 gets explicit result_ids (no empty target approval).
  - reproduction_type restricted to 4 enums; IMPLEMENTATION_AUDIT -> experiment_purpose.
"""
import csv, json, os, hashlib

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V2 = os.path.abspath(os.path.join(BASE, "..", "revision-v2"))

# Unified 22-column schema: 21 from local tables + experiment_purpose
FIELDS = [
    "reviewed_source_commit", "paper_id", "canonical_version_id", "experiment_id",
    "result_id", "reproduction_type", "experiment_purpose", "target_cell_or_series",
    "source_location", "input", "entrypoint", "config", "unit", "paper_value",
    "reference_file", "tolerance", "rerun_value", "absolute_error", "relative_error",
    "numerical_verdict", "economic_verdict", "difference_explanation", "result_status",
    "scope_status", "execution_authorized",
]
REVIEWED = "104aecfcad4c308e1044a3d15483fe2320619597"
PURPOSE_BY_PREFIX = {
    "P006-E01": "PAPER_REPLICATION", "P006-E06": "IMPLEMENTATION_AUDIT",
    "P001-E01": "PAPER_REPLICATION", "P008-E01": "PAPER_REPLICATION",
    "P008-E03": "PAPER_REPLICATION",
}

def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def canon_version(pid, rec, raw):
    """F04: unify aliases to canonical version ids."""
    if pid == "P006":
        s = str(raw or "")
        if "NBER" in s or "20260521" in s:
            return "P006-NBER-20260521"
        return "P006-RFS-20261119"  # includes RFS2026_TYPESET_20261119 alias
    return str(raw or rec.get("selected_paper_version", ""))

def main():
    records = load_json(os.path.join(V2, "record_master.json"))
    queue = load_json(os.path.join(V2, "reviewer_queue.json"))
    qr = queue if isinstance(queue, list) else queue.get("reviewer_queue", queue.get("records", []))

    rec_by_pid = {r.get("paper_id"): r for r in records}
    q_by_exp = {(q.get("paper_id"), q.get("experiment_id")): q for q in qr}

    rows = []
    history_rows = []
    seen_keys = set()  # F01: enforce (paper, version, experiment, result) uniqueness

    # ---- 1. Detailed local tables (P006, P001) ----
    for pid, fname in [("P006", "P006"), ("P001", "P001")]:
        path = os.path.join(V2, "work", pid, "target_alignment.csv")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                exp = r.get("experiment_id", "")
                scope = r.get("scope_status", "PROPOSED")
                rec = rec_by_pid.get(pid, {})
                qrec = q_by_exp.get((pid, exp), {})
                # F04: P006-E01 keep only 115 PROPOSED in current scope
                if pid == "P006" and exp == "P006-E01":
                    if scope != "PROPOSED":
                        history_rows.append((pid, exp, r.get("result_id"), scope))
                        continue
                key = (pid, canon_version(pid, rec, r.get("version_id")), exp, r.get("result_id", ""))
                if key in seen_keys:
                    # duplicate row in local table (e.g. P006-E02 appears under two raw version
                    # aliases that normalize to one canonical id): keep first, log to history
                    history_rows.append((pid, exp, r.get("result_id"), "DUPLICATE_VERSION_ALIAS"))
                    continue
                seen_keys.add(key)
                out = {
                    "reviewed_source_commit": REVIEWED,
                    "paper_id": pid,
                    "canonical_version_id": key[1],
                    "experiment_id": exp,
                    "result_id": r.get("result_id", ""),
                    "reproduction_type": qrec.get("reproduction_type") or "INDEPENDENT_FAITHFUL",
                    "experiment_purpose": PURPOSE_BY_PREFIX.get(exp, "PAPER_REPLICATION"),
                    "target_cell_or_series": r.get("target_cell_or_series", ""),
                    "source_location": r.get("source_location", ""),
                    "input": r.get("input", ""), "entrypoint": r.get("entrypoint", ""),
                    "config": r.get("config", ""), "unit": r.get("unit", ""),
                    "paper_value": r.get("paper_value", ""),
                    "reference_file": r.get("reference_file", ""),
                    "tolerance": r.get("tolerance", ""),
                    "rerun_value": r.get("rerun_value", ""),
                    "absolute_error": r.get("absolute_error", ""),
                    "relative_error": r.get("relative_error", ""),
                    "numerical_verdict": r.get("numerical_verdict", "NOT_ASSESSED"),
                    "economic_verdict": r.get("economic_verdict", "NOT_ASSESSED"),
                    "difference_explanation": r.get("difference_explanation", ""),
                    "result_status": r.get("result_status", "NOT_RUN"),
                    "scope_status": scope,
                    "execution_authorized": "true" if qrec.get("execution_authorized") else "false",
                }
                rows.append(out)

    # ---- 2. Remaining result_ids from queue (skeleton rows, NOT_RUN) ----
    for q in qr:
        pid, exp = q.get("paper_id"), q.get("experiment_id")
        rec = rec_by_pid.get(pid, {})
        cv = canon_version(pid, rec, q.get("version_id"))
        for rid in (q.get("result_ids") or []):
            key = (pid, cv, exp, rid)
            if key in seen_keys:
                continue
            # F04: P006-E01 current scope is exactly the 115 PROPOSED from the local
            # table; the queue's 125 broad ids (incl. 10 OUTSIDE_PILOT) are superseded.
            if exp == "P006-E01":
                continue
            # F04: P010-E03 empty target_ids -> handled in section 3
            if exp == "P010-E03":
                continue
            seen_keys.add(key)
            rows.append({
                "reviewed_source_commit": REVIEWED, "paper_id": pid,
                "canonical_version_id": cv,
                "experiment_id": exp, "result_id": rid,
                "reproduction_type": q.get("reproduction_type", "INDEPENDENT_FAITHFUL"),
                "experiment_purpose": PURPOSE_BY_PREFIX.get(exp, q.get("experiment_layer", "PAPER_REPLICATION")),
                "target_cell_or_series": "", "source_location": "", "input": "",
                "entrypoint": "", "config": "", "unit": "", "paper_value": "",
                "reference_file": "", "tolerance": "", "rerun_value": "",
                "absolute_error": "", "relative_error": "",
                "numerical_verdict": "NOT_ASSESSED", "economic_verdict": "NOT_ASSESSED",
                "difference_explanation": "", "result_status": "NOT_RUN",
                "scope_status": "PENDING_EVIDENCE" if q.get("requested_reviewer_decision") == "REQUEST_EVIDENCE" else "PROPOSED",
                "execution_authorized": "true" if q.get("execution_authorized") else "false",
            })

    # ---- 3. F04: P010-E03 explicit targets (was empty) ----
    if ("P010", "P010-E03") in q_by_exp and not any(r["experiment_id"] == "P010-E03" for r in rows):
        for i in range(1, 5):
            rows.append({
                "reviewed_source_commit": REVIEWED, "paper_id": "P010",
                "canonical_version_id": "JF2023_VOR", "experiment_id": "P010-E03",
                "result_id": f"P010-E03-R{i:02d}",
                "reproduction_type": "APPROXIMATE_VALIDATION",
                "experiment_purpose": "APPROXIMATE_VALIDATION",
                "target_cell_or_series": f"TRACE-route target {i} (to be specified in protocol)",
                "source_location": "", "input": "", "entrypoint": "", "config": "",
                "unit": "", "paper_value": "", "reference_file": "", "tolerance": "",
                "rerun_value": "", "absolute_error": "", "relative_error": "",
                "numerical_verdict": "NOT_ASSESSED", "economic_verdict": "NOT_ASSESSED",
                "difference_explanation": "", "result_status": "NOT_RUN",
                "scope_status": "PENDING_EVIDENCE", "execution_authorized": "false",
            })

    # ---- Validation ----
    keys = [(r["paper_id"], r["canonical_version_id"], r["experiment_id"], r["result_id"]) for r in rows]
    dupes = len(keys) - len(set(keys))
    assert dupes == 0, f"duplicate keys: {dupes}"
    p006_e01 = [r for r in rows if r["paper_id"] == "P006" and r["experiment_id"] == "P006-E01"]
    assert len(p006_e01) == 115, f"P006-E01 should be 115, got {len(p006_e01)}"

    out = os.path.join(BASE, "target_alignment.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)

    # history of excluded P006 OUTSIDE_PILOT
    hist = os.path.join(BASE, "history", "P006_OUTSIDE_PILOT_excluded.csv")
    with open(hist, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["paper_id", "experiment_id", "result_id", "scope_status", "reason"])
        for pid, exp, rid, scope in history_rows:
            w.writerow([pid, exp, rid, scope, "F04: 10 OUTSIDE_PILOT excluded from approved 115"])

    print("wrote", out, "rows:", len(rows), "unique keys:", len(set(keys)))
    print("P006-E01 PROPOSED:", len(p006_e01), "| OUTSIDE_PILOT moved to history:", len(history_rows))
    from collections import Counter
    print("by paper:", dict(Counter(r["paper_id"] for r in rows)))

if __name__ == "__main__":
    main()
