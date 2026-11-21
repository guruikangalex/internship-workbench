#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R3 canonical build: single source of truth -> record_master.json, master_table.csv,
reviewer_queue.json.

Applies reviewer freeze (REVIEW-104AECF-20261121 / commit 104aecf):
  F04 version aliases + experiment ids unified.
  F05 stale instructions removed from current records (moved to history/).
  §2 approvals: P001-E01, P006-E01, P006-E06, P008-E01, P008-E03 authorized;
  P010-E03 gets explicit targets; P002-E01/E21 merge relationship recorded.
"""
import csv, json, os, copy

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V2 = os.path.abspath(os.path.join(BASE, "..", "revision-v2"))
REVIEWED = "104aecfcad4c308e1044a3d15483fe2320619597"
APPROVAL = "REVIEW-104AECF-20261121"

# ---- F04 canonical version map ----
VERSION_ALIAS = {
    "RFS2026_TYPESET_20261119": "P006-RFS-20261119",
    "RFS 2026 typeset 2026-11-19": "P006-RFS-20261119",
    "NBER20260521": "P006-NBER-20260521",
}

# ---- §2.1 authorized experiments ----
AUTHORIZED = {
    ("P001", "P001-E01"): ("JF2013_A15STAR", "INDEPENDENT_FAITHFUL", "APPROVE_FAITHFUL_REPLICATION"),
    ("P006", "P006-E01"): ("P006-RFS-20261119", "AUTHOR_CODE_RERUN", "APPROVE_FAITHFUL_REPLICATION"),
    ("P006", "P006-E06"): ("P006-RFS-20261119", "INDEPENDENT_FAITHFUL", "APPROVE_FAITHFUL_REPLICATION"),
    ("P008", "P008-E01"): ("JFE2021_VOR", "INDEPENDENT_FAITHFUL", "APPROVE_FAITHFUL_REPLICATION"),
    ("P008", "P008-E03"): ("JFE2021_VOR", "INDEPENDENT_FAITHFUL", "APPROVE_FAITHFUL_REPLICATION"),
}

def canon_version(pid, raw):
    s = str(raw or "")
    if pid == "P006":
        if "NBER" in s or "20260521" in s:
            return "P006-NBER-20260521"
        return "P006-RFS-20261119"
    return VERSION_ALIAS.get(s, s)

def main():
    recs = json.load(open(os.path.join(V2, "record_master.json"), encoding="utf-8"))
    queue = json.load(open(os.path.join(V2, "reviewer_queue.json"), encoding="utf-8"))
    qr = queue if isinstance(queue, list) else queue.get("reviewer_queue", queue.get("records", []))

    history = []

    # ---------- F05: record-level current-state corrections ----------
    for r in recs:
        pid = r.get("paper_id")
        old = copy.deepcopy(r)
        r["schema_version"] = "2.0"
        r["reviewed_source_commit"] = REVIEWED
        r["approval_record_id"] = APPROVAL if any(k[0] == pid for k in AUTHORIZED) else None
        r["selected_paper_version"] = canon_version(pid, r.get("selected_paper_version"))

        # F05 P006: retire E05 as current request; current = E01 + E06
        if pid == "P006":
            r["requested_experiment_ids"] = ["P006-E01", "P006-E06"]
            r["agent_recommendation"] = "RECOMMEND_FAITHFUL_REPLICATION"
            r["evidence_maturity"] = "EXECUTION_IN_PROGRESS"
            r["one_click_reproduction_note"] = (
                "作者 README 称 run_all.py --all 25-35min；静态核查确认默认 --all 读取 "
                "outputs/computed/*.p 缓存重绘，只有 --compute 才从5个CSV重算。"
                "本轮 E01 从隔离空计算目录执行 --main --compute 实测（见 executions/P006_E01_author）。")
            for e in (r.get("review_experiments") or []):
                e["version_id"] = canon_version(pid, e.get("version_id"))
            r.setdefault("review_experiments", []).append({
                "version_id": "P006-RFS-20261119", "experiment_id": "P006-E06",
                "execution_status": "NOT_RUN",
                "requested_reviewer_decision": "APPROVE_FAITHFUL_REPLICATION",
                "approval_source": APPROVAL,
            })
            history.append({"paper_id": pid, "field": "requested_experiment_ids/selected_paper_version",
                            "old": old.get("requested_experiment_ids"),
                            "old_version": old.get("selected_paper_version"),
                            "reason": "F04/F05: E05(HOLD) retired; RFS alias canonicalized"})

        # F05 P009: author official repo, not third-party
        if pid == "P009":
            r["author_code_source"] = (
                "AUTHOR: github.com/bkelly-lab/ReplicationCrisis (author official repository); "
                "JKP live factor data separate maintained snapshot")
            r["code_source_type"] = "AUTHOR"
            r["author_code_available"] = True
            history.append({"paper_id": pid, "field": "code_source_type/author_code_source",
                            "old": old.get("author_code_source"), "reason": "F05: official repo not third-party"})

        # F05 P010: official MATLAB package obtained
        if pid == "P010":
            r["author_code_available"] = True
            r["code_source_type"] = "AUTHOR"
            r["agent_recommendation_note"] = (
                "官方 MATLAB 公共代码包已从作者主页 Code and Data 取得并核验（见 support/P010/code_audit）；"
                "ICE 忠实数值仍 HOLD；TRACE 替代需明确目标后审批。")
            r["reproduction_type_note"] = (
                "AUTHOR 代码已取得；ICE 专有数据仍不可得；TRACE 路线为 APPROXIMATE_VALIDATION，"
                "不宣称原文 ICE 数值。")
            history.append({"paper_id": pid, "field": "author_code_available/note",
                            "old": old.get("author_code_available"), "reason": "F05: official code package obtained"})

        # F05 P008: remove stale "empirical can only be approximate" reasoning
        if pid == "P008":
            r["planned_reproduction_types_note"] = (
                "理论闭式与约束最优组合为 INDEPENDENT_FAITHFUL；作者公开组合收益"
                "(ESG_efficient_frontier_portfolios_vF.xlsx)若与目标明确对应，可申请范围受限的忠实复现"
                "(R10/R11 Table4均值)；底层 ESG/证券数据重建另列 REQUEST_EVIDENCE。")
            history.append({"paper_id": pid, "field": "planned_reproduction_types_note",
                            "old": old.get("planned_reproduction_types_note"),
                            "reason": "F05: derived author outputs can support scoped faithful replication"})

        # F05 P003: equity/futures scope already split; keep, record as confirmed
        if pid == "P003":
            r["requested_experiment_ids"] = ["P003-E01"]

        # F05 P007: classification current
        if pid == "P007":
            r["canonical_version_id"] = "JF2023_VOR"

        # F05 P001: no figure 5, figure 3 is empirical
        if pid == "P001":
            r["figure_numbering_note"] = (
                "正式版 Figure 3 为市场数据(原油/黄金期货持仓)实证；无 Figure 5。"
                "理论核对目标限 R01/R02/R03/R09，不重建原图坐标。")
            history.append({"paper_id": pid, "field": "figure_numbering_note",
                            "old": "旧尽调曾列 Figure 5", "reason": "F05: corrected figure numbering"})

    # ---------- §2 reviewer_queue corrections ----------
    outq = []
    for q in qr:
        pid, exp = q.get("paper_id"), q.get("experiment_id")
        q2 = copy.deepcopy(q)
        q2["reviewed_source_commit"] = REVIEWED
        q2["approval_record_id"] = APPROVAL if (pid, exp) in AUTHORIZED else q.get("approval_record_id")

        # F04: P006-E01 125 -> 115
        if pid == "P006" and exp == "P006-E01":
            q2["result_ids"] = [
                rid for rid in (q.get("result_ids") or [])
            ]
            # authoritative 115 from rebuilt target_alignment
            ta = os.path.join(BASE, "target_alignment.csv")
            if os.path.exists(ta):
                q2["result_ids"] = [r["result_id"] for r in csv.DictReader(open(ta, encoding="utf-8-sig"))
                                    if r["experiment_id"] == "P006-E01"]
            q2["version_id"] = "P006-RFS-20261119"
            q2["scope_note"] = "115 PROPOSED targets; 10 OUTSIDE_PILOT excluded (history/)."

        # F04: P002 E01/E21 relation
        if pid == "P002" and exp == "P002-E01":
            q2["superseded_by"] = "P002-E21"
            q2["scope_note"] = "旧泛化E01由细化E21继承，不重复计数（F04）。"

        # F04: P010-E03 explicit targets, no empty result_ids
        if pid == "P010" and exp == "P010-E03":
            if not q2.get("result_ids"):
                q2["result_ids"] = [f"P010-E03-R{i:02d}" for i in range(1, 5)]
                q2["scope_note"] = "F04: explicit TRACE-route targets added (were empty)."

        # §2.1 authorization flags
        if (pid, exp) in AUTHORIZED:
            v, rt, dec = AUTHORIZED[(pid, exp)]
            q2["version_id"] = v
            q2["reproduction_type"] = rt
            q2["execution_authorized"] = True
            q2["requested_reviewer_decision"] = dec
            q2["approval_source"] = APPROVAL
        else:
            q2["execution_authorized"] = False

        # F04: IMPLEMENTATION_AUDIT is a purpose, not a reproduction_type
        if q2.get("reproduction_type") == "IMPLEMENTATION_AUDIT":
            q2["experiment_purpose"] = "IMPLEMENTATION_AUDIT"
            q2["reproduction_type"] = "INDEPENDENT_FAITHFUL"

        outq.append(q2)

    # Add P006-E06 if absent (authorized this round)
    if not any(q["paper_id"] == "P006" and q["experiment_id"] == "P006-E06" for q in outq):
        outq.append({
            "schema_version": "2.0", "batch_id": "CO-REP-20261120-02-R3",
            "paper_id": "P006", "version_id": "P006-RFS-20261119",
            "experiment_id": "P006-E06", "reproduction_type": "INDEPENDENT_FAITHFUL",
            "experiment_purpose": "IMPLEMENTATION_AUDIT",
            "execution_authorized": True, "result_ids": ["P006-R01", "P006-R02", "P006-R03", "P006-R04"],
            "requested_reviewer_decision": "APPROVE_FAITHFUL_REPLICATION",
            "approval_source": APPROVAL,
            "scope_statement": "论文T-1留一公式独立实现 + 同输入对照(A作者/B0固定Tz/B1论文T-1)",
            "execution_status": "NOT_RUN",
        })

    # ---------- write outputs ----------
    with open(os.path.join(BASE, "record_master.json"), "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=2)

    with open(os.path.join(BASE, "reviewer_queue.json"), "w", encoding="utf-8") as f:
        json.dump({"schema_version": "2.0", "batch_id": "CO-REP-20261120-02-R3",
                   "reviewed_source_commit": REVIEWED, "approval_record_id": APPROVAL,
                   "records": outq}, f, ensure_ascii=False, indent=2)

    # master_table.csv from canonical recs (core columns)
    fields = ["paper_id", "candidate_status", "title", "journal", "journal_group", "DOI",
              "publication_status", "selected_paper_version", "canonical_version_id",
              "topic_class", "code_source_type", "author_code_available",
              "candidate_status_note", "agent_recommendation", "reviewer_decision",
              "execution_status", "requested_experiment_ids", "critical_evidence_ids"]
    with open(os.path.join(BASE, "master_table.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in recs:
            row = dict(r)
            row["canonical_version_id"] = canon_version(r["paper_id"], r.get("selected_paper_version"))
            row["requested_experiment_ids"] = ";".join(r.get("requested_experiment_ids") or [])
            row["critical_evidence_ids"] = ";".join(r.get("critical_evidence_ids") or [])
            w.writerow(row)

    with open(os.path.join(BASE, "history", "F05_superseded_current_fields.json"), "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print("records:", len(recs), "| queue:", len(outq), "| history corrections:", len(history))
    print("authorized:", [f"{p}/{e}" for p, e in AUTHORIZED])
    p6 = next(q for q in outq if q["experiment_id"] == "P006-E01")
    print("P006-E01 result_ids:", len(p6["result_ids"]))

if __name__ == "__main__":
    main()
