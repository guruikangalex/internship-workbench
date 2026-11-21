#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 review-package delivery validator (Agent A, P0).

Runs 8 independent checks (a)-(h) over a delivery root and exits 0 only when
all hard checks pass. Designed so that every check fails loudly on a corrupted
or incomplete fresh clone; see metadata/fault_injection_results.json for the
5 destructive fault-injection cases exercised against temporary copies.

Usage:
    python3 validate_delivery.py [--root DIR] [--manifest FILE]
                                 [--json-report FILE] [--quiet]

Exit codes:
    0 = all checks pass
    1 = one or more hard errors
    2 = validator could not start (bad arguments / unreadable root)
"""
from __future__ import print_function

import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import sys

# --------------------------------------------------------------------------- #
# Report plumbing
# --------------------------------------------------------------------------- #
CHECKS = ["a_manifest", "b_parse", "c_ids", "d_shape", "e_logs",
          "f_enums", "g_evidence", "h_verdict"]

CHECK_TITLES = {
    "a_manifest": "(a) manifest 每个文件存在且 SHA256 一致",
    "b_parse": "(b) CSV/JSON 可解析且字段结构正确",
    "c_ids": "(c) 实验ID / 目标(result)ID / 检查ID 跨文件一致",
    "d_shape": "(d) 数据形状 / 频率 / 样本区间符合冻结记录",
    "e_logs": "(e) 运行日志与实际输出存在",
    "f_enums": "(f) 审批与执行状态为合法枚举且互相兼容",
    "g_evidence": "(g) evidence_id 可解析",
    "h_verdict": "(h) PASS/FAIL 判定可按冻结容差重算",
}


class Report(object):
    def __init__(self):
        self.errors = []          # list of (check, message)
        self.warnings = []        # list of (check, message)
        self.infos = []           # list of (check, message)
        self.stats = {}

    def error(self, check, msg):
        self.errors.append((check, str(msg)))

    def warn(self, check, msg):
        self.warnings.append((check, str(msg)))

    def info(self, check, msg):
        self.infos.append((check, str(msg)))

    def stat(self, key, value):
        self.stats[key] = value

    def has_errors(self, check):
        return any(c == check for c, _ in self.errors)

    def to_dict(self, root):
        return {
            "tool": "validate_delivery.py",
            "root": os.path.abspath(root),
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "exit_code": 1 if self.errors else 0,
            "checks": [{"id": c, "title": CHECK_TITLES[c],
                        "status": "FAIL" if self.has_errors(c) else "PASS"}
                       for c in CHECKS],
            "errors": [{"check": c, "message": m} for c, m in self.errors],
            "warnings": [{"check": c, "message": m} for c, m in self.warnings],
            "infos": [{"check": c, "message": m} for c, m in self.infos],
            "stats": self.stats,
        }


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path, encoding="utf-8-sig"):
    with open(path, "r", newline="", encoding=encoding, errors="replace") as f:
        return list(csv.reader(f))


def read_dicts(path, encoding="utf-8-sig"):
    with open(path, "r", newline="", encoding=encoding, errors="replace") as f:
        return list(csv.DictReader(f))


def load_json(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        return json.load(f)


def rel(root, path):
    try:
        return os.path.relpath(path, root)
    except Exception:
        return path


def find_files(root, suffix):
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in ("__pycache__", ".git")]
        for fn in fns:
            if fn.lower().endswith(suffix):
                out.append(os.path.join(dp, fn))
    return sorted(out)


# --------------------------------------------------------------------------- #
# Tolerance parser for check (h)
# --------------------------------------------------------------------------- #
NUM_IN_RULE = re.compile(
    r"(?:<=|<\s*=|abs\s*<=\s*|\+/-\s*|\+\s*-\s*|within\s+|half\s+unit\s+)"
    r"\s*([0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?)",
    re.IGNORECASE,
)


def parse_number(value):
    """Parse a numeric cell, tolerating percentages, % signs and commas.
    Returns None when the cell is not numeric (e.g. 'NOT_PRINTED_IN_PAPER')."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() in ("null", "none", "n/a", "na"):
        return None
    pct = s.endswith("%")
    if pct:
        s = s[:-1].strip()
    s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return v


