# P001 有限理论核对与条件实证协议

**执行单位** P001-E01 × JF 2013 68(6):2309–2340（DOI 10.1111/jofi.12080）+ 官方 A15* 勘误 × P001-R01/R02/R03/R09。版本锁定使用作者托管正式版及附件中的一页勘误。已独立访问 AFA 官方 PDF，核对 A15* 及可交换条件，未取得官方 URL 本地二进制来验证和附件逐字节相同。两个本地证据页及 SHA-256 见 sources。用户来件第四节直接授权有限理论核对，未提供独立编号。结果审批保持 PENDING。

## 已执行

| 结果 ID | 正式版定位 | 复核结果 |
| --- | --- | --- |
| P001-R01 | Fig. 1 Panels A–C（p.2311），Eqs. 7–13，§III | 脚注 9 条件下 \(a=0.7421582911\)，部分调仓率 \(a/\lambda=0.3710791456\)，Markowitz 初始持仓 (2, 2)，aim 初始持仓 (1.7415054572, 1.2549203601)。确定性闭式与 Bellman 最优首仓最大差 \(1.67\times10^{-16}\) 合约；无限加权形式用 160 项近似核对，最大差 \(1.33\times10^{-15}\) 合约。 |
| P001-R02 | 同一 Fig. 1，Prop. 4，Eq. 14 与 Appendix A34 | 慢信号相对 Markowitz 保留 87.0753%，快信号保留 62.7460%，满足理论方向。 |
| P001-R03 | Fig. 2 Panels A–C（p.2322），Eqs. 18–21（pp.2320–2321），Appendix A37–A55 | 脚注 9 已披露的理论条件下，另选零初始旧仓。临时冲击份额 1、0.5、0 的首笔交易欧氏范数为 0.796539、0.955134、1.551842 合约。Bellman 对照独立组装的 160 期直接二次优化，前 30 期最大仓位差分别为 \(4.44\times10^{-16},4.89\times10^{-14},2.47\times10^{-12}\) 合约。三组 Bellman 绝对 Frobenius 残差均不超过 \(7.74\times10^{-15}\)，时序闭环谱半径均小于 1。实际只验收有限理论数值和方向。 |
| P001-R09 | Eq. 9／A24–A25，Appendix A7/A10/A14/A15（pp.2333–2335），AFA A15* | 标量 \(a\Sigma\) 对矩阵 \(A_{xx}\) 最大元素差 \(1.11\times10^{-16}\)。两个可交换用例的旧式与更正式都一致。研究者非交换用例，交换子 Frobenius 范数 1.6122，更正 A15* 代回 A7 相对残差 \(4.88\times10^{-16}\)，旧式残差 0.0289456。非交换案例无论文图的市场估计含义。 |

**量纲与时序** \(x_t\) 是证券或期货合约数量；\(r_{t+1}=\Delta p_{t+1}-r^f p_t\) 在正式版 §II 是每单位证券的超额价格变化。\(x_t^\top r_{t+1}\) 是货币盈亏；\(\Sigma\) 是单期价格变化风险，\(\Delta x_t^\top\Lambda\Delta x_t/2\) 为货币成本。没有换算成资金权重或百分比收益。观察 \(f_t\) 和当期价格冲击状态 \(D_t\) 后选择 \(x_t\)，持有至 \(t+1\)。本轮只有确定性的理论条件期望路径，无历史样本、训练、种子或数据订阅。

**复跑** 在本目录执行 OPENBLAS_NUM_THREADS=1 python run.py。配置 config.json，预设条件 predeclared_checks.md，环境 environment.json，完整输出 results.json 与 trajectories.csv。执行后检查 stdout.log 的九项 True，stderr.log 为空；未使用缓存、外部数据或作者代码。固定输入与软件版本由 environment.json、manifest.sha256 记录。

**持久冲击与初次失败** 直接把 Eq. 19 的当期效用配零终值做有限期递推时，纯持久分支初次求解的动作步不满足所用正定求解器要求。初次日志 attempt_01_stderr.log 保留，并将环境专有路径缩写。修订只处理终端记账。以 \(W=x_{t-1}^{\top}D_t\)，从即时目标移除 \(\beta W_{t+1}-W_t\)，其中 \(\beta=1-\rho\)，\(\beta(1+r^f)=1\)。根据 Eq. 18/19，持久冲击部分化简为 \(-\Delta x_t^\top D_t-\Delta x_t^\top C\Delta x_t/2\)。在稳定路径上 \(\lim_{T\rightarrow\infty}\beta^T W_T=0\)，所以修订不改变无限期最优策略，有限期直接优化显式施加同一终端记账；容差、参数和比较项目保持预设值。通过状态迭代与独立整段开环二次求解交叉检验。

**自行选择** 零初始旧仓、轨迹 30 期、直接求解时域 160 期、两个额外矩阵用例及数值精度阈值。原图精确坐标和未披露旧仓、绘图期数不纳入数值验收。理论机制在上述限定范围 PASS；实盘经济结果 NOT_ASSESSED。

## 尚未执行

P001-E02，P001-R04–R08，INDEPENDENT_FAITHFUL 条件下的正式版市场数据复现。VoR Table I p.2326，Table II p.2330，Fig. 3 p.2330（原油与黄金头寸），Fig. 4 p.2331（信号冲击）。VoR 没有 Fig. 5。NBER 工作稿旧 Fig. 3–5 映射到 VoR Fig. 2–4。期货数据需要 15 个品种的 1996-01-01 至 2009-01-23 合约级每日价格、成交量与合约乘数，含用于 5 年信号的早期历史、同合约价格变化和逐日最流动合约识别。附件中 Table I/II 只提供描述值。LME 官方历史价格与成交量数据为购买产品，且其当代 closing price 不能与原文历史口径自动等同；CME 官方历史结算入口 DataMine，ICE 对 NYBOT/ICE 品种的历史持有集合和口径仍待确认。已定位渠道，数据权属为 ENTITLEMENT_UNCONFIRMED。尚无研究团队原始逐日面板。

按 §VI 先核对 Table I、各价格变化、滚动信号、FGLS 系数、50% 协方差收缩、低成本 \(\lambda=5.0\times10^{-7}\) 和高成本 \(\lambda=10^{-6}\)，再复算 Table II 的 Markowitz、Dynamic 与逐档 Static 策略。使用作者论文报告 λ 属条件限定的派生输入，不算重做 2010 年 Reuters 成交量校准链。保留原论文样本内参数估计和原换月成本假设。Table II 每格按显示到两位小数，预设绝对误差上限 0.005；图形先锁定可获得的原始比较数据再设容差。审计 P001-E03 含改用滚动样本外估计或不同成本的工作另列，当前 NOT_RUN。

## 来源定位

- 正式版作者链接 https://pages.stern.nyu.edu/~lpederse/papers/DynamicTrading.pdf
- AFA 官方勘误 https://afajof.org/wp-content/uploads/Corrigendum_DynamicTrading.pdf
- LME 历史产品 https://www.lme.com/en/market-data/accessing-market-data/historical-data
- CME 结算与 DataMine https://www.cmegroup.com/market-data/daily-settlements.html
- 原包旧文件 P001_accepted_manuscript.pdf 经 file 和 HTML title 实查是拦截页，不进入 PDF 来源清单；原 zip 保留原样。
