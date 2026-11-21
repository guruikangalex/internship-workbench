# P001-E01 R4 执行链修复 + 干净重跑摘要（run_id R4-P001-001）

## 0. 执行链修复
- 旧脚本（`source_v3_backup.py`）尾部只打印 `ALL CHECKS PASS = False` 却返回 exit **0**。
- 修复版 `source.py`：checks 分为 `REQUIRED_SOURCE`（→exit 1）、`REQUIRED_MATH`（→exit 2）、`DIAGNOSTIC`（PARTIAL，不影响 exit 0）；`main()` 返回 `exit_code`，入口 `sys.exit(main())`。
- 本次重跑 **exit code = 0**（全部 REQUIRED 通过），`execution_status=EXECUTED`。

## 1. 性质与批准
- THEORY / FORMULA VERIFICATION ONLY；不是图复现、不是市场经济实证、无商品期货数据。
- 批准：REVIEW-104AECF-20261121 / reviewed_source_commit `104aecfcad4c308e1044a3d15483fe2320619597`；范围 A15*、Riccati A7/A10/A11、标量与矩阵公式、交易速度 γ 与 aim、非对易数值例子、有限时域终端记账（R01/R02/R03/R09）。
- 环境：Python 3.9.6（env_py396）、numpy 2.0.2；容差沿用 R3 冻结值（2026-11-21T07:29:34Z，未改）；命令见 `commands.txt`；`run_stderr.log` 末行 `PROCESS_EXIT_CODE=0`。

## 2. 关键数值（reviewer 高精度值仅作参考，非论文印刷值）
| 项 | reviewer 参考值 | 本 run 复算值 | verdict |
|---|---|---|---|
| a（Eq.9） | 0.7421582911108061 | **0.7421582911108061** | PASS |
| a/λ（Eq.10） | 0.371079145555403 | **0.3710791455554031** | PASS |
| aim0 | (1.7415054571868176, 1.2549203600714012) | **(1.7415054571868176, 1.2549203600714012)** | PASS |
| aim/Markowitz 比 | 0.870752728593409 / 0.6274601800357007 | 同值 | PASS |
| 首笔交易 L2（w=1/0.5/0） | 0.796539 / 0.955134 / 1.551842 | 0.7965390292891897 / 0.9551339448438003 / 1.5518416579735714 | PASS |

- 上述 reviewer 值在 `target_comparison.csv` 中一律 `reference_kind=REVIEWER_CALCULATION`，**不写成论文印刷值**（`paper_value=NOT_PRINTED…`）。
- 非对易例子：`reference_kind` 相关行标 `FORMULA_VERIFICATION`，不冒充论文图；交换子值因矩阵对不同而 `NOT_COMPARABLE`，但独立确认同一机制（A15* 满足 A7、原式 A15 失效）。

## 3. 来源核验（hash 全部通过）
| 来源 | 预期 SHA256 | 本 run 实测 | 结果 |
|---|---|---|---|
| 正式版论文 PDF | b9b01f48bd7ff0ce0431615d88b76f8a076b6593cc1d7765bd6ec2eb617473ab | 同 | PASS |
| 官方勘误 PDF | 99469db904292d2a909bd40151009891103bd11b95b94c95a8d0b25f3717baa2 | 同 | PASS |
| 包内勘误 PDF | 99469db904292d2a909bd40151009891103bd11b95b94c95a8d0b25f3717baa2 | 同 | PASS |

- 官方勘误与包内勘误逐字节一致；来源输入只读、无网络、无市场数据。

## 4. 范围与口径更正（已核对）
- **Figure 3 = 市场数据实证**（原油/黄金期货头寸）；**正式版无 Figure 5**；Figure 1/2/4 为理论/冲击响应。本 run 不复制任何图坐标、不做市场数据实证。
- 理论恒等式/残差零目标（A7/A10/A11、几何和 aim、Bellman、160 期直接求解、终端记账）一律标 `THEORETICAL_IDENTITY`。
- 市场经济评价 `market_economic_verdict = NOT_ASSESSED`；脚注9参数、零旧仓、30/160 期等自选项单列，不冒充论文印刷值。
- 终端记账：20 随机点代数恒等式 maxabs ≈ 3.55e-15；β^t|W_t| 在 t=30 趋零。

## 5. 交付文件
`source.py`（修复版）、`source_v3_backup.py`、`config.json`、`environment.json`、`commands.txt`、`run_stdout.log`、`run_stderr.log`、`results.json`、`target_comparison.csv`、`target_comparison_v3_backup.csv`、`summary.md`（R3 原件）、`summary_r4.md`（本文件）、`sha256sums.txt`、`exit_code_test.md`。
