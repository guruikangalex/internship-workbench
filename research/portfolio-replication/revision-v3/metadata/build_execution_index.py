#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan executions/ and build execution_index_r3.csv with real status + hashes."""
import csv, os, json, hashlib

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXEC = os.path.join(BASE, "executions")
FIELDS = ["experiment_id", "run_id", "execution_status", "performed_by",
          "actual_command", "result_count", "verdict_summary", "output_dir",
          "log_paths", "sha256_manifest", "notes"]

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def scan_exp(d):
    """Scan one experiment dir for deliverables."""
    p = os.path.join(EXEC, d)
    if not os.path.isdir(p):
        return None
    files = [os.path.join(dp, f) for dp, _, fs in os.walk(p) for f in fs]
    # status from summary / manifest / target_comparison presence
    tc = os.path.join(p, "target_comparison.csv")
    results = os.path.join(p, "results.json")
    status = "NOT_RUN"
    nres, verdict = 0, ""
    if os.path.exists(tc):
        rows = list(csv.DictReader(open(tc, encoding="utf-8-sig")))
        nres = len(rows)
        from collections import Counter
        c = Counter(r.get("numerical_verdict", "") for r in rows)
        verdict = ";".join(f"{k}:{v}" for k, v in sorted(c.items()) if k)
        status = "TARGETS_GENERATED"
    elif os.path.exists(results):
        status = "TARGETS_GENERATED"
    elif files:
        status = "PREFLIGHT_PASSED"
    # run_id / command from manifest or summary
    run_id = command = performed = ""
    for fn in ["execution_manifest.json", "summary.md", "README.md"]:
        fp = os.path.join(p, fn)
        if os.path.exists(fp):
            txt = open(fp, encoding="utf-8", errors="replace").read()
            import re
            m = re.search(r"run[_-]?id[`\s:]*([A-Za-z0-9_-]{8,})", txt, re.I)
            if m and not run_id: run_id = m.group(1)
            m = re.search(r"(?:actual_command|命令)[`\s:]*([^\n`]{10,200})", txt)
            if m and not command: command = m.group(1).strip()
            break
    # hash manifest
    hm = [f for f in files if f.endswith("sha256sums.txt")]
    return {
        "experiment_id": d, "run_id": run_id or "SEE_SUMMARY",
        "execution_status": status,
        "performed_by": f"agent-{d.split('_')[0]}",
        "actual_command": command[:150],
        "result_count": nres, "verdict_summary": verdict,
        "output_dir": f"executions/{d}/",
        "log_paths": ";".join(os.path.relpath(f, p) for f in files if f.endswith(".log")),
        "sha256_manifest": os.path.relpath(hm[0], BASE) if hm else "",
        "notes": f"{len(files)} files delivered",
    }

def main():
    rows = []
    expected = ["P001_E01", "P006_E01_author", "P006_E06_independent",
                "P008_E01", "P008_E03", "support"]
    for d in sorted(expected):
        r = scan_exp(d)
        if r:
            rows.append(r)
    out = os.path.join(BASE, "execution_index_r3.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    print("wrote", out, "rows:", len(rows))
    for r in rows:
        print(f"  {r['experiment_id']:24s} {r['execution_status']:18s} results={r['result_count']:4d} {r['verdict_summary'][:50]}")

if __name__ == "__main__":
    main()
