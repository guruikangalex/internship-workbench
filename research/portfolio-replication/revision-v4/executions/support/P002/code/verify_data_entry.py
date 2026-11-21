#!/usr/bin/env python3
"""P002 data-entry preflight (read-only).

Goal: determine whether the three author-required inputs
  usa.csv, usa_dsf.csv, world_ret_monthly.csv
can be obtained from public endpoints (Ken French / JKP / ReplicationCrisis),
or must be recorded as NOT_FOUND (WRDS-proprietary).

This script does NOT fabricate stock-level panels. It:
  1. searches local mounted copies for the exact filenames;
  2. records the real Ken French FF3 monthly ZIP we downloaded
     (public factor return series, a proxy for D07 ff3_m.csv ONLY, not D01-D03);
  3. records the cloned ReplicationCrisis repo contents and commit;
  4. records the failed JKP endpoint;
  5. emits a JSON manifest with explicit status enums.

Run:  python verify_data_entry.py > ../results/data_entry_manifest.json
"""
import csv
import hashlib
import io
import json
import os
import re
import zipfile

SUPPORT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(SUPPORT, "data")
HERE = os.path.dirname(os.path.abspath(__file__))

EXACT_FILES = ["usa.csv", "usa_dsf.csv", "world_ret_monthly.csv"]

# Local mounts that might legitimately hold author data (none expected).
SEARCH_ROOTS = [
    "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/CO-REP-20261120-02/execution/P002_repo",
    "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/CO-REP-20261120-02/execution/P002_data",
    "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/CO-REP-20261120-02/evidence",
    DATA,
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_exact(name):
    hits = []
    for root in SEARCH_ROOTS:
        if not os.path.isdir(root):
            continue
        for dp, dn, fn in os.walk(root):
            # skip .git to avoid scanning packfiles
            dn[:] = [d for d in dn if d != ".git"]
            if name in fn:
                p = os.path.join(dp, name)
                hits.append({"path": p, "bytes": os.path.getsize(p), "sha256": sha256(p)})
    return hits


def ken_french_probe():
    zp = os.path.join(DATA, "F-F_Research_Data_Factors_CSV.zip")
    out = {"source": "Kenneth French Data Library",
           "url": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip",
           "http_status_observed": 200, "zip_bytes": os.path.getsize(zp),
           "zip_sha256": sha256(zp), "status": "ACCESSED"}
    with zipfile.ZipFile(zp) as z:
        member = "F-F_Research_Data_Factors.csv"
        raw = z.read(member).decode("latin-1")
        rows = list(csv.reader(io.StringIO(raw)))
        out["member"] = member
        out["member_sha256"] = hashlib.sha256(z.read(member)).hexdigest()
        out["member_rows"] = len(rows)
        # find monthly block: header row containing "Mkt-RF"
        hdr = None
        for i, r in enumerate(rows):
            if any("Mkt-RF" in c for c in r):
                hdr = i
                break
        if hdr is not None:
            out["header_row_index"] = hdr
            out["header"] = rows[hdr]
            data_rows = []
            for r in rows[hdr + 1:]:
                if not r or not re.match(r"^\d{6}$", r[0].strip()):
                    break
                data_rows.append(r)
            out["monthly_n"] = len(data_rows)
            out["first_month"] = data_rows[0][0] if data_rows else None
            out["last_month"] = data_rows[-1][0] if data_rows else None
        out["vintage_note"] = rows[0][0] if rows else None
    out["fits"] = "D07 ff3_m.csv (RF only) as APPROXIMATE_VALIDATION proxy; NOT a substitute for D01-D03 stock panel"
    return out


def replication_crisis_probe():
    repo = os.path.join(DATA, "ReplicationCrisis_repo")
    files = []
    for dp, dn, fn in os.walk(repo):
        dn[:] = [d for d in dn if d != ".git"]
        for f in fn:
            files.append(os.path.relpath(os.path.join(dp, f), repo))
    present_exact = {n: [f for f in files if f.lower().endswith(n)] for n in EXACT_FILES}
    commit = "UNKNOWN"
    gdir = os.path.join(repo, ".git")
    if os.path.isdir(gdir):
        head = open(os.path.join(gdir, "HEAD")).read().strip()
        if head.startswith("ref:"):
            ref = head.split(" ", 1)[1]
            rp = os.path.join(gdir, ref)
            if os.path.exists(rp):
                commit = open(rp).read().strip()
    return {
        "source": "bkelly-lab/ReplicationCrisis (GitHub, public code repo)",
        "url": "https://github.com/bkelly-lab/ReplicationCrisis",
        "commit": commit,
        "status": "ACCESSED_CODE_ONLY",
        "exact_stock_panels_present": present_exact,
        "note": "README: repo no longer maintained; stock returns & firm characteristics are on WRDS Global Factor Data (entitlement required); only long-short factor returns are on public Dropbox. No usa.csv/usa_dsf.csv/world_ret_monthly.csv in repo.",
    }


def jkp_probe():
    return {
        "source": "JKP factor website",
        "url": "https://www.jkpfactor.com/data/",
        "status": "NOT_FOUND",
        "observation": "curl -L --max-time 60 -> curl (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL; HTTP 000, 0 bytes. WebFetch also failed. No public URL exposed for a US 115-characteristic stock-level panel, daily stock returns, or world monthly returns. Published JKP data requires WRDS Global Factor Data entitlement.",
    }


def main():
    man = {
        "batch": "CO-REP-20261120-02",
        "paper": "P002",
        "task": "public-entry data availability preflight for D01 usa.csv / D02 usa_dsf.csv / D03 world_ret_monthly.csv",
        "rule": "No fabricated or substituted panel is written. Status enums: FOUND / NOT_FOUND / ACCESSED / ACCESSED_CODE_ONLY / SAMPLE_ACCESSED.",
        "exact_files": {},
        "public_endpoints": {},
        "author_readme_provenance": {
            "usa.csv": "WRDS (Jensen Kelly Pedersen 2023 replication data); filter excntry=='USA' -> ENTITLEMENT_REQUIRED",
            "usa_dsf.csv": "generate via ReplicationCrisis code from WRDS, or email author -> ENTITLEMENT_REQUIRED",
            "world_ret_monthly.csv": "generate via ReplicationCrisis code from WRDS, or email author -> ENTITLEMENT_REQUIRED",
            "source": "README.md of author repo commit 13d836b5187cbfa69730dd256d8eb767e65ca21f, section 'Data'",
        },
        "verdict": None,
    }
    for n in EXACT_FILES:
        hits = find_exact(n)
        man["exact_files"][n] = {
            "status": "FOUND" if hits else "NOT_FOUND",
            "hits": hits,
        }
    man["public_endpoints"]["ken_french_ff3_monthly"] = ken_french_probe()
    man["public_endpoints"]["replication_crisis_github"] = replication_crisis_probe()
    man["public_endpoints"]["jkp_website"] = jkp_probe()
    all_found = all(man["exact_files"][n]["status"] == "FOUND" for n in EXACT_FILES)
    man["verdict"] = (
        "D01-D03 NOT_FOUND via public endpoints; WRDS/author entitlement required. "
        "Ken French FF3 monthly accessed only as APPROXIMATE_VALIDATION proxy for D07 (RF), "
        "not a stock-level panel."
        if not all_found else
        "Exact files found locally; inspect hits before any further claim."
    )
    json.dump(man, open(os.path.join(SUPPORT, "results", "data_entry_manifest.json"), "w"),
              indent=2, ensure_ascii=False)
    print(json.dumps(man, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
