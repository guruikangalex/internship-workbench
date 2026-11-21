# P008-E01 R4 执行链修复 + 干净重跑摘要（run_id R4-P008-001）

## 0. 执行链修复
- 旧脚本（`source_v3_backup.py`）尾部只打印 `ALL CHECKS PASS = False` 却返回 exit **0**。
- 修复版 `source.py`：checks 分三层——`REQUIRED_SOURCE`（→exit 1）、`REQUIRED_MATH`（正常条件数命题，→exit 2）、`DIAGNOSTIC`（病态压力测试，PARTIAL/REPORTED）；`main()` 返回 `exit_code`，入口 `sys.exit(main())`。
- 本次重跑 **exit code = 0**（全部 REQUIRED 通过），`execution_status=EXECUTED`。

## 1. 范围与批准
- Pedersen, Fitzgibbons & Pomorski (2021), JFE 142(2):572-597；批准 REVIEW-104AECF-20261121；范围 P008-R01（约束组合优化、KKT、投影、四基金张成、Prop.2 前沿）。
- 环境：Python 3.9.6（env_py396）、numpy 2.0.2；KKT 相对残差阈值 **1e-10** 冻结于 2026-11-21T07:29:34Z（未改）；`run_stderr.log` 末行 `PROCESS_EXIT_CODE=0`。
- 无市场数据、无论文图坐标重建。

## 2. 正常条件数例子（纳入 PASS 判定）
| 检查项 | 本 run 值 | 冻结阈值 | verdict |
|---|---|---|---|
| cond(Σ) | 5.1856 | [5, 200] | PASS |
| KKT 相对残差 | **3.494e-16** | ≤ 1e-10 | PASS |
| 闭式解 vs 直接 KKT solve（maxabs） | 1.041e-17 | ≤ 1e-9 | PASS |
| 闭式解 vs 零空间投影（maxabs） | 1.041e-17 | ≤ 1e-9 | PASS |
| 四基金张成重构误差 | 3.469e-18 | ≤ 1e-9 | PASS |
| 前沿 s* 处 dSR/ds | ≈0 | ≤ 1e-6 | PASS |
| q=0 / 投影收益为零 / 风险净头寸为零 | 显式处理 | — | PASS |

## 3. 病态压力测试（单独判定，不计入正常条件 PASS）
- 构造 cond(Σ) ≈ **1.000e+09**（`diag[1e-8,1,2,3,10]` 正交相似）；KKT 相对残差 = 2.173e-09。
- 该项记为 `PARTIAL` / `REPORTED`，`degeneracies.ill_conditioned.excluded_from_pass = true`；按预声明协议，1e-10 阈值**仅适用于正常条件数例子**，病态例不冒充正常条件 PASS，也不反向否定正常条件结论。

## 4. 来源核验
- 论文 PDF（ScienceDirect OA 出版版）实测 SHA256 = `5beedbbc054e915e9d82e8c6a3de2b1cde58ff4ec61dd4ec5d700262c38283c2`，与 config 记录一致；与 CBS 出版版逐字节一致性仍 UNKNOWN（protocol B02 open，如实记录）。

## 5. 交付文件
`source.py`（修复版）、`source_v3_backup.py`、`config.json`、`environment.json`、`commands.txt`、`run_stdout.log`、`run_stderr.log`、`results.json`、`target_comparison.csv`、`target_comparison_v3_backup.csv`、`summary.md`（R3 原件）、`summary_r4.md`（本文件）、`sha256sums.txt`、`exit_code_test.md`。
