# P006-E01 作者入口静态核查（AUTHOR_CODE_RERUN 冷运行）

批次 CO-REP-20261120-02-R2；冻结提交 `104aecfcad4c308e1044a3d15483fe2320619597`；
协议 `revision-v2/work/P006/protocol_v2.md`。核查对象：作者包
`CO-REP-20261120-02/evidence/P006_package`（从 ZIP SHA256 `a20c2fbf...` 解压）。
本核查只读作者源码，不修改算法。

## 1. 入口与调用链

`run_all.py`：`--main` 选中主文分支；`--compute` 作为 `force=args.compute` 传入
`compute_main(force=...)`（run_all.py:42）。默认（无 `--compute`）只读
`outputs/computed/*.p` 缓存重绘；`--main --compute` 触发真实重算：

```
run_all.py:39-43  main 分支
  -> scripts/compute_main_figures.py:30-43  compute_main(force=True)
       -> src/portfolios.py:92-159  run_rolling_window(factors, benchmark, 120, Z_GRID)  # 真实重算
       -> _is_vs_oos(force=True) -> run_is_vs_oos(...)                                  # 真实重算
       -> 写 outputs/computed/main_bundle.p、is_vs_oos.p（wb 覆盖）
  -> scripts/plot_main_figures.py:20-59  plot_main(bundle, load_panel("factors_main"), FIG_DIR)
       -> Fig1-13 + tab_01_r2_theme.tex 的语义名图
  -> scripts/finalize_outputs.py:125-157  finalize()  重命名为 fig_NN_* 并刷新 manifest.csv
```

结论：`--main --compute` = 仅主文图表 + 强制从 CSV 重算（非读缓存重绘）。

## 2. 五个输入 CSV（存在性与维度）

| 文件 | 实际 shape（含 date 列） | 因子/列数 | 日期范围 | 协议预期 |
| --- | --- | --- | --- | --- |
| factors_main.csv | 614 × 154 | 153 | 1971-11-30 .. 2022-12-31 | 614 月 × 153 ✓ |
| benchmark.csv | 738 × 7 | 6（mkt/smb/hml/rmw/cma/mom） | 1963-07-31 .. 2024-12-31 | 738 月 × 6 ✓ |
| factors_large.csv | 614 × 153 | 152 | 1971-11 .. 2022-12 | 614 × 152 ✓ |
| factors_mega.csv | 614 × 152 | 151 | 1971-11 .. 2022-12 | 614 × 151 ✓ |
| factors_small.csv | 614 × 153 | 152 | 1971-11 .. 2022-12 | 614 × 152 ✓ |

`src/data.py:13-19` 用 `float_precision="round_trip"` 读回 float64。`portfolios.py:98-99`
去掉 benchmark 的 `mom` 并按交集对齐。冷目录与证据包五个 CSV 的 SHA256 逐项一致。

## 3. 目标函数与作者实现（源码逐条确认）

- **二阶矩、非中心化 X'X/T**：`upsa.py:132-143` 中 P≤T 时 `covariance = features.T @ features / T`；
  `portfolios.py:60` 中 `ins_sec = f_ins.T @ f_ins / len(f_ins)`。均为未中心化二阶矩，未减均值。
  FF5 基准另用 `np.cov` 中心化样本协方差（`portfolios.py:49`），对 UPSA 无替代关系。
- **LOO 分母（论文 T−1 vs 作者 T）**：`upsa.py:109-113` 用 `H = U(λ+z)^{-1}U' / T + w_adj/z`
  构造 T 分母帽子矩阵；`upsa.py:122-129` 用 Sherman–Morrison 秩一删除
  `(w̄−W_tt)/(1−W_tt)`。论文 §2.2 Eq.(9)-(10) 定义为按 T−1 直接重拟合。这是已批准的
  P006-B07 差异（protocol_v2 §2.1）；本次忠实保留作者实现，不改分母、不追数。
- **W 非负、无单纯形**：`upsa.py:145-153` `markowitz_constrained`：`G=-I, h=0, P=Q, q=-u`，
  无等式约束 → 仅逐项 W_j≥0；`get_upsa_weights` (47-53) 另做迹缩放
  `scale = Σ(1/inv_eigs) / Σ(eigenvalues)`，不归一化 W 之和。
