# P010 TRACE 近似验证协议（与 ICE 路线严格分离）

- 批次 CO-REP-20261120-02；论文 JF 78(4):1967–2008，DOI 10.1111/jofi.13233。
- 执行日期 2026-11-21。本文件只注册 TRACE 路线协议与验收量，**未运行任何 IPCA/组合/成本计算**，全部 `NOT_RUN`。
- 顶层原则：**ICE 与 TRACE 是两条独立路线，不得混用**。ICE 忠实路线需原研究成员的 ICE 快照（P010-B01，仍 `ENTITLEMENT_UNCONFIRMED`）；TRACE 路线用作者公开 "Reconciling TRACE bond returns" 归档，恒为 `APPROXIMATE_VALIDATION`，**不宣称原文 ICE 数值**。

## 1. 为什么 TRACE 是近似验证而非忠实复现

- 原文表 I–IX 基于 ICE（DtS 缩放的债券超额收益、OAS 等字段）。"Reconciling TRACE bond returns" 明确指出 TRACE 收益与 ICE 意义不同，核心结论用 WRDS/TRACE 稳健。因此 TRACE 可检验**方法方向与量级**，不能核对 ICE 表格的精确单元格。
- `JF2_pubdata.m` 自注：公开 `corp_jkp_mergedv2.csv` 的 spread 等字段**并非 OAS**；`code_audit.md` 记载的 `zeroedoutdata.mat` 是全零占位，禁止当真实输入。
- 严禁用**不同 ICE 样本表格的数值**判定 TRACE 成败；TRACE 的验收对象是本身快照上跑出的方向/单调性/量级，不是与 ICE 表的逐格匹配。

## 2. 输入快照（TRACE，已实取并核验）

| 项 | 值 |
|---|---|
| 来源 | `https://www.dropbox.com/sh/16uqp1ab73gxqnn/AABm0Da-0ezo9TgR0_g8bEc-a?dl=1`（作者 research 页直链） |
| 本地 | `data/trace_public_archive.zip`，491,720,701 B |
| 归档 SHA-256 | `681725ee28b9773f859116fb523b1550d88db9485e0a993d5ba47576cfca5991`（与 v2 一致） |
| 主输入 | `JF2_pubdata.mat` 75,116,003 B / `e4cb674cda3ec61110f1cf0541cbde588e52ea20dd8af9deb1adf94dc621cea4` |
| 面板形状 | EXCESS_RETURN / TOTAL_RETURN / VOL / NONMISSING_OBS / DTS 均 206×8759；CHARS 206×30×8759；T=206 月，N=8759 ISIN，唯一债券 6,507，非缺失收益观测 262,649 |
| 收益月范围 | 2003-08-31 至 2020-09-30（归档内 `first_last_return_month`；不同于公开脚本模板的 1999-01-31 起） |
| 特征 | 30 个 charcell（29 特征+常数），含 `unique_charnames`、`charcell`；缺失计数见 v2 `input_audit.json` 的 `trace_csv_feature_missing_counts` |
| 配套估计 | `JF2_pubdata_DTSScaled25_IPCA_IS_Estimates_K5.mat` 4,912,983 B / `109a00ca...e68`（样本内 K5，可作 warm start/结构核对，不直接当 TRACE 运行结果） |
| 原始表 | `corp_jkp_mergedv2.csv` 349,327,084 B / `4d7b60b2...db906`，483,888 行；200207–202009 月；`nextretexcwins` 为 chosenretname |
| 状态 | `SNAPSHOT_VERIFIED`；用作 `APPROXIMATE_VALIDATION` 输入 |

## 3. 成本、样本与会计（照作者源码/论文 Eq.12–14）

- 交易成本：`tcost = 0.00189`（Table_8.m，即论文 19bps 单边；readme Appendix A.IV 0.0019，Internet Appendix IA.IV 0.0025/0.0010/0.0040 为替代场景）。净收益 `= Σ w_i,t r_i,t+1 − 19bps × Σ |w_i,t − w_i,t−1|`；换手 Turnover=`(1/T)Σ[Σ|Δw|]/[Σ|w_{t−1}|]`；平滑 `w̃=(1−γ)w+γw̃_{t−1}`、`w̃0=w1`。成本用绝对权重变化×费率；**净 Sharpe 分母用扣成本前的毛收益样本波动、年化 sqrt(12)**，不得用净波动。
- 样本：TRACE 面板自身 2003-08…2020-09；`JF2_pubdata.m` 模板 `startdate/enddate` 与 `nextretexcwins`（winsorized 下一期超额收益，`next` 不能改，保证滞后时点）；Ks=1..5、主 K=5；扩张窗 OOS 首个评估为起点后 36 月；ALS `MaxIterations=2000`、`Tolerance=1e-4`、warm start。
- 信息时点：`β_it=z_it Γ_β` 用 t 时特征；`f̂_{t+1}` 用 t+1 实现收益的截面回归（估计步骤，非可交易信号）；组合权重用截至 t 的因子均值/协方差；无执行成本以外的市场冲击/融资融券模型。

## 4. 结果 ID 与验收量（TRACE 近似验证口径）

| 结果 ID | 论文目标（仅供方向对照） | TRACE 验收量（本路线自身） | 判定 |
|---|---|---|---|
| `P010-R06` | Table VII 切线/价差毛 Sharpe 随 K 单调上升（K=5 切线 6.23、价差 3.53） | TRACE 面板上重算 K=1..5 的 OOS 切线/价差毛 Sharpe；验收**随 K 单调方向与量级**，不要求 6.23/3.53 | `APPROXIMATE_VALIDATION` |
| `P010-R07` | Table VIII 19bps 后净 Sharpe（γ=0 净 2.48/1.37；γ=0.3 净 2.93/1.47；换手随 γ 单调下降） | TRACE 面板上用 0.00189 成本与式 12–14，验收 γ 网格下**换手随 γ 单调下降、净 Sharpe 与毛 Sharpe 的方向和相对量级**；不要求精确 2.48/1.37/2.93/1.47；γ=.3 与 .4 都可显示最优，不设唯一 γ | `APPROXIMATE_VALIDATION` |
| `P010-R03/R04`（可选方向检查） | OOS/基准 R² 优势 | 仅方向：IPCA 相对 MKT/BBW/FF 的优势方向；不逐格比 ICE 表 | `APPROXIMATE_VALIDATION` |

验收细节：结果按发表位数显示，但 TRACE 与 ICE 样本不同，只核方向与量级；如需数值区间，先在主审审批中冻结 TRACE 自身的容差，**不得借用 ICE 表容差**。任何数值、t 统计、R² 当前 `NOT_RUN`/`NOT_ASSESSED`。

## 5. 执行边界与状态

- 本轮不运行 IPCA/组合/成本（既无 ICE 也无运行审批）；作者 MATLAB 代码已取得并静态核验（`code_audit.md`），运行环境/MATLAB 版本未锁定。
- TRACE 作者改编路线与独立实现路线都标 `APPROXIMATE_VALIDATION`；ICE 忠实路线（AUTHOR_CODE_RERUN / INDEPENDENT_FAITHFUL）因 ICE 快照不可得仍 `BLOCKED`。
- 所有结果 `NOT_RUN`，主审 `PENDING`。不得把 `zeroedoutdata.mat` 的清零占位当真实输入，不得用不同 ICE 样本表格数值判 TRACE 成败。
