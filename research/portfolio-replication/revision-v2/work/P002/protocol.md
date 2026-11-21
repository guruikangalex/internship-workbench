# P002｜Machine Learning and the Implementable Efficient Frontier

## 第二轮建议

`CORE · DIRECT_OPTIMIZATION · HIGH · REQUEST_EVIDENCE`。发表版作者重跑路线有明确证据。正式实验保持 `NOT_RUN`，数值和经济结论均 `NOT_ASSESSED`，主审批准字段留空。先审 P002-E21 及其 Table 2 目标，卖空费、规模组、前沿网格、经济特征重要性和模拟另立实验。

## 论文、身份和代码版本

RFS 39(10), 3035–3078，2026-03-15 首次在线，2026-10 卷期，DOI 10.1093/rfs/hhag022。哈希对应 CBS 标记 Final published version 的论文在线排版版本，PDF 带 CBS 封面 1 页及 RFS 正文 44 页，使用正文印刷页码。DOI 相同，卷期正式重排 PDF 逐页字节比对未完成。首页脚注列 Bryan Kelly、Lasse Heje Pedersen 的 AQR 署名。Malamud 顾问关系独立记录，不用于判定本篇的同期员工资格。

§5 p20 直接链接作者 GitHub，正文 p42 声明 Harvard Dataverse。MIT 许可 Dataverse v1.0 2026-01-09 公开的代码文件与 GitHub `13d836b5187cbfa69730dd256d8eb767e65ca21f` 层级规范化后 **97 个文件逐一 SHA-256 相同**，ZIP 容器 hash 不同。Dataverse 服务记录 MD5 已对照。Git 提交时间 2025-03-06，README 自引 2024，反映引文年代，不足以推翻发表版 §5 与官方 Dataverse 双重指定。源码采用 NYSE 过滤，并在 Figure 4 活跃 ID 使用 Johnson & Johnson 与 Xerox，均与 2026 纸版一致。完整结果是否对齐仍待真实数据运行。

