# 任务 C：样本外信息泄漏排查（FF5 基准权重）

run_id：`P006-E06-R4-AUDIT-001`。证据：`results/audit_C_leakage.json`。
定位：`independent_upsa.py:412-419`（`compute_metrics`）。

## 代码事实

- E06 现行：`b = benchmark.reindex(dates)`（dates = 494 个 OOS 月），
  `ff5 = b[[mkt,smb,hml,rmw,cma]]`，`bw = solve(cov(ff5), mean(ff5))`，
  `ff5_ret = ff5 @ bw` —— **对全部 494 个样本外月估一次权重**，
  每个 OOS 月都用到包括未来月在内的全样本均值/协方差。
- 作者代码 `src/portfolios.py:49`（`_window_one`）：
  `ff5_ins = FF5[i:rw+i]`，`b_weights = solve(cov(ff5_ins), mean(ff5_ins))`，
  `opt['FF5'] = ff5_oos @ b_weights` —— **逐窗仅用窗内 FF5**，无前瞻。

## 判定

| 问题 | 结论 |
| --- | --- |
| 是否前瞻偏差？ | **是**。单一 FF5 权重用到所有 494 OOS 月，对每个日期都含未来信息。 |
| 论文/作者原文口径？ | 作者原文用窗内 FF5 估计逐窗基准，E06 与之**不一致**。 |
| 属于原文比较口径？ | 否。E06 的 FF5_sharpe 与 alpha_vs_FF5 未按作者口径构造。 |
| 能否作为真实可交易策略？ | **不能**（需未来 FF5）。滚动/扩展窗版本可交易。 |
| 影响范围？ | 仅 `benchmark.FF5_sharpe` 与 `alpha_vs_FF5_pp`；**不影响** B0/B1 UPSA 策略收益、Sharpe、换手、pricing R²、alpha_vs_ridge、alpha_vs_CAPM（这些从不读 benchmark）。 |

## 数值影响（同一批 494 月，三种 FF5 基准口径）

| 口径 | FF5 Sharpe | alpha(B0) vs FF5 (pp) | alpha(B1) vs FF5 (pp) |
| --- | --- | --- | --- |
| 全 OOS 一次性估计（E06 现行） | **1.22488** | 17.840 | — |
| 窗内滚动（作者口径） | 1.12932 | 17.069 | — |
| 扩展窗（研究扩展） | 1.09177 | 16.770 | — |

- 复算的全 OOS FF5 Sharpe 1.2248758 与 `metrics.json` 记录值 1.2248758 逐位一致，确认复现了 E06 代码路径。
- 全 OOS vs 滚动的月收益序列 maxabs = **1.5126**；Sharpe 相差 **0.0956**；alpha 相差约 **0.77 pp**。
- 复算与作者口径的 FF5 基准差异是**实实在在的数值差异**，不应判为"无害"。

## 处理

按要求：另立**无前瞻基准**（滚动窗为作者可比口径，扩展窗为研究扩展）为
`RESEARCH_EXTENSION / DIAGNOSTIC`；全 OOS 版本明确标注为 look-ahead 诊断。
`ff5_series` 三种口径的逐月序列已存入 `audit_C_leakage.json`。
本项**不混入**原文复现判定；24 个 FAIL 中不含 FF5_sharpe 或 alpha_vs_FF5，
故该泄漏不是任何 FAIL 的直接原因（见任务 F）。
