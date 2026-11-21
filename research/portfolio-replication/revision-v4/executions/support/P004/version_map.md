# P004 版本映射与梯度预检补证

- 批次 CO-REP-20261120-02；论文 *Distributionally robust end-to-end portfolio construction*，DOI 10.1080/14697688.2023.2236148。
- 执行日期 2026-11-21。本轮补交版本映射、DGP/窗口/初始化证据与实测梯度预检；**Table 11/Figure 7 正式目标仍 `NOT_RUN`，经济结论 `NOT_ASSESSED`**。
- 作者代码冻结：`/CO-REP-20261120-02/execution/P004_repo/`，commit `b5e299ad7748468bc39e3e711eceee809143c648`（2023-04-15），ZIP 12,459,740 B / SHA256 `b9c88d7f05238e2a1485372474b5b23f8d1fd632acceccb5a8731d5aa1fc6573`（v2 已取）。

## 1. 版本统一映射（QF 正式版候选 / arXiv v1 / 代码快照 / R05-R06）

| 版本 ID | 实体 | 关键事实 | 本轮处置 |
|---|---|---|---|
| `QF2023_VOR_CANDIDATE` | 正式出版版候选 | Quantitative Finance 23(10):1465–1482，2023-08-08 在线，DOI 10.1080/14697688.2023.2236148；publisher full/PDF 请求 403，合成实验正文/附录/minor procedural correction `NOT_READ` | `selected_paper_version`（record_master），**不对刊物版目标做推定** |
| `ARXIV_V1_2022` | arXiv v1 工作稿 | 2022-06-10 提交，PDF 首页 2022-06-13，SHA256 `00d8b080068e305742dc4f3ed93e6fa6999cf858967734b0fec7667ae2ff2fb1`；§2/§3.3、Table 10/11、Figure 7、Appendix E/F、Table 13 已核 | 数值目标（Table 11/Fig 7）的**当前可读来源**；不等于 QF 正式版 |
| `E2EDRO_SNAPSHOT_b5e299a` | 作者代码快照 | commit `b5e299ad...`，根 `main.py`/`e2edro/`/`cache/`，Apache-2.0；README 链 arXiv | 梯度预检实际调用对象；不改算法 |
| `P004-R05` | 结果 ID（Exp4 Table 9 Learning θ） | reviewer_queue：Table 9 四系统 PO 0.88/Base 0.64/Nominal 1.21/DR 1.21；固定 γ,δ、学习 θ；target scope 中 Exp2/3/4 为"随后" | `NOT_RUN`；版本归属（QF vs v1）未锁定 |
| `P004-R06` | 结果 ID（Exp5 合成 Table 11/Fig 7） | record_master `preliminary_result_values`：Exp5 synthetic Sharpe Linear DR 1.88 vs Nom 1.16；2-layer 0.73 vs 0.21；3-layer 2.11 vs 0.08 | `NOT_RUN`；本轮只做梯度结构预检，不触及该目标 |

**映射判定**：R05（Exp4/Table 9）与 R06（Exp5/Table 11/Fig 7）都是作者代码快照可定位的实验，但**正式 QF 版是否与 arXiv v1 的编号/数值一致尚未核验**（v2 protocol I02/I03/I04 开放）。因此 R05/R06 当前只能标"按作者快照计算"的待测目标，不能记为匹配正式版。主审须裁定：优先按公开 commit 复跑并报差异，还是另设按论文规范的独立实现。

## 2. DGP / 窗口长度 / 初始化（真实源码证据）

来源：`e2edro/DataLoad.py:233–260`、`e2edro/PortfolioClasses.py:15–50`、`e2edro/e2edro.py:269–385`、`main.py:478–625`；实测见 `results/gradient_preflight.json`。

