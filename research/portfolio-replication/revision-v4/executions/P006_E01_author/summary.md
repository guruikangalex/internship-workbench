# P006-E01 作者代码冷重跑执行摘要（AUTHOR_CODE_RERUN）

Run ID `RUN-P006-E01-AUTHOR-20261121-01`；提交 `104aecf`；审批 `REVIEW-104AECF-20261121`。

## 实际运行了什么

- **ZIP 核验**：`P006_upsa_reproduction_RFS_v2.zip` SHA256 = `a20c2fbf...`（与预期一致）、MD5 = `b8cac94b...`（一致），123737306 B。
- **冷目录**：仅复制作者源码 + 5 个 CSV 到 `cold_run/`，删除整树 `outputs/` 后重建空 `computed/` 与 `figures/`，运行前文件数 0；源码与输入逐文件 SHA256 与证据包一致，算法未改。
- **命令**：`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg <env_py396>/bin/python -u run_all.py --main --compute`。
- **结果**：exit 0，耗时 88 s（15:26:37→15:28:05 +0800）。stdout 明确打印 rolling-window engine 计算与 `cached -> main_bundle.p`，新 bundle 哈希 `3ebba382...` 与手稿缓存 `e767297e...`、作者再生缓存 `a1d6a3c4...` 均不同 → 真从 CSV 重算，非读缓存重绘。
- **输出**：22 个产物（2 个 computed bundle + 19 张主文图 fig_01..fig_13 + tab_01_r2_theme.tex）。`finalize` 另报 41 个 missing，均为附录/仿真图，属 `--main` 范围外。912 条 RuntimeWarning（小 z 近奇异 matmul）；`opt_port` 实测 NaN=0、Inf=0。

## 115 个 PROPOSED 目标达成情况（计算层 verdict）

`target_comparison.csv` 共 115 行 × 40 列：**PASS 90 / FAIL 17 / PARTIAL 8 / NOT_ASSESSED 0**；理论机制与经济判断均 NOT_ASSESSED，最终验收交主审。

- **通过**：Fig3 全样本 UPSA 1.92 / Ridge 1.59 / PCA 1.45 / FF5 1.13 / CAPM 0.54；Fig5 HAC t 3.72；Fig8 换手 UPSA 12.4% / Ridge 16.3%；Table 1 多数单元；Fig6 的 PCA/FF5/CAPM 三面板（数值与手稿缓存逐点一致，图也逐字节相同）。
- **未通过（17）**：Fig3 全样本 **LW 1.2741 vs 发表 1.31**、After-2000 LW；Fig5 Ridge alpha **4.4512 vs 4.46**；Table 1 中 LW 的 12 个主题单元（Low Risk −1.2216 vs −1.37 等）及 Skewness-UPSA、Low-Risk-UPSA、Low-Leverage-UPSA 等擦边单元。这些是 `--compute` 后的数值漂移，非实现缺失；按局部表容差 0.005 判 FAIL，未放宽容差追数。
- **PARTIAL（8）**：Table 1 All-UPSA fresh 0.664512（手稿 0.665224、作者再生 0.664916、发表 0.67）——跨 0.665 舍入边界，协议预先标注该敏感性；Fig3 After-2000-UPSA 跨两位舍入边界（差 0.0008）；PANEL-FIG3/FIG5/FIG6A-C/FIG8 面板级逐点数组超出参考阈值。

## 缓存比较 vs 发表值比较（分别结论）

- **对发表数值**（以 fresh 值 vs 论文锚点，容差来自局部表）：90 项计算层 PASS，17 FAIL，8 PARTIAL。LW 家族漂移最大，符合协议 §3 既有观察，不能归为舍入。
- **对作者缓存**（reference_value 取手稿 `main_bundle.p`，非 rerun_value）：Fig6 逐点阈值 5e-6 Sharpe 下 UPSA 151/153 点、LW 153/153 点、Ridge 18/153 点超出；PCA/FF5/CAPM 全部在阈值内。Fig8 12 月滚动逐点阈值 1e-5 个百分点下 UPSA 470/483 点、Ridge 54/483 点超出；均值仍分别落在 12.4%、16.3% 的发表显示精度内。缓存图逐字节比较：Fig6d/e/f 相同，其余不同（JPG 字节相等不作判据）。两类结论独立归档，未把缓存值回填为复跑值。

## 阻塞

- RFS 排版版 PDF SHA256 = null（HTML 全文已读），不影响本轮计算层比较；若主审要求纸质 PDF 可核验，另送已核 NBER 源作 E05。
- 最终数值验收由主审执行；本执行不替代验收，未改作者算法，未放宽容差。

## 写入路径（仅本独占目录）

`revision-v3/executions/P006_E01_author/`
- `execution_manifest.json`、`static_check.md`、`summary.md`
- `run_stdout.log`、`run_stderr.log`、`run_start.txt`、`run_end.txt`
- `outputs/`（22 产物 + `sha256sums.txt`）；`cold_run/`（隔离冷目录）
- `extract_values.py`、`extracted_values.json`、`extract_stderr.log`、`build_comparison.py`、`target_comparison.csv`