def parse_tolerance(rule):
    """Return (kind, value, decimals) or (None, None, None) when unknown.

    kind in {'abs','rel','exact_display','gt','exact'}.
    Rules with no frozen numeric threshold are intentionally skipped and
    reported by check (h) rather than guessed.
    """
    if not rule:
        return (None, None, None)
    s = str(rule).strip()
    low = s.lower()

    # displayed rounding, e.g. "Absolute half unit 0.005; apply original displayed rounding"
    m = re.search(r"half\s+unit\s+([0-9]*\.?[0-9]+)", low)
    if m:
        half = float(m.group(1))
        # half unit = 0.5 * 10^-decimals  =>  0.005 -> 2dp, 0.05 -> 1dp
        import math
        decimals = max(0, int(round(-math.log10(2.0 * half)))) if half > 0 else 2
        return ("exact_display", half, decimals)

    if low.startswith("exact") or low == "0 (identity)" or "0 (identity)" in low:
        return ("exact", 0.0, None)

    m = re.search(r"must\s+exceed\s+([0-9.eE+-]+)", low)
    if m:
        return ("gt", float(m.group(1)), None)

    if "relative" in low:
        m = NUM_IN_RULE.search(s)
        if m:
            return ("rel", float(m.group(1)), None)
        m = re.search(r"([0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?)", s)
        if m:
            return ("rel", float(m.group(1)), None)

    m = NUM_IN_RULE.search(s)
    if m:
        return ("abs", float(m.group(1)), None)
    # '+/-0.005 pp', 'within 1e-9 pp', '<=1e-9' already covered; fallback bare number
    m = re.search(r"(?<![\w.])([0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?)\s*(?:pp)?", s)
    if m and re.search(r"(abs|<=|\+/-|within|equal|pp|exact|1e-|0\.00)", low):
        return ("abs", float(m.group(1)), None)
    return (None, None, None)


def apply_tolerance(kind, tol, decimals, paper_v, repl_v):
    absdiff = abs(repl_v - paper_v)
    if kind == "abs":
        return absdiff <= tol + 1e-15
    if kind == "rel":
        denom = max(abs(paper_v), 1e-300)
        return absdiff / denom <= tol + 1e-15
    if kind == "exact":
        return absdiff <= 1e-12
    if kind == "gt":
        return repl_v > tol
    if kind == "exact_display":
        return (absdiff <= tol + 1e-15) or (round(repl_v, decimals) == round(paper_v, decimals))
    return None


