# Exit code 修复验证 — P008_E03（R4）

## 1. 问题与修复
- R3 问题：`source.py` 尾部仅打印 `ALL CHECKS PASS = False`，`main()` 正常返回，进程 exit **0**。
- R4 修复：
  - 入口前置校验：工作簿缺失或 hash/size 不符时，写正式阻塞状态记录并 `return 1`（`sys.exit(main())` 传递为进程 exit 1）。
  - checks 分三层：`REQUIRED_SOURCE`（→exit 1）、`REQUIRED_MATH`（R10/R11 容差与 reviewer 一致，→exit 2）、`DIAGNOSTIC`（PARTIAL）。
- 退出码语义：**0**=PASS；**1**=SOURCE_FAIL（工作簿缺失/hash+size 不符）；**2**=MATH_FAIL（R10/R11 越界或与 reviewer 不符）。

## 2. 测试环境与方法
- Python 3.9.6（env_py396），2026-11-21。
- 方法：复制 `source.py` + `config.json` 到 `/tmp/r4_exit_code_tests/P008_E03/`（**不复制** `downloaded_from_aqr.xlsx`，构造输入缺失），运行并捕获进程退出码。原目录未被改动。

## 3. 注入场景与结果
| 项 | 结果 |
|---|---|
| 注入场景 | `downloaded_from_aqr.xlsx` 缺失 |
| 进程退出码 | **1**（非零，正式阻塞） |
| `execution_status` | `BLOCKED_SOURCE_VERIFICATION_FAILED` |
| `source_present` | `false` |
| 阻塞态记录 | `reviewer_reference_not_recomputed`（reviewer 值保留为证据，标记 NOT_RECOMPUTED，不判为数学错误） |
| `check_alignment` | 阻塞态仍声明 approved_result_ids=`[P008-R10, P008-R11]` 与 4 个 supporting check_id |

- 日志证据：`SOURCE LAYER BLOCKED: missing=True hash_ok=False size_ok=False -> exit 1`；`EXIT CODE = 1 (BLOCKED_SOURCE_VERIFICATION_FAILED)`。
- 关键结论：**必要输入缺失触发非零退出与正式阻塞状态；reviewer 已核实数值不被否定，仅标记为本 run 未重算**。

## 4. 对照：正常重跑
- 原目录（run_id `R4-P008-003`）：实时 curl 下载 HTTP 200 / 215209 字节 / SHA256 `153423fd…` 校验通过，exit **0**；R10=7.836146824925816%、R11=3.014250756676558%。

## 5. 证据文件
- 临时副本：`/tmp/r4_exit_code_tests/P008_E03/{out.log,err.log,results.json}`。
- 原目录：`run_stdout.log`、`run_stderr.log`、`results.json`（含 `check_alignment`：2 approved + 4 supporting）、`download_stderr.txt`。
