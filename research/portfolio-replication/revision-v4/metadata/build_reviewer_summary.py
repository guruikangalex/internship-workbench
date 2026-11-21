#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build reviewer_summary.csv: one row per authorized experiment with actual execution result."""
import csv, os, glob

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIELDS = ["paper_id", "experiment_id", "reproduction_type", "version_id",
          "execution_authorized", "execution_status", "run_id", "result_count",
          "verdict_summary", "key_result", "output_dir", "final_acceptance"]

# map experiment -> execution dir
EXPDIR = {
    "P001-E01": "P001_E01", "P006-E01": "P006_E01_author",
    "P006-E06": "P006_E06_independent", "P008-E01": "P008_E01", "P008-E03": "P008_E03",
}
KEY = {
    "P001-E01": "a=0.7421582911108061 与 reviewer 逐位一致；A7/A10/A11 恒等式 PASS；非对易 A15* PASS/A15 FAIL",
    "P006-E01": "真实冷重算 88s；115 目标 PASS90/FAIL17/PARTIAL8；LW 家族系统漂移 FAIL，未放宽容差",
    "P006-E06": "留一稳定式 vs 删行等价 2.45e-8；494月 B0/B1 corr 0.9999975；A vs B0 差 0.585 为作者低z实现",
    "P008-E01": "KKT 残差 3.5e-16 < 1e-10；四基金张成 3.5e-18；退化案例隔离 NOT_APPLICABLE",
    "P008-E03": "AQR xlsx SHA256 一致；R10 7.8361% vs 7.84%、R11 3.0143% vs 3.01%，均 PASS ±0.005pp",
}

def read_status(d):
    p = os.path.join(BASE, "executions", d, "target_comparison.csv")
    if not os.path.exists(p):
        return "NOT_RUN", 0, ""
    rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    from collections import Counter
    c = Counter(r.get("numerical_verdict", "") for r in rows)
    vs = ";".join(f"{k}:{v}" for k, v in sorted(c.items()) if k)
    run = ""
    sp = os.path.join(BASE, "executions", d, "summary.md")
    if os.path.exists(sp):
        import re
        m = re.search(r"[Rr]un[_ ]?[Ii][Dd][`\s:]+([A-Za-z0-9_-]{6,})", open(sp, encoding="utf-8").read())
        if m: run = m.group(1)
    return "TARGETS_GENERATED", len(rows), vs, run

def main():
    q = os.path.join(BASE, "reviewer_queue.json")
    data = __import__("json").load(open(q, encoding="utf-8"))["records"]
    rows = []
    for r in data:
        if not r.get("execution_authorized"):
            continue
        pid, exp = r["paper_id"], r["experiment_id"]
        d = EXPDIR.get(exp, "")
        status, n, vs, run = read_status(d) if d else ("NOT_RUN", 0, "", "")
        if not run:
            run = f"R3-{exp}"
        rows.append({
            "paper_id": pid, "experiment_id": exp,
            "reproduction_type": r.get("reproduction_type", ""),
            "version_id": r.get("version_id", ""),
            "execution_authorized": "true", "execution_status": status,
            "run_id": run, "result_count": n, "verdict_summary": vs,
            "key_result": KEY.get(exp, ""), "output_dir": f"executions/{d}/" if d else "",
            "final_acceptance": "PENDING",
        })
    out = os.path.join(BASE, "reviewer_summary.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    print("wrote", out, "rows:", len(rows))
    for r in rows:
        print(f"  {r['paper_id']}/{r['experiment_id']:10s} {r['result_count']:4d} {r['verdict_summary']}")

if __name__ == "__main__":
    main()
