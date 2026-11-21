# P008 正式版全文、依赖及按实验拆分的协议

批次 CO-REP-20261120-02。采用 JFE 142(2), 572–597，正式版 DOI 10.1016/j.jfineco.2020.11.001，2020-11-09 首次在线。CBS 托管的出版社全文连同 p.592 后的 Appendix A.1–A.4 可读，相关正文、表／图和附录已核查；执行器本地下载尝试超时，PDF 字节与 SHA-256 为 UNKNOWN。首面三位作者均明确署 AQR；Pedersen 此版另署 CBS、CEPR。不得把早期稿中的 NYU 地址继承到正式版。三个实验全部 NOT_RUN，主审待定。

## P008-E01 公式与理论机制

申请独立忠实实现，先限 P008-R01。Fig. 1 A/B、§2 Propositions 1–3、Eq. (8)–(12)、附录 A.1/A.4。对指定 \(\bar s\) 以 \(q=s-\bar s\mathbf1\) 写零约束 \(x^\top q=0\)，用正定 \(\Sigma\) 和固定风险核对最大 Sharpe；\(x\propto\Sigma^{-1}(\mu+\pi q)\)，\(\pi=-q^\top\Sigma^{-1}\mu/(q^\top\Sigma^{-1}q)\)。对照独立等式约束优化，验收正常条件数例子的 KKT 残差相对小于等于 \(10^{-10}\)、无约束切点为前沿峰位，以及现金、\(\Sigma^{-1}\mu,\Sigma^{-1}s,\Sigma^{-1}\mathbf1\) 的四基金张成空间。若风险资产净仓为零则平均 ESG 比无定义，记录可行性。公式验证用自定正定数值且只核对命题，不申请精确 Fig. 1 坐标。Fig. 2（R02）为 ESG-CAPM 理论，不是前沿实证。Fig. 3 A/B 也是理论，示意 A 与 M 的无差异曲线。原绘图输入在本次核查范围未确认。

## P008-E02 从底层数据重建

### 前沿及筛选

- **P008-R03／Fig. 4 A–B**。在历史 S&P 500 月度成分上，E 为 Trucost scope 1+2 的 CO₂ 排放/销售之负值，E 原始覆盖 2009-01 至 2019-03。构造截面 Z 分数。Paper Fig. 4 图题、横轴和 §4.2 均明确 E，后半图注混入 G／accruals 的句子，保留冲突并以构造段落定目标。主要目标为碳分数约 0 时接近 Sharpe 峰，U/A 的实现前沿基本重叠。
- **P008-R08／Fig. 5 A–B 和 Fig. 6**。G 为负 accruals/assets，Sloan 口径见脚注 14。G 源覆盖 1963-01 至 2019-03，前沿实用年月须从 Barra 和合并后的交集核定，不能用代理的覆盖期代替。Fig. 5 G 的 A 相对 U 最大感知年化 Sharpe 提升约 12%，实现提升约 11%；Panel A 感知峰位约 A 2.25、U 0.25。Fig. 6 屏除最低分股票 0%/10%/20% 的 A 峰位约 2.25/1.5/1.0。按月逐一求约束切点、保留截面有效资产数、平均感知前沿并用下一月回报重算实现前沿。行列的图上数值待数字化后冻结读图误差。

两个前沿均需要历史 Barra USE3L 版本的股票因子暴露、协方差、特异风险及时点，历史 S&P 500 成分和映射，XpressFeed 的证券收益与市值，Compustat 的账面市值比所需字段；G 还需会计资产和应计利润字段。所有商业底层数据权限未确认。依 Appendix A.3 用 Barra 残差协方差做截面 GLS 并求各自因子组合和波动，按原文全样本波动标准化因子回报来估恒定因子 Sharpe。A 用市场、价值和 ESG，U 只用市场和价值。不把滚动样本估计带入原实验；改动以独立审计 ID 处理。图 4/5/6 不需要总体 ESG 的 MSCI 评级，也不需要 13F 或签单流。

### Tables 1–4 的底层重建

- **P008-R04 Table 1**。四个代理预测未来 12 个月 RNOA 或总资产毛利率。XpressFeed、Compustat、各目标的代理值、股票市场 beta、规模与账面市值比。Pooled 月固定效应并在股票层聚类，Fama–MacBeth 的标准误为 Newey–West。Table 4 的统计口径不能直接借用。
- **P008-R05 Table 2**。A 为 Thomson Reuters 聚合的 13F 持仓，对 3 个月后做预测；B/C 是下一月交易数量及签单流代理，要求论文所用、1993-01 至 2012-12 的 Chordia 派生变量或其同版底层数据。不是前沿的共同输入。
- **P008-R06 Table 3**。当期估值 ln(P/B)，按四个代理逐列匹配证券、Compustat/XpressFeed、市场 beta，避免把规模或账面市值比作为机械重叠的控制。
- **P008-R07 Table 4 底层重建**。每月按各代理分组，下一月最高－最低（S 为二元，不强行五分组），Panel A 等权，Panel B 市值加权。要证券历史收益、市值、代理分数、证券识别和当时可用时点；不依赖 Barra USE3L 和 13F。Trucost 只用于 E，MSCI 评分只用于总体 ESG，G 用 Compustat，S 按 Hong–Kacperczyk 的定义。应按实际交集锁每个表列的股票覆盖与月数，数据源区间不直接等同目标收益区间。

