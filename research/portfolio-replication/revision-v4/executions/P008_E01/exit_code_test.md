# Exit code 修复验证 — P008_E01（R4）

## 1. 问题与修复
- R3 问题：`source.py` 尾部仅打印 `ALL CHECKS PASS = False`，`main()` 正常返回，进程 exit **0**。
- R4 修复：checks 分三层——`REQUIRED_SOURCE`（→exit 1）、`REQUIRED_MATH`（正常条件数命题，→exit 2）、`DIAGNOSTIC`（病态 cond≈1e9 压力测试，记为 PARTIAL/REPORTED，不参与正常条件 PASS）；`main()` 返回 `exit_code`，入口 `sys.exit(main())`。
- 退出码语义：**0**=PASS；**1**=SOURCE_FAIL（PDF 缺失/hash 不符）；**2**=MATH_FAIL（正常条件 KKT>1e-10、四基金张成、前沿恒等式等失败）。

## 2. 测试环境与方法
- Python 3.9.6（env_py396），numpy 2.0.2，2026-11-21。
- 方法：复制 `source.py` + `config.json` 到 `/tmp/r4_exit_code_tests/P008_E01/`，将 `paper_pdf.path` 指向不存在的 `/tmp/r4_exit_code_tests/MISSING.pdf`，运行并捕获进程退出码。原目录未被改动。

## 3. 注入场景与结果
| 项 | 结果 |
|---|---|
| 注入场景 | 论文 PDF 输入缺失 |
| 进程退出码 | **1**（非零，正式阻塞） |
| `execution_status` | `BLOCKED_SOURCE_VERIFICATION_FAILED` |
| `failed_source_checks` | `['paper_pdf_present', 'paper_pdf_hash_observed']` |
| `failed_math_checks` | `[]`（空） |
| 正常条件数学检查 | KKT、直接 KKT/投影一致性、前沿峰值、四基金张成、各退化情形**全部仍为 True** |
| 病态压力测试 | cond=1.000e+09、KKT rel=2.173e-09，仅作 REPORTED/PARTIAL，不影响 exit |

- 日志证据：`[GRADED] source_failed=['paper_pdf_present','paper_pdf_hash_observed'] math_failed=[] partial_failed=[] -> exit_code=1`；`EXIT CODE = 1 (BLOCKED_SOURCE_VERIFICATION_FAILED)`。
- 关键结论：**来源失败非零阻塞；正常条件数学结论与病态压力测试分开判定，前者未被资料缺失否定，后者不冒充正常条件 PASS**。

## 4. 对照：正常重跑
- 原目录（run_id `R4-P008-001`）：exit **0**；正常例 cond=5.1856、KKT rel=3.494e-16（远小于 1e-10）；病态例单独报告。

## 5. 证据文件
- 临时副本：`/tmp/r4_exit_code_tests/P008_E01/{out.log,err.log,results.json}`。
- 原目录：`run_stdout.log`、`run_stderr.log`、`results.json`（含 `check_grades`、`degeneracies.ill_conditioned.excluded_from_pass=true`）。
