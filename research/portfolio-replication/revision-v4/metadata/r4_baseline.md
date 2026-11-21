# R4 审核基线与交接记录

## 基线（任务开始时记录，2026-11-21 16:38 CST）
- 仓库：guruikangalex/internship-workbench
- 审查基线分支：research/portfolio-replication-r3
- 审查冻结 commit：f548dbd934ed4773f60a27f5abbae7c355d469cb（已 fetch 验证存在）
- 审查目录：research/portfolio-replication/revision-v3/
- 本轮工作分支：research/portfolio-replication-r4（新建，基于 f548dbd）
- 本批目录：research/portfolio-replication/revision-v4/
- 批次：CO-REP-20261120-02-R4
- 审核附件：本轮未提供 txt/zip 附件；依据任务正文、冻结 commit 与原始来源推进，不声称读过未取得附件。

## P0 交付完整性根因（总控实测）
- 主审检查 R3 ZIP：manifest 195 文件，105 存在且 hash 一致、76 缺失、14 不匹配。
- 根因：R3 通过 MCP push_files 分批推送时，165 个待推文本文件中仅 120 个进入远端 Git（批次逻辑 bug：多批只有 1 文件），本地实际有 284 文件（含 P006-E01 冷计算 src/*.py、scripts/*.py、run_all.py、5个CSV、日志、115项 target_comparison；P006-E06 weights_B0/B1.csv；support P010 产物）。
- 本地 revision-v3 全程 untracked（从未 git commit），远端 Git 树不含上述文件。
- R4 处理：把本地完整备份（284 文件，1.4GB）复制到 revision-v4，排除大型第三方二进制（912M/480M P010 archives、15M bundle .p、23M FF25 CSV、xlsx），保留 240 文件/46MB；自编源码/配置/日志/结果/小CSV 全部入库，大文件以 external_dependencies.json 交接。

## 文件所有权
| Agent | 独占写入范围 |
|---|---|
| A（交付完整性） | metadata/validate_delivery.py, external_dependencies.json, delivery_audit.md, fault_injection_results.json, review_package_manifest.sha256, .gitignore |
| B（P006-E01） | executions/P006_E01_author/ |
| C（P006-E06） | executions/P006_E06_independent/ |
| D（P001/P008） | executions/P001_E01/, P008_E01/, P008_E03/ |
| E（主档） | 顶层 master_table/record_master/reviewer_queue/target_alignment/check_alignment/evidence_index/execution_index/issue_closure_r4/00_review_response/coverage_matrix |
| 总控/F（独立验收） | history/independent_review/, 最终汇总, Git 推送 |

## 关键约束
- 保留所有旧 FAIL/PARTIAL/失败日志；修复生成新 run_id，不覆盖旧结果。
- 不得事后放宽容差、改样本、替换算法提高 PASS。
- 论文结果数与辅助检查数分开（check_alignment.csv）。
- reference_kind 区分 PUBLISHED_VALUE / AUTHOR_CACHE / REVIEWER_CALCULATION / THEORETICAL_IDENTITY。
- 退出码：输入缺失/来源hash失败/必需数值检查失败 → 非零；数学通过与来源失败分别报告。
