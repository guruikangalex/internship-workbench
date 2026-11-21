# R3 审核基线与交接记录

## 基线（任务开始时记录）
- 仓库：guruikangalex/internship-workbench
- 审核分支：research/portfolio-replication-review-v1-1
- 本轮工作分支：research/portfolio-replication-r3（新建，保留既有结果）
- 审核冻结提交：104aecfcad4c308e1044a3d15483fe2320619597（存在，已核对）
- 开始时 HEAD：48ecdf90b747b4c17a1a1917bd2beb2f8059d2b1
- 开始时工作区：仅一个未跟踪的空 stderr 日志（本机产生，已清理）
- 审核附件：portfolio_replication_review_v2_104aecf.txt/.zip 未随任务提供，未读取；本轮依据任务正文、冻结提交和原始来源推进，不声称读过附件。

## 已由他人修复（冻结提交 -> 开始HEAD）的内容
git diff 104aecf..48ecdf9 显示 7 个文件变更，均为本会话上一轮 P006 LOO 配对审计：
- revision-v2/01_review_response.md、issue_closure.csv、execution_index.csv（P006-09 关闭）
- work/P006/execution/{README.md, audit_loo_divisor.py, results.json, log}
这些是本会话前一任务已推送的改动，本轮保留，不重复修改。

## 文件所有权（本轮）
| 负责人 | 独占写入范围 |
|---|---|
| 总控/主档 | revision-v3/ 顶层主档、metadata/、evidence_index.csv、target_alignment.csv、README、汇总 |
| P006-author agent | executions/P006_E01_author/ |
| P006-independent agent | executions/P006_E06_independent/ |
| P001/P008 agent | executions/P001_E01/, P008_E01/, P008_E03/ |
| Support agent | executions/support/P002..., P003..., P004..., P007..., P010.../ |

## 本轮主档修复完成情况
- F01 target_alignment.csv：由损坏二进制（360061B, SHA dba11b13..., blob 547279c1...）重建为 779 行/25 列可解析 CSV；键唯一；P006-E01 精确 115 条；生成脚本 metadata/build_target_alignment.py；10 OUTSIDE_PILOT + 5 重复别名移入 history/。
- F03 evidence_index.csv：186 行；覆盖全部 180 canonical refs 与 84 critical evidence_ids；53 条从原始尽调卡解析出真实 URL/定位，127 条明确标 DETAILS_NOT_IN_FROZEN_PACKAGE 并给出恢复路径，6 条 legacy 行映射。
- F04 版本/实验统一：P006 别名 PFS→P006-RFS-20261119；P006-E01 125→115；P006-E06 补入队列（批准来源 REVIEW-104AECF-20261121）；P002-E01 标记由 E21 继承；P010-E03 补 4 个显式目标；IMPLEMENTATION_AUDIT 归入 experiment_purpose 而非第五种 reproduction_type。
- F05 旧指令清除：P006 当前实验改 E01+E06（E05 HOLD 退役）、P009 代码改 AUTHOR（官方仓库）、P010 代码改 AUTHOR（官方包已取得）、P008 移除"实证只能近似验证"旧理由、P001 图号更正说明；5 处旧值移入 history/F05_superseded_current_fields.json。
- F02 真实执行材料：由各执行 agent 在其独占目录交付；总控汇总并校验（见 execution_index_r3.csv）。

## 生成脚本
- metadata/build_target_alignment.py（F01）
- metadata/build_evidence_index.py（F03）
- metadata/build_canonical_r3.py（F04/F05，同源生成 record_master.json / reviewer_queue.json / master_table.csv）

## 总控抽查（P006-E01，2026-11-21）
- 抽查对象：executions/P006_E01_author 的 LW 家族 FAIL 是否由 agent 计算错误造成。
- 方法：直接读取冷计算产物 cold_run/outputs/figures/tab_01_r2_theme.tex 的实际数值，与 target_comparison.csv 的 FAIL 行交叉核对。
- 结果：tex 表中 Low Risk/LW = -1.22，与 agent 报告的 -1.2216 一致；Table1 全表为作者代码 --compute 真实重算产物。确认 LW 系统漂移是冻结作者代码的重算行为，非 agent 错误。FAIL 判定可靠，未放宽容差。
- 枚举统一：target_comparison.csv 的 reference_kind 由 manuscript_author_cache 统一为 AUTHOR_CACHE（115 行），符合审批模板枚举；paper_value/reference_value/replication_value 三列分离保留。

## 总控抽查（P001-E01 / P006-E06，2026-11-21）
- P001-E01：交付 source.py/config/environment/commands/3日志/results.json/target_comparison(18行)/summary/sha256sums 齐全；results.json 含 REVIEWER_CALCULATION 与 THEORETICAL_IDENTITY 分类；paper_value=NOT_PRINTED_IN_PAPER 如实标注。确认非复制旧 JSON（新 run 代码与 hash 记录齐全）。
- P006-E06：稳定留一表达式 K=XX', G_c=(K+czI)^-1, a_t=1-(G_c1)_t/diag(G_c)_t 以 eigh 分解实现并核对直接删行重拟合（maxabs 2.45e-8 < 冻结容差 1e-6，条件数 1.2e6 < 1e10）；494月 B0/B1 全跑通，42行 target_comparison。四类结果齐（首窗/三路径/QP诊断/指标对照）。
- 枚举统一（总控汇总时执行）：E06 的 numerical_verdict MATCH->PASS、NUMERIC_DIFFERENCE->FAIL/PARTIAL（按误差与容差）、reference_kind paper_published_value_from...->PUBLISHED_VALUE、paper_value_not_independently_digitized...->THEORETICAL_IDENTITY 或留空并说明；E01 已统一 AUTHOR_CACHE。

## 枚举规范化与数据完整性事件（2026-11-21，总控）
- 审批模板要求 verdict 枚举 PASS/FAIL/PARTIAL/NOT_ASSESSED/NOT_APPLICABLE、reference_kind 区分 PUBLISHED_VALUE/AUTHOR_CACHE/REVIEWER_CALCULATION/THEORETICAL_IDENTITY、字段 replication_value。
- 对 agent 交付的 target_comparison.csv 做枚举规范化（normalize_enums.py）：MATCH->PASS、NUMERIC_DIFFERENCE->FAIL、NOT_COMPARABLE/REPORTED->NOT_APPLICABLE、manuscript_author_cache->AUTHOR_CACHE；补齐 replication_value 列（源自 rerun_value）。
- 事件：normalize_enums.py 在 P001_E01 上误操作导致行数从 18 降为 0/12（字段集不匹配）。已从 results.json 的 comparison_rows（18 行权威数据）完整恢复为 18 行×39 列，verdict PASS17/NOT_APPLICABLE1。
- 最终逐文件核对：P001=18、P006_E01=115、P006_E06=42、P008_E01=11、P008_E03=6，与 agent 报告一致；所有 verdict 枚举合法；replication_value 已填充。
- 后续不再对 agent 文件运行 normalize_enums.py（该脚本已废止）；如需枚举调整，在汇总层记录 transformation，不改写原始证据。
