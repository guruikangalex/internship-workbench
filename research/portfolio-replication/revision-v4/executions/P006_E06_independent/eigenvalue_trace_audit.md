# 任务 A：特征值缩放与 trace 归一化审计

run_id：`P006-E06-R4-AUDIT-001`。全部数值来自 `audit_r4/taskA_eigen_trace.py`、
`taskA_corrected_rerun.py` 的真实进程运行；证据文件：
`results/audit_A_eigen_trace.json`、`audit_A_corrected_summary.json`、
`audit_A_corrected_vs_author.json`。首窗 T=120，P=153（**P>T**）。

## 1. lam 到底是 XX' 还是 XX'/T 的特征值

| 对象 | 定义 | min | max | trace |
| --- | --- | --- | --- | --- |
| `indep.eig_K` 返回 lam | eig(XX')，T 维 | 3.3563e-05 | 4.73776 | 11.5580 |
| 作者 `smart_eigenvalue_decomposition_covariance` 返回 | eig(XX'/T)，T 维 | 2.7969e-07 | 0.0394813 | 0.0963169 |
| z 网格 | logspace(-10,-1,10) | 1e-10 | 0.1 | — |

逐元素排序后 `max|lam / (T·eig_author) − 1| = 9.08e-13`（另用独立重算 XX'/T 得同一结果）。
**结论：lam 是 XX' 的特征值，不是 XX'/T 的特征值；恰为作者特征值的 T=120 倍。**
作者 `fit()` 中 `z_list` 为显式数组时直接用之，故作者的 z 与 eig(XX'/T) 同尺度；
E06 的 z 与 eig(XX') 不同尺度（相差 T 倍）。

## 2. z 网格与 lam 尺度是否匹配

- 按作者口径 eig(XX'/T)：z 中位数 / eig_min = **19.66**，4 个 z 小于最小特征值，z 覆盖并高于谱底，收缩有效。
- 按 E06 口径 eig(XX')：z 中位数 / lam_min = **0.164**，6 个 z 小于 lam_min，低 z 相对 lam 过小（等效 z_eff = z/T）。

## 3. full ridge basis 的 Tz 是否一致

E06 `prepare_full_basis` 用 `(K + T·z I)^-1`；作者用 eig(XX'/T)+z。
由 push-through 恒等式 `X'(XX'+TzI)^-1 1 = (X'X/T + zI)^-1 X'1`，两者应一致。
数值：首窗 eff_port（153×10）逐元素 `maxabs = 2.89e-06`、`relative_fro ≈ 2.5e-08`。
作者的 `l_adj/z` 项：`‖l_adj‖ = 1.2810e-15`（纯舍入），相对 `‖XX'/T‖_F` 可忽略，eff_port 相对误差 2.33e-08；
**该步无实质错误**，B0/B1 保留原始 T 的做法正确。

## 4. trace normalization 是否符合作者与论文

三者公式文字相同：`scale = Σ(1/inv_eigs) / Σ(eigenvalues)`，`inv_eigs = W·1/(eig+z)`。
差别只在 `eig` 用什么：

| 口径 | eig | 首窗 scale（同一 W） |
| --- | --- | --- |
| E06 现行 `asset_weights` | eig(XX') = lam | **0.9453174** |
| 一致口径（作者 / 论文） | eig(XX'/T) = lam/T | **1.1381860** |
| 比值 | — | **0.8305474（现行偏小 17%）** |

ridge 口径同样：现行 1.0010382 vs 一致 1.1245888。
`config.json:58` 文字声称 "eigenvalues are of K/T (T-dim)"，但代码 `independent_upsa.py:170` 用 lam（K 的特征值），**代码与自身配置文档不一致**。
论文与作者代码用二阶矩（除以 T）的特征值，因此**作者/论文是对的，E06 代码 trace 缩放有错**。

## 5. 固定输入下作者 π 与 E06 π 逐元素比较（首窗）

| 对照 | maxabs | meanabs | relative_fro | corr |
| --- | --- | --- | --- | --- |
| E06 现行 π vs 作者 π | 1.62995 | 0.38420 | 0.17501 | 0.99993 |
| E06 改一致 scale 后 π vs 作者 π | 0.12328 | 0.02833 | 0.01287 | 0.99993 |
| 现行 π vs 改后 π（纯 scale 效应） | 1.60501 | 0.36813 | 0.16945 | 1.00000 |
| 作者 eff_port 重算 π vs getter | **0.0** | 0.0 | 0.0 | 1.0 |

- 作者权重和 ≈ 120.21；E06 现行 ≈ 99.65；改一致 scale ≈ 119.98（接近 T=120 的归一目标）。
- 仅修正 trace 缩放即消除约 94% 的权重相对误差；剩余 ~1.3% 来自低 z 实现差异（见任务 B）。

## 6. 对全期收益 / Sharpe / alpha / R² / 换手的影响（修正后重算，新 run_id）

修正仅改 `asset_weights`/`ridge_weights` 中 scale 用 lam/T；LOO、eff_port、QP 全部不变。
新产物：`results/audit_A_corrected_*`（new run_id `P006-E06-R4-AUDIT-001`），旧文件保留。

| 序列 | 年化 Sharpe |
| --- | --- |
| 作者 A（缓存三路径） | 1.922774 |
| 作者 A（当前 `_stage_P006/main_bundle.p`） | 1.923475 |
| 原 B0（有 trace bug） | 1.915169 |
| 原 B1（有 trace bug） | 1.915609 |
| **修正 B0** | **1.923487** |
| **修正 B1** | **1.923801** |

收益序列差异：

| 对照 | maxabs | meanabs | corr |
| --- | --- | --- | --- |
| 缓存 A vs 原 B0 | 0.58517 | 0.07121 | 0.99840 |
| 缓存 A vs 修正 B0 | **0.01638** | **0.000492** | 0.999993 |
| 当前 bundle A vs 原 B0 | 0.60116 | 0.07126 | 0.99839 |
| 当前 bundle A vs 修正 B0 | 0.04371 | 0.000597 | 0.999993 |

**结论**：trace 缩放错误是 A-vs-B0 全期差异的**主导原因**，使 Sharpe 偏低约 0.0083、
月收益 meanabs 偏大约 0.071。修正后 B0 与作者 A 的数值几乎一致（差异 ~5e-4 meanabs）。
之前报告把 A-vs-B0 归因于低 z 舍入放大，是**不完整/主次颠倒**的：低 z 效应真实存在但量级小得多（见任务 B）。

### 溯源备注（次要）
`compare_paths.py:16-18` 指向的 A bundle 路径 `revision-v3/.../main_bundle.p` 现已不存在；
`results/three_path_comparison.json` 中缓存 A（Sharpe 1.922774）与现存
`_stage_P006/.../main_bundle.p`（1.923475）/ `main_bundle_regen.p`（1.923322）逐月差 maxabs 0.044/0.036。
这是 A 侧产物版本溯源问题，不改变"修正 trace 后 B0 与作者一致"的结论；已在证据 JSON 中记录。