- **DGP**：`synthetic_exp(n_x=5,n_y=10,n_tot=1200,n_obs=100,split=[0.7,0.3])`，seed 123。特征 `clip(N(0,1),-3,3)/10`（按行独立抽样，无累积）；`alpha=sort(rand(n_y).clip(0.2,1)/1000)`；`beta=randn(n_x,n_y).clip(-3,3)/n_x`；`Y=(alpha+X@beta+exp_noise+gauss_noise).clip(-0.2,0.3)/15`，其中 exp_noise 为 `0.2*choice([-1,0,1],p=[.15,.7,.15])*exponential(1)` 并 clip 到 [-0.3,0.3]，gauss_noise 为 `0.2*randn`。**源码 DGP 与论文 §3.3 的"独立 Brownian 特征"描述不一致**（P004-V2-I02 开放），精确采用源码并登记，不互相替代。实测 X_train/Y_train 均 840×5 / 840×10。
- **窗口长度 perf_period**：`main.py:502 perf_period=13`；`SlidingWindow.__getitem__:46` 用 `Y[index+n_obs : index+n_obs+perf_period+1]`，故首个训练窗 `y_perf` 实测 **14×10**（13 参数 +1 的切片端点）；训练窗 x 101×5、y 100×10，总窗数 727。保留源码切片，**禁止静默改成 13**。论文 §3.1 的"13 条绩效期（v=12）"与源码 14 行未来收益是 I03 开放差异，正式版意图未定。
- **初始化**：主脚本 seed 2000/3000/4000；CPU RNG。实测 γ 初值 linear/2layer/3layer = 0.024194/0.081052/0.072181，δ 初值 = 0.099247/0.358408/0.163173，与 v2 记录一致。DR 构造时先取一次 δ 再构造 θ（与 Nom 同 seed 但 θ 初值不同）；线性 θ 在 train/CV 被作者改成 OLS（配对裸 θ 差归零），NN 组仍有初始化差。不能把同 seed 当配对 θ 完全相同。
- **模型/求解**：loss `(1/n_train)*(sharpe_loss(z,y_perf)+(pred_loss_factor/n_y)*MSE(y_hat,y_perf[0]))`，`pred_loss_factor=0.5`；Adam lr 0.005/0.0125/0.02、epochs 20/40/60；ECOS `max_iters=120, abstol=1e-7`；γ/δ 更新后 clamp≥1e-4。本预检只用 lr=0.005、1 个 batch、1 epoch。

## 3. 最小合成数据梯度预检（本次实跑）

- 脚本：`code/gradient_preflight.py`；输出：`results/gradient_preflight.json`；日志：`logs/gradient_preflight.stdout.log`、`logs/gradient_preflight.stderr.log`（stderr 空）。
- 环境：Python 3.13.12 / torch 2.15.0 / numpy 2.5.5（p004_venv；为导入作者模块补装 `pandas_datareader`/`alpha_vantage`/`statsmodels`/`psutil`，未改算法）。首次运行因缺 `pandas_datareader` 失败（错误见 `logs/gradient_preflight.stderr.log` 的历史说明），安装依赖后成功。
- 方法：直接调用作者 `e2e_net`，对六个 Exp5 配置（Nom/DR × linear/2layer/3layer）各取第一个训练窗，做一次 forward→backward→Adam step；**未读 `cache/exp5/*.pkl` 或任何作者已训练模型/回测**；未跑 CV/roll_test。
- 结果（六项全 PASS）：
  - 形状：x 101×5、y 100×10、y_perf 14×10，与源码一致。
  - 权重和：六项 `|Σz−1|` 在 3.4e-11 ~ 9.6e-10；最小权重均 > −1e-6（实际为 1e-12~1e-10 的正值，无显著负权重）。
  - 梯度：六项全部有限（`all_grads_finite=True`）；更新 L2 非零（0.005~0.035 量级）。
  - 说明：2layer/3layer 的 γ（及 DR 的 δ）在本轮首窗回传中为 0 或近 0，属首窗特定初值下的现象，不外推到完整训练；本预检仅验证可微通路存在且无 NaN。
- **目标状态**：Table 11 / Figure 7 / Appendix F 仍 `NOT_RUN`；预检不构成论文数值或经济结论证据。

## 4. 状态枚举

| 项 | 状态 |
|---|---|
| 版本映射（QF v1 代码 R05/R06） | `MAPPED_UNVERIFIED`（QF 版编号待核） |
| DGP / 窗口 / 初始化证据 | `DOCUMENTED`（源码逐行 + 实测） |
| 最小合成梯度预检 | `PASS`（结构，非论文数值） |
| Table 11 / Fig 7 / Appendix F | `NOT_RUN` |
| 经济结论 | `NOT_ASSESSED` |
| 送审结论 | `REQUEST_EVIDENCE`（v2 一致） |
