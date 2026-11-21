# R4 数值差异报告（P006 FAIL / PARTIAL 与 E06 审计）

批次：`CO-REP-20261120-02-R4` ｜ 审核基线：`f548dbd`（research/portfolio-replication-r3）
所有 verdict 均为计算层判断，最终验收交主审逐 result_id 完成。旧 FAIL/PARTIAL 全部保留，不删改。

---

## 1. P006-E01 作者原码冷重跑：18 FAIL + 7 PARTIAL

### 1.1 verdict 变化（R3 → R4）
| 版本 | PASS | FAIL | PARTIAL | 说明 |
|---|---|---|---|---|
| R3（target_comparison.csv） | 90 | 17 | 8 | 保留原样 |
| R4（target_comparison_r4.csv） | 90 | 18 | 7 | 唯一变化：P006-T01-ALL-UPSA PARTIAL→FAIL |

变化原因：R3 `build_comparison.py:184-186` 对 ALL-UPSA 无条件把 FAIL 改为 PARTIAL（无依据硬编码豁免）；R4 改为统一 `scalar_verdict()` 按冻结容差判定，fresh 0.6645123437（显示 0.66）vs 印刷 0.67，绝对误差 0.005488 > 容差 0.005 → FAIL。这是取消无依据豁免，不是放宽/收紧容差追数。

### 1.2 18 FAIL 逐项（完整表见 executions/P006_E01_author/discrepancy_analysis.csv）
代表性条目（result_id / paper / author_cache / cold_run / abs_err / tolerance / verdict）：
- P006-F03-FULL-SAMPLE-LW：1.31 / 1.3083 / 1.2741 / 0.03588 / 显示半单位 0.005 / FAIL
- P006-F03-AFTER-2000-LW：（作者参考仅）/ 1.3453 / 1.3445 / 0.00082 / 作者参考容差 / PARTIAL
- P006-F05-FULL-RIDGE-ALPHA：4.46 / 4.4512 / ... / >0.005 / FAIL
- Table1 LW 家族 12 个主题单元（Low Risk −1.22 vs −1.37 等）：FAIL
- P006-T01-ALL-UPSA：0.67 / 0.6652 / 0.6645 / 0.005488 / 0.005 / FAIL（R4 新判定）
- 3 个 UPSA 擦边单元 + 1 Ridge alpha：abs 0.0055~0.0088，FAIL

全部 18 项均填 suspected_cause 与 confirming_test（见 discrepancy_analysis.csv 25 行）。

### 1.3 LW 家族 14 个 FAIL 根因（证据，非推测）
| 层次 | 是否致因 | 证据 |
|---|---|---|
| 输入/样本/标准化 | 否 | cold_run 30/30 源码与输入逐字节等于 ZIP（SHA a20c2fb…）；494 月 1981-11..2022-12；NaN=0/Inf=0；index/columns 严格一致 |
| 收缩参数/特征值截断 | 否 | z_grid=logspace(-10,-1,10) 与源码一致；do_lw(remove_pc_pert=0) 未截断；T=120 |
| LAPACK/BLAS 数值环境 + 缓存时点 | **是（根因层）** | 冷/缓存 LW 权重在首个窗口 1981-11-30 即分叉（max 2.45）；手稿缓存日期 2026-05-30 早于滚动窗口源码定稿 2026-05-31；冷重跑同环境 22/22 哈希复现 |
| LW 非线性收缩放大 | **是（放大层）** | 对全部 120 特征值求逆（最小 2.797e-7、逆权重 3.57e6、条件数 1.41e5）；1e-12 相对扰动 → 权重差 1.67e-3、回报差 1.6e-3 |
| PCA/FF5/CAPM 对照 | 反证 | PCA（独立分解）max 4.9e-11、FF5/CAPM 一致 → 非输入/时序层问题 |

结论：作者缓存生成环境的数值差异经 LW 近零特征值极端敏感性放大；不是源码缺失、输入错误或容差问题。作者缓存（1.3083）贴近论文 1.31，冷重算 1.2741——缓存值不作 rerun_value。

### 1.4 7 PARTIAL 结论
- Fig3 After-2000-UPSA：作者参考仅，abs 0.00082 ≤ 0.005 但显示跨档 → PARTIAL。
- 6 个面板逐点超冻结阈值（Fig6 的 5e-6 Sharpe、Fig8 的 1e-5 个百分点）；索引/长度/顺序严格一致，非实现缺失 → PARTIAL（不自动判 PASS）。
- All-UPSA 已转 FAIL（见 1.1）。

