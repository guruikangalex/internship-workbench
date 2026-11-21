# R3 主审用摘要（执行与结果交付）

批次：`CO-REP-20261120-02-R3` ｜ 审核基线：`REVIEW-104AECF-20261121` / `104aecf`
工作分支：`research/portfolio-replication-r3` ｜ 状态：执行进行中，逐实验汇总

> 已批准实验的依赖准备和常规预检不需重复申请；数值 verdict 只表示计算层判断，最终验收由主审逐 result_id 完成。

## 1. 本轮实际完成情况

### 主档修复（F01–F05，已完成并通过 metadata/validate_r3.py 校验）
- **F01**：冻结版损坏的 `target_alignment.csv`（360061B，SHA `dba11b13…`，blob `547279c1…`）已重建为 779 行 × 25 列 UTF-8 CSV，键唯一，P006-E01 精确 115 条；10 个 OUTSIDE_PILOT 与 5 个重复版本别名移入 `history/`。生成脚本 `metadata/build_target_alignment.py`。
- **F02**：执行材料按"每个实验独占目录"交付真实源码/配置/环境/命令/日志/结果/哈希；大型输入以稳定 URL + 哈希 + 形状 + 日期交接；旧执行记录不补造。
- **F03**：证据索引从 6 行扩至 186 行；84/84 critical evidence_id 全覆盖；53 条从原始尽调卡解析出真实 URL/定位，127 条如实标 `DETAILS_NOT_IN_FROZEN_PACKAGE` 并给出恢复路径，未编造 URL。
- **F04**：P006 两个版本别名统一为 `P006-RFS-20261119` / `P006-NBER-20260521`；P006-E01 由 125 收缩为 115；P006-E06 补入队列并标注批准来源；P002-E01 标为被 E21 继承；P010-E03 补 4 个显式目标；`IMPLEMENTATION_AUDIT` 归入 `experiment_purpose`。
- **F05**：P001 图号、P003 范围、P007 分类、P008 "实证只能近似验证"旧理由、P009/P010 代码状态等现行结论统一；旧值移入 `history/F05_superseded_current_fields.json`。

### 已执行的实验（详见第 2 节状态表）
- **P006-E01（AUTHOR_CODE_RERUN）**：已从隔离空目录真实冷计算完成（`--main --compute`，88 秒），20 个主文输出生成，115 目标逐项比较完成。
- P006-E06、P001-E01、P008-E01/E03、support 补证：执行中，按各独占目录交付。

## 2. 执行状态表（每实验：版本 / 批准范围 / run_id / 状态 / 输出）

| 实验 | 规范版本 | 复现类型 | 批准范围 | run_id | 状态 | 输出位置 |
|---|---|---|---|---|---|---|
| P001-E01 | JF2013_A15STAR | INDEPENDENT_FAITHFUL | R01/R02/R03/R09 有限理论 | R3-P001-001 | **TARGETS_GENERATED**（18：PASS 17 / N/A 1） | executions/P001_E01/ |
| P006-E01 | P006-RFS-20261119 | AUTHOR_CODE_RERUN | 115 PROPOSED | RUN-P006-E01-AUTHOR-20261121-01 | **TARGETS_GENERATED**（115：PASS 90 / FAIL 17 / PARTIAL 8） | executions/P006_E01_author/ |
| P006-E06 | P006-RFS-20261119 | INDEPENDENT_FAITHFUL | 论文 T−1 留一实现 + 同输入对照 | P006-E06-INDEP-20261121-01 | **TARGETS_GENERATED**（42：PASS 12 / FAIL 24 / N/A 6） | executions/P006_E06_independent/ |
| P008-E01 | JFE2021_VOR | INDEPENDENT_FAITHFUL | R01 理论/四基金 | R3-P008-001 | **TARGETS_GENERATED**（11：PASS 10 / N/A 1） | executions/P008_E01/ |
| P008-E03 | JFE2021_VOR | INDEPENDENT_FAITHFUL | R10/R11 Table4 均值 | R3-P008-003 | **TARGETS_GENERATED**（6：PASS 6） | executions/P008_E03/ |
| P002/P003/P004/P007/P010 | 各规范版本 | — | 仅具体缺口补证/预检 | — | PREFLIGHT_PASSED（无正式结果） | executions/support/ |

