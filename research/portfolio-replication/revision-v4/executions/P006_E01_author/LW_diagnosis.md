# P006-E01 LW 家族 FAIL / 舍入边界 PARTIAL 根因诊断（R4）

Run ID `RUN-P006-E01-AUTHOR-20261121-R4`。所有数字来自实际运行：
`lw_diagnosis_data.json`（冷 bundle vs 作者手稿/再生缓存逐对象比较 + 扰动实验）、
`extracted_values.json`、`manifest_license_check.json`、22 产物 `sha256sums.txt` 复核。

## 0. 结论先行

| 层次 | 是否致因 | 证据 |
| --- | --- | --- |
| 输入 CSV / 样本 / 标准化 | 否 | 30/30 源码与输入文件与 ZIP `P006_upsa_reproduction_RFS_v2.zip` 逐字节一致；冷 bundle `opt_port` 494 月、1981-11..2022-12、NaN=0、Inf=0；所有比较 index/columns 严格相等，无时序错位或缺失处理差异。 |
| 收缩参数 / 特征值截断 | 否 | `z_grid=logspace(-10,-1,10)` 与源码一致；`do_lw(remove_pc_pert=0)` 未截断特征值；T=120 窗口、月末索引一致。 |
| LAPACK/BLAS 数值环境 + 缓存来源 | **是（根因层）** | 冷/缓存 LW 权重在**首个窗口 1981-11-30** 即分叉（`weights_LW` max 2.45）；手稿缓存文件日期 2026-05-30，早于滚动窗口源码最终修改 2026-05-31；冷重跑在同一环境逐字节复现（22/22 哈希 OK），说明差异来自作者缓存生成环境与本地固定环境的数值差异，而非实现缺失。 |
| 中间权重 -> 回报统计（LW 放大层） | **是（放大层）** | LW 非线性收缩**对全部 120 个特征值求逆**（最小 2.797e-7，逆权重 3.57e6，条件数 1.41e5）。1e-12 相对特征值扰动 → LW 权重差 1.67e-3、OOS 回报差 1.6e-3；特征值的微小环境差异被放大 1e9 量级。 |
| 作者缓存 vs 冷计算 | 是（比较口径层） | 论文锚点贴近手稿缓存（LW 全样本 1.3083 vs 论文 1.31），冷重算为 1.2741；手稿缓存再生缓存 `a1d6a3c4`、手稿 `e767297e`、冷重算 `3ebba382` 三者哈希各异，缓存数值不作 rerun_value（protocol §3）。 |

**根因结论**：LW 家族 14 个 FAIL 的根因是「作者缓存生成环境的数值差异（LAPACK/BLAS、缓存来源时点）经 LW 非线性收缩对近零特征值的极端敏感性放大」；不是源码缺失、不是输入时序/缺失处理、不是容差放宽，也不是样本/收缩参数错误。作者源码与输入逐字节一致，冷重跑确定性复现。

## 1. 源码层核查（不改算法）

- `src/shrinkage.py:11-34` `do_lw`：`remove_pc_pert=0` 默认，不截断特征值；`lw_weights = eigvec·(1/lw_eigenvalues)·(eigvec'μ)`，权重与全部特征值倒数成正比。
- `src/shrinkage.py:37-58` `lw_nonlinear_shrinkage`：带宽 `h=T^(-1/3)`，含 `1/H`、`log|·|`、平方分母，对 `lam` 极敏感。
- `src/upsa.py:132-143` 二阶矩非中心化：`P>T` 时 `cov=features@features.T/T`（120×120），`np.linalg.eigh` 求 120 个特征值；最小特征值 2.797e-7 → 近奇异。
- `src/portfolios.py:48-54`：LW 权重 `do_lw(returns=f_ins, eigenvalues=upsa.eigenvalues, eigenvectors=upsa.eigenvectors)`，即用 UPSA 同一套特征分解；PCA 走独立 `pca_cv`（自带 `_smart_eig`）。
- `src/portfolios.py:59-67`：`ins_sec=f_ins.T@f_ins/len(f_ins)` 非中心化；`opt[c_]=f_oos@w[c_]`，权重漂移直接线性进入 OOS 回报。

## 2. 首个差异点定位（数值实验）

比较对象：冷重算 `main_bundle.p`(3ebba382) vs 作者手稿缓存(e767297e)/再生缓存(a1d6a3c4)。索引、列、长度全部严格相等（494×6 / 494×153 / 494×1000）。

| 对象 | vs 手稿缓存 max abs | vs 再生缓存 max abs | 首个非零单元格 |
| --- | --- | --- | --- |
| `opt_port_UPSA` | 4.39e-2 | 3.61e-2 | 1981-11-30 / UPSA |
| `opt_port_Ridge` | 1.23e-3 | 1.41e-3 | 1981-11-30 / Ridge |
| `opt_port_LW` | **2.73** | 0.614 | 1981-11-30 / LW |
| `opt_port_PCA` | 4.89e-11 | 2.01e-11 | 1981-11-30 / PCA（量级 1e-11，实质一致） |
| `opt_port_FF5` | 2.89e-15 | — | 1981-11-30 / FF5（一致） |
| `weights_LW` | 2.45 | 0.599 | 1981-11-30 / age |
| `z_grid_weights` | 0.481 | — | 1981-11-30 |
| `eigcurve_UPSA` (494×1000) | 5.09e-4 | 6.59e-4 | 1981-11-30 / 1e-07 |

所有方法在**同一首窗口、同一天**分叉；PCA（独立特征分解）与 FF5/CAPM（不走 UPSA 特征分解）实质一致 → 分叉起点是 UPSA 特征分解/权重层，而非输入装载或收益统计层。手稿缓存的 LW 回报差（2.73）约为再生缓存（0.614）的 4.4 倍，与「手稿缓存更旧、漂移更大」的来源时点一致。

