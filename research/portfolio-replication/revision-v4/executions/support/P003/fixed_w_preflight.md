# P003 固定 w 子实验预检（PREPARED / NOT_RUN）

- 批次 CO-REP-20261120-02；论文 FAJ 77(2):124–151，DOI 10.1080/0015198X.2020.1854543；版本 P003-FAJ-2021-VOR。
- 子实验：**固定 w（in-sample shrinkage of w）· Equity 1**，月频，60 月风险窗。对应 Table 5 的 Equity 1 列与 Table 6 回归的 LHS。
- 执行日期 2026-11-21。本轮只做输入预检与配置冻结，**没有回测、没有目标数值**；所有结果 `NOT_RUN` / `NOT_ASSESSED`。
- 关键判定：**OOS w 网格缺口不拖住固定 w 准备**。论文只披露 OOS 使用"有限网格、逐月选择、扩展样本"（p.138 Fig.2 注、Table 5 注），未给实际网格/平局/最少历史月数。Table 5 的 `[0,.10,.25,.50,.75,.90,.99,1]` 是**可核的展示压力范围**，不能当作者 OOS 全集；这不影响先把固定 w 的配置、资格、缺失与累计收益定义冻结。

## 1. 输入快照（APPROXIMATE_VALIDATION，不沿用忠实标签）

- 实取：Ken French 49 Industry Portfolios，`49_Industry_Portfolios_CSV.zip`，489861 B，SHA256 `d1a3b0b9896e1e633ed2aa85e24ca144d7998f8ab2ff344e2379383ebeb7b836`；成员 `49_Industry_Portfolios.csv` 2264554 B，SHA256 `633958bf36d25da6d95876bfc468536029db600c32c65b7a3e0f7fba59a04609`。
- 内容：49 行业、1203 个月（192607–202609），value-weighted 含分红段；论文窗口 1942-01–2018-12 共 924 月；sentinel `-99.99/-999` 共 2868 单元，涉及 Soda/Hlth/FabPr/Guns/Gold/Softw/Paper/PerSv/Rubbr 等晚Start行业。
- **vintage 未恢复**：v2 协议中的 FIZ 2024-12 / CIZ 2026-09 冻结快照不在本 workbench；本轮对 `Data_Library_202412` 等归档 URL 的探测均 HTTP 404。当前 202609 CRSP vintage 仅为**替代/近似验证**快照，不能标 `PAPER_REPLICATION` / `INDEPENDENT_FAITHFUL`。原始实证终点 2018-12 与发表时封存版都未确认。
- 证据：`code/verify_fixed_w_inputs.py` → `results/fixed_w_input_audit.json`，日志 `logs/verify_fixed_w_inputs.*.log`。

## 2. 固定 w 子实验定义（已冻结，待审批）

- 风险模型（Eq.19/20，v2 protocol §3）：
  - `V = diag(Sigma_raw)`；`Sigma_tilde = 0.95*Sigma_raw + 0.05*V`；`Sigma_w = (1-w)*Sigma_tilde + w*V`。
  - 解 `gamma*Sigma_w*x = s`，等价 `max s'x - gamma/2 x'Sigma_w x`，**无额外预算/盒式持仓约束**；`gamma=1` 作风险尺度。
  - 秩不足时**不得静默用伪逆**，须记录条件数；Equity 1 的 60 月窗一般满秩（49<60），但仍记录。
- 信号（Eq.24/25，XSMOM）：过去 12 个可用月的行业累计超额收益，横截面去均值；正端归一 sum=1、负端绝对和 sum=1。Eq.(25) PDF 右侧负信号带符号印成 `+1` 是排版错误（去均值向量和为 0，负侧只能解释为绝对和 1）。12 月超额复合口径（逐月超额连乘 vs 总和减同期复合 RF）**UNRESOLVED**，看结果前须冻结，不用表值反推。
- 累计收益：月 `x_t' r_{t+1,excess}`（毛）；Sharpe = `mean/std*sqrt(12)`，**无执行成本**；与 Table 6 的 FF5 回归分离。输出月权重、目标收益、各候选 w 训练 SR、样本起点、预收缩/无收缩协方差条件数。
- Equity 1 风险窗：**过去 60 个月**行业超额收益、样本均值去中心化、分母 K−1（脚注 17），时间 t−1..t−60。基准 1/N、INDMOM、完全未收缩 MVO（w=0 行）须与"5% 预收缩 MVO"区分——Table 5 是两行，不能混同。

## 3. 行业资格 / 缺失处理 / 样本（事前定义）

- 行业资格（EX_ANTE_ONLY）：同时满足 (a) 完整 12 月信号历史、(b) 完整 60 月风险窗、(c) 无实现收益前知。晚进入行业（Soda、Hlth、FabPr、Guns、Gold、Softw、Paper、PerSv、Rubbr）在 sentinel 消失前排除；逐期可投资池变化必须记录，不使用"到 2018 才知道的完整样本资格"。
- 缺失处理：sentinel `-99.99/-999` 视为 **MISSING**，**绝不当 0**；当期实现收益缺失按事前规则停记/单列，不做事后按表现过滤。`1/N` 与 INDMOM 是否与 EPO 用同一当期可交易宇宙：**UNKNOWN**，看结果前锁定。
- 样本：输入最早 1927-01，Table 5 目标 1942-01–2018-12；至少 15 年初始历史；因 60 月风险窗，最早可评估月晚于原始起点，原始 15 年与实际可算候选的月数不同，冻结起始条件与并列规则前正式 OOS 行不运行。所有决策在月频决策时点。

## 4. 状态枚举与剩余阻塞

| 项 | 状态 |
|---|---|
| 固定 w 配置（网格/公式/收益/窗口） | `PREPARED` |
| 行业资格规则 | `PREPARED_EX_ANTE` |
| 输入快照 | `APPROXIMATE_VALIDATION` |
| OOS w 网格 | `UNKNOWN`（不阻塞固定 w 准备） |
| 12 月超额复合口径 | `UNRESOLVED`（看结果前冻结） |
| 回测 / 目标值 | `NOT_RUN` / `NOT_ASSESSED` |
| 作者代码 | `NOT_FOUND` |
| 审批 | `PENDING` |

阻塞：原始/FIZ/CIZ vintage 未恢复；OOS 网格/平局/最少历史月数待作者文件或主审判定；12 月复合口径待冻结；日 RF 与 Table 6 t 统计/收益计量（P003-B09）未定。固定 w 准备已完成，不受 OOS 网格缺口阻塞。
