# R4 审查逐项回应

批次：CO-REP-20261120-02-R4 ｜ 基线：`104aecfcad4c308e1044a3d15483fe2320619597` / `REVIEW-104AECF-20261121`
说明：凡标注「占位」的路径为其他 Agent 正在交付的文件，本轮不编造其内容或数值结果。

## 1. Manifest 完整性

- 实际修改：本 Agent 不拥有 manifest 写入权（Agent A 负责）。顶层 `review_package_manifest.sha256` 
  原样保留，未改写。
- 证据路径：`review_package_manifest.sha256`（占位，待 Agent A 重建/核验）；
  `metadata/validate_delivery.py`（占位，Agent A 交付）。
- 关闭状态：**PENDING_AGENT_A**。

## 2. 校验脚本

- 实际修改：新增 `metadata/build_canonical_r4.py`，生成后自检 CSV/JSON 可解析、枚举合法、ID 唯一；
  R3 的 `metadata/validate_r3.py` 保留。交付级校验由 Agent A 的 `validate_delivery.py` 负责。
- 证据路径：`metadata/build_canonical_r4.py`；`metadata/validate_r3.py`；
  `metadata/validate_delivery.py`（占位）。
- 关闭状态：**PARTIAL**（本 Agent 自检 PASSED，交付级待 Agent A）。

## 3. 证据占位（127 条 DETAILS_NOT_IN_FROZEN_PACKAGE / 57 个 critical NOT_READ）

- 实际修改：`evidence_index.csv` 新增五列分级（ID 覆盖 / 原始来源可访问 / 原文实际阅读 / 
  决定性事实核验 / 独立复核）。占位行**保持 NOT_READ / UNVERIFIED / NOT_DONE**，
  只补可追溯 ID 与 2026-11-21 实测 HTTP 状态；不把「ID 存在」改写成「已核实」。
- 五个率（全体）：见 `metadata/evidence_coverage_summary.md`；
  ID 覆盖 186/186，原文实际阅读仅 5 行 READ_FULL，决定性事实核验 5 行，独立复核 2 行。
- 证据路径：`evidence_index.csv`；`metadata/evidence_coverage_summary.md`。
- 关闭状态：**FIXED_DISCLOSURE**（占位如实披露；原文层面的补全需后续来源卡回收）。

## 4. 状态冲突（reviewer_queue vs execution_index）

- 实际修改：`reviewer_queue.json` 五个已批准实验的 `execution_status` 由 NOT_RUN 统一为
  `executions/*/target_comparison.csv` 的实读值；未批准实验保持 NOT_RUN。
  共修正 5 条（P001-E01/P006-E01/P006-E06/P008-E01/P008-E03）。
  `execution_index.csv` 含真实 run_id 与输出 hash（`output_sha256`）。
- 证据路径：`reviewer_queue.json`（`r4_status_reconciliation`）；`reviewer_queue_r4.json`；
  `execution_index.csv`。
- 关闭状态：**FIXED**。

## 5. P006-E01 四脚本问题 + 17 FAIL

- 实际修改：`static_check.md` 的入口链路核查结论保留（run_all.py --main --compute 真实重算，
  非缓存重绘）；17 个 FAIL **未放宽容差**，总控抽查 LW=-1.22 与冷计算 tex 一致，
  确认是冻结作者代码重算行为而非 agent 错误。
- 证据路径：`executions/P006_E01_author/static_check.md`；
  `executions/P006_E01_author/summary.md`；`executions/P006_E01_author/target_comparison.csv`；
  `executions/P006_E01_author/run_end.txt`（EXIT_CODE=0，实读）。
- 关闭状态：**FIXED_NO_TOLERANCE_CHANGE**。

## 6. P006-E06 六项

- 实际修改：42 行 check 按 4 核心目标分层（4 PAPER_TARGET / 19 SUB_CHECK / 19 DIAGNOSTIC）；
  六项结论（留一稳定式、删行等价、494 月 B0/B1、QP 诊断、低 z 舍入、alpha 差异）
  保留在实验 summary，不追数。
- 证据路径：`executions/P006_E06_independent/summary.md`；
  `executions/P006_E06_independent/target_comparison.csv`；`check_alignment.csv`。
- 关闭状态：**FIXED_MAPPED**。

## 7. P001 / P008 退出码

- 实际修改：P001_E01、P008_E01、P008_E03 目录内 stderr 为空、stdout/results.json 齐全，
  但**未留存显式 EXIT_CODE 文件**；本轮不编造退出码，登记为 LOG_BASED_INFERENCE，
  请对应执行 agent 补交 `run_end.txt`（占位路径）。
- 证据路径：`executions/P001_E01/{run_stdout.log,run_stderr.log,results.json,run_end.txt(占位)}`；
  `executions/P008_E01/...`；`executions/P008_E03/...`。
- 关闭状态：**PENDING_EXIT_CODE_FILE**。

## 8. check_alignment 分层汇总结论

- 共 192 行；计入论文结果 126 行，辅助/子检查/诊断 66 行。
- P006-E01 115 行全部计为论文结果（含 17 FAIL / 8 PARTIAL，不因 verdict 改计数）；
  P001-E01 4 行计入、14 行子检查；P008-E01 1 行计入、10 行子检查；
  P006-E06 4 行计入、38 行分层；P008-E03 仅 R10/R11 两行计入、4 行辅助。
- 证据路径：`check_alignment.csv`。
- 关闭状态：**FIXED**。

## 9. 执行目录 R3/R4 版本变体并存（披露，不擅自裁决）

- 执行 Agent 在原位更新了 `target_comparison.csv`，并保留 `target_comparison_v3_backup.csv`；
  P006-E01 另有 `target_comparison_r4.csv`（run_id `-R4`，FAIL 18 / PARTIAL 7）。
- 本 Agent 的 `check_alignment.csv` 与 `execution_index.csv` 统一读取当前 `target_comparison.csv`，
  五个实验行数保持 18/115/42/11/6；版本差异交总控最终裁定，本轮不改写、不编造裁决结果。
- 证据路径：`executions/*/target_comparison*.csv`；`issue_closure_r4.csv`（R4-DOC-02）。
- 关闭状态：**DISCLOSED_PENDING_CONTROL**。

## 口径声明

所有数值结论均来自已落盘的 source/target_comparison/summary/日志；
凡本 Agent 未实际读取的文件（其他 agent 交付物）只写路径占位，不写数值。
