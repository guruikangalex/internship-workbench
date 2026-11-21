# R4 P0 交付完整性审计（Agent A）

生成时间：2026-11-21　｜　对象：`revision-v4/`　｜　修复目标：R3 审查发现的 Manifest/Git 快照不一致、校验脚本无效、故障注入缺失。

---

## 1. 结论摘要

| 指标 | 数值 |
|---|---|
| revision-v4 本地文件总数 | 315（审计时刻；其他 agent 仍在写入，最终以 manifest 为准） |
| 必须入库（自编文本/结果/小 CSV） | 309 |
| 不入库外链文件（本地存在） | 6：`review_package_manifest.sha256`（不含自身）+ FF25 23MB CSV + 2 个 `.p` + 1 个 `.npz` + 1 个 `.xlsx` |
| `external_dependencies.json` 条目数 | 11（含 4 个不在 revision-v4 的备份/公开下载项） |
| 外链条目 SHA256 实算一致率 | 11/11 = 100% |
| manifest 对入库文件覆盖率 | 100%（入库文件 100% 有 hash；manifest 不含自身、不含外链大文件） |
| `validate_delivery.py` 基线 | PASS（`errors=0`，1 条授权记录缺单列 approval_record_id 的 WARN） |
| 故障注入 | 5/5 全部检测到并返回非零退出码 |

---

## 2. 文件分类与判定依据

### 2.1 (a) 自编、必须入库

判定依据：**由本项目 agent 自己生成或整理**，且为文本/小体量结果，fresh clone 无法从公开稳定来源逐字节复得，必须随 Git 交付。

- 源码与构建脚本：`.py` 55 个（含 `metadata/build_*.py`、`metadata/validate_delivery.py`、`executions/**/source.py`、`code/*.py`、`.R`/`.sas` 源码）。
- 控制与主表：`.csv`（除 FF25 外）：`master_table.csv`、`target_alignment.csv`、`evidence_index.csv`、`reviewer_queue.json` 对应的汇总表、`coverage_matrix.csv`、`execution_index_r3_inherited.csv`、`issue_closure_r3_inherited.csv`、各实验 `target_comparison.csv`、`results/*.csv`。
- 配置/结果/日志/证据索引：`.json` 44、`.md` 33、`.log` 35、`.txt` 19、`.tex`/`.rproj`/`.html`/`.deprecated`。
- 结果图：`.jpg` 38（冷重算/独立审计产生的图表，体量小，属结果物）。
- 派生数据 CSV（虽 >1MB 仍入库）：`factors_main/large/small/mega.csv`（约 2MB）、`weights_B0/B1.csv`（约 1.4MB）——它们是**自编可复算的派生结果**，不是第三方下载输入，故按"小 CSV/结果"入库。

### 2.2 (b) 大型第三方输入/缓存，必须外链

判定依据：**非自编**、来源 URL 稳定、体量大（放 Git 会污染仓库）、且接收方可按 URL + 冻结 SHA256 重新取得或由源码重算。

| 文件 | 体量 | 理由 | 登记位置 |
|---|---|---|---|
| `executions/support/P010/data/official_code_archive.zip` | 955,004,837 B | 作者 Dropbox 公开归档，含全零占位 `.mat` | external_dependencies.json |
| `executions/support/P010/data/trace_public_archive.zip` | 491,720,701 B | TRACE 公开数据 Dropbox 归档 | 同上 |
| `P006_upsa_reproduction_RFS_v2.zip` | 123,737,306 B | RFS 作者补充材料 | 同上 |
| `executions/support/P007/data/25_Portfolios_5x5_Daily.csv` | 24,101,059 B | Ken French 数据解压产物 | 同上 |
| `main_bundle.p` / `is_vs_oos.p` | 15,976,897 / 1,125 B | 作者代码冷重算 pickle 缓存，可重算 | 同上 |
| `audit_A_corrected_full_raw.npz` | 1,274,478 B | 独立审计数组缓存，可重算 | 同上 |
| AQR `ESG_efficient_frontier_portfolios_vF.xlsx`（`downloaded_from_aqr.xlsx`） | 215,209 B | AQR 公开工作簿 | 同上 |
| P002 `Factor Details.xlsx` / `Country Classification.xlsx` | 39,959 / 11,554 B | ReplicationCrisis 公开仓库 | 同上 |

`.gitignore` 规则：`*.zip *.p *.npz *.xlsx *.xls *.pdf *.mat *.h5 *.so *.dylib ...` 等一律排除；自编 `.py/.md/.csv/.json/.log/.txt/.sha256/.r/.sas` 全部入库。

