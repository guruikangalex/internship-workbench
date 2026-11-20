# 组合优化论文复现尽调包 v2

批次：`CO-REP-20261120-02-R2`。本包是主审审批前的研究包，不是正式复现结果发布。

## 结论

当前最适合启动的是 **P001：Dynamic Trading with Predictable Returns and Transaction Costs** 的有限理论核对（`P001-E01`）。本轮已在独立实现中完成修正后理论公式、标量情形、动态规划与 DARE 的数值一致性检查；最大残差约 `1.03e-15`，结果可复核。正式市场数据与论文图表仍为 `NOT_RUN`。

明确备选为 **P006：Universal Portfolio Shrinkage**。其作者代码、Dataverse 数据包和 RFS/NBER 两个版本均已锁定，首个 120 个月冷窗口预检通过；但论文 LOO 分母与作者实现存在已记录差异，需主审先选择作者代码重跑或忠实独立实现。

## 状态边界

- 主表、逐篇尽调卡、证据索引、检索覆盖、排除记录和审批队列均已生成。
- P001 仅执行用户明确授权的有限理论范围；P006/P002/P003/P004/P007/P008/P010 只做来源、数据、代码和首窗/单步预检。
- 除 P001 有限理论核对外，所有正式目标结果均标记 `NOT_RUN`；agent 建议不会替代主审批准，审批字段保持 `PENDING` 或 `REQUEST_EVIDENCE`。
- 作者代码重跑、忠实独立实现、近似验证、研究扩展在记录中分开，不混用缓存值作为重跑结果。

## 交付目录

`record_master.json` 与 `master_table.csv` 是文献主表；`work/P*/` 是逐篇尽调卡与协议；`target_alignment.csv` 是唯一细粒度目标账簿；`reviewer_queue.json` 是待主审审批队列；`issue_closure.csv` 和 `01_review_response.md` 记录第二轮问题闭环；`search/` 与 `coverage_matrix.csv` 记录检索覆盖和排除。

正式复现入口：先审核 `reviewer_queue.json`，锁定具体论文版本、实验范围和复现类型，再执行对应 `protocol.md`。不得把本包中的预检、作者缓存或派生统计量写入正式结果栏。