- RFS PDF 镜像 [CBS API](https://research-api.cbs.dk/ws/portalfiles/portal/126068694/hhag022.pdf)，附件 `inputs/hhag022.pdf`，SHA256 `8fc13f07eb5fa1cb151e5adec0efb0b75c7d008c5066aa0170a40b2d9dc662cf`。
- [发表记录](https://academic.oup.com/rfs/article/39/10/3035/8524346)。
- [作者 Git commit](https://github.com/theisij/ml-and-the-implementable-efficient-frontier/commit/13d836b5187cbfa69730dd256d8eb767e65ca21f)，附件 `inputs/author_code.zip`。
- [作者 Dataverse](https://doi.org/10.7910/DVN/GKLU6G)，[文件 13323001](https://dataverse.harvard.edu/api/access/datafile/13323001)，附件 `inputs/author_dataverse.zip`，SHA256 `b761a99dc1700b2ca9e00fcdcc2d5d5e150f240f064ad74846155d26cfe56b5a`。
- 正式 Internet Appendix 从正文 p2 链接的 [发布入口](https://academic.oup.com/rfs/article-lookup/doi/10.1093/rfs/hhag022#supplementary-data) HTTP 403。全文主体已读关键方法和全部主结果定位。附录独立正文为 NOT_READ。若运行 Appendix B/C/D/E 目标，不借工作稿附录填正式版本。

## 数据实际取得和实验依赖

| 数据 ID | 实际输入与源码消费位置 | 本轮结果 | 精确性／影响 |
|---|---|---|---|
| P002-D01 `usa.csv` | `1 - Prepare Data.R:49–61`，月末证券 ID、SIC/FF49、市值、NYSE 交易所标识、日波动估计、126 日平均美元成交量和 115 个特征（源码字段表见 `Main.R:142–192`） | WRDS 官方组接口会重定向登录；stock-level 并未下载，ENTITLEMENT_UNCONFIRMED | 阻塞所有股权历史回测和股票权重结果。WRDS 或作者提供的最初生成快照。网站公开因子收益仅为因子组合时间序列，不能替代证券级 panel |
| P002-D02 `usa_dsf.csv` | `1 - Prepare Data.R:158` 读 `id,date,ret_exc`，`3 - Estimate Covariance Matrix.R` 用主题特征和行业虚拟变量回归日收益 | 已定位生成路径，未取得面板，ENTITLEMENT_UNCONFIRMED | 影响全量风险及基准复跑；也需至少覆盖从 1952 年后的风险预热至 2020 年 |
| P002-D03 `world_ret_monthly.csv` | `1 - Prepare Data.R:35–46`，只消费 USA、id≤99999 的 ID、期末日期和 ret_exc；派生 t+1..t+12 | 已定位生成路径，未取得面板，ENTITLEMENT_UNCONFIRMED | 阻塞收益训练、持仓损益和超额收益；可请求作者提供按列筛过的 US 子表，须保留原筛选边界 |
| P002-D04/D05 `Factor Details.xlsx`、`Cluster Labels.csv` | `1 - Prepare Data.R:24–33`，abr_jkp、direction、characteristic、cluster | 直接下载 author JKP GitHub，读表头、角色和形态，153 label/13 groups，附件/hash 已交回 | 官方明确下载路径的当前内容。冻结文件哈希，原运行历史 vintage 未记录 |
| P002-D06 `market_returns.csv` | `1 - Prepare Data.R:5–17`，USA、eom、mkt_vw_exc，用于财富路径 | 作者 README 份中的默认最新 PaperFactors ZIP 为 93,143,440,450 字节，范围请求未生效。另一条 JKP Analysis README 的 paper archive 实际取得：`Data/market_returns.csv` 3,684,824 字节，US 1926-01 至 2020-12 共 1,140 月，1952-12 至 2020-12 全 817 月有数值 | `SAMPLE_ACCESSED` 对 P002 准确 vintage，FULL_REQUIRED_DATA_ACCESSED 对替代快照；2022-02-10 JKP 作者归档，P002 论文使用特定列和日期 YYYYMMDD。已生成只改格式的 USA staging CSV；不得将不同来源未经核准当成原始作者输入 |
| P002-D07 `ff3_m.csv` | `1 - Prepare Data.R:1–2`，yyyymm、RF；月度百分比转小数 | 实得 French 当前 202609 版及 202107、202407 归档，三个版本均覆盖 817 月。相对 202609 版，202107/202407 在论文覆盖内分别有 5/10 个月 RF 差 1bp | 数据已取，正式原跑 vintage 未知。差异年月和值已写入日志，不能默认为零差 |
| P002-D08 `Data/short_fees.csv` | `6 - Short selling fees.R:2–24`，Markit 费用、日期、permno、market_area、record_type、dcbs | 文档确认，未获授权、未取得 | **仅** Figure 7（E25），不阻塞 E21/E22/E23/E24/E26/E27（运行 E21 时不调用汇总器无关部分） |
| P002-D09 模拟 | `simulations/sim_functions.R` 合成 DGP，不读取 CRSP/WRDS/Markit | 代码和参数实际取得；模拟未运行 | E27 不受真实行情权限限制。先取正式附录定位、对照参数和输出命名，再提交单一参数的预检或正式多任务运行 |

公开文件和 URL 逐项见 `evidence_manifest.csv`。仅执行 `python verify_inputs.py >preflight/input_check.json`，校验双档、原始文件、列描述、美国月份覆盖、French 样本/历史差分，不执行 R、训练、回测或结果复算。环境中 `Rscript` 不在 PATH，作者 joblist 的 R/4.3.0-foss-2020b 未搭建，本轮仅静态核查。作者报告的 HPC 时间和内存仅作配置估计。

## P002-E21 主表优先协议

范围为正式 Table 2。必要时仅先对 Portfolio-ML、Markowitz-ML、Market 行提交受限技术预检，同一拟议 E21 的完整正式目标为全部 11 行。所有目标数值逐格列于 `target_alignment.csv`。主要对照：Portfolio-ML SRnet 1.33、Utility 0.086、Turnover 0.25、Lev 3.00；Markowitz-ML SRgross 2.06。Markowitz-ML TC 的加号和三列破折号属论文呈现约定，输出精确数另外审计，不能写入正式目标数值。主要结论单列统计，避免以排序代替数值。

1. 冻结 Dataverse 原件、Git 提交、R 4.3.0 与库版本/BLAS、数据版本、市场月份和格式。锁定月份观察范围，原文 Dec 1952 至 Dec 2020，组合表现 1981–2020（月度 480 月），初始训练截至 1970-12，1971–1980 决策参数验证，往后每年只用当时可知完整收益重新估计和选择超参。记录 `id,eom,eom_pred_last` 并检查 t+h 收益窗口截至年份。对最终策略用 NYSE 普通股且名义筛选 above-median，记录先前连续有效与出入池规则。正式版报告首/中/最大股票数 184/646/805，建议先作数据核对。
2. 给 `Data/Generated/Models` 和 `Data/Generated/Portfolios` 创建目录，绑定路径参数（纯文件路径变更已记录，保存补丁与 SHA256）。通过作者命令 `Rscript slurm_fit_models.R config_files/config_modelsN.txt` 分开生成 12 个 `model_N.RDS`。作者估每期收益子脚本显式允许非 NYSE 训练，组合选择脚本才使用 NYSE。保留两套筛选并报告差异，待主审确定作者样本过滤如何解释。记录随机种子 `1`、横截面 RF/特征标准化，检查并行 RNG 子流。
3. `Rscript slurm_build_portfolios.R config_files/config_pfchoice_base.txt`，冻结 `size_screen=perc_low50_high100_min50`、`industry_cov=TRUE`、`wealth=1e10`（2020 末美元）与 `gamma_rel=10`。路径读取仅指向本次 12 个生成结果。保留生成的 `static-ml.RDS`、`portfolio-ml.RDS`、`multiperiod-ml.RDS`、`bms.csv` 及集群日志。保留月序列及权重，样本重复与非预设缓存拒绝运行。
4. 分析阶段使用 `separate_analysis_run.R` L1–36 的基础设置，跳过 L38 的 IEF、L40–44 的规模/特征/卖空/RF 图。仅调用 `6 - Base analysis.R` 后保存未舍入 `pf_summary`、`pfs`、`prob_outperformance`、`pf_cors`；以 `7 - Tables.R` L25–47 输出 LaTeX Table 2 或统一审计 CSV。作者分析文件未自动 source `7 - Tables.R`，并假设指定 Base 子目录，有些输出命名日期、R 脚本大小写不同；先修纯文件路由，保留作者计算函数。运行命令保留在执行时生成的日志；当前这些是复现协议中的拟运行命令。
5. 原文公式 (6)/(11)、§5 与代码差异采用平行判定，见下。数值验收对所有发表单元按显示位数舍入匹配，二位小数默认半个刻度 0.005，三位小数 0.0005，另比较逐单元绝对/适用时相对误差与可用性。对表 3 一位百分比接口用半个刻度 0.05 个百分点，相关系数表用 0.005；图用时间序列/持仓底层数据而非渲染像素。排序、正负效用、成本调整后的优势独立作经济验收。
6. 成本使用每月 126 日日均美元成交量，单资产斜率 `Lambda=0.2/V`，TC 为单期美元交易的二次成本 `tau' Lambda tau/2`，再换算为 AUM 占比；收益为小数超额收益；资产权重是资金比例，可为负；风险以多主题/行业 Barra 式模型，因子相关 EWMA 378 日、方差 126 日、残差 126 日，档案代码 `Main.R:116–124`。除换手和杠杆以外为年化。正式实验不加短借费。

### 源码与正文的可核验差异

| issue_id | 证据 | 处置 |
|---|---|---|
| P002-I21 | 论文 §1.3 式11及 Table 3 注以 **净收益** 相对其全样本均值计算方差惩罚。作者档 `6 - Base analysis.R:25–26,34–40,104–110` 以 gross `r` 构造 utility_t 和年化 obj；`sr` 用 `sd(r)` 而非 `sd(r-tc)`。Table 2 Vol.列和净 Sharpe 分母是否采用毛风险在正式表注未明确同一概念 | AUTHOR_CODE_RERUN 首跑固定执行不改计算，纸版声明另行以 **同样已生成预测和权重** 计算 Eq11 名为 P002-E28 IMPLEMENTATION_AUDIT。逐格比较并提供差异分解。发表表最终生成口径需审定，不能把相似即可视作关闭 |
| P002-I22 | 正文 §5.1.3 p22 前向模型 `w[t]=w[t-1]*(1+Rm[t])`。代码 `1 - Prepare Data.R:9–17` 从 2020 年末逆向计算 `cumprod(1-tret)*wealth_end`，不是直接除以 `1+tret`；而 `tret=mkt_vw_exc+rf` | 初跑原码后单独比较 AUM 路径比率，影响成本、可实施前沿及模型选择。仅计算替代路径是审计；若重训改变策略，另设 `APPROXIMATE_VALIDATION` 分支，不代入作者代码原跑 |
| P002-I23 | §5.1.1 描述只纳入 NYSE；`slurm_fit_models.R:4–7` 在收益模型拟合明确关闭 NYSE 过滤，`Main.R:71–76` 与组合脚本保留 | 确认论文该句是否仅投资池。如主审要求检查训练总体，平行跑固定版本消融，记录 train/invest universe，禁止静默修改 |
| P002-I24 | 正文 §5 股票至少 50% 特征，源码 `1 - Prepare Data.R:87–91` 使用 `floor(0.5*115)=57`；L77–79 过滤缺失 t+1 记录，并在 L136–141 检查连续月；L145 后施加 12 次纳入/排除持久性 | 作者重跑保留；登记日历审计 t+1 缺失筛选可能使用当前未知是否有下一月可观测，核对证券退出和退市返回。独立改动必须单列 |
| P002-I25 | R 脚本路径字面值如 `6 - RF Example.R` 与仓库实为 `6 - RF example.R`；调用它的作者脚本内部还 `source("main.R")` 而原文件 `Main.R` | Linux 环境属于可修路径项，日志保留差异；E21 跳过此脚本；附录 RF 目标仅在定位后单列 |

## 其他实验映射

| 实验 | 目标 | 运行—分析—产物 | 特殊输入和范围 |
|---|---|---|---|
| P002-E22 | Tables 3/4、Figs 2/3/4；正文 pp30–33 | E21 base；`6 - Base analysis.R:46–110,148–201` 出时间序列、配对概率、相关、权重；另 `6 - Economic intuition.R` 输出流动性持仓；`7 - Tables.R:53–70` stdout；`7 - Figures.R` 输出 cumret_pf.pdf/w_liq.pdf/example_weights.pdf | 与 E21 同输入，无 Markit；Table 3 方差差异见 I21；Figure 4 active ID 22111/27983 |
| P002-E23 | Figure 1 A、B；正文 Figure 1、§6.2 | `Joblists/joblist_pfchoice_ief.txt` 和 20 配置；`6 - Implementable efficient frontier.R` 读基准及 IEF RDS/CSV，`7 - Figures.R:25–30` 输出 ief_by_method.pdf、ief_by_wealth.pdf | Wealth 近零/1B/10B/100B、风险厌恶 1/5/10/20/100。各风险收益点分开保存，非统一纳入 E21 |
| P002-E24 | Figures 5、6；正文 pp36、38 | `joblist_pfchoice_fi.txt` 三配置 → `5 - Feature importance {base,ief,ret}.R` → `6 - Feature importance.R` → Figures/feat_imp.pdf、ef_cf_tc.pdf、ef_cf_no_tc.pdf | 13 主题 permutation、Table D.1；需股权历史和确切特征；Figure 6 风险厌恶 5 个规格 |
| P002-E25 | Figure 7；正文 p39 §6.4 | E21 权重＋`6 - Short selling fees.R` → Figures/shorting.pdf | 额外 Markit，前六个月及缺失字段按文章正文核；股权直接卖空支付 100% 费用、贷出多头收到 70%；不把成本当成 E21 必需 |
| P002-E26 | Figure 8；p41 §6.5 | 1 all+5 size `Joblists/joblist_pfchoice_{all,size}.txt` → `6 - Performance across size distribution.R` → Figures/by_size.pdf | NYSE 全体和五个规模组，报告归属频次、区间、换手；仍需历史输入 |
| P002-E27 | Appendix E 模拟；正文 p41 引用 | `simulations/simulations.R` 与 15 configs、每组 seeds 1–3、500 股票、70 年月频，输出 `simulations/results/results...csv`；`simulations/sim_results.R` 汇总，Figures/simulations.pdf | 不读外部行情数据；附录 PDF 未读，准确图号和指标验收尚待；汇总器的字符串 `-05-18` 只指历史产物，应以本次真实文件名重绑 |
| P002-E28 | Table 2/3 会计定义差异审计 | 同一已生成月收益上分别重算 gross/net 风险惩罚、净 Sharpe 两种分母、AUM 路径直接诊断 | 不前视、不调参；如重新拟合，需另申扩展边界 |

## 阻塞与下次送审

1. D01–D03 的合法数据访问和版本为历史实验的硬阻塞。建议询问既有 WRDS CRSP/Compustat 和 Global Factor Data 权限，或优先申请次发布快照；不自行申请付费或发邮件。D06/D07 数据存在且有区间，但需主审认可版本处理；若官方证据能确认版本或证明无关键差分，可以继续讨论忠实范围。
2. I21–I24 需要在冻结文件后保留作者线和纸版审计线。脚本可运行性需要 R 依赖和路径安排。发布代码已查实，科学上的版本归属否决撤销。
3. 主审须逐项确认 E21+Table 2 目标，E22/E23/E24/E25/E26 按表图升级。E27 可在历史数据缺口持续期间并行补附录和隔离环境，但本轮未执行。审批限制使用 `reviewer_queue.json`，不是已批准动作。