## 3. 核心结果表（已完成实验；verdict 均为计算层，最终验收交主审）

### P001-E01 有限理论核对（INDEPENDENT_FAITHFUL，R3-P001-001）
- a=0.7421582911108061、a/λ=0.37107914555540306、初始 aim=(1.7415054571868176, 1.2549203600714012) 与 reviewer 参考逐位一致。
- 冲击分解首笔交易 L2（w=1/0.5/0）=0.796539/0.955134/1.551842，与 reviewer 一致；慢/快信号保留比 87.0753%/62.7460%。
- A7/A10/A11 恒等式、标量/矩阵解、几何和 aim、160 期交叉核对全 PASS；非对易案例 A15* 满足 A7（残差 3.6e-16）、原式 A15 失效（残差 0.0415）。reviewer 交换子 1.6122 构造不同 → NOT_APPLICABLE；自构造 ||[Σ,Λ]||_F=3.5355 独立确认机制（FORMULA_VERIFICATION）。终端记账修订恒等式 maxabs 3.6e-15。
- 理论恒等式类标 THEORETICAL_IDENTITY；市场经济评价 NOT_ASSESSED；P001-E02 仍 REQUEST_EVIDENCE，不扩大到商品期货实证/原图坐标。

### P006-E06 论文 T−1 独立实现（INDEPENDENT_FAITHFUL / IMPLEMENTATION_AUDIT，P006-E06-INDEP-20261121-01）
- 稳定留一表达式（K=XX′，G_c=(K+czI)^−1，a_t=1−(G_c1)_t/(G_c)_tt；eigh 分解实现）vs 直接逐点删行重拟合：maxabs 2.45e−8（冻结容差 1e−6），条件数 1.2e6（警戒 1e10）→ 等价 PASS。494/494 QP optimal，KKT 残差最大 2.1e−7。
- B0(T) vs B1(T−1) 月收益 maxabs 0.00874、corr 0.9999975、Sharpe 1.91517→1.91561：分母效应经济上很小。
- A(作者) vs B0 月收益 maxabs 0.585、corr 0.9984：数值实现差异——作者 w_adj/z、l_adj/z 在 z≤1e−7 放大舍入；论文换手 12.4% 绑定在作者低 z 不稳定实现上（B0/B1 为 12.74/12.76%）。
- alpha 4.46 vs 5.34pp、t 3.72 vs 4.12 等差异如实 FAIL，不追数。

### P008-E01 理论命题（INDEPENDENT_FAITHFUL，R3-P008-001）
- KKT 相对残差 3.494e−16（阈值 1e−10，事前冻结）；闭式 vs 直接 KKT vs 零空间投影优化最大差 ≈1e−17。
- 无约束切点=前沿峰位 SR(s*)=0.180756165009、dSR/ds|=0；四基金张成重构误差 3.47e−18；x′1=0.0967>0 可行。
- 退化显式处理：q=0、投影收益为零、净仓为零（平均 ESG 比未定义）、病态 Σ（cond≈1e9，isolated，NOT_APPLICABLE）。理论机制 PASS，市场经济 NOT_ASSESSED。

### P008-E03 作者组合收益复算（INDEPENDENT_FAITHFUL，R3-P008-003）
- 从 AQR URL 实际下载（HTTP 200，215209 B，SHA256 153423fd… 一致）；674 月连续唯一。
- R10 Table4 Panel A/G：原文 7.84%，复算 7.836146824925816%，差 −0.003853 pp（容差 ±0.005 pp，PASS）。
- R11 Table4 Panel B/G：原文 3.01%，复算 3.014250756676558%，差 +0.004251 pp（PASS）。与 reviewer 值逐位一致；reviewer 计算另以 REVIEWER_CALCULATION/performed_by=reviewer 登记。

