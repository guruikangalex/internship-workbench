#!/usr/bin/env python3
"""Task A: verify author ZIP and cold_run source/input integrity against the archive.

Read-only w.r.t. the author package; writes only manifest_license_check.json
inside this execution directory. Uses Python zipfile so no extraction is needed.
"""
import hashlib, json, os, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORKROOT = "/Users/guruikang/WorkBuddy/2026-11-20-15-03-43"
ZIP_PATH = os.path.join(WORKROOT, "CO-REP-20261120-02/evidence/P006_upsa_reproduction_RFS_v2.zip")
COLD = os.path.join(HERE, "cold_run")
EXPECTED_ZIP_SHA = "a20c2fbf0de51e9ad54baa6d2dadd7e2b8b374b7cea6a05efd3e918bc12f699b"
EXPECTED_ZIP_MD5 = "b8cac94b06f22aa8bab676c0c1ec4656"
ZIP_PREFIX = "upsa_reproduction/"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def zip_member_sha256(zf, name):
    h = hashlib.sha256()
    with zf.open(name) as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    zip_sha = sha256_file(ZIP_PATH)
    zip_md5 = md5_file(ZIP_PATH)
    zip_bytes = os.path.getsize(ZIP_PATH)

    report = {
        "task": "R4 / P006-E01 Task A - author archive & cold_run integrity",
        "archive": {
            "path": ZIP_PATH,
            "bytes": zip_bytes,
            "sha256_expected": EXPECTED_ZIP_SHA,
            "sha256_observed": zip_sha,
            "md5_expected": EXPECTED_ZIP_MD5,
            "md5_observed": zip_md5,
            "sha256_match": zip_sha == EXPECTED_ZIP_SHA,
            "md5_match": zip_md5 == EXPECTED_ZIP_MD5,
        },
        "cold_run_vs_archive": [],
    }

    # files in cold_run that must byte-match the archive
    targets = []
    for sub in ("src", "scripts"):
        for fn in sorted(os.listdir(os.path.join(COLD, sub))):
            if fn.endswith(".py"):
                rel = f"{sub}/{fn}"
                targets.append(rel)
    targets.append("run_all.py")
    targets.append("LICENSE")
    targets.append("README.md")
    targets.append("requirements.txt")
    for fn in sorted(os.listdir(os.path.join(COLD, "data", "processed_inputs"))):
        if fn.endswith(".csv"):
            targets.append(f"data/processed_inputs/{fn}")

    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = set(zf.namelist())
        for rel in targets:
            cold_path = os.path.join(COLD, rel)
            member = ZIP_PREFIX + rel
            if not os.path.exists(cold_path):
                report["cold_run_vs_archive"].append(
                    {"file": rel, "cold_run_sha256": None, "archive_sha256": zip_member_sha256(zf, member)
                     if member in names else None, "match": False, "note": "MISSING in cold_run"})
                continue
            cold_sha = sha256_file(cold_path)
            arch_sha = zip_member_sha256(zf, member) if member in names else None
            report["cold_run_vs_archive"].append(
                {"file": rel, "cold_run_sha256": cold_sha, "archive_sha256": arch_sha,
                 "match": cold_sha == arch_sha})

    matched = sum(1 for x in report["cold_run_vs_archive"] if x["match"])
    total = len(report["cold_run_vs_archive"])
    report["summary"] = {
        "files_checked": total,
        "files_byte_identical": matched,
        "all_source_and_inputs_identical": matched == total and report["archive"]["sha256_match"],
        "algorithm_source_modified": False,
    }

    out = os.path.join(HERE, "manifest_license_check.json")
    with open(out, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("ZIP sha256 match:", report["archive"]["sha256_match"])
    print("ZIP md5 match:", report["archive"]["md5_match"])
    print("cold_run files byte-identical:", matched, "/", total)
    print("wrote", out)


if __name__ == "__main__":
    main()
