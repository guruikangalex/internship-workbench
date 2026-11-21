# P010 官方 MATLAB 代码包审计（AUTHOR_CODE，下载+核验，未运行）

- 批次 CO-REP-20261120-02；论文 JF 78(4):1967–2008，DOI 10.1111/jofi.13233。
- 执行日期 2026-11-21。本文件只做**下载、hash/成员核验与入口静态阅读**；未运行任何 MATLAB，未生成任何表格值，全部目标 `NOT_RUN`。
- 入口页：`https://sethpruitt.net/research`（本轮实取 57,563 B，存档于 `data/sethpruitt_research.html`），"Modeling Corporate Bond Returns" 与 "Reconciling TRACE bond returns" 两节分别给出两个公开 Dropbox 文件夹直链；与 v2 S16/S17 记录一致。

## 1. 官方 ICE 代码包（AUTHOR，非 TRACE）

- 下载：`https://www.dropbox.com/sh/4yu0xsopnnre571/AAAieXICkt2_iaoWEwNBkXfEa?dl=1`（research 页 "Code and Data"）。实取 `data/official_code_archive.zip`，HTTP 200，955,004,837 B，`application/zip`。
- **归档 SHA-256 `43bf7bcd3869ab3a71e1c5c971d8d54136e4aa736158f2cf20f443080169bb09`，与 v2 `input_audit.json` 的 `official_archive_sha256` 逐字节相同**。ZIP 成员数（含根）64，与 v2 `official_member_count_including_root` 一致。
- 关键成员 hash 本轮独立重算，全部与 v2 `official_key_members` 一致（`results/official_member_hash.json`）：
  - `readme_public.docx` 5,494,154 B / `1bb71ab6...28308`
  - `zeroedoutdata.mat` 949,310,374 B / `8bb6c629...3d780`
  - `Table_3.m` 18,663 B / `fe3460fe...088b`
  - `Table_4.m` 20,068 B / `180c993a...6465`
  - `Table_8.m` 5,016 B / `83961cea...6502e`
  - `JF2_pubdata.m` 11,064 B / `1a574987...82ccbe6`
  - 其余 `JF2_scaling_choices.m`/`num_IPCA_estimate_ALS.m`/`tanptfnext.m`/`JF2_turnover_calcs.m`/`JF2_zeroedout_aqrdata.m`/`cssort_sp.m` 均一致。
- `zeroedoutdata.mat` 头：`MATLAB 7.3 MAT-file, Platform: PCWIN64, Created on: Mon Mar 28 11:57:07 2022 HDF5 schema 1.00`。**按 readme_public.docx 的 PRELIMINARIES/OTHER NOTES，该 MAT 把 DATA 非缺失项全部置零，随机值仅用于演示；原 ICE 数据 `JF2_aqr_0.mat` 等未释放。严禁用它当真实 ICE 输入。**
- 出版商 Wiley SI ZIP（63.2 MB）本轮仍 403 未取，不能声称与 Dropbox 归档逐字节相同（v2 S16/S21 一致）。

## 2. 入口脚本静态阅读（与结果映射）

| 入口 | 规格（源码字面） | 对应论文目标 |
|---|---|---|
| `Table_3.m` | `dataname='JF2_pubdata'`、`scaling_choice='DTSScaled25'`、`Krange=2`、`use_obs_factor=false`；样本内 IPCA 估计/报告；调用 `JF2_scaling_choices.m` | Table III（R02，样本内 R²/定价误差）；K=2 默认与论文 K=1:5 需改 |
| `Table_4.m` | `Krange=1:5`、`use_obs_factor=true`、`obs_factor_choice_name='Comp'`；报告列含 `Tan_Net_SR/Spd_Net_SR/Tan_Turnover/Spd_Turnover`；调用 `JF2_turnover_calcs.m` | Table IV（R03，OOS R²）与 Table VII 毛利路径来源；作者默认 `JF2_pubdata` 非 ICE，需按 readme 改用 ICE 输入、`use_obs_factor=false`、`Krange=1:5` 并保存 K5（v2 S18） |
| `Table_8.m` | `tcost=0.00189`（19bps）、`estimatename='IPCA_OOS_Estimates_K2'`、`EWMAgammas=0:0.1:0.9`；调用 `JF2_turnover_calcs.m`，报告 Turnover / Gross Sharpe / Net Sharpe | Table VIII（R07，净收益+成本/换手）；K2→K5 需改，γ=.3/.4 都显示 2.93/1.47，不能强设唯一 γ=.3（v2 S19） |
| `JF2_pubdata.m` | 读 `corp_jkp_mergedv2.csv`、`chosenretname='nextretexcwins'`、`totalretname='nextretwins'`、`startdate='31-Jan-1999'`、`enddate='31-Dec-2020'`；`sampleperiod` 显式过滤并重写 CHARS/EXCESS_RETURN/TOTAL_RETURN/DTS/VOL/NONMISSING_OBS | 公开 TRACE 派生输入（**APPROXIMATE_VALIDATION**）；脚本自注 spread 等并非 OAS，不等于 ICE 输入 |

- 成本口径（源码+论文）：`tcost=0.00189` 即 Eq.12 的 19bps 单边；`JF2_turnover_calcs.m` 成本 = 绝对权重变化 × 成本率；净 Sharpe 分母用扣成本前毛收益的样本波动，年化 `sqrt(12)`，**不得自行改用净波动**（v2 S19）。
- ALS 停止规则（v2 S18）：初次 SVD，后续 warm start，`MaxIterations=2000`，`Tolerance=1e-4`，新旧 Γ/F 最大绝对差；`num_IPCA_estimate_ALS.m` 做 Cholesky/SVD 旋转与符号识别。

## 3. TRACE 公开数据归档（与 ICE 分离，仅作近似验证输入）

- 下载：`https://www.dropbox.com/sh/16uqp1ab73gxqnn/AABm0Da-0ezo9TgR0_g8bEc-a?dl=1`（research 页 "Reconciling TRACE bond returns → Publicly available data"）。实取 `data/trace_public_archive.zip`，HTTP 200，491,720,701 B。
- **SHA-256 `681725ee28b9773f859116fb523b1550d88db9485e0a993d5ba47576cfca5991`，与 v2 `trace_archive_sha256` 一致**；6 个成员 hash 重算一致（`results/trace_member_hash.json`）：`JF2_pubdata.mat` 75,116,003 B / `e4cb674c...1cea4`（CHARS 206×30×8759、EXCESS_RETURN 206×8759 等，首末收益月 2003-08-31…2020-09-30，非缺失观测 262,649，有效债券 6,507），`corp_jkp_mergedv2.csv` 349,327,084 B / `4d7b60b2...db906`，`readme.docx` 等。
- 该归档是**已准备的 TRACE 数据**，不含作者 ICE `JF2_aqr_0.mat`；任何 ICE 表格数值不得用于判定 TRACE 路线成败（见 `trace_protocol.md`）。

## 4. 状态枚举

| 项 | 状态 |
|---|---|
| 官方代码包下载 + 归档/成员 hash | `VERIFIED_MATCH_V2` |
| 关键入口阅读（Table_3/4/8、JF2_pubdata） | `DONE_STATIC` |
| `zeroedoutdata.mat` 作为真实 ICE 输入 | `FORBIDDEN_PLACEHOLDER` |
| TRACE 公开归档下载 + hash | `VERIFIED_MATCH_V2` |
| MATLAB 运行 / 任何目标值 | `NOT_RUN` / `NOT_ASSESSED` |