- **惩罚网格**：`compute_main_figures.py:16` `Z_GRID = np.logspace(-10,-1,10)`（10 点：1e-10..1e-1）；
  经 `run_rolling_window(...,120,Z_GRID)` 传入，`portfolios.py:48` `UPSA(z_list=z_grid)` 显式使用，
  不走 `upsa.py` 的特征值自适应网格。
- **T=120、月度、滚动 t+1 会计**：`compute_main_figures.py:37` 传 120；`portfolios.py:45-46`
  `f_ins = X[i:120+i]`、`f_oos = X[120+i]`，即前 120 月训练、下一月样本外归因；月度月末索引。
- **OOS 1981-11..2022-12（494 月）**：`portfolios.py:100` `index_ = factors.index[120:]`。
  冷运行 `main_bundle.p` 实测 `opt_port.index` 起 1981-11-30、止 2022-12-31、长度 494，一致。
- **Fig3/5 分期**：`plotting.py:38,110` 用 pandas `(None,"2000")` / `("2000",None)` 切片：
  Before = 1981-11..2000-12（230 月），After = 2000-01..2022-12（276 月），重叠 12 月；
  按批准范围跟随作者代码，互斥分期属 E03。
- **Fig5 alpha**：`plotting.py:75-81` `_alpha_one` 将 y/X 按 10% 年化波动缩放，
  `statsmodels OLS + HAC(maxlags=5)`，`alpha = const × 12 × 100`（年化百分点），t 为 const 的 HAC t。
- **Fig6 R²**：`pricing.py:16-28` SDF 预测 Sharpe；`src/plotting.py:196-211` 每方法散点
  `R² = r2_score(realized, predicted)`；Table 1 用 `pricing.r_2_table_gen`（同一 All 口径，
  各主题用主题内 pooled std，见 `pricing.py:31-65`）。
- **Fig8 换手**：`metrics.py:17-32` 相邻目标持仓绝对变动和 / 前期总绝对持仓的一半 ×100，
  首月 0；`plotting.py:171-193` 12 月滚动均值，图例均值由 `raw.mean()` 给出。

## 4. 缓存隔离与从空目录重算（已执行）

1. 仅复制源码、`scripts/`、`data/` 五个 CSV 到 `cold_run/`；未复制 `_stage_P006` 中的
   `main_bundle.p` 等作者缓存或旧图。
2. 删除冷目录 `outputs/` 整树后重建空 `outputs/computed/` 与 `outputs/figures/`；
   运行前 `outputs` 下文件数 = 0（已记录）。
3. `src/**`、`scripts/**`、`run_all.py` 与证据包逐文件 SHA256 完全一致（算法未改）；
   `data/**` 五个 CSV 亦逐文件一致（输入未改）。
4. `stdout` 明确出现 `[main] computing rolling-window engine (bryan_monthly_vw_cap, rw=120)...`
   与 `[main] cached -> .../main_bundle.p`、`[main] computing in/OOS complexity sweep...`，
   证明实际跑了 rolling engine 而非读缓存重绘。新 `main_bundle.p` SHA256
   `3ebba3824caace88485a0ea7d557f591c0303f930f05a727ad92e73a9e503a91`，
   与手稿缓存 `e767297e...`、作者再生缓存 `a1d6a3c4...` 三者均不同。

## 5. 运行诊断

- `python --version` = CPython 3.9.6；numpy 2.0.2 / scipy 1.13.1 / pandas 2.3.3 /
  sklearn 1.6.1 / statsmodels 0.14.6 / cvxopt 1.3.3 / matplotlib 3.9.4 / seaborn 0.13.2。
- `run_stderr.log` 有 912 条 RuntimeWarning（divide-by-zero / overflow / invalid in matmul，
  各 304 条），来自小 z 下近奇异特征分解的 matmul；`opt_port` 实测 NaN=0、Inf=0，
  未污染参与发表数值比较的 OOS 组合收益序列。
- `finalize()` 报告 41 个 expected outputs missing：均为附录图、仿真图与附录表，属
  `--main` 分支范围外，非失败。本分支应产出 20 个主文图/表 + 2 个 computed bundle。

## 6. 静态核查结论

入口、调用链、五个输入、目标函数关键口径（非中心化二阶矩、作者 T 分母 LOO、非负无单纯形 W、
logspace 惩罚网格、T=120、月度、OOS 1981-11..2022-12）均与协议一致；`--main --compute`
已确认为真实重算；缓存已隔离且冷目录从空启动。作者算法源码未改。该静态核查不构成发表数值
验收，数值比较见 `target_comparison.csv`，最终验收交主审。
