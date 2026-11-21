# P003 第三轮补证 summary

## 关闭了什么
1. 固定 w 子实验（Equity 1，月频 60 月窗）的配置冻结：`fixed_w_preflight.md` + `config.json` 明确累计收益公式、行业资格（事前）、缺失处理、样本窗口、收缩公式、优化目标与 gamma。
2. 明确 OOS w 网格缺口**不阻塞**固定 w 准备：Table 5 网格标 `TABLE5_INSAMPLE_STRESS_RANGE_ONLY`，OOS 网格 `UNKNOWN`，不沿用忠实标签。
3. 输入快照预检：实取 Ken French 49 行业组合月频 CSV（vintage 202609），核验 hash/形状/日期/sentinel，明确标 `APPROXIMATE_VALIDATION`（原始/FIZ/CIZ vintage 未恢复）。

## 实际下载 / 运行了什么
- `curl` 下载 `49_Industry_Portfolios_CSV.zip`（489861 B，HTTP 200）；探测 202412 归档 URL 均 404。
- Python 3.9.6 运行 `verify_fixed_w_inputs.py`，输出 `results/fixed_w_input_audit.json` 与日志（exit 0，无 stderr）。

## 剩余阻塞
- 原始/FIZ 2024-12/CIZ 2026-09 冻结快照未恢复；当前仅近似验证。
- OOS w 网格、平局规则、最少历史月数待作者/主审；12 月超额复合口径 UNRESOLVED；日 RF 与 Table 6 t 统计待定 (P003-B09)。
- 作者代码 NOT_FOUND；所有回测/目标值 NOT_RUN/NOT_ASSESSED，审批 PENDING。

## 写入路径
`.../revision-v3/executions/support/P003/`
- `code/verify_fixed_w_inputs.py`
- `data/ind49_current.zip`（及探测残留 `ind49_202412.zip`/`ind49_page.html`）
- `results/fixed_w_input_audit.json`
- `logs/verify_fixed_w_inputs.stdout.log`、`logs/verify_fixed_w_inputs.stderr.log`
- `config.json`、`fixed_w_preflight.md`、`summary.md`、`sha256sums.txt`
