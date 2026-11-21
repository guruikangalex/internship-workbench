# P002 静态核对（STATIC_AUDIT，非实证复跑）

- 批次：CO-REP-20261120-02；论文：RFS 39(10) 3035–3078，DOI 10.1093/rfs/hhag022。
- 作者代码：`CO-REP-20261120-02/execution/P002_repo/`，commit `13d836b5187cbfa69730dd256d8eb767e65ca21f`（2025-03-05），与 Dataverse v1.0 的 97 个文件逐字节同 hash（v2 protocol 已记录）。
- 论文正文抽取：`CO-REP-20261120-02/evidence/P002_hhag022_text.txt`（源 PDF SHA256 `8fc13f07eb5fa1cb151e5adec0efb0b75c7d008c5066aa0170a40b2d9dc662cf`）。
- 执行日期：2026-11-21。执行者：补证 agent。
- **范围声明**：本文件只做"作者源码字面 vs 论文正文口径"的逐行静态核对。未运行 `Rscript`、未训练、未回测、未生成任何目标数值。所有实验状态仍为 `NOT_RUN`，经济结论 `NOT_ASSESSED`。发现差异只登记为 **PAPER–CODE DIVERGENCE / 待运行时审计**，**不据此宣称作者错误**：发表版 Table 2 的实际生成脚本版本、打印舍入与未公开的生成日志均不在本轮证据内。

## 1. 数据输入入口（实际尝试，非推测）

脚本：`code/verify_data_entry.py`；结果：`results/data_entry_manifest.json`；stdout/stderr：`logs/verify_data_entry.*.log`。

| 数据 ID | 作者 README 指定来源 | 本轮公开入口实测 | 状态 |
|---|---|---|---|
| D01 `usa.csv` | WRDS（Jensen–Kelly–Pedersen 2023 复制数据，筛 `excntry=="USA"`） | 本地挂载（repo/P002_data/evidence/support）全量文件名检索无命中；ReplicationCrisis 公开仓库无此文件；JKP 网站不可达且未公开该面板 | `NOT_FOUND` / `ENTITLEMENT_REQUIRED` |
| D02 `usa_dsf.csv` | 按 ReplicationCrisis 仓库代码从 WRDS 生成，或邮件向作者索取 | 同上；RC 仓库 `Analysis/1 - Prepare Data.R` 仅代码，不含生成后的日频股票面板 | `NOT_FOUND` / `ENTITLEMENT_REQUIRED` |
| D03 `world_ret_monthly.csv` | 同 D02 | 同上；无公开月度全股票面板 | `NOT_FOUND` / `ENTITLEMENT_REQUIRED` |
| D04/D05 因子表 | GitHub `bkelly-lab/ReplicationCrisis/GlobalFactors/` | 已克隆 commit `67174c7f170bf8b952b3c86876f187fd9970b5ba`，`Factor Details.xlsx`、`Cluster Labels.csv` 实存 | `ACCESSED_CODE_ONLY` |
| D07 `ff3_m.csv`（仅 RF 列） | Kenneth French Data Library | ZIP 实取：13078 B，SHA256 `b03d39e4bb253dda0f14893db3b78e64b40b8d6549a0fc0fd4111dae84c98618`；成员 `F-F_Research_Data_Factors.csv` 52533 B，1203 个月度行，首月 192607、末月 202609，文件头 "This file was created using the 202609 CRSP database." | `SAMPLE_ACCESSED` |

**结论**：三个硬阻塞文件在公开 Ken French / JKP / ReplicationCrisis 入口均 `NOT_FOUND`。Ken French 仅提供因子组合时间序列，不提供证券级特征/收益面板；不得当作 D01–D03 的替代输入。D07 的 French 下载只可作 `APPROXIMATE_VALIDATION` 的 RF 代理，且需主审认可 vintage（v2 protocol 已记录 202107/202407 在论文覆盖内有 RF 差 1bp）。

## 2. 逐行静态核对表（保留作者原码 + 论文口径的对照边界）

### I21｜净收益方差惩罚口径（P002-I21 / E28）

- 论文正文式(11)（抽取第 497–513 行）：
  `utilityᵉᵐᵖ_T = 1/T Σ_{t=1}^T [ r^{gross}_{t+1} − TC_t − γ/2 (r^{net}_{t+1} − r̄^{net})² ]`；
  并明确 "the last term captures disutility of risk, `1/T Σ γ/2 (r^{net}_{t+1} − r̄^{net})²`, where `r̄^{net}` is the average net return"，Table 3 脚注（第 1461–1463 行）再次写 `r^{util} = r^{gross} − TC − γ/2 (r^{net} − r̄^{net})²`。
- 作者源码 `6 - Base analysis.R:25–26,34–40`：
  ```
  25  pfs[, e_var_adj := (r-mean(r))^2, by=type]
  26  pfs[, utility_t := r-tc-0.5*e_var_adj*pf_set$gamma_rel]
  35    sd = sd(r)*sqrt(12),
  36    sr_gross = mean(r)/sd(r)*sqrt(12),
  38    r_tc = mean((r-tc))*12,
  39    sr = mean(r-tc)/sd(r)*sqrt(12),
  40    obj = (mean(r)-0.5*var(r)*pf_set$gamma_rel-mean(tc))*12
  ```
