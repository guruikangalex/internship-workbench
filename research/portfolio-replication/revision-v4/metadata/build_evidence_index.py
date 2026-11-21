#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F03 rebuild: complete evidence index.

- Extracts real evidence rows from original due-diligence cards (D1/D2/D3), which
  carry URL / locator / verification status.
- Covers every evidence_id referenced by canonical records (critical_evidence_ids,
  evidence_ids, institution_relations.evidence_ids) with an ID-resolution row:
  paper_id + canonical_version_id + source_type + URL when known + resolution status.
- Unresolvable historical ids are marked DETAILS_NOT_IN_FROZEN_PACKAGE with a
  recovery path, never given a fabricated URL.
- Preserves the 6 existing E-P0XX-SXX manifest rows as legacy entries with a
  new_id mapping where possible.
"""
import csv, json, os, re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V2 = os.path.abspath(os.path.join(BASE, "..", "revision-v2"))
OLD_AGENTS = "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/research_package/agents"

FIELDS = ["evidence_id", "paper_id", "canonical_version_id", "source_type", "url",
          "locator", "supported_fact", "verification_status", "local_file", "sha256",
          "access_condition", "resolution_status", "recovery_path", "legacy_id"]

def canon_version(pid, raw):
    if pid == "P006":
        s = str(raw or "")
        if "NBER" in s or "20260521" in s:
            return "P006-NBER-20260521"
        return "P006-RFS-20261119"
    return str(raw or "")

def extract_card_rows():
    """Parse markdown evidence tables from D1/D2/D3 cards."""
    found = {}
    for fn in ["D1_duediligence.md", "D2_duediligence.md", "D3_duediligence.md",
               "D4_duediligence.md"]:
        path = os.path.join(OLD_AGENTS, fn)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            for ln in f:
                m = re.match(r'^\|\s*(P0\d{2}-S\d+)\s*\|', ln)
                if not m:
                    continue
                cells = [c.strip() for c in ln.strip().strip("|").split("|")]
                if len(cells) < 6:
                    continue
                eid = cells[0]
                found[eid] = {
                    "supported_fact": cells[1], "source_type": cells[2],
                    "url": cells[3], "locator": cells[4],
                    "version_date": cells[5] if len(cells) > 5 else "",
                    "verification_status": cells[6] if len(cells) > 6 else "",
                    "note": cells[7] if len(cells) > 7 else "",
                }
    return found

def main():
    records = json.load(open(os.path.join(V2, "record_master.json"), encoding="utf-8"))
    card_rows = extract_card_rows()
    rec_by_pid = {r.get("paper_id"): r for r in records}

    # collect all referenced evidence ids (critical + general + relation-level)
    refs = {}  # eid -> (pid, version)
    for r in records:
        pid = r.get("paper_id")
        cv = canon_version(pid, r.get("selected_paper_version"))
        ids = set(r.get("critical_evidence_ids") or []) | set(r.get("evidence_ids") or [])
        for rel in (r.get("institution_relations") or []):
            ids |= set(rel.get("evidence_ids") or [])
        for eid in ids:
            refs.setdefault(eid, (pid, cv))

    rows = []
    for eid, (pid, cv) in sorted(refs.items()):
        c = card_rows.get(eid)
        if c:
            rows.append({
                "evidence_id": eid, "paper_id": pid, "canonical_version_id": cv,
                "source_type": c["source_type"], "url": c["url"], "locator": c["locator"],
                "supported_fact": c["supported_fact"][:200],
                "verification_status": c["verification_status"],
                "local_file": c["url"] if c["url"].startswith((".", "/")) else "",
                "sha256": "", "access_condition": c["version_date"],
                "resolution_status": "RESOLVED_FROM_SOURCE_CARD",
                "recovery_path": f"../research_package/agents/D*_duediligence.md",
                "legacy_id": "",
            })
        else:
            rows.append({
                "evidence_id": eid, "paper_id": pid, "canonical_version_id": cv,
                "source_type": "UNKNOWN", "url": "", "locator": "",
                "supported_fact": "", "verification_status": "NOT_READ",
                "local_file": "", "sha256": "", "access_condition": "",
                "resolution_status": "DETAILS_NOT_IN_FROZEN_PACKAGE",
                "recovery_path": "../research_package/agents/{A_search,B_search,C_search,D*_duediligence}.md",
                "legacy_id": "",
            })

    # legacy rows from v2 manifest (E-P0XX-SXX) with mapping when possible
    v2man = os.path.join(V2, "search", "evidence_manifest.csv")
    legacy_n = 0
    if os.path.exists(v2man):
        for lr in csv.DictReader(open(v2man, encoding="utf-8-sig")):
            rows.append({
                "evidence_id": lr.get("evidence_id", ""), "paper_id": lr.get("paper_id", ""),
                "canonical_version_id": "", "source_type": lr.get("source_type", ""),
                "url": lr.get("url", ""), "locator": lr.get("locator", ""),
                "supported_fact": "", "verification_status": lr.get("verification_status", ""),
                "local_file": lr.get("relative_path", ""), "sha256": lr.get("sha256", ""),
                "access_condition": lr.get("access_condition", ""),
                "resolution_status": "LEGACY_MANIFEST_ROW",
                "recovery_path": "../revision-v2/search/evidence_manifest.csv",
                "legacy_id": lr.get("evidence_id", ""),
            })
            legacy_n += 1

    out = os.path.join(BASE, "evidence_index.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)

    critical = set()
    for r in records:
        critical |= set(r.get("critical_evidence_ids") or [])
    covered = {r["evidence_id"] for r in rows}
    print("wrote", out, "rows:", len(rows))
    print("canonical refs:", len(refs), "| critical:", len(critical),
          "| critical covered:", len(critical & covered),
          "| resolved from cards:", sum(1 for r in rows if r["resolution_status"] == "RESOLVED_FROM_SOURCE_CARD"),
          "| legacy:", legacy_n)

if __name__ == "__main__":
    main()