## 3. 放大机制（扰动实验，窗口 0，T=120，P=153，n_eig=120）

基准：`|w_LW|=57.40`，OOS 回报=0.2065376；`eig_min=2.797e-07`，`eig_max=0.03948`，条件数≈1.41e5；`1/(eig_min+z_min)=3.57e6`，`1/(eig_max+z_min)=25.3`（逆权重比 1.41e5）。

| 特征值相对扰动 | LW 权重 max abs 差 | OOS 回报差 |
| --- | --- | --- |
| 1e-14 | 3.68e-6 | -3.61e-6 |
| 1e-12 | 1.67e-3 | -1.63e-3 |
| 1e-10 | 9.30e-4 | -9.11e-4 |
| 1e-8 | 1.24e-3 | -1.22e-3 |
| 1e-6 | 1.17e-3 | -1.14e-3 |

即使 1e-12 量级特征值差异（典型 LAPACK/BLAS 版本舍入范围）也产生 ~1.6e-3 的单月回报扰动；494 月累积足以把 Sharpe 从 1.3083 拉到 1.2741（论文锚点 1.31）。这解释了为何 LW 家族 14 个单元（Fig3 全样本/After-2000 + Table1 12 主题）的 abs_error 多在 0.03~0.15，远超冻结容差 0.005，而同样用特征分解的 UPSA/Ridge 仅擦边或 PASS：LW 把近零特征值倒数放大到百万量级，是脆弱性放大器。

## 4. 排除的其他层次（逐条）

- **样本/时序缺失**：5 个 CSV 与 ZIP 逐字节一致；`load_panel` 用 `float_precision="round_trip"`；冷 bundle 与缓存 index 严格相等（1981-11..2022-12，494 月）；NaN=0、Inf=0。无差异。
- **标准化/二阶矩**：源码未改动，非中心化 `X'X/T` 口径一致（static_check §3）。无差异。
- **收缩参数/网格**：`Z_GRID=logspace(-10,-1,10)` 由 `compute_main_figures.py:16` 固定并经 `UPSA(z_list=z_grid)` 显式传入，不走自适应网格；`do_lw` 不截断。无差异。
- **中间权重 vs 回报统计**：权重差异（weights_LW max 2.45）先于回报差异（opt_port_LW max 2.73）出现，回报层仅是线性传递 `f_oos@w`；根因在权重/特征值层。
- **缓存回填**：比较的 replication_value 始终是冷重算 fresh 值，reference_value 才是手稿缓存；未把缓存值当复跑值（protocol §3）。

## 5. All-UPSA PARTIAL 单独舍入边界分析（R4 判定：FAIL）

冻结容差来自局部表 `Absolute half unit 0.005; apply original displayed rounding`。数值：

- paper 锚点 0.67（显示两位 0.67）；冷重算 fresh 0.6645123437（显示 0.66）；手稿缓存 0.6652235374（显示 0.67）；作者再生缓存 0.6649162636（显示 0.66）。
- 舍入边界 0.6650；fresh 到边界距离 0.0004876563（显示 0.66 与 0.67 跨一档）。
- `|fresh - paper| = 0.005487656265 > 0.005` 冻结容差 → 按统一规则（无 result_id 特判）判 **FAIL**。

R3 旧脚本第 185-186 行对该单元格无条件降级 PARTIAL，属无数值依据的硬编码豁免。R4 从当次运行数值与冻结容差计算 verdict：0.005488 稳定超过 0.005（超出 9.8%），不是「仅落在边界上」的相等情形，不构成舍入不确定性豁免。该边界分析字符串已由 `boundary_note()` 从 fresh/manuscript/regen/paper 实时生成写入 `difference_explanation`（无硬编码数值）。All-UPSA 的绝对误差量级（0.0055）与同族 UPSA 擦边单元（Skewness-UPSA 0.0057、Low-Risk-UPSA 0.0055）一致，统一规则下三者均为 FAIL，标准一致、未放宽容差、未无限豁免。

## 6. 系统结论对 25 个逐项单元的覆盖

- **LW 家族 14 FAIL**（Fig3 full/after-2000 LW + Table1 12 主题 LW）：根因=第 2/3 节数值环境差异 + LW 近零特征值放大；数值实验逐项 confirming test 见 `discrepancy_analysis.csv`。
- **UPSA 擦边 3 FAIL**（Skewness/Low-Risk/Low-Leverage-UPSA）：同一数值漂移量级（abs 0.0055~0.009），显示两位小数较锚点低一档，统一规则判 FAIL。
- **Ridge alpha 1 FAIL**（F05 4.4512 vs 4.46）：Ridge 权重漂移 max 1.23e-3 经 HAC(5) alpha 累积，abs 0.0088。
- **All-UPSA 1（R3 PARTIAL → R4 FAIL）**：见第 5 节。
- **7 PARTIAL**：Fig3 After-2000-UPSA（作者参考仅，abs 0.000817≤0.005 但显示跨档）+ 6 个面板级（FIG3/FIG5/FIG6A-C/FIG8 逐点超参考阈值 5e-6 Sharpe / 1e-5 百分点），索引/长度严格一致，非实现缺失；面板阈值来自协议冻结值，非本次放宽。

诊断不构成发表数值验收；最终验收交主审。原始证据：`lw_diagnosis_data.json`、`lw_diagnosis_experiment.py`、`lw_diagnosis_stderr.log`、`manifest_license_check.json`、`run_computation_r4_stdout.log`、`outputs/sha256sums.txt`。
