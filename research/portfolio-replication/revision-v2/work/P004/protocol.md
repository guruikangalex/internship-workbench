# P004 合成实验修订协议与实际预检

## 送审结论

已固定作者仓库 commit `b5e299ad7748468bc39e3e711eceee809143c648`，实取源码 ZIP 12,459,740 字节，SHA-256 `b9c88d7f05238e2a1485372474b5b23f8d1fd632acceccb5a8731d5aa1fc6573`。六个作者模型均以同一份代码合成数据从初始权重完成一次可微优化、反传和 Adam 更新，未读取作者已训练模型、回测或图形。**预检通过，Table 11、Figure 7 与 Appendix F 正式目标仍为 NOT_RUN；建议 REQUEST_EVIDENCE。** 开放日程主要取决于工作稿与实际源码的可观察冲突及 QF 版目标尚未锁定。

## 版本和实现证据

| evidence_id | 证据位置 | 文件与版本 | 核对结果 |
|---|---|---|---|
| P004-V2-S01 | [QF 出版者](https://www.tandfonline.com/doi/full/10.1080/14697688.2023.2236148) | 2023-08-08 线上，23(10):1465–1482，DOI 10.1080/14697688.2023.2236148 | 作者栏 Costa=Millennium Management，数据声明可读；publisher full/PDF 请求 403，合成实验、附录、minor procedural correction 正文 NOT_READ，不对刊物版目标做推定 |
| P004-V2-S02 | [arXiv v1 PDF](https://arxiv.org/pdf/2206.05134v1) | 2022-06-10 提交，PDF 首页 2022-06-13；SHA-256 `00d8b080068e305742dc4f3ed93e6fa6999cf858967734b0fec7667ae2ff2fb1` | §2、§3.3、Table 10、11、Figure 7、Appendix E/F 与 Table 13 已核 |
| P004-V2-S03 | [作者固定 commit](https://github.com/Iyengar-Lab/E2E-DRO/tree/b5e299ad7748468bc39e3e711eceee809143c648)／[下载](https://codeload.github.com/Iyengar-Lab/E2E-DRO/zip/b5e299ad7748468bc39e3e711eceee809143c648) | 根目录 `main.py`、`e2edro/`、`cache/`，Apache-2.0 适用于作者代码 | root `main.py` 的 Exp5 区块 L474 起；不存在 `Journal/main.py`。README 链接 arXiv |
| P004-V2-S04 | 同一 commit 的 `DataLoad.py:233–259,303–358`、`PortfolioClasses.py:15–47`、`e2edro.py:273–430,524–721` | 源码与 DGP、训练窗、最优化层、CV、滚动测试 | 精确数据形状、种子及版本冲突见下 |
| P004-V2-S05 | 仓库缓存文件 `cache/asset_weekly.pkl` 和 `cache/factor_weekly.pkl` | 1135×20 与 1135×8，2000-01-07…2021-10-01 同一周五索引；SHA-256 依次 `c59cc048bc52dc05c4b9b8aadd920ad824c3adbd42f4a7b020a0ad2d100a6d8f`、`2ae7e1dc571fd3cf32c1ad67a55a55ed6007b682b87861b0074355177ecdfaba` | 缓存字节已取得；只读 pickle 指令检查静态矩阵与索引，未执行反序列化，也未开始历史拟合 |
| P004-V2-S06 | `preflight.py`、`preflight_output.json` 与日志 | 仅诊断，代码首次编排为本轮运行 | P004-PF01 已运行，P004-E02/R06 完整目标未运行 |

## arXiv v1、正式版与代码逐项对齐

| 对齐项 | arXiv v1 原文 | 作者源码与本次确认 | QF 2023 状态和处置 |
|---|---|---|---|
| 数据与分割 | §3.3 1200 期，5 特征/10 资产，840/360；训练内单折 | `synthetic_exp` 用 NumPy seed 123；原作者 CV 单折内部 672/168，测试含 100 预热但实际 360 次持有；历史数据无关 | QF 相同实验样本 NOT_READ；不自动映射 |
| 生成分布 | §3.3 描述零均值独立 Brownian 特征及线性收益＋高斯＋指数跳跃，文中列分布参数 | 源码特征 `clip(N(0,1),-3,3)/10` 按行独立直接抽样，无累积；alpha 排序且 `clip(U,0.2,1)/1000`，beta 做固定截断与缩放，高斯噪声与带符号指数噪声再整体 clip 并除 15；精确采用源码并登记 DGP 不是逐字按论文实现 | P004-V2-I02 开放。源代码分布和论文描述不得互相替代 |
| 残差和损失窗 | T=100，§3.1 描述 13 条绩效期（v=12），MSE 权重 0.5，损失给风险和收益端 | `perf_period=13` 但 `SlidingWindow` 的 Python 末索引含额外 `+1`，实测训练早期 y_perf 是 14×10；`sharpe_loss` 对全部条目计算。训练窗长度 559，最后边界切片可能为 13。保留源码作为作者快照证据，禁止静默改切片 | P004-V2-I03 开放 |
| 初始化 | §3.3 三种预测层均随机；Table 10 同架构 Nom. 与 DR 的 θ 初始相同。线性 γ .089、DR δ .146；2 层 .081/.358；3 层 .072/.163 | 主脚本使用 2000/3000/4000，torch CPU RNG；网络构造 DR 在构造 θ 之前多取一次 δ。预检配对裸 θ 的 L2 差分别 2.97458/4.41268/4.74385。轮到 train/CV 时作者源码把线性 θ 改为 OLS，因此该组初始化 θ 差为 0，两个 NN 组差异仍在。实测 γ/δ 分别 .024194/.099247、.081052/.358408、.072181/.163173。不能把同 seed 当作配对 θ 完全相同 | P004-V2-I04 开放。线性初值亦无法匹配 v1 Table 10 的显示舍入 |
| 训练与模型 | 相同资产、相同数据下以线性、两/三隐藏层比较 Nom. 与 DR，学 γ、δ、θ | 源 `net_cv` 一次时序折，学习率 .005/.0125/.02，epochs 20/40/60，验证选最小 loss，重新拟合所有 840 期，`net_roll_test(...n_roll=1)`；PyTorch Adam，每 epoch 汇总每个输入窗梯度后一步更新；γ、δ 更新后 clamp 到至少 .0001；`net_cv/net_roll_test` 临时存取本次新初始化 state_dict，区别于作者现成模型 | QF Table 10/11/Fig 7 编号和相应方法均未完成核验 |
| 目标与资金单位 | §2 持仓 z 为全投资、仅做多资金权重 | `cp.sum(z)=1`，`z≥0`；有历史误差 e_i=Y_i−gθ(X_i)，Nom. 最小化 `(1/T)∑(e_i'z−c)^2−γ μ̂'z`，DR 对 Hellinger 概率球最坏偏差加权平均并减 `γ μ̂'z`。源码 SOC 对偶形式在 `e2edro.py:236–264`，ECOS `max_iters=120, abstol=1e-7`，未显式给的其余 ECOS 默认项记录版本 | 不能声称实际交易可行，只请求毛组合统计 |
| 结果单位 | 年化 Return、Vol、Sharpe，Fig 7 按深度三组路径 | `portfolio.stats` 使用累计乘积和总体标准差；`fin_table` 用 52 次年化，Sharpe 使用未舍入的年化复利收益除年化波动。图/表由正文约定输出；原函数将 Return/Vol 保留 1 位，再以论文 2 位格式显示，Sharpe 2 位 | QF 证据待获取 |

## 缓存和随机性

- `main.py` 对 `dl.AV` 设置输入 `use_cache=True`，直接取得上述两个历史输入。训练与结果的另外两个 `use_cache=True` 分支（历史、合成各一）会反序列化已训练模型及回测输出，属于展示和诊断，不能作拟合复跑。
- 历史用 seed=1000，重新取得原始 AlphaVantage 价格需适当权限；起点为已发布衍生周收益的历史目标可使用作者输入缓存，须在审批中写清覆盖边界。合成不需行情 API。固定 CPU 和 NumPy/torch seeds；代码内未发现 Python `random` 或 DataLoader shuffle 的独立实验随机配置，使用相同求解环境及 as-of 版本；GPU 与依赖更新另登记。
- 作者仓库直接依赖说明不是锁文件。本次环境为 Python 3.12.14、numpy 2.3.5、pandas 2.2.3、torch 2.6.0+cpu、CVXPY 1.6.5、cvxpylayers 0.1.9、diffcp 1.1.4、ECOS 2.0.14，完整包清单见 `environment.freeze.txt`。旧版原文约 Python 3.8.5/PyTorch 1.10.0/cvxpylayers 0.1.4，无证据表明与本次依赖数值等效。初次两次因 six、statsmodels 缺失失败，安装后二进制正常；错误日志保留。Pandas 2.2.3 下主脚本 `set_axis(..., inplace=True)` 的旧 API 必须用兼容等价命令或锁旧版，区分训练核心与结果导出；此预检没有调用它。

## 实际执行和预先诊断标准

`P004-PF01` 只用第一个训练窗，六模型均执行了 `net(x,y)`、凸求解、`net_train([batch], lr=.005, epochs=1)`，没有打开任何作者已有模型缓存、没有执行实际的交叉验证和样本外回测。预先断言：形状和分割精确，权重和误差 ≤1e-6，最小权重 ≥−1e-6，所有可训练梯度有限且更新 L2>0。实际最大权重和误差 2.18e-13，最小权重 −1.42e-12，六项梯度均有限、更新 L2 约 .0389–.0595。第二次完整记录运行用时见 JSON，限诊断环境。数值和经济意义的论文结论均 NOT_ASSESSED。

可重复命令，在仓库本地解压并校验 SHA 后，使用当前目录相对路径：

```bash
MPLBACKEND=Agg PYTHONHASHSEED=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  python preflight.py --source E2E-DRO-b5e299ad7748468bc39e3e711eceee809143c648 --output preflight_output.json \
  > preflight.stdout.log 2> preflight.stderr.log
```

## P004-E02 申请和验收（NOT_RUN）

请求范围为 arXiv v1 §3.3 Table 11 的 18 个单元格和 Figure 7 的 6 个底层财富序列，均为 P004-R06 原目标的稳定单元格子 ID。附录 Table 13 全部验证损失用于版本补证（遇有限制先从每模型选定最佳超参记录来源）。不要把正式 QF 或历史数据整段归为已通过。版本封闭前可另标同一公开 commit 的“按作者快照计算”，不把结果记为匹配论文。要求主审裁定是优先按源码快照复跑并报告差异，还是另设按论文规范的独立实现。对输出容差先按表的报告精度做核对，Return/Vol 用印刷 2 位显示若作者一位数值复格式须完全一致，留未舍入实际值和 0.05 个百分点的作者源值舍入界线；Sharpe 采用 0.005 的舍入半单位。单独报告实际绝对误差、经济排序和训练阶段显式版本差异，不因版本冲突放宽容差；原图未提供可移交未压缩数字序列，报告重算数组及与图源视觉检查，不能用视觉相似替代数值验收。禁止事后为接近原数据改种子、改目标窗或删掉失败模型。

复制作者源码到新运行目录，限定仅 Exp5，合成生成该路径自己的新数据及工件，对历史数据和作者结果 pickle 一律不读。循 `net_cv` → `net_roll_test` → 导出各套输入/损失/测试每期权重、收益、财富索引和表；兼容输出层要用等价 set_axis 并记录补丁。可定位匹配的 Figure 7 曲线逻辑为 `PlotFunctions.py:wealth_plot`；Table 11 统计 `fin_table`。运行失败保持目标 NOT_MATCHED/BLOCKED 等准确状态。完整实验和所有经济结论当前 NOT_RUN/NOT_ASSESSED。