- 对照：作者档以 **gross** `r` 构造 `e_var_adj`、`utility_t`、`obj` 的方差项与 `sr`/`sr_gross` 的分母 `sd(r)`；论文式(11) 的方差项以 **net** 收益相对其全样本均值计算。净收益的均值/方差与毛收益不同，理论上影响 Utility 列与 `obj` 的排序与数值。
- 边界：发表版 Table 2 的 Utility/SR 列是否由该 `pf_summary` 直接打印，尚未取得打印时脚本与未舍入底稿；`7 - Tables.R` 的列名/舍入映射也未逐格核验。因此本条登记为 `PAPER_CODE_DIVERGENCE_DETECTED`，处置为 **不改作者代码、不回填目标值**；首跑固定作者线，随后以同一已生成预测和权重另算净方差线（协议 P002-E28 IMPLEMENTATION_AUDIT），逐格分解差异，再交主审裁定哪一口径为发表目标。

### I22｜财富递推 / AUM 路径（P002-I22）

- 论文正文 §5.1.3（第 1021–1028 行）："the investor wealth grows according to the realized market return, `w_t = w_{t-1}(1+R_{m,t})` ... This assumption means that the investor withdraws money when the portfolio has outperformed the market and vice versa when ... underperformed ... baseline ... $10 billion by 2020."
- 作者源码 `1 - Prepare Data.R:9–17`：
  ```
   9  wealth_func <- function(wealth_end, end, market, risk_free) {
  10    wealth <- risk_free[, .("eom_ret"=eom, rf)][market, on=.(eom_ret)][, tret := mkt_vw_exc+rf]
  11    wealth <- wealth[eom_ret <= end]
  12    wealth <- wealth[order(-eom_ret)][, wealth := cumprod(1-tret)*wealth_end]
  ...
  17  wealth <- wealth_func(wealth_end = pf_set$wealth, end = settings$split$test_end, ...)
  ```
  `pf_set$wealth=1e10`（`Main.R:133`），`settings$split$test_end=2020-12-31`（`Main.R:60`）。
- 对照：作者档从 2020 年末 wealth 反向 `cumprod(1−tret)`（按降序日期）生成路径，且 `tret = mkt_vw_exc + rf`；论文写的是正向递推 `w_t = w_{t−1}(1+R_{m,t})`，其中 `R_{m,t}` 的"已实现市场收益"口径未进一步拆成超额+RF。两条路径在时点标签、是否含末月、以及 RF 的处理上可能不同，需要以实际 `market_returns.csv` + `ff3_m.csv` 计算 AUM 路径比率才能判定影响成本与可实施前沿的程度。
- 边界：不把反向累乘直接判为"错误实现"——它在给定 `tret` 序列时数学上等价于某条正向路径，差别在 `mu_ld0` 的错位与 `tret` 定义。处置：原码首跑，另存 AUM 路径诊断（同输入下正向 vs 反向逐月比率）；若重训改变策略，另立 `APPROXIMATE_VALIDATION` 分支，不代入作者原跑结果。

### I23｜训练宇宙 vs 投资宇宙（P002-I23）

- 论文正文 §5（第 974–980 行）："We restrict our sample to common stocks (shrcd 10, 11, 12) traded on the New York Stock Exchange (NYSE; exchcd 1) ... our empirical analysis is better aligned with our theoretical analysis, which assumes a fixed set of stocks."
- 作者源码：
  - `Main.R:75` `nyse_stocks = T`（默认）；
  - `1 - Prepare Data.R:64–67`：`if (settings$screens$nyse_stocks) { ... chars <- chars[crsp_exchcd==1] }`；
  - `slurm_fit_models.R:6–7`（收益预测模型拟合的实际入口）：
    ```
     6  settings$screens$size_screen <- "all"
     7  settings$screens$nyse_stocks <- F # Also include non-NYSE stocks when fitting expected return models
    ```
- 对照：组合构建/投资池保留 NYSE 过滤，但 **收益预测模型的训练显式关闭 NYSE 过滤**（纳入非 NYSE）。论文的"restrict our sample to ... NYSE"一句未区分训练池与投资池，可能只指后者；作者源码的注释明确这是有意的训练设定，并非误配。
- 边界：在取得作者/主审对论文该句适用范围的书面确认前，不判定冲突。处置：冻结并登记 `train_universe = all CRSP (nyse_stocks=F)` 与 `invest_universe = NYSE common (nyse_stocks=T, above-median size)` 两套；如主审要求检查训练总体，做平行固定版本消融并单列结果，禁止静默修改作者开关。

### I24｜缺失值与筛选（P002-I24）