---

## 2. P006-E06 独立实现审计：六项发现

run_id `P006-E06-R4-AUDIT-001`；旧 R3 结果（target_comparison.csv，PASS12/FAIL24/NA6）保留。

### 2.1 特征值缩放与 trace normalization（审查任务 A）——发现真实错误
- 作者 `smart_eigenvalue_decomposition_covariance`：返回 `XX'/T` 特征值；`get_upsa_weights` 用 `1/(eig+z)`，两处同尺度。
- E06 `eig_K`：返回 `XX'` 特征值（= 作者的 T=120 倍）。`prepare_full_basis` 用 `1/(lam+T·z)`，经 push-through 恒等式与作者 basis 一致（eff_port 相对误差 2.3e-8，正确）。
- **E06 `asset_weights` 用 `1/(lam+z)`（未除 T）**：首窗 scale 0.9453 vs 作者一致口径 1.1382，**偏小 17%**；config.json 文字声称 eigenvalues of K/T 但代码用 K 特征值，代码与自身配置不一致。
- 修正（用 lam/T）后：B0 Sharpe 1.91517 → **1.92349**、B1 1.91561 → **1.92380**，作者 A = 1.92348（差约 1e-5）；A vs 修正 B0 月收益 meanabs **0.0712 → 0.00049**、maxabs 0.585 → **0.0437**、相对 fro 0.0034、corr 0.9999926。结论：trace bug 是 A/B0 差异主因，修正后独立实现与作者对齐。
- 9 步逐项分解（discrepancy_decomposition.csv）：步1数据、步2网格差 0；步3 LOO 差 0.123；步5 线性求解 1.9e-7；**步6 trace 缩放 1.605（主导）**；步8收益 0.039、步9 Sharpe 0.0076。

### 2.2 A/B0/B1 差异分解（任务 B，一次只改一个约定）
| 对照 | maxabs | meanabs | corr | 主因 |
|---|---|---|---|---|
| A vs B0（原） | 0.58517 | 0.07121 | 0.99840 | trace 缩放 bug（主导）+ 低 z 舍入（次要）+ eff_port 求解差 ~2e-7 |
| B0 vs B1 | 0.00874 | 0.00111 | 0.9999975 | 仅留一分母 T→T−1 |
| A vs B1（原） | 0.58452 | 0.07205 | 0.99841 | A-vs-B0 实现差 + B0-vs-B1 分母差 |

低 z 舍入假设验证（不预设接受）：作者 smoother 的 w_adj/z 在低 z 确实放大——首窗 z=1e-10 时 ‖w_adj‖/z=9.24e-7、LOO 因 w_adj 变化 maxabs=0.219；去掉 w_adj 后 vs 稳定实现 maxabs 降至 2.8e-7。**假设成立但为次要因素**；修正 trace 后主导差异消失，证实原 R3 归因不完整。

### 2.3 样本外信息泄漏（任务 C）
E06 `compute_metrics`（line 412-419）用全部 494 个 OOS 月 FF5 一次性估计基准权重（前瞻）。作者 `portfolios.py` 逐窗仅用窗内 FF5（`ff5_ins`），无前瞻。数值影响：全 OOS FF5 Sharpe 1.2249 vs 窗内滚动 1.1293（差 0.0956）、alpha 差约 0.77pp、月收益 maxabs 1.5126——是实实在在差异，非"无害"。结论：E06 该处是**独立实现引入的 look-ahead 偏差**，不属于原文比较口径，不能解释为可交易策略；已另立无前瞻基准（滚动=作者可比口径，扩展窗=RESEARCH_EXTENSION）为诊断，不混入 E01/E06 忠实目标。该泄漏不是 24 FAIL 的直接原因（FAIL 中不含 FF5_sharpe / alpha_vs_FF5）。证据 results/audit_C_leakage.json。

### 2.4 QP 精度（任务 D，阈值 1e-7）
原 B0 max KKT 2.105e-7、B1 1.555e-7 超阈值；494 窗中 cvxopt 默认设置下 B0 有 14/494、B1 有 15/494 窗 KKT > 1e-7。`status='optimal'` 只说明其内部 abstol/reltol/feastol（默认 1e-7）满足，不等于本 KKT 测度通过。残差定义为乘子自由 KKT `max(max(0,-W), max(0,u-QW), max|W·(QW-u)|)`。保留原配置结果不事后放宽 1e-7；另跑高精度诊断：cvxopt 高精度（1e-12）后 B0/B1 max KKT 降至 8.11e-13 / 9.20e-13，超阈 0 窗——超阈值是求解器精度所致，不是算法不可行。证据 results/qp_highprecision.json、history/qp_diagnostics_*_v3_backup.json。