# --------------------------------------------------------------------------- #
# (a) manifest existence + hash
# --------------------------------------------------------------------------- #
def check_a(root, manifest_path, rep):
    if not os.path.isfile(manifest_path):
        rep.error("a_manifest", "manifest 不存在: %s" % rel(root, manifest_path))
        return
    entries = []
    with open(manifest_path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                rep.error("a_manifest", "manifest 第 %d 行格式错误: %r" % (lineno, line))
                continue
            digest, path = parts[0].strip().lower(), parts[1].strip()
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                rep.error("a_manifest", "manifest 第 %d 行非法 SHA256: %r" % (lineno, digest))
                continue
            entries.append((digest, path, lineno))

    rep.stat("manifest_entries", len(entries))
    if len(entries) == 0:
        rep.error("a_manifest", "manifest 无任何有效条目")
        return

    seen = set()
    for digest, path, lineno in entries:
        if path in seen:
            rep.error("a_manifest", "manifest 重复条目: %s (第 %d 行)" % (path, lineno))
        seen.add(path)
        if os.path.normpath(path) == os.path.normpath(os.path.relpath(manifest_path, root)):
            rep.error("a_manifest", "manifest 不应包含自身: %s" % path)
            continue
        full = os.path.join(root, path)
        if not os.path.isfile(full):
            rep.error("a_manifest", "manifest 文件缺失: %s" % path)
            continue
        actual = sha256_file(full)
        if actual != digest:
            rep.error("a_manifest",
                      "manifest SHA256 不一致: %s expected=%s actual=%s"
                      % (path, digest, actual))

    # External large files must never be committed into the manifest.
    ext_path = os.path.join(root, "metadata", "external_dependencies.json")
    if os.path.isfile(ext_path):
        try:
            ext = load_json(ext_path)
            for e in ext.get("entries", []):
                if e.get("present_in_revision_v4") and e.get("expected_sha256") in seen:
                    rep.error("a_manifest",
                              "外链大文件被错误列入 manifest: %s" % e.get("file_name"))
        except Exception as exc:
            rep.error("a_manifest", "external_dependencies.json 解析失败: %s" % exc)

    rep.info("a_manifest", "manifest 条目=%d，已逐一核对存在性与 SHA256" % len(entries))


# --------------------------------------------------------------------------- #
# (b) CSV / JSON parse + field structure
# --------------------------------------------------------------------------- #
REQUIRED_COLUMNS = {
    "target_alignment.csv": ["experiment_id", "result_id", "paper_value", "tolerance"],
    "evidence_index.csv": ["evidence_id", "verification_status"],
    "execution_index_r3_inherited.csv": ["experiment_id", "execution_status", "output_dir"],
    "issue_closure_r3_inherited.csv": ["issue_id", "closure_status"],
    "master_table.csv": ["paper_id", "execution_status", "critical_evidence_ids"],
    "reviewer_summary.csv": ["paper_id", "experiment_id", "execution_status"],
    "coverage_matrix.csv": ["institution", "search_status"],
}


def check_b(root, rep):
    csvs = find_files(root, ".csv")
    jsons = find_files(root, ".json")

    # 第三方外链数据（如 Ken French 23MB CSV）不按自编 CSV 结构规则解析
    external_paths = set()
    ext_json = os.path.join(root, "metadata", "external_dependencies.json")
    if os.path.isfile(ext_json):
        try:
            for e in load_json(ext_json).get("entries", []):
                lp = e.get("local_path", "")
                if not lp:
                    continue
                full = lp if os.path.isabs(lp) else os.path.join(root, lp)
                external_paths.add(os.path.normpath(full))
        except Exception:
            pass

    csvs = [p for p in csvs if os.path.normpath(p) not in external_paths]
    jsons = [p for p in jsons if os.path.normpath(p) not in external_paths]
    rep.stat("csv_files", len(csvs))
    rep.stat("json_files", len(jsons))
    rep.stat("external_files_skipped_parse", len(external_paths & set(find_files(root, ".csv") + find_files(root, ".json"))))

    for path in csvs:
        rpath = rel(root, path)
        try:
            data = read_rows(path)
        except Exception as exc:
            rep.error("b_parse", "CSV 不可解析 %s: %s" % (rpath, exc))
            continue
        if not data:
            rep.error("b_parse", "CSV 空文件: %s" % rpath)
            continue
        header = data[0]
        if not any(h.strip() for h in header):
            rep.error("b_parse", "CSV 无表头: %s" % rpath)
            continue
        width = len(header)
        bad = [(i + 2, len(row)) for i, row in enumerate(data[1:]) if len(row) != width]
        if bad:
            rep.error("b_parse",
                      "CSV 列数不一致 %s (表头 %d 列, 第 %d 行 %d 列, 共 %d 行异常)"
                      % (rpath, width, bad[0][0], bad[0][1], len(bad)))
        base = os.path.basename(path)
        if base in REQUIRED_COLUMNS:
            missing = [c for c in REQUIRED_COLUMNS[base] if c not in header]
            if missing:
                rep.error("b_parse", "CSV 缺少必需字段 %s: %s" % (rpath, missing))

    for path in jsons:
        rpath = rel(root, path)
        try:
            load_json(path)
        except Exception as exc:
            rep.error("b_parse", "JSON 不可解析 %s: %s" % (rpath, exc))

    # reviewer_queue.json must be an object with a records list
    rq = os.path.join(root, "reviewer_queue.json")
    if os.path.isfile(rq):
        try:
            d = load_json(rq)
            if not isinstance(d, dict) or not isinstance(d.get("records"), list):
                rep.error("b_parse", "reviewer_queue.json 缺少 records 列表")
            else:
                rep.stat("reviewer_records", len(d["records"]))
        except Exception as exc:
            rep.error("b_parse", "reviewer_queue.json 结构错误: %s" % exc)
    else:
        rep.error("b_parse", "reviewer_queue.json 缺失")

    rep.info("b_parse", "解析 CSV=%d 个, JSON=%d 个" % (len(csvs), len(jsons)))


# --------------------------------------------------------------------------- #
# (c) cross-file ID consistency
# --------------------------------------------------------------------------- #
def check_c(root, rep):
    rq_path = os.path.join(root, "reviewer_queue.json")
    ta_path = os.path.join(root, "target_alignment.csv")
    ca_path = os.path.join(root, "check_alignment.csv")
    if not os.path.isfile(rq_path) or not os.path.isfile(ta_path):
        rep.error("c_ids", "ID 一致性所需文件缺失 (reviewer_queue.json / target_alignment.csv)")
        return

    rq = load_json(rq_path)
    records = rq.get("records", [])
    q_expts = set(str(r.get("experiment_id", "")) for r in records if r.get("experiment_id"))
    ta_rows = read_dicts(ta_path)
    ta_pairs = set((r.get("experiment_id", ""), r.get("result_id", "")) for r in ta_rows)
    ta_rids = set(r.get("result_id", "") for r in ta_rows if r.get("result_id"))
    rep.stat("target_alignment_rows", len(ta_rows))
    rep.stat("queue_experiment_ids", len(q_expts))

    tc_files = find_files(root, "target_comparison.csv")
    rep.stat("target_comparison_files", len(tc_files))
    if not tc_files:
        rep.error("c_ids", "未找到任何 target_comparison.csv")
    registered = 0
    exempt = 0
    for path in tc_files:
        rpath = rel(root, path)
        for lineno, row in enumerate(read_dicts(path), 2):
            eid = (row.get("experiment_id") or "").strip()
            rid = (row.get("result_id") or "").strip()
            if not eid or not rid:
                rep.error("c_ids", "%s:%d 缺少 experiment_id/result_id" % (rpath, lineno))
                continue
            if eid not in q_expts:
                rep.error("c_ids", "%s:%d 未知实验ID %s" % (rpath, lineno, eid))
            scope = (row.get("scope_status") or "").strip()
            if scope in ("E06_AD_HOC_PAPER_VALUE_MAP", "E06_OUT_OF_SCOPE"):
                exempt += 1
                continue
            if (eid, rid) in ta_pairs or rid in ta_rids:
                registered += 1
            else:
                rep.error("c_ids",
                          "%s:%d 目标(result)ID 未在 target_alignment.csv 注册: %s/%s"
                          % (rpath, lineno, eid, rid))
    rep.stat("tc_targets_registered", registered)
    rep.stat("tc_targets_exempt_declared", exempt)

    # check_alignment.csv: R4 distinguishes paper target result_ids from auxiliary check_ids.
    # Only PAPER_TARGET rows must resolve against target_alignment.csv (the canonical result
    # ledger). SUB_CHECK / DIAGNOSTIC / AUXILIARY check_ids are defined locally by
    # check_alignment.csv itself (that is the whole point of the R4 layering), so they must
    # NOT be looked up in target_alignment.csv. Enforce this explicitly.
    if os.path.isfile(ca_path):
        ca_rows = read_dicts(ca_path)
        rep.stat("check_alignment_rows", len(ca_rows))
        n_paper, n_aux = 0, 0
        for lineno, row in enumerate(ca_rows, 2):
            ctype = (row.get("check_type") or "").strip().upper()
            # R4 check_alignment has no `result_id` column: the canonical paper target
            # lives in `source_target_result_id`, and the full approved set in
            # `approved_result_ids` (semicolon-separated). check_id is the local
            # check identifier (Pxxx-E yy-Cnnn) and is intentionally not a result id.
            # source_target_result_id is the concrete canonical target this check maps to
            # (must resolve in target_alignment.csv). approved_result_ids is the approved
            # upper-level result declaration (e.g. P006-E06 maps 4 approved abstract results
            # P006-R01..R04 onto its sub-checks); it need not be a target_alignment key.
            rid = (row.get("result_id") or row.get("source_target_result_id") or "").strip()
            cid = (row.get("check_id") or "").strip()
            counted = (row.get("counted_as_paper_result") or "").strip().lower()
            if ctype == "PAPER_TARGET" or counted == "true":
                n_paper += 1
                if not rid:
                    rep.error("c_ids", "check_alignment.csv:%d PAPER_TARGET 无 result_id/source_target_result_id" % lineno)
                elif rid not in ta_rids:
                    rep.error("c_ids", "check_alignment.csv:%d PAPER_TARGET ID 未在 target_alignment 注册: %s" % (lineno, rid))
            else:
                n_aux += 1
                if not cid:
                    rep.error("c_ids", "check_alignment.csv:%d 辅助检查缺少 check_id" % lineno)
                if ctype not in ("SUB_CHECK", "DIAGNOSTIC", "AUXILIARY"):
                    rep.error("c_ids", "check_alignment.csv:%d 未知 check_type: %s" % (lineno, ctype))
        rep.stat("check_alignment_paper_targets", n_paper)
        rep.stat("check_alignment_aux_checks", n_aux)
        rep.info("c_ids", "check_alignment 分层核对: paper_target=%d aux=%d (aux check_id 不要求外部注册)" % (n_paper, n_aux))
    else:
        rep.info("c_ids", "check_alignment.csv 不存在（本包未声明），跳过该交叉核对")

    # 每个 queue 实验必须在 target_alignment 或某份 tc 中有目标
    tc_expts = set()
    for path in tc_files:
        for row in read_dicts(path):
            if row.get("experiment_id"):
                tc_expts.add(row["experiment_id"])
    for r in records:
        eid = r.get("experiment_id")
        if eid and eid not in q_expts:
            continue
        # q_expts is built from the same records; check coverage instead
    for eid in q_expts:
        if eid not in tc_expts and eid not in set(x[0] for x in ta_pairs):
            rep.error("c_ids", "实验ID 无任何目标表登记: %s" % eid)

    rep.info("c_ids", "目标ID 注册核对 registered=%d, 声明性豁免=%d" % (registered, exempt))


# --------------------------------------------------------------------------- #
# (d) shape / frequency / sample interval
# --------------------------------------------------------------------------- #
def find_key_recursive(obj, key):
    """First occurrence of key in a nested dict/list, or None."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = find_key_recursive(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_key_recursive(v, key)
            if found is not None:
                return found
    return None


def check_d(root, rep):
    # factors_main.csv: 614 data rows x 153 factors (+ date column)
    fpath = os.path.join(root, "executions", "P006_E01_author", "cold_run",
                         "data", "processed_inputs", "factors_main.csv")
    if not os.path.isfile(fpath):
        rep.error("d_shape", "P006 factors_main.csv 缺失: %s" % rel(root, fpath))
    else:
        data = read_rows(fpath)
        nrows, ncols = len(data) - 1, len(data[0]) if data else 0
        rep.stat("factors_main_data_rows", nrows)
        rep.stat("factors_main_factor_cols", ncols - 1)
        if nrows != 614:
            rep.error("d_shape", "factors_main.csv 数据行数应为 614, 实为 %d" % nrows)
        if ncols - 1 != 153:
            rep.error("d_shape", "factors_main.csv 因子列数应为 153, 实为 %d" % (ncols - 1))
        if len(data) > 1:
            first, last = data[1][0][:7], data[-1][0][:7]
            rep.stat("factors_main_date_range", first + ".." + last)
            if not (first <= "1971-11" and last >= "2022-12"):
                rep.error("d_shape", "factors_main.csv 日期区间异常: %s..%s" % (first, last))

    # P006 OOS window: 494 months 1981-11..2022-12 (frozen in extracted_values.json)
    ev = os.path.join(root, "executions", "P006_E01_author", "extracted_values.json")
    if not os.path.isfile(ev):
        rep.error("d_shape", "P006 extracted_values.json 缺失（494月区间记录）")
    else:
        try:
            d = load_json(ev)
            n = find_key_recursive(d, "oos_months")
            s = str(find_key_recursive(d, "oos_start") or "")[:7]
            e = str(find_key_recursive(d, "oos_end") or "")[:7]
            rep.stat("p006_oos_months", n)
            rep.stat("p006_oos_window", s + ".." + e)
            if n != 494:
                rep.error("d_shape", "P006 oos_months 应为 494, 实为 %r" % n)
            if s != "1981-11" or e != "2022-12":
                rep.error("d_shape", "P006 OOS 区间应为 1981-11..2022-12, 实为 %s..%s" % (s, e))
        except Exception as exc:
            rep.error("d_shape", "P006 extracted_values.json 解析失败: %s" % exc)

    rep.info("d_shape", "形状/频率/区间检查完成")


# --------------------------------------------------------------------------- #
# (e) logs and declared outputs exist
# --------------------------------------------------------------------------- #
def check_e(root, rep):
    idx = os.path.join(root, "execution_index_r3_inherited.csv")
    if not os.path.isfile(idx):
        rep.error("e_logs", "execution_index_r3_inherited.csv 缺失")
        return
    rows = read_dicts(idx)
    rep.stat("execution_index_rows", len(rows))
    checked_logs = 0
    for row in rows:
        eid = row.get("experiment_id", "?")
        od = (row.get("output_dir") or "").strip()
        if not od:
            rep.error("e_logs", "%s 未声明 output_dir" % eid)
            continue
        full_od = os.path.join(root, od)
        if not os.path.isdir(full_od):
            rep.error("e_logs", "%s 输出目录缺失: %s" % (eid, od))
            continue
        for lp in (row.get("log_paths") or "").split(";"):
            lp = lp.strip()
            if not lp:
                continue
            checked_logs += 1
            target = lp if os.path.isabs(lp) else os.path.join(full_od, lp)
            if not os.path.isfile(target):
                rep.error("e_logs", "%s 日志缺失: %s/%s" % (eid, od, lp))
        sm = (row.get("sha256_manifest") or "").strip()
        if sm:
            target = sm if os.path.isabs(sm) else os.path.join(root, sm)
            if not os.path.isfile(target):
                rep.error("e_logs", "%s 输出 hash 清单缺失: %s" % (eid, sm))

    # every authorized + generated experiment must have a target_comparison.csv
    rq = os.path.join(root, "reviewer_queue.json")
    if os.path.isfile(rq):
        for r in load_json(rq).get("records", []):
            if r.get("execution_authorized") is True and r.get("execution_status") == "TARGETS_GENERATED":
                eid = r.get("experiment_id", "")
                token = eid.replace("-", "_")
                if not any(token in p.replace(os.sep, "_") for p in find_files(root, "target_comparison.csv")):
                    rep.error("e_logs", "已授权且已生成目标的实验无 target_comparison.csv: %s" % eid)
    rep.stat("logs_checked", checked_logs)
    rep.info("e_logs", "已核对执行记录=%d, 日志路径=%d" % (len(rows), checked_logs))


# --------------------------------------------------------------------------- #
# (f) enums + approval/execution compatibility
# --------------------------------------------------------------------------- #
LEGAL_EXEC_STATUS = {"NOT_RUN", "TARGETS_GENERATED", "EXECUTED", "COMPLETED"}
LEGAL_DECISION = {"APPROVE_FAITHFUL_REPLICATION", "REQUEST_EVIDENCE", "HOLD"}
LEGAL_VERDICT = {"PASS", "FAIL", "PARTIAL", "NOT_ASSESSED", "NOT_APPLICABLE",
                 "NOT_COMPARABLE", "REPORTED"}
LEGAL_CANDIDATE_STATUS = {"CORE", "EXTENDED", "EXCLUDED", "PENDING_EVIDENCE"}


def check_f(root, rep):
    rq_path = os.path.join(root, "reviewer_queue.json")
    if not os.path.isfile(rq_path):
        return
    records = load_json(rq_path).get("records", [])
    rep.stat("queue_records", len(records))
    n_auth = 0
    for r in records:
        eid = r.get("experiment_id", "?")
        st = r.get("execution_status")
        if st not in LEGAL_EXEC_STATUS:
            rep.error("f_enums", "%s execution_status 非法枚举: %r" % (eid, st))
        dec = r.get("requested_reviewer_decision")
        if dec is not None and dec not in LEGAL_DECISION:
            rep.error("f_enums", "%s requested_reviewer_decision 非法枚举: %r" % (eid, dec))
        v = r.get("numerical_verdict")
        if v is not None and v not in LEGAL_VERDICT:
            rep.error("f_enums", "%s numerical_verdict 非法枚举: %r" % (eid, v))
        auth = r.get("execution_authorized")
        if auth not in (True, False, "true", "false", "TRUE", "FALSE", None):
            rep.error("f_enums", "%s execution_authorized 非法值: %r" % (eid, auth))
        auth_bool = auth is True or str(auth).lower() == "true"

        # 未运行不得给出 PASS/FAIL/PARTIAL 判定
        if st == "NOT_RUN" and v in ("PASS", "FAIL", "PARTIAL"):
            rep.error("f_enums",
                      "%s 状态为 NOT_RUN 却标记判定 %s（错标 PASS/FAIL）" % (eid, v))

        # 授权必须与 reviewer 决定一致
        if auth_bool:
            n_auth += 1
            if dec != "APPROVE_FAITHFUL_REPLICATION":
                rep.error("f_enums",
                          "%s 标为 authorized 但 reviewer 决定为 %r（未批准实验被标 authorized）"
                          % (eid, dec))
            if not r.get("approval_record_id"):
                rep.warn("f_enums",
                         "%s 标为 authorized 且 reviewer 已批准，但未单列 approval_record_id（由 reviewed_source_commit 与 batch 协议承载）"
                         % eid)
        else:
            if dec == "APPROVE_FAITHFUL_REPLICATION":
                rep.warn("f_enums", "%s reviewer 已批准但 execution_authorized 非 true" % eid)
    rep.stat("queue_authorized", n_auth)

    # master_table 枚举
    mt = os.path.join(root, "master_table.csv")
    if os.path.isfile(mt):
        for row in read_dicts(mt):
            pid = row.get("paper_id", "?")
            st = row.get("execution_status")
            if st and st not in LEGAL_EXEC_STATUS:
                rep.error("f_enums", "%s master_table execution_status 非法枚举: %r" % (pid, st))
            cs = row.get("candidate_status")
            if cs and cs not in LEGAL_CANDIDATE_STATUS:
                rep.error("f_enums", "%s candidate_status 非法枚举: %r" % (pid, cs))

    # target_comparison 枚举与授权
    for path in find_files(root, "target_comparison.csv"):
        for lineno, row in enumerate(read_dicts(path), 2):
            st = row.get("execution_status")
            if st and st not in LEGAL_EXEC_STATUS:
                rep.error("f_enums", "%s:%d execution_status 非法枚举: %r"
                          % (rel(root, path), lineno, st))
            v = row.get("numerical_verdict")
            if v and v not in LEGAL_VERDICT:
                rep.error("f_enums", "%s:%d numerical_verdict 非法枚举: %r"
                          % (rel(root, path), lineno, v))
            auth = str(row.get("execution_authorized", "")).strip().lower()
            if auth and auth not in ("true", "false"):
                rep.error("f_enums", "%s:%d execution_authorized 非法值: %r"
                          % (rel(root, path), lineno, auth))
            if st == "NOT_RUN" and v in ("PASS", "FAIL", "PARTIAL"):
                rep.error("f_enums", "%s:%d NOT_RUN 却给出判定 %s"
                          % (rel(root, path), lineno, v))

    rep.info("f_enums", "授权实验=%d，枚举合法性检查完成" % n_auth)


# --------------------------------------------------------------------------- #
# (g) evidence_id resolvable
# --------------------------------------------------------------------------- #
EVIDENCE_ID_RE = re.compile(r"^P\d{3}-[SE]\d+$")


def check_g(root, rep):
    ei = os.path.join(root, "evidence_index.csv")
    if not os.path.isfile(ei):
        rep.error("g_evidence", "evidence_index.csv 缺失")
        return
    ids = set(r.get("evidence_id", "") for r in read_dicts(ei) if r.get("evidence_id"))
    rep.stat("evidence_index_ids", len(ids))

    refs = set()
    for path in find_files(root, "target_comparison.csv"):
        for row in read_dicts(path):
            for x in (row.get("evidence_ids") or "").split(";"):
                if x.strip():
                    refs.add(x.strip())
    mt = os.path.join(root, "master_table.csv")
    if os.path.isfile(mt):
        for row in read_dicts(mt):
            for x in (row.get("critical_evidence_ids") or "").split(";"):
                if x.strip():
                    refs.add(x.strip())

    canonical = set(x for x in refs if EVIDENCE_ID_RE.match(x))
    tags = sorted(refs - canonical)
    unresolved = sorted(canonical - ids)
    rep.stat("evidence_refs_canonical", len(canonical))
    rep.stat("evidence_refs_unresolved", len(unresolved))
    rep.stat("evidence_refs_nonstandard_tags", len(tags))

    for x in unresolved:
        rep.error("g_evidence", "evidence_id 无法在 evidence_index.csv 解析: %s" % x)
    if tags:
        rep.info("g_evidence",
                 "非标准标签(不按 evidence_id 解析, 已跳过): %s" % ", ".join(tags[:12]))
    rep.info("g_evidence", "标准 evidence_id 引用=%d, 未解析=%d" % (len(canonical), len(unresolved)))


# --------------------------------------------------------------------------- #
# (h) PASS/FAIL recomputation
# --------------------------------------------------------------------------- #
def check_h(root, rep):
    checked = 0
    skipped_verdict = 0
    skipped_rule = 0
    skipped_value = 0
    for path in find_files(root, "target_comparison.csv"):
        rpath = rel(root, path)
        for lineno, row in enumerate(read_dicts(path), 2):
            verdict = (row.get("numerical_verdict") or "").strip()
            if verdict not in ("PASS", "FAIL"):
                skipped_verdict += 1
                continue
            rule = (row.get("tolerance_rule") or "").strip() or (row.get("tolerance") or "").strip()
            rv = parse_number(row.get("replication_value"))
            paper_v = parse_number(row.get("paper_value"))
            ref_v = parse_number(row.get("reference_value"))
            # 规则声明"与 reviewer 参考值一致"时，基准是 reference_value 而非 paper 显示值
            baseline = ref_v if (ref_v is not None and "reviewer reference" in rule.lower()) else paper_v
            if baseline is None:
                baseline = ref_v
            pv = baseline
            if pv is None or rv is None:
                skipped_value += 1
                continue
            kind, tol, decimals = parse_tolerance(rule)
            if kind is None:
                skipped_rule += 1
                continue
            # 相对容差的分母为 0 时无定义；按已声明的绝对阈值处理（理论恒等式残差）
            if kind == "rel" and abs(pv) < 1e-15:
                kind = "abs"
            expected = apply_tolerance(kind, tol, decimals, pv, rv)
            if expected is None:
                skipped_rule += 1
                continue
            checked += 1
            expected_verdict = "PASS" if expected else "FAIL"
            if expected_verdict != verdict:
                rep.error("h_verdict",
                          "%s:%d 判定不可重算: paper=%s repl=%s rule=%r -> 应=%s, 实=%s"
                          % (rpath, lineno, pv, rv, rule[:60], expected_verdict, verdict))
    rep.stat("verdict_recomputed", checked)
    rep.stat("verdict_skipped_verdict", skipped_verdict)
    rep.stat("verdict_skipped_rule", skipped_rule)
    rep.stat("verdict_skipped_value", skipped_value)
    rep.info("h_verdict",
             "重算 %d 行；跳过(非PASS/FAIL)=%d, 规则不明=%d, 非数值=%d"
             % (checked, skipped_verdict, skipped_rule, skipped_value))
    if checked == 0:
        rep.error("h_verdict", "没有任何可重算的 PASS/FAIL 行（校验脚本或数据异常）")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv=None):
    parser = argparse.ArgumentParser(description="R4 review package delivery validator")
    here = os.path.dirname(os.path.abspath(__file__))
    default_root = os.path.dirname(here)
    parser.add_argument("--root", default=default_root, help="delivery root (default: parent of metadata/)")
    parser.add_argument("--manifest", default=None, help="manifest path (default: <root>/review_package_manifest.sha256)")
    parser.add_argument("--json-report", default=None, help="optional path for a JSON report")
    parser.add_argument("--quiet", action="store_true", help="suppress per-check INFO lines")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("FATAL: root 不存在: %s" % root, file=sys.stderr)
        return 2
    manifest = os.path.abspath(args.manifest) if args.manifest else os.path.join(root, "review_package_manifest.sha256")

    rep = Report()
    check_a(root, manifest, rep)
    check_b(root, rep)
    check_c(root, rep)
    check_d(root, rep)
    check_e(root, rep)
    check_f(root, rep)
    check_g(root, rep)
    check_h(root, rep)

    print("=" * 78)
    print("R4 DELIVERY VALIDATION  root=%s" % root)
    print("=" * 78)
    for cid in CHECKS:
        status = "FAIL" if rep.has_errors(cid) else "PASS"
        print("[%s] %-4s %s" % (status, cid, CHECK_TITLES[cid]))
        if not args.quiet:
            for c, m in rep.infos:
                if c == cid:
                    print("       INFO : %s" % m)
        for c, m in rep.warnings:
            if c == cid:
                print("       WARN : %s" % m)
        for c, m in rep.errors:
            if c == cid:
                print("       ERROR: %s" % m)
    print("-" * 78)
    print("STATS: %s" % json.dumps(rep.stats, ensure_ascii=False, sort_keys=True))
    print("SUMMARY: %s  errors=%d warnings=%d"
          % ("FAIL" if rep.errors else "PASS", len(rep.errors), len(rep.warnings)))
    print("=" * 78)

    if args.json_report:
        try:
            with open(args.json_report, "w", encoding="utf-8") as f:
                json.dump(rep.to_dict(root), f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print("WARN: 无法写 JSON 报告: %s" % exc, file=sys.stderr)

    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