- 论文正文（第 981–993、1017–1020 行）：要求 me/return/dollar volume/SIC 非缺失，当前及过去 11 个月至少 50%（=57）的信号非缺失；连续 12 个月满足才纳入、连续 12 个月不满足才排除；缺失特征设 0.5。
- 作者源码 `1 - Prepare Data.R`：
  ```
  76   chars <- chars[!is.na(me)]
  79   chars <- chars[!is.na(tr_ld0) & !is.na(tr_ld1)]
  82   chars <- chars[!is.na(dolvol) & dolvol > 0]
  85   chars <- chars[!is.na(sic)]
  88–91 feat_available <- ... apply(... sum(!is.na(x)))
       min_feat <- floor(length(features)*settings$screens$feat_pct)   # =floor(115*0.5)=57
       chars <- chars[feat_available >= min_feat]
  112  chars[, (features) := lapply(.SD, function(x) if_else(is.na(x), 0.5, x)), ...]  # 缺失设 0.5
  137–141 lb <- pf_set$lb_hor+1  # 12；eom_lag:=shift(eom,n=lb); month_diff==lb 过滤
  146  size_screen_fun(type=settings$screens$size_screen)
  149  addition_deletion_fun(addition_n=12, deletion_n=12)
  ```
- 对照：源码与论文在 57 个特征门槛、0.5 缺失插补、12 个月连续资格上字面一致。需运行时审计的点：`tr_ld1`（t+1 收益）非缺失筛选实际上使用了"下一月是否可观测"信息，可能存在前视/退市选择效应；`1 - Prepare Data.R:39` 的 `long_horizon_ret(..., impute="zero")` 对 t+1..t+12 缺收益补零，与"剔除缺失"的交互须在真实面板上核对。
- 边界：本条为 `REQUIRES_RUNTIME_CHECK`，不是已确认的作者错误。处置：作者原码首跑；另出日历审计（t+1 缺失筛选的可用时点、退市收益、零填充占比），独立改动必须单列并标 `IMPLEMENTATION_AUDIT`。

### I25｜路径字面值（P002-I25）

- `1 - Prepare Data.R` 与配置中的路径字面值大小写/命名（如 `6 - RF Example.R` vs 仓库实存 `6 - RF example.R`，内部 `source("main.R")` vs 实存 `Main.R`）在 Linux 区分大小写环境下会失败。P002-E21 分析链跳过 RF 脚本，不阻塞 Table 2；附录 RF 目标须在定位后单列。状态：`PATH_ISSUE_DETECTED`，处置为运行前仅做不改变计算的文件路由补丁并记录 SHA256。

## 3. P002-E21（99 单元）状态与 E01/E21 关系

- P002-E21 的 99 个目标单元来自 `target_alignment.csv`（11 策略 × 9 指标，含 `P002-T02-*`，如 `...PFML-SRNET`、`...MARKOWITZ-SRGROSS`）与 reviewer_queue.json 的 `result_ids` 列表。本轮 **未运行任何单元**，全部 `NOT_RUN` / `NOT_ASSESSED`；审批字段 `PENDING_EVIDENCE`。状态保持 **`REQUEST_EVIDENCE`**（与 v2 protocol 一致），原因：D01–D03 `NOT_FOUND`、I21/I22 口径待运行时审计、R 环境与 HPC 配置未搭建。
- E01 与 E21 关系：
  - `P002-E01` 是早期宽口径条目（result_id `P002-R01`），scope = "RFS Table 2 baseline Portfolio-ML 优先"，入口 `Main.R; 5 - Base case.R; 6 - Base analysis.R; 7 - Tables.R`。
  - `P002-E21` 是精化条目，scope = "RFS Table 2, 11 strategies, 1981–2020, NYSE core"，入口 `slurm_fit_models.R → slurm_build_portfolios.R → 6 - Base analysis.R → 7 - Tables.R L25–47`，并把 99 个单元格拆成稳定 `P002-T02-*` ID。
  - 两者针对 **同一篇论文的同一张 Table 2**，E21 是 E01 的细化/扩展（E01 的 Portfolio-ML 基线单元是 E21 的子集）。**建议**：将 E01 标记为 E21 的历史别名并合并追踪（保留 `P002-R01` 作为血缘 ID），正式送审与验收只保留 E21 的 99 单元；E28 净方差审计作为 E21 的平行分支。该合并需主审确认，本 agent 不改主档。
- 任何数值声明必须先解决 D01–D03 访问，再在冻结快照上按协议跑作者线 + 审计线；本文件不提供任何"接近论文即通过"的容差放宽依据。

## 4. 本轮状态枚举

| 项 | 状态 |
|---|---|
| D01/D02/D03 公开入口 | `NOT_FOUND` |
| D07 Ken French FF3 | `SAMPLE_ACCESSED`（`APPROXIMATE_VALIDATION` 代理） |
| I21/I22/I23/I24 静态核对 | `DONE`（差异登记，非错误判定） |
| P002-E21 正式目标（99 单元） | `NOT_RUN` / `REQUEST_EVIDENCE` |
| P002-E28 净方差审计 | `NOT_RUN`（待 E21 冻结输入后平行执行） |
| R 运行时验证、真实回测 | `NOT_RUN` |
