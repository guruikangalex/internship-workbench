# P007 第三轮补证 summary

## 关闭了什么
1. **可审时间线**：`timeline.md` 用原文句子区分信号期(20日累计收益)、训练收益期(120对非重叠20日)、缓冲(1日)、预测持有期(20日)，并明确"一日缓冲"**不自动推出所有持有起点相隔21日**；给出两种读法的实际首末日期、块数、OOS次数。
2. **真实下载 + 切块演示**：实取 Ken French FF25 日频 ZIP，解出 CSV 并核验 hash/形状/日期；`code/block_ff25.py` 实际演示 20 交易日非重叠切块（严格21步 vs 相邻20步），记录首块原点导致的 676/677 与 710/711 差异（P007-B02）。
3. **不变量比较**：实算两种读法的 Π̂ 算子、奇异值、对称/反对称部分、符号不变性（翻转奇异向量后算子最大绝对差 0.0）；明确特征向量正负/相位差异不单独判失败，最终收益另核。

## 实际下载 / 运行了什么
- `curl` 下载 `25_Portfolios_5x5_Daily_CSV.zip`（HTTP 200，4,043,238 B），解压得 24,101,059 B CSV，SHA256 `ef7d17f85368e9618ac3fd855e3fca9ea955e0188a48a6d05dec10ccc0622c23`，论文窗 14,223 交易日。
- Python 3.9.6 运行 `block_ff25.py`（修复 rank_demean 死循环后）：exit 0，stderr 空，输出 `results/block_ff25_results.json`。

## 剩余阻塞
- 出版时代 FF25/FF5 ZIP (2021 vintage) 未恢复 (P007-B01)；首块原点与"一日缓冲"对应日历未冻结 (P007-B02)；Wiley 官方代码 403 (P007-B03)；138 因子特征张量 (P007-E02/B04)。
- 全部 Figure/Table 目标 `NOT_RUN`，经济结论 `NOT_ASSESSED`。

## 写入路径
`.../revision-v3/executions/support/P007/`
- `data/25_Portfolios_5x5_Daily_CSV.zip`、`data/25_Portfolios_5x5_Daily.csv`
- `code/block_ff25.py`
- `results/block_ff25_results.json`
- `logs/block_ff25.stdout.log`、`logs/block_ff25.stderr.log`
- `timeline.md`、`summary.md`、`sha256sums.txt`
