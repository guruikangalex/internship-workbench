# Exit code 修复验证 — P001_E01（R4）

## 1. 问题与修复
- R3 问题：`source.py` 尾部仅打印 `ALL CHECKS PASS = False`，`main()` 正常返回，进程 exit **0**（失败被静默）。
- R4 修复：checks 分为三层——`REQUIRED_SOURCE`（失败→exit 1）、`REQUIRED_MATH`（失败→exit 2）、`DIAGNOSTIC`（失败记为 PARTIAL，不影响 exit）；`main()` 返回 `exit_code`，入口改为 `sys.exit(main())`。
- 退出码语义：**0**=PASS；**1**=SOURCE_FAIL（缺失输入/来源 hash 失败）；**2**=MATH_FAIL（关键数值/恒等式失败）。

## 2. 测试环境与方法
- Python 3.9.6（`/Users/guruikang/WorkBuddy/2026-11-20-15-03-43/CO-REP-20261120-02/execution/env_py396/bin/python`），numpy 2.0.2，2026-11-21。
- 方法：复制 `source.py` + `config.json` 到临时目录 `/tmp/r4_exit_code_tests/P001_E01/`，把 `config.json` 的 `input_paths.paper_pdf` 指向不存在的 `/tmp/r4_exit_code_tests/MISSING.pdf`，运行并捕获**进程退出码**。原目录未被改动。

## 3. 注入场景与结果
| 项 | 结果 |
|---|---|
| 注入场景 | 正式版论文 PDF 输入缺失 |
| 进程退出码 | **1**（非零，正式阻塞） |
| `execution_status` | `BLOCKED_SOURCE_VERIFICATION_FAILED` |
| `failed_source_checks` | `['input_present_paper_pdf', 'hash_paper_pdf']` |
| `failed_math_checks` | `[]`（空） |
| 数学检查 | A7/A10/A11、标量/矩阵、reviewer a/λ/aim0、Bellman、160 期交叉核对**全部仍为 True** |

- 日志证据：`[GRADED] source_failed=['input_present_paper_pdf','hash_paper_pdf'] math_failed=[] partial_failed=[] -> exit_code=1`；`EXIT CODE = 1 (BLOCKED_SOURCE_VERIFICATION_FAILED)`。
- 关键结论：**来源核验失败触发非零退出与正式阻塞状态，但已独立核实的数学结论未被否定**（`failed_math_checks` 为空，数学 verdict 仍 PASS）。

## 4. 对照：正常重跑
- 原目录正常输入（run_id `R4-P001-001`）：exit **0**，全部 REQUIRED checks 通过；`run_stderr.log` 末行 `PROCESS_EXIT_CODE=0`。

## 5. 证据文件
- 临时副本：`/tmp/r4_exit_code_tests/P001_E01/{out.log,err.log,results.json}`。
- 原目录：`run_stdout.log`、`run_stderr.log`、`results.json`（含 `exit_code`/`failed_source_checks`/`failed_math_checks`/`check_grades`）。
