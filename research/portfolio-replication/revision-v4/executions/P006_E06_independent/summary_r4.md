# P006-E06 R4 独立实现重点修复与数学审计 — 总摘要

run_id：`P006-E06-R4-AUDIT-001`。旧结果全部保留（R3 42 行备份为
`target_comparison_v3_backup.csv`；关键 JSON 备份在 `history/`）。
新文件均在本目录；新运行产物在 `results/audit_*`、`results/qp_highprecision.json`、
`results/target_comparison_r4.csv`。所有数值来自真实进程运行。

## 核心结论（按任务）

| 任务 | 结论 |
| --- | --- |
| A 特征值/trace | `eig_K` 返回 **eig(XX')**（= T×作者 eig(XX'/T)，验证误差 9e-13）；作者/论文用 K/T，**作者对、E06 错**。trace scale 现行 0.9453 vs 一致 1.1382（偏小 **17%**）。修正后全期 Sharpe B0 **1.91517→1.92349**、B1 **1.91561→1.92380**，与作者 A（1.9228/1.9235）几乎一致；A-vs-B0 月收益 meanabs **0.0712→0.00049**。 |
| B 9 步分解 | 步 1/2（数据/网格）0 差；步 3 LOO 0.123；步 5 线性求解 1.9e-7；**步 6 trace 缩放 1.605 为主导**；步 8/9 收益/Sharpe 差 0.039/0.0076。低 z 假设 **SUPPORTED**（w_adj~1e-16 经 1/z 与近奇异分母放大到 0.2），但仅次要，绝非 A-vs-B0 主因——旧归因主次颠倒。 |
| C 信息泄漏 | **存在**：E06 用全部 494 OOS 月估一次 FF5 基准权重（前瞻）；作者用窗内 FF5（portfolios.py:49）。FF5 Sharpe 1.2249（泄漏）vs 1.1293（作者口径）；仅污染 FF5 基准与 alpha_vs_FF5，不污染 UPSA 策略本身。另立无前瞻为 RESEARCH_EXTENSION/诊断。 |
| D QP 精度 | 原配置 B0 14/494、B1 15/494 窗 KKT>1e-7（max 2.105e-7/1.555e-7），status 全 optimal 不等于 KKT 通过。收紧 cvxopt 到 1e-12 后 max **8.1e-13/9.2e-13**，全通过 ⇒ 容差限制、非 QP 不可行。原结果与 1e-7 阈值保留。 |
| E 警告/环境 | matmul 的 divide/overflow/invalid 告警 FP 标志**真实置位**（errstate raise），但**纯随机有限数组也触发**，494 窗全扫描输出均有限、无选择性损坏 ⇒ BLAS/numpy quirk，不篡改数值。requirements 误锁 `python==3.9.6`（非 pip 包）；environment 缺 pip 版本（实测 pip 26.0.1）。 |
| F 24 FAIL 重释 | 24 FAIL **不是 24 个恒等式失败**：18 个主题 R²、2 alpha、2 HAC t、2 换手，全是"B0/B1 复现值 vs 论文发表值超容差"。trace 修正后平均绝对误差 **0.153→0.0045**（B0 alpha 5.3307→**4.4599** vs 4.46；t 4.1196→**3.7189** vs 3.72；换手 12.7405→**12.398%** vs 12.4）。所有 R4 判定标 DIAGNOSTIC_ONLY，未获批准改判。 |

## 24 FAIL 的六类分解（按任务要求分开报告）

1. **LOO 数学等价**：通过（稳定式 vs 直接删行 maxabs 2.45e-8），非 FAIL 来源。
2. **QP 可行性**：494/494 optimal；KKT 超阈仅容差问题（任务 D），非 FAIL 来源。
3. **A/B0 数值一致性**：trace 缩放 bug 是主因，低 z 舍入为次要（任务 A/B），但这是诊断发现，不直接等于 24 个发表值对照。
4. **B0/B1 约定差异**：仅 T vs T−1 分母，Sharpe +0.00044、换手 +0.017pp，量级远小于实现差。
5. **作者代码与论文数值一致性**：作者 A（缓存 Sharpe 1.9228、换手 12.388%）与论文 1.92/12.4 一致；低 z 不稳定实现绑定发表数字（详细见 `eigenvalue_trace_audit.md`、`decomposition.md`）。
6. **发表结果是否匹配**：24 FAIL 全属此类；修正 trace 后 14/24 落入半单位容差，其余 10 个为舍入边界主题 R² 与 B1 t（论文仅发表单一值，B1 对照本身是 R4 增设），平均误差降 34 倍。

## 关键修正的可复现产物

- 修正全期收益/权重：`results/audit_A_corrected_returns_{B0,B1}.csv`、
  `audit_A_corrected_weights_{B0,B1}.csv`、`audit_A_corrected_ridge_{B0,B1}.csv`、
  `audit_A_corrected_full_raw.npz`（new run_id）。
- 证据 JSON：`audit_A_eigen_trace.json`、`audit_A_corrected_summary.json`、
  `audit_A_corrected_vs_author.json`、`audit_B_decomposition.json`、
  `audit_C_leakage.json`、`results/qp_highprecision.json`、`audit_E_warnings.json`、
  `audit_F_r4_summary.json`。
- 逐项分流：`discrepancy_decomposition.csv`（9 步）、`target_comparison_r4.csv`（42 行，
  新增 `r4_category`/`r4_status`/`r4_corrected_value` 等列；R3 旧版备份保留）。

## 边界与未决

- 所有 R4 新判定为**诊断结果**，未经审批不改 R3 的 PASS/FAIL/verdict。
- A 侧产物溯源：`compare_paths.py` 指向的旧 A bundle 路径已不存在；缓存 A（Sharpe 1.922774）
  与现存 `_stage_P006/main_bundle.p`（1.923475）逐月差 maxabs 0.044。已在证据中记录，
  不影响"修正 trace 后 B0 与作者一致"的结论。
- 未修改顶层主档、E01 或其他实验目录；仅写本目录。
