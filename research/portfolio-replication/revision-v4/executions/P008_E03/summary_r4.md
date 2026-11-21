# P008-E03 R4 下载+复算+范围纠正摘要（run_id R4-P008-003）

## 0. 执行链修复
- 旧脚本（`source_v3_backup.py`）尾部只打印 `ALL CHECKS PASS = False` 却返回 exit **0**；且工作簿缺失时直接抛异常。
- 修复版 `source.py`：前置校验工作簿存在/hash/size，失败写正式阻塞记录并 exit 1；checks 分 `REQUIRED_SOURCE`（→1）、`REQUIRED_MATH`（→2）、`DIAGNOSTIC`（PARTIAL）；`main()` 返回 `exit_code`，入口 `sys.exit(main())`。
- 本次重跑 **exit code = 0**（全部 REQUIRED 通过），`execution_status=EXECUTED`。

## 1. 实际下载与来源 hash
- 本 run 从 AQR URL **实际 curl 下载**：HTTP 200，215209 字节。
- SHA256 = **153423fd6356e41423271ddcdfe0280508e69e73273e023171aaf83e6cf8b676**（与预期/reviewer 证据逐字节一致）。
- URL：`https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/ESG_efficient_frontier_portfolios_vF.xlsx?sc_lang=en`；证据见 `download_stderr.txt`、`downloaded_from_aqr.xlsx`。

## 2. 冻结口径（未改）
- 674 个月，1963-02-28..2019-03-31，连续唯一；供应方 U 列（G5-G1）；小数月收益；算术均值 ×12×100；不重复扣 RF；不筛月。
- 容差 ±0.005 百分点（冻结于 2026-11-21T07:35:00Z）；解析方式 zipfile + xml.etree 直读 OOXML（无 pandas/openpyxl）；环境 Python 3.9.6。

## 3. 复算结果（仅两项为批准论文结果）
| approved_result_id | 论文值 | 本 run 复算 | 绝对误差 | 容差 | verdict |
|---|---|---|---|---|---|
| **P008-R10** Table4 PanelA/G 平均超额收益 | 7.84% | **7.836146824925816%** | -0.003853 pp | ±0.005 pp | PASS |
| **P008-R11** Table4 PanelB/G 平均超额收益 | 3.01% | **3.014250756676558%** | +0.004251 pp | ±0.005 pp | PASS |

- 两表均 674 个连续唯一月末；U 与 T−P 行级最大差：等权 1.25e-7、市值加权 8.33e-8（工作簿原始单位）。
- 复算值与 reviewer 高精度参考值逐位一致（差 0.000e+00）；reviewer 值登记为 `REVIEWER_CALCULATION`、`performed_by=reviewer`、`original_run_acceptance=NOT_ASSESSED`，不冒称本 run 之外产生。

## 4. 范围纠正：approved_result_id vs check_id（核心）
- 正式批准的论文结果 **只有 2 项**：`P008-R10`、`P008-R11`。
- `target_comparison.csv` 共 **6 行**，其中：
  - **2 行** `alignment_role=APPROVED_PAPER_TARGET`（真正的 Table 4 单元格目标，approved_result_id=P008-R10/P008-R11）；
  - **4 行** `alignment_role=SUPPORTING_CHECK`，携带独立 `check_id`：**P008-E03-CHK-01**（reviewer R10 一致性）、**CHK-02**（reviewer R11 一致性）、**CHK-03**（工作簿 sha256）、**CHK-04**（日期/样本形状）。
- 这 4 个 check_id 是辅助证据，**不得计入论文目标**。`results.json` 的 `check_alignment` 明确记录：`csv_approved_rows=2`、`csv_supporting_rows=4`。

## 5. 交付文件
`source.py`（修复版）、`source_v3_backup.py`、`config.json`、`environment.json`、`commands.txt`、`run_stdout.log`、`run_stderr.log`、`results.json`、`target_comparison.csv`、`target_comparison_v3_backup.csv`（旧版 6 行备份）、`downloaded_from_aqr.xlsx`、`download_stderr.txt`、`summary.md`（R3 原件）、`summary_r4.md`（本文件）、`sha256sums.txt`、`exit_code_test.md`。
