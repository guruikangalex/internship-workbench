# P008-E03 作者工作簿输入层复算摘要（run_id R3-P008-003）

- 结果：实际从 AQR URL 独立下载并复算成功（非仅登记 reviewer evidence）。
  URL: https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/ESG_efficient_frontier_portfolios_vF.xlsx?sc_lang=en
  HTTP 200，215209 字节，SHA256 153423fd6356e41423271ddcdfe0280508e69e73273e023171aaf83e6cf8b676（与 reviewer 证据文件逐字节一致）。
- 方法在查看输出前冻结于 config.json（2026-11-21T07:35:00Z）：供应方 U 列（G5-G1）、674 月 1963-02-28..2019-03-31、小数月收益、算术均值×12×100、不扣 RF、不筛月；容差 ±0.005 百分点。
- 解析方式：zipfile + xml.etree 直接读 OOXML（无 pandas/openpyxl）。

| 结果 | 原文值 | 本 run 复算 | 绝对误差 | 容差 | verdict |
|---|---|---|---|---|---|
| R10 Table4 PanelA/G 平均超额收益 | 7.84% | 7.836146824925816% | -0.003853 pp | ±0.005 pp | PASS |
| R11 Table4 PanelB/G 平均超额收益 | 3.01% | 3.014250756676558% | +0.004251 pp | ±0.005 pp | PASS |

- 两表均 674 个连续唯一月末；U 与 T−P 行级最大差：等权 1.25e-7、市值加权 8.33e-8（工作簿原始单位）。
- 复算值与 reviewer 高精度参考值逐位一致（差 0.000e+00）；reviewer 计算作为 REVIEWER_CALCULATION 另行登记，performed_by=reviewer、original_run_acceptance=NOT_ASSESSED，不冒称为本 run 之外产生。
- 理论机制列 NOT_APPLICABLE（输入层均值核对）；市场经济评价 NOT_ASSESSED。R12/R13 六因子 alpha/t 值仍属 P008-E04 NOT_RUN。