### 2.5 数值警告与环境（任务 E）
run_full.log 的 divide by zero / overflow / invalid matmul 已定位到具体计算位置与影响范围（见 warnings_audit.md），不笼统声明"无害"。requirements 锁定直接依赖，environment 记录 Python/pip 版本可重建。

### 2.6 24 FAIL 重新解释（任务 F）
42 项检查中 24 FAIL **不是** 24 个数学恒等式失败，全部是"B0/B1 复现值 vs 论文发表值超容差"：18 个主题 R²、2 alpha、2 HAC t、2 换手。六类分层：
1. LOO 数学等价：PASS（2.45e-8 < 1e-6），非 FAIL 来源；
2. QP 可行性：494/494 optimal，KKT 超阈仅求解器精度（任务 D），非 FAIL 来源；
3. A/B0 数值一致性：trace bug 主因、低 z 次要（诊断发现，不直接等于 24 个对照）；
4. B0/B1 约定差异：仅分母，Sharpe +0.00044、换手 +0.017pp；
5. 作者代码与论文数值一致：作者 A 缓存 Sharpe 1.9228、换手 12.388% 与论文 1.92/12.4 一致；低 z 不稳定实现绑定发表数字；
6. 发表结果匹配：24 FAIL 全属此类；trace 修正后平均绝对误差 **0.153 → 0.0045**（B0 alpha 5.3307→4.4599 vs 4.46；t 4.1196→3.7189 vs 3.72；换手 12.7405→12.398% vs 12.4），14/24 落入半单位容差。
所有 R4 新判定标 DIAGNOSTIC_ONLY，未经审批不改 R3 的 PASS/FAIL。R4 target_comparison_r4.csv 新增 r4_category/r4_status/r4_corrected_value 列；R3 42 行备份为 target_comparison_v3_backup.csv。

### 2.7 未解决问题（诚实记录）
- requirements.txt 误锁 `python==3.9.6`（非 pip 包），environment.json 缺 pip 版本（实测 pip 26.0.1）——环境可重建性需修正（不影响已跑结果）。
- matmul 的 divide/overflow/invalid 告警 FP 标志真实置位，但纯随机有限数组也触发；494 窗全扫描输出均有限、无选择性损坏 → BLAS/numpy quirk，不篡改数值（证据 audit_E_warnings.json）。
- A 侧产物溯源：compare_paths.py 指向的旧 A bundle 路径已不存在；缓存 A（Sharpe 1.922774）与现存 _stage_P006/main_bundle.p（1.923475）逐月差 maxabs 0.044——已记录，不影响"修正后 B0 与作者一致"结论。

---

## 3. P001 / P008 数学与来源（分别报告）
- P001-E01（R4-P001-001，exit 0）：a=0.7421582911108061、a/λ=0.3710791455554031、aim0=(1.7415…,1.2549…) 与 reviewer 逐位一致，reference_kind=REVIEWER_CALCULATION（非印刷值）；A7/A10/A11 恒等式 PASS（THEORETICAL_IDENTITY）；非对易案例标 FORMULA_VERIFICATION；市场数据 Figure3、正式版无 Figure5 已核对；市场经济发展 NOT_ASSESSED。
- P008-E01（R4-P008-001，exit 0）：正常例 cond=5.19、KKT=3.49e-16 ≤ 1e-10、四基金张成一致；病态 cond≈1e9 单独 PARTIAL/REPORTED。
- P008-E03（R4-P008-003，exit 0）：AQR xlsx SHA 153423fd… 一致；R10=7.836146824925816%（论文 7.84%）、R11=3.014250756676558%（论文 3.01%），均 ±0.005pp 内。仅 R10/R11 计为论文目标，其余 4 行为辅助检查。

---

## 4. 判定原则
- 不通过事后放宽容差、改样本、换算法提高 PASS；修复生成新 run_id，旧结果保留。
- 数值一致性（numerical_verdict）与理论机制（theoretical_mechanism_verdict）、市场经济（market_economic_verdict）分开。
- 作者缓存比较与发表数值比较分别给结论；缓存值不作 rerun_value。