### P006-E01 作者代码冷重跑（计算层 verdict，最终验收交主审）
- 真实重算证据：新 bundle SHA256 `3ebba382…` 与手稿缓存 `e767297e…`、作者再生缓存 `a1d6a3c4…` 均不同 → 从 5 个 CSV 重算，非缓存重绘；`opt_port` NaN=0/Inf=0。
- 115 目标：**PASS 90 / FAIL 17 / PARTIAL 8**（`target_comparison.csv`，94 个发表值锚点、12 个作者分期参考、9 个数组/图形诊断）。
- 示例：Fig3 全样本 UPSA 1.92（发表 1.92，PASS）、LW **1.2741 vs 1.31（FAIL）**；Table1 All-UPSA R² 0.6645 vs 0.67（PARTIAL，跨 0.665 舍入边界，协议已预标注）。
- 作者缓存比较（独立）：Fig6 逐点 5e-6 Sharpe 阈值下 UPSA/LW/Ridge 超阈、PCA/FF5/CAPM 在阈内；Fig8 逐点 1e-5 个百分点阈值下 UPSA 470/483 超阈。缓存值未回填为 rerun_value。

## 4. 差异解释
- P006 LW 家族漂移：`--compute` 全量重算与手稿缓存/发表值存在系统差异，作者 README 已披露部分 R² 舍入边界差异；本轮未放宽容差追数，FAIL 如实登记。属证据（重算复现）与推测（成因）分开：成因为作者缓存与冻结代码的版本/数值约定差异，需主审结合版本决断。
- P006 作者缓存 vs 发表值：两者分别对照，未混为同一目标。

## 5. 剩余阻塞

### 已批准实验的阻塞
- P006-E01/E06：RFS 排版版 PDF 二进制 hash = null（HTML 全文可读、DOI 锚定，不影响本轮计算层比较；影响最终数值验收的版本凭证）；LW 家族 17 个 FAIL 与 8 个 PARTIAL 待主审判处（未放宽容差）；作者低 z 实现的舍入放大已由 E06 独立确认。
- P001-E01：reviewer 交换子构造与研究者构造不同，1 项标 NOT_APPLICABLE；市场经济评价整体 NOT_ASSESSED，不扩大到商品期货实证。
- P008-E01：病态 Σ（cond≈1e9）退化案例隔离为 NOT_APPLICABLE；E03 两项通过不扩大到股票形成/ESG 优化前沿/回归。

### 补证范围（support，未批准完整实证）
- P002：`usa.csv`/`usa_dsf.csv`/`world_ret_monthly.csv` 经 Ken French/JKP/ReplicationCrisis 三条公开入口实检均 NOT_FOUND，需 WRDS 授权或作者快照；E21 99 单元维持 REQUEST_EVIDENCE，E01 标为由 E21 继承；I21/I22 运行时审计 NOT_RUN。
- P003：Ken French 49 行业月频快照实取但 vintage 非冻结原始，标 APPROXIMATE_VALIDATION；OOS w 网格/平局规则/最少历史月数待定；作者代码 NOT_FOUND，回测 NOT_RUN。固定 w 子实验配置已冻结。
- P004：QF 正式版合成实验正文 403 NOT_READ，与 arXiv v1 的 R05/R06 表图编号未核；完整训练需专门审批；旧依赖数值等效性无证据。
- P007：FF25 日频数据已实取（hash 记录于 code/block_ff25.py），20 交易日切块脚本已写；原文图表完整复现仍 REQUEST_EVIDENCE，138 因子预测张量未成套取得（P007-E02 REQUEST_EVIDENCE）。
- P010：官方 MATLAB 代码包核验与 TRACE 路线协议补证进行中；ICE 实证 HOLD，TRACE 不得以清零占位 MAT 判成败。

所有未批准的完整实证均保持 REQUEST_EVIDENCE/HOLD，不因预检成功自动升级。

## 6. 交付入口
- 分支 `research/portfolio-replication-r3`；规范主档 `revision-v3/{record_master.json,master_table.csv,reviewer_queue.json,target_alignment.csv,evidence_index.csv}`；执行材料 `revision-v3/executions/`；校验 `metadata/validate_r3.py`（PASSED）。
- Git commit：待最终汇总后提交并记录 SHA。

## 7. 待主审验收项
- P006-E01：115 个 result_id（PASS 90 / FAIL 17 / PARTIAL 8），特别是 LW 家族 FAIL 与 Table1 All-UPSA PARTIAL 的处置。
- 其余实验的 result_id 在 agent 返回后逐项列出，不泛问"是否开始"。
