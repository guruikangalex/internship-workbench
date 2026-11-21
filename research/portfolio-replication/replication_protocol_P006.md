# P006｜Universal Portfolio Shrinkage 首批协议

plan_version: 1.0  
review_package_version: 1.1  
execution_stage: DUE_DILIGENCE  
execution_status: NOT_RUN  
reviewer_decision: PENDING  
approval_record_id: PENDING  
approved_version_and_scope: PENDING  
approved_experiment_ids: PENDING  
approved_result_ids: PENDING  
reviewed_by: PENDING  
reviewed_at: PENDING  
conditions_and_followups: PENDING

## 版本与启动条件

RFS DOI [10.1093/rfs/hhag084](https://doi.org/10.1093/rfs/hhag084)，出版社标记 Accepted Manuscript，2026-09-24 首次在线。SFI 的 2026-07-16 是机构页面日期。卷期页码未定。作者包 [Dataverse V1](https://doi.org/10.7910/DVN/OHZFKD) 于 2026-06-16 UTC 发布，静态检查实际下载文件 14008244、123737306 bytes，MD5 `b8cac94b06f22aa8bab676c0c1ec4656`，SHA256 `a20c2fbf0de51e9ad54baa6d2dadd7e2b8b374b7cea6a05efd3e918bc12f699b`。缓存与派生输入均可得，原始 CRSP/Compustat 重建未列入首批。

首批只申请 NBER 工作稿的 P006-E05。RFS 路径需要取得精确录用稿全文后单独提交。

- RFS 路径。将期刊 PDF 的作者身份、图表、样本和附录逐项锁定，再启用 P006-E01 到 E02。出版社的 [准确 PDF 入口](https://academic.oup.com/rfs/advance-article-pdf/doi/10.1093/rfs/hhag084/71393687/hhag084.pdf) 已定位。核查是否取得并完成交叉表见本包 `checks/P006.md`。
- NBER 路径。明确以 [NBER w32004，稿内 2026-05-21](https://www.nber.org/papers/w32004) 为论文版本，P006-E05 只申请准确映射的派生输入后目标。批准文件不得将该目标标注成 RFS 版。相同历史证据与目标数值用于说明两版潜在差异，不自动重新使用审批。

## 数据、方法与基线

作者 ZIP 的主表、large、mega、small 各含 614 个月（1971-11 至 2022-12），因子列分别 153、152、151、152。配套基准含 738 个月和 6 个因子字段（不含日期列）。主实验在月末获得可用收益后，以 120 个月滚动估计、下一月计收益，1981-11–2022-12 为目标样本外期。数据以小数读取，核验日期排序、重复值、列名、缺失规则、训练结束月份严格早于评估月份；现成因子收益不把标的成分、退市和交易成本回溯为已重建。

以每个岭惩罚下的切点方向为基函数，作者代码用交叉验证辅助估计在给定滚动窗口内的组合；主惩罚网格为 10 的 −10 至 −1 次幂。比较单岭、Ledoit–Wolf、PCA、FF5、CAPM，机器可用时记录 QP 收敛诊断与求解精度。期刊/NBER §4.1 的样本内波动归一保持统一，图 4 专用事后年化 10% 缩放；不把图形缩放误写成所有目标的风险设定。实际交易时点与现金、融资、融券费用不在毛收益指标内。完整 OOS 共 494 月。图 8 换手保留原式。已知原文月均换手 UPSA 12.4%、Ridge 16.3%，均值按显示末位 ±0.05 个百分点。价格漂移、真实报价、成本和容量只能在另行批准的经济设定中使用。

## 结果与固定验收

表中 NBER 原文值来自 §4–5，RFS 对应值须依正式版本证据；未经审批不执行。

| result_id | 原文位置（NBER） | 指标与既有值 | 预先验收 | 当前状态 |
|---|---|---|---|---|
| P006-R01 | Fig 3，全期及 2000 前后面板 | 全期年化夏普 UPSA 1.92、Ridge 1.59、LW 1.31、PCA 1.45、FF5 1.13、CAPM 0.54 | 相同月份与样本划分；可核原值四舍五入至 2 位，各面板另核柱高与相对排序 | NOT_RUN |
| P006-R02 | Fig 4 | 10% 事后波动归一的累计对数收益 | 导出月度路径与终值，与锁定基准数列比；只有纸图时记录数字化范围 | NOT_RUN |
| P006-R03 | Fig 5 | 年化 alpha，HAC 5 lags；UPSA 对 Ridge 4.46%、t=3.72 | 原发表至两位，检查 HAC 口径和面板误差棒 | NOT_RUN |
| P006-R04 | Fig 6a–f、Table 1 All | SDF 样本外 R²，UPSA 0.67、Ridge 0.39、LW −0.10、PCA 0.22、FF5 −0.39、CAPM −2.35 | 基准 45 度线、样本/轴/方法相同，逐格记录；缓存和重算分开 | NOT_RUN |
| P006-R05 | Table 1 13 个主题 | 10 主题 UPSA 最高，例外 Low Risk、Low Leverage、Profit Growth | 不只比排名，列逐格差异并核对三例外 | NOT_RUN |
| P006-R06 | Fig 1 | 维数比变化的 IS/OOS 夏普机制 | 依源码锁定重复次数、种子和参数，比较同一横轴格点 | NOT_RUN |
| P006-R07 | Fig 8 | 12 月滚动换手；Ridge 在约四分之三月份较低，但平均约高 30%，标准差近五倍 | 核对基于样本范围的日历、计算口径、原数列与定性统计；三项指标分别记录 | NOT_RUN |
| P006-R08 | Fig 10a/b | 主成分数量与年化夏普、与不可行组合相关 | 同 PC 计数网格与 RFS/NBER 各自纸图位置，数值和峰值分开 | NOT_RUN |
| P006-R09 | Fig 11 | 两种收缩曲线机制 | 输出每格特征值和惩罚，核对所用图轴和排序 | NOT_RUN |
| P006-R10 | Fig 13 | 主题 Shapley 贡献 | 同主题集合，检查贡献和及逐主题数值 | NOT_RUN |
| P006-R11 | Figs 14–16 和相关附图 | 三个模拟条件下尾部谱、夏普及换手结论 | 保留原种子索引和原始场景，核均值、分位与散点匹配 | NOT_RUN |
| P006-R12 | Appendix Table A.1 | in-sample beta 稳健性，逐主题 R² | 同 Table 1 逐格比较，报告差分 | NOT_RUN |

精度规则：论文明确报告到两位小数的数值以显示精度区间评估。作者记录 Table 1 的 UPSA/All 0.6652→0.6649，提前登记为两种参考产物间的已知差异；如重算吻合作者重算值仍单列与原稿的数值差，不能把纸面单元格写成完全一致。作者对部分 LW 单元格仅给出约 0.1–0.2 的量级，须先从可信原表和随包重算参考锁定具体单元格与未舍入差；这个区间不作通用容差。只有定性可核对目标时保留相应状态，避免用近似图片的像素误差替代数值。跨平台 JPEG 的字节差保留为渲染差异，主核验依据为输出数据、表格数值、绘图序列、轴与图例。独立比较样本精确性、方法忠实度、经济排序和未覆盖目标。

## 实验划分

| experiment_id | experiment_layer | reproduction_type | 批次范围、配置和产物 | 状态 |
|---|---|---|---|---|
| P006-E01 | PAPER_REPLICATION | AUTHOR_CODE_RERUN | RFS 待补证路线 R01/R03/R04/R05/R07，主窗口、原派生 CSV，拟 `--main --compute`，输出 `results/P006/E01/` | NOT_RUN |
| P006-E02 | PAPER_REPLICATION | AUTHOR_CODE_RERUN | 余下 R02/R06/R08–R12 和 manifest 余项，需逐项版本映射及独立审批范围，拟 `--all --compute`，输出 `results/P006/E02/` | NOT_RUN |
| P006-E03 | IMPLEMENTATION_AUDIT | AUTHOR_CODE_RERUN | 同版、原参数的日期、风险归一、成交量公式、缓存与重算分路审计，输出 `results/P006/E03/` | NOT_RUN |
| P006-E04 | IMPLEMENTATION_AUDIT | APPROXIMATE_VALIDATION | 仅在另批后更新数据或成本/现实调仓口径，输出 `results/P006/E04/`，不得反填原文 | NOT_RUN |
| P006-E05 | PAPER_REPLICATION | AUTHOR_CODE_RERUN | NBER 2026-05-21 版首批 R01/R03/R04/R05/R07，冻结同作者包，输出 `results/P006/E05/` | NOT_RUN |
| P006-E06 | PAPER_REPLICATION | INDEPENDENT_FAITHFUL | 冻结版派生输入、独立核对切点基、优化、对齐后的收益及诊断；另审，输出 `results/P006/E06/` | NOT_RUN |
| P006-E07 | RESEARCH_EXTENSION | RESEARCH_EXTENSION | 加入显式成本、杠杆、容量约束；另审，输出 `results/P006/E07/` | NOT_RUN |

## 预运行与变更

1. 审批仅确定选定版本、实验 ID 和目标 ID。安装文档要求的 Python 3.9.6 与 9 个固定版本包，保存 wheel、系统/BLAS、求解器版本。顶层 pin 不代表传递依赖已锁定。
2. 显式区分两个解压树。只读存档包与哈希，单独检查随包作者缓存；第二个树用 `--compute`，源码会重写 bundle。启动前记录输出和缓存哈希，使用空结果目录或先移开旧输出，不以旧文件存在作为成功信号。
3. 首先审计 120 个月窗口结束时点及首个 1981-11 的预测/权重/实现收益；先对齐基准月收益，再评估主方法。保存命令、stderr/stdout、环境、内存、时间、实际生成图表路径和哈希。作者 12 核 25–35 分钟为完整路线参考，本次时长 NOT_RUN。
4. 缓存重绘属于再渲染诊断。严禁将缓存画图、缓存数值、README 示例标记成实跑成果。已知舍入、平台和“引入交易成本”三类变更分开记录。正式结果以后按附件 §6.4 追加。

| blocker_id | 类型 | 关闭条件 |
|---|---|---|
| P006-B01 | VERSION_CONFLICT | 能逐目标引用确切 RFS 位置，或批准独立的 NBER 版 E05 |
| P006-B02 | NUMERICAL | 先锁各漂移单元格的稿件与重算基准，然后评估结果 |
| P006-B03 | DATA_VERSION | 仅影响微观重建。若要开展需原始字段、权限和历史版本 |
| P006-B04 | ENVIRONMENT | 作者环境能够可靠建立并留存锁定记录，入口执行仅在获批后 |
| P006-B05 | CODE | 用两棵树验证缓存不污染原始证据、生成结果确为新输出 |

## 核查表

[P006 61 项版本对照](P006_version_crosswalk.csv) 与 [106 项发表值](P006_pilot_numeric_targets.csv) 使用本批编号。独立复核原稿编号见 agent_result_id。CVXOPT 1.3.3 静态核得 abstol=1e-7、reltol=1e-6、feastol=1e-7、maxiters=100，实际运行仍需保存参数。