---

## 3. fresh clone 检查方法

```bash
# 3.1 只看 Git 实际会提交的文件（含未跟踪时先按 .gitignore 过滤）
git add -A && git ls-files | sort > /tmp/tracked.txt

# 3.2 只归档入库文件，验证包自洽
git archive --format=tar HEAD | tar -tf - | sort > /tmp/archived.txt

# 3.3 用 manifest 校验所有入库文件（fresh clone 后执行）
shasum -a 256 -c review_package_manifest.sha256        # 全行 OK 即通过

# 3.4 运行交付校验器（8 项检查）
<py396>/bin/python metadata/validate_delivery.py --json-report /tmp/delivery.json
#   exit 0 = PASS；非 0 = FAIL
```

`validate_delivery.py` 不依赖本地私有路径：外链大文件的路径只用于 `external_dependencies.json` 记录；fresh clone 缺这些二进制时不报错（它们不在 manifest 中），但会提示按 URL 重下并核对 hash。

覆盖率定义：`manifest 条目数 == 入库文件数`，且每个入库文件的 SHA256 与 manifest 一致。当前 `review_package_manifest.sha256` 对入库文件覆盖率 100%，不含自身，不含 6 个外链/二进制文件。

> 注：并行 agent 仍在写入 `executions/` 与 `metadata/`。**任何主档文件在 manifest 生成之后再被修改，都必须重新生成 manifest 并重跑 `validate_delivery.py` 与 `shasum -a 256 -c`**，否则会因 hash 漂移fail。

---

## 4. 校验器检查项（8 项）

- (a) manifest 每个文件存在且 SHA256 一致；外链大文件不得列入 manifest。
- (b) 所有 CSV/JSON 可解析、列数一致、关键文件必需字段齐全（外链 CSV 按记录跳过）。
- (c) `target_comparison.csv` 的 `experiment_id` 必须在 `reviewer_queue.json` 中；`result_id` 必须在 `target_alignment.csv` 注册（E06 声明性 ad-hoc 审计变体豁免并计数）。`check_alignment.csv` 若存在则同规则核对。
- (d) `factors_main.csv` 614 数据行 × 153 因子；P006 OOS 494 月 1981-11..2022-12（递归读取 `extracted_values.json`）。
- (e) `execution_index_r3_inherited.csv` 声明的 output_dir / 日志 / sha256sums 均存在；已授权且生成目标的实验必须有 `target_comparison.csv`。
- (f) `execution_status`/`requested_reviewer_decision`/`numerical_verdict`/`candidate_status` 合法枚举；NOT_RUN 不得标 PASS/FAIL/PARTIAL；authorized 必须与 reviewer 批准决定一致。
- (g) 形如 `P\d{3}-[SE]\d+` 的 evidence_id 必须在 `evidence_index.csv` 可解析；非标准标签（如 `FIG-DRIFT`、`P008-B02`）跳过并报告。
- (h) 对每行 PASS/FAIL 按冻结容差重算：解析 `abs<=X`/`+/-X pp`/`half unit 0.005` 显示舍入/`relative <= X`/`exact`/`must exceed X`；"reviewer reference" 规则以 `reference_value` 为基准；分母为 0 的相对规则退化为绝对阈值；规则不明的行跳过并计数。当前重算 154 行、0 不一致。

---

## 5. 故障注入证据

见 `metadata/fault_injection_results.json`。5 项测试均在 `tempfile.mkdtemp` 临时副本中执行，基线 errors=0，注入后：

| 编号 | 注入 | 命中检查 | 退出码 |
|---|---|---|---|
| FI-01 | 删除必需文件 `README.md` | a_manifest | 1 |
| FI-02 | `master_table.csv` 末尾加 1 字节 | a_manifest（+b_parse） | 1 |
| FI-03 | 从 `target_alignment.csv` 删目标 ID `P001-R01` | c_ids | 1 |
| FI-04 | NOT_RUN 实验错标判定 PASS | f_enums | 1 |
| FI-05 | 未批准实验 `P001-E02` 标为 authorized | f_enums | 1 |

结论：校验脚本具备真实检测能力，非纸面声明。

---

## 6. 写入路径（本 agent 所有权范围）

- `metadata/validate_delivery.py`
- `metadata/external_dependencies.json`
- `metadata/delivery_audit.md`
- `metadata/fault_injection_results.json`
- `review_package_manifest.sha256`
- `.gitignore`

未修改其它主档文件，未修改 `executions/` 实际内容（仅读取与临时快照）。
