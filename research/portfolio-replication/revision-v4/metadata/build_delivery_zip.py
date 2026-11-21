#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build final R4 delivery ZIP from Git-trackable files + SHA256 manifest.

Rule: ZIP content must equal the set of files listed in review_package_manifest.sha256
(self-authored small files). Large third-party inputs are external dependencies.
"""
import os, hashlib, zipfile, json

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST = os.path.join(BASE, "review_package_manifest.sha256")
ZIP_OUT = os.path.abspath(os.path.join(BASE, "..", "CO-REP-20261120-02-R4.zip"))
ZIP_SHA = ZIP_OUT + ".sha256"

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def main():
    entries = []
    for line in open(MANIFEST, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2:
            continue
        entries.append((parts[1], parts[0]))
    print("manifest entries:", len(entries))

    missing, mismatch = [], []
    with zipfile.ZipFile(ZIP_OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        # stable order
        for rel, expected in sorted(entries):
            p = os.path.join(BASE, rel)
            if not os.path.exists(p):
                missing.append(rel); continue
            actual = sha256_file(p)
            if actual != expected:
                mismatch.append((rel, expected[:12], actual[:12])); continue
            z.write(p, os.path.join("revision-v4", rel))
        # include manifest itself (content fixed pre-zip)
        z.write(MANIFEST, "revision-v4/review_package_manifest.sha256")
    if missing or mismatch:
        print("ABORT: missing", len(missing), "mismatch", len(mismatch))
        for m in missing[:10]: print("  MISSING", m)
        for m in mismatch[:10]: print("  MISMATCH", m)
        os.remove(ZIP_OUT)
        return 1
    zh = sha256_file(ZIP_OUT)
    with open(ZIP_SHA, "w") as f:
        f.write(f"{zh}  {os.path.basename(ZIP_OUT)}\n")
    print("ZIP:", ZIP_OUT, os.path.getsize(ZIP_OUT), "bytes")
    print("SHA256:", zh)
    print("files in zip:", len(entries) + 1)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
