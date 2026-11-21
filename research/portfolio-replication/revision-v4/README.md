# 组合优化论文复现尽调包 · R3（执行与交付）

批次：`CO-REP-20261120-02-R3`
审核基线：`REVIEW-104AECF-20261121` / 冻结提交 `104aecfcad4c308e1044a3d15483fe2320619597`
工作分支：`research/portfolio-replication-r3`（保留 v2 与先前审计改动，不覆盖）

> 本包是主审审批后、执行与结果交付工作包。已批准实验的依赖准备与常规预检不需重复申请；
> 最终验收仍由主审逐 result_id 完成。数值 verdict 仅表示计算层判断，不等于 main reviewer acceptance。

## 唯一入口与阅读顺序

1. `00_summary_r3.md` —— 本轮实际完成、执行状态、核心结果、差异与阻塞、待验收项。
2. `reviewer_queue.json` —— 18 条审批/执行记录；5 条 execution_authorized=true（P001-E01、P006-E01、P006-E06、P008-E01、P008-E03）。
3. `record_master.json` / `master_table.csv` —— 21 篇规范主记录（同源生成于 `metadata/build_canonical_r3.py`）。
4. `target_alignment.csv` —— 779 行全局目标账簿（F01 重建，P006-E01 精确 115 条）。
5. `evidence_index.csv` —— 186 行完整证据索引（F03）。
6. `issue_closure_r3.csv` —— F01–F05 与审批边界闭环。
7. `executions/` —— 各实验源码、配置、环境、命令、日志、结果与哈希（按负责人分目录）。
8. `metadata/r3_baseline.md` —— 审核基线、文件所有权、修复记录。
9. `history/` —— 已退役的旧指令/旧目标（带版本与原因，不作为现行执行依据）。

## 复现类型（仅四种）

`AUTHOR_CODE_RERUN` / `INDEPENDENT_FAITHFUL` / `APPROXIMATE_VALIDATION` / `RESEARCH_EXTENSION`
`IMPLEMENTATION_AUDIT` 是 `experiment_purpose`，不是复现类型。

## 本轮修复摘要（F01–F05）

- F01：损坏的 target_alignment.csv 重建为可解析 779 行 CSV，键唯一。
- F02：各已批准实验在独占目录交付真实执行材料；大型输入以稳定 URL + 哈希交接。
- F03：证据索引从 6 行扩展到 186 行，84 个 critical evidence_id 全覆盖。
- F04：P006 别名与 115 目标统一、E06 补入；P002 E01→E21 继承；P010-E03 补显式目标。
- F05：P001/P003/P007/P008/P009/P010 旧指令清除，旧值移入 history/。

## 大型输入取得方式

作者数据包与第三方大型归档不随仓库逐字节存放；在 `evidence_index.csv`、`input_manifest` 与各实验
`execution_manifest.json` 中给出 URL、版本、取得时间、哈希、形状、日期范围与列定义。
自编小文件（源码、配置、环境、脚本、日志、结果）均随本包真实交付。
