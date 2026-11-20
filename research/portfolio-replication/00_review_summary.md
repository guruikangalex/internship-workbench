# 组合优化论文复现立项包 v1.1

| 字段 | 本批次 |
|---|---|
| batch_id | CO-REP-20261120-02 |
| search_cutoff_date | 2026-11-20，Asia/Shanghai |
| agent_names_and_roles | search_a：AQR、J1/J2 及引文；search_b：Citadel、Millennium、P004/P010 数据代码；search_c：J3/J4 与拓展机构；paper6：P006 独立复核；backup：P001/P003/P008；due：P009 及其余篇目；总控：去重、补查、合并和终检 |
| scope_and_deviations | 四本指定期刊、补充刊物及工作稿，跨市场、不设起始年份。部分正式全文、附录、历史来源受限。 |
| records_screened | 21 篇主表记录（含 P005），另有初筛线索和排除日志；前包称约 90 条含重叠，本轮不把命中或重复数冒充独立文献数量。 |
| eligible_core_count | 11 |
| eligible_extended_count | 7 |
| awaiting_evidence_count | 2 |
| excluded_count | 排除日志 20 条，其中 P005 同时列主表 |
| deduplication_rule | 优先按 DOI，不足时用题名、作者、年份及研究对象；版本、勘误和代码证据分别保留。 |
| coverage_matrix_path | [coverage_matrix.csv](coverage_matrix.csv) |
| screening_log_path | [search_log.md](search_log.md) · [exclusion_log.csv](exclusion_log.csv) |
| best_first_project | P006-E05 · NBER w32004 2026-05-21 · AUTHOR_CODE_RERUN · R01/R03/R04/R05/R07 |
| backup_projects | P001-E01 正式期刊理论；P003-E01 Equity 3 实证；P004 合成试点；P002 正式版条件候选 |
| concentrated_questions_for_reviewer | 见下方 |
| reviewer_decision | PENDING |

## 首批与备选

**P006｜Universal Portfolio Shrinkage。** 建议审批 NBER w32004，2026-05-21 工作稿 + Harvard Dataverse V1 的 **P006-E05**。作者 ZIP 实下并校验，使用五份派生输入重算 Fig. 3、5、6a–f、8 和 Table 1。原始股票级数据不在首批边界。目标对照含 106 个数值与 61 项图表位置。RFS 在线录用稿 2026-09-24 上线，精确全文仍未取回，期刊版单独补证。 [协议](replication_protocol_P006.md)

**P001-E01｜正式期刊备选。** 锁定 JF 2013 正式版及 A15* 勘误，独立核对闭式动态调仓、信号衰减及持久冲击。可先跑公式和机制，精确坐标仍需确认初始持仓及绘图期数。历史商品实证另需 15 期货数据。 [尽调卡](cards/P001.md)

**P003-E01｜实证备选。** 推荐先审 Equity 3 对应的 Tables 5–6，需核定 French 49 行业历史数据及 w 的选择口径。Equity 2 的 40 日窗口不能支持 49 资产满秩样本协方差，原 MVO 单元格需补证。P004 合成试验可作为机器学习备选，前提是代码、目标版本与真实重训路径匹配。P010 已取得作者代码，但分发数据将原始观测置零，ICE 原始数值仍不可重算。 [P003](cards/P003.md) · [P004](cards/P004.md) · [P010](cards/P010.md)

## 集中待审

1. 是否批准 P006-E05 以指定 NBER 工作稿、派生数据、五组结果启动。RFS 路径所需补证单列。
2. P006 Table 1 UPSA All 的已知舍入差与 LW 个别格差须逐项验收。缓存重绘和 CSV 重算各留输出，不扩大通用容差。
3. 若首批必须为正式期刊，是否批准 P001-E01 的解析机制与勘误。精确图坐标及期货数据另审。
4. 是否先限 P003 Equity 3，并在历史输入和基准冻结后决定是否扩到 Equity 2。
5. P004 是选择 arXiv v1 的合成试点，还是补齐 QF 版本和勘误再立项。P002 与 P010 的历史数据授权单列。
6. P009 的事后切点诊断是否满足主题准入。P015 尚待工作稿全文。

实验及复现结果均为 **NOT_RUN**。全部审批字段为 **PENDING**。