## P008-E03 作者组合收益输入层

作者数据页链接 E/S/G/ESG 组合和 long-short factors；作者直链尝试超时后，从 AQR 官方数据页的媒体链接取得 [ESG_efficient_frontier_portfolios_vF.xlsx](https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/ESG_efficient_frontier_portfolios_vF.xlsx?sc_lang=en)，共 215209 字节，SHA-256 为 153423fd6356e41423271ddcdfe0280508e69e73273e023171aaf83e6cf8b676。已执行只读结构预检，代码 inspect_input.py，结果 input_preflight.json，目标统计量全部 NOT_RUN。2019–2020 年间的文件标签仍称 JFE forthcoming，发布时点早于首次在线，未证明逐字节对应后来的发表版，但论文与表注给出的 G 两种组合及时间范围和工作簿列定义相符。

- Panel A map：Equal-weighted excess returns 工作表，第 10 行标题；O 日期、P/G1、T/G5、U/G5−G1。
- Panel B map：Value-weighted excess returns 工作表，第 13 行标题；其四个列位置相同。
- 两表各 674 个连续且唯一的月末日期，覆盖 1963-02-28–2019-03-31，无非数值单元格。U 与 T−P 行级差最大为等权 1.25e−7 和市值加权 8.33e−8（工作簿原始单位），要用供应方 U 作为预注册主输入。单元格格式 General，源工作簿无显式单位标记，查验原始回报量级并冻结小数／百分数解读，不以目标对齐倒推。工作簿受来源披露条款约束，审批包提供直链和元数据。
- E03 表输入实测已取得（FULL_REQUIRED_DATA_ACCESSED）。提请批准 INDEPENDENT_FAITHFUL，范围是 **从作者组合收益到 Table 4 两个均值**，核定标签、单位及对发表版可比性后运行。没有官方运行代码。

| 结果 ID | 正式版 Table 4 p.592 的目标单元格 | 原文值 | 初次验收 |
| --- | --- | --- | --- |
| P008-R10 | Panel A/G/Average excess return | 7.84% 年化 | 实际作者序列核定后，比较精度 ±0.005 百分点。 |
| P008-R11 | Panel B/G/Average excess return | 3.01% 年化 | 同上。 |
| P008-R12 | Panel A/G/Six-factor alpha | 8.71% 年化，t 4.76 | 条件第二阶段。点估计 ±0.005 百分点；t ±.005 且须锁定标准误。 |
| P008-R13 | Panel B/G/Six-factor alpha | 3.07% 年化，t 2.52 | 同上。 |

首轮拟审批目标 R10/R11。工作簿同时提供高/低两腿及价差；已检查 U 与两腿在舍入级别一致。最高减最低的自融资价差不再扣第二次 RF。明确收益单位、月标签为形成时点还是下一月收益、是否存在可用／无回报断点，保存月数、缺值和行级核对；用月度均值的算术年化提出实施方案，并在查看输出之前确认其合适性，不能匹配后才挑年化方式。回归阶段需要原论文所用市场超额、SMB、HML、RMW、CMA、MOM 同期因子与切版；不拿替代数据直接判忠实。Table 4 附注只明确列年化、百分比和 t 值；这次未在相关段落找到该表误差模型设定，暂缓 t 值与回归全层判断，不套 Table 1 的 Newey–West。该表 A/G 六因子列的 8.71% 与 p.592 叙述中约 7% 的表述不一致，数值关以指定单元格为准，保留该冲突。P008-R12/R13 另列 P008-E04，仍 NOT_RUN。该进路不要求采购底层商业库；保留独立的文件来源、许可、可接受的数据代际和版本核查。

## 核验记录与关闭动作

- P008-B01 DATA_ACCESS：E02 依目标取得上列商业数据与历史快照，验证日期、证券映射和源字段；当前保留 ENTITLEMENT_UNCONFIRMED。
- P008-B02 DATA_VERSION：下载与结构验证条目已完成。余项为正式出版版所用切版是否与 forthcoming 标签工作簿完全相同，以及单位确认。工作簿目录、哈希、日期列及定义已明确。
- P008-B03 CODE：未定位本论文官方运行代码；准备独立实现。
- P008-B04 METHOD_DETAIL：理论原图坐标输入未知，理论命题不受影响；E03 第二阶段标准误与因子切版待证。
- P008-B05 VERSION_CONFLICT：Fig. 4 图注混写、Table 4 与正文近似数值不一致；按正式版具体实验、图题和数据构建定位，记录而不替换原值。

[正式版含附录](https://research-api.cbs.dk/ws/portalfiles/portal/68795021/Heje_Pedersen_Fitzgibbons_Pomorski_Resposible_Investing_PublishersVersion.pdf)  
[作者数据入口](https://www.lhpedersen.com/data)  
[AQR 数据定义](https://www.aqr.com/Insights/Datasets/Responsible-Investing-The-ESG-Efficient-Frontier-Original-Paper-Data)
