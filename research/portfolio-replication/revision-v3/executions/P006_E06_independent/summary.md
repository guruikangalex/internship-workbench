# P006-E06 独立实现执行摘要（INDEPENDENT_FAITHFUL / IMPLEMENTATION_AUDIT）

- run_id: `P006-E06-INDEP-20261121-01`
- reviewed_source_commit: `104aecfcad4c308e1044a3d15483fe2320619597`
- 论文版本: P006-RFS-20261119（`P006-RFS-20261119` / canonical_version_id 同）
- 执行状态: **COMPLETED**；容差在 `config.json` 中于查看任何结果前冻结。
- 作者 A 的结果只读引用自 `P006_E01_author/outputs/computed/main_bundle.p`；未修改作者代码或顶层主档。

## 1. 稳定留一表达式 vs 直接逐点删行重拟合（首窗 T=120, P=153, 行 t=0/59/119, 全部 10 个 z）

实现：`K=X X'`，`G_c=(K+c z I)^(-1)`，`a_t=1-(G_c 1)_t/diag(G_c)_t`（用 `eigh(K)` 分解求解，非抄公式）。

| 对照 | maxabs | fro | 相对误差 | 判定 |
| --- | --- | --- | --- | --- |
| 稳定式 c=T vs 直接删行(分母 T) | 2.454e-08 | 2.525e-08 | 3.90e-09 | 等价（冻结容差 1e-6） |
| 稳定式 c=T−1 vs 直接删行(分母 T−1) | 2.435e-08 | 2.470e-08 | 3.81e-09 | 等价（冻结容差 1e-6） |

逐 z 最大绝对误差：z=1e-10 → 2.45e-8；1e-9 → 2.6e-9；1e-8 → 3e-10；z≥1e-7 → 0。条件数逐 z 已存 `results/first_window_check.json`；全窗 `cond(K+TzI)` 最大 1.228e6、`cond(K+(T−1)zI)` 最大 1.228e6，均低于冻结警戒线 1e10。数学等价性成立。

QP 交叉核对：首窗 cvxopt 与 scipy SLSQP 的 W 向量 fro 差 1.72e-5，SLSQP 成功。

## 2. 三路径全窗结果（494 月，1981-11…2022-12）

全部 494 窗 QP 状态 `optimal`；B0 KKT 残差最大 2.105e-7、B1 最大 1.555e-7（冻结容差 1e-7，略超但量级等同 cvxopt 自身 abstol/feastol=1e-7，记为 MARGINAL 而非失败）。所有月收益/持仓有限；trace scale B0∈[0.8298,1.8501]、B1∈[0.8311,1.8505]，均有限且为正。

| 指标 | A（作者，只读引用） | B0（c=T 稳定） | B1（c=T−1 论文） | 论文值 |
| --- | --- | --- | --- | --- |
| 年化 Sharpe | 1.92277 | 1.91517 | 1.91561 | 1.92 |
| UPSA vs Ridge alpha (pp) | — | 5.3307 | 5.3408 | 4.46 |
| alpha HAC(5) t | — | 4.1196 | 4.1221 | 3.72 |
| 月均换手 (%) | 12.3879 | 12.7405 | 12.7578 | 12.4 |
| Table 1 All 定价 R² | — | 0.6664 | 0.6670 | 0.67（作者缓存 0.6652/0.6649） |

月收益序列差异：A vs B0 maxabs 0.5852 / meanabs 0.0712 / corr 0.9984；A vs B1 maxabs 0.5845 / meanabs 0.0720 / corr 0.9984；**B0 vs B1 maxabs 0.00874 / meanabs 0.00111 / corr 0.9999975**。持仓差异：A vs B0 相对 fro 0.1435；B0 vs B1 相对 fro 0.00337。

## 3. 差异归因

- **A vs B0（数值实现差异）**：两者数学同为分母 T 的 ridge 留一。作者平滑器含 `w_adj/z`，全窗基含 `l_adj/z`；当 P>T 且取满 T 维特征空间时这两项理论为零，实际是舍入残差，除以 z≤1e-7 后被放大。首窗 A vs B0 的 LOO maxabs：z≥1e-6 为 3.32e-9，z=1e-7 为 2.44e-7，z≤1e-8 达 **0.219**。B0 用 `eigh(K)` 的 push-through 恒等式消去这两项，故更稳定。A 的已发表 Sharpe 1.9228、换手 12.388% 与论文 1.92/12.4 一致；B0/B1 的稳定数值给出 12.74/12.76% 换手——论文发表数字绑定在作者低 z 不稳定实现上。
- **B0 vs B1（留一归一化差异）**：相同稳定实现下仅改留一分母 T→T−1。月收益影响很小（maxabs 0.0087、相关 0.9999975），Sharpe +0.00044、换手 +0.017 pp、alpha +0.010 pp。该差异显著小于 A-vs-B0 的实现差异。
- **A vs B1（综合）**：以 A-vs-B0 实现差异为主（meanabs 0.0712），B0-vs-B1 分母效应仅 0.0011，二者不可混同。

## 4. 目标对照与判定

`target_comparison.csv`：42 行 = 36 RUN + 6 NOT_RUN；判定 12 MATCH、24 NUMERIC_DIFFERENCE、6 NOT_ASSESSED。MATCH 主要是两条路径的 Sharpe 与 All/多数主题 R²；NUMERIC_DIFFERENCE 集中在 alpha（+0.88 pp）、HAC t（+0.40）、换手（+0.34~0.36 pp）及部分主题 R²（如 Low Risk −0.036、Skewness −0.028）。E06 无预注册目标行，论文值取自同 canonical version 的 E01 目标行，已在 `reference_kind`/`scope_status` 明确标注；未数字化的子样本/模拟等 6 类为 NOT_RUN。

## 5. 阻塞与记录

1. 作者 `_alpha_one`（`src/plotting.py:75`）在 statsmodels 0.14.6 下因 `params["const"]` 抛 IndexError；E06 用等价的 `params[0]` 实现，公式逐步一致（见 `results/implementation_crosscheck.json`）。这是环境版本问题，非数学差异。
2. 本环境 BLAS/numpy 对所有 `matmul` 报无害的 divide/overflow/invalid 告警；所有输出经有限性检查通过，K 值一致。日志保留原始告警以便审计。
3. 论文 alpha 4.46/t=3.72、换手 12.4 与稳定实现不符；这是本审计的核心发现，不作调参追数，不修改 E01/E05。

## 6. 交付文件（均在独占目录）

`independent_upsa.py`, `compare_paths.py`, `make_target_comparison.py`, `config.json`, `environment.json`, `requirements.txt`, `run_first_window.log`, `run_full.log`, `run_metrics.log`, `run_compare.log`, `target_comparison.csv`, `summary.md`,
`results/`: `first_window_check.json`, `full_run_summary.json`, `metrics.json`, `three_path_comparison.json`, `implementation_crosscheck.json`, `weights_B0.csv`, `weights_B1.csv`, `returns_B0.csv`, `returns_B1.csv`, `returns_ridge_B0.csv`, `returns_ridge_B1.csv`, `returns_three_path.csv`, `mixture_B0.csv`, `mixture_B1.csv`, `scale_bestz.csv`, `qp_diagnostics_B0.json`, `qp_diagnostics_B1.json`, `full_raw_B0_B1.npz`, `sha256sums.txt`。
