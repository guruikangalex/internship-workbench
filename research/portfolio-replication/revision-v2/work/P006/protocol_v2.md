# P006 · Universal Portfolio Shrinkage · 复现协议 v2

批次 CO-REP-20261120-02。首选 P006-RFS-20261119 / P006-E01 / target_alignment.csv 中 PROPOSED 条目。从作者发布的处理后月度收益复算明确表图。建议主审批准限定的 AUTHOR_CODE_RERUN，需在批准记录中接受源码与论文公式的 LOO 分母冲突，且所有正式数值结果均为 NOT_RUN。本轮已实际完成三项可逆预检。主审批准记录仍为空。

## 1. 版本、数据与资格

| version_id | 版本与证据 | 日期 | 校验与访问 |
| --- | --- | --- | --- |
| P006-RFS-AM-20260924 | OUP 首次上线的 Accepted manuscript，DOI 10.1093/rfs/hhag084。OUP 当时版本标签与 Crossref published-online 相符 | 2026-09-24 | Crossref 的历史 PDF URL 本轮 shell HTTP 403。PDF SHA256 UNKNOWN |
| P006-RFS-20261119 | 当前 OUP 作者同名、同 DOI 的排版修订全文。实际读 §2.2 Lemma 2、§3、§4.2、§5、附录 C–F、数据与代码声明。当前页明确指向下列 Dataverse 归档 | 2026-11-19 corrected and typeset，首发日期 2026-09-24 | 出版社 HTML 全文与附录已读，PDF 字节未取得，PDF SHA256 null。精确来源定位和两张发表表格数值快照见 evidence |
| P006-NBER-20260521 | NBER Working Paper 32004，2023 年 12 月发行，Revised May 2026，论文正文起首页 2026-05-21；完整 PDF 含附录 | 2026-05-21 | SHA256 c95cbae7f2bd5d9221c7fc4886ccfd9dbf5b55bace3762281771c1cd2e069906 |
| P006-DATAVERSE-V1 | Harvard Dataverse，DOI 10.7910/DVN/OHZFKD，文件 ID 14008244，包内稿号 MS 20240297 | 2026-06-16 18:42:23Z 公开发布 | 本轮实下 123737306 B，MD5 b8cac94b06f22aa8bab676c0c1ec4656，SHA256 a20c2fbf0de51e9ad54baa6d2dadd7e2b8b374b7cea6a05efd3e918bc12f699b，107 个文件逐项 CRC32 与 SHA256 |

OUP 出版时作者栏列 Bryan Kelly 任职 AQR，Yale SOM，NBER。NBER 2026 年 5 月工作稿同样明确 Bryan Kelly 在 AQR。Semyon Malamud 在 RFS 致谢和 NBER 初始脚注中均确认为 AQR 顾问，归 FORMAL_ADVISOR_OR_COLLABORATOR。Kelly 对该试点可分别确认为 STAFF_AT_PUBLICATION 和 STAFF_AT_RESEARCH。其他任职边界与目前任职具体日期 UNKNOWN。正式刊物 RFS，J1_NAMED，DIRECT_OPTIMIZATION，PUBLISHED。SFI 日期与数据包创建时间不作期刊发表日期。当前排版 HTML 与早期上线录用稿独立登记。过去的“38天版本差”删除。

出版社正文及附录 https://academic.oup.com/rfs/advance-article/doi/10.1093/rfs/hhag084/8835505?rss=1 。NBER 备选 https://www.nber.org/system/files/working_papers/w32004/w32004.pdf 。作者归档 https://doi.org/10.7910/DVN/OHZFKD 。

| 数据 | 确认内容 | 本次范围 |
| --- | --- | --- |
| factors_main.csv | 614 月×153 特征因子，1971-11–2022-12，月末索引，decimal return，US 股票 capped value-weighted long–short | E01、E05 必需 |
| benchmark.csv | 738 月×6，1963-07–2024-12，mkt、smb、hml、rmw、cma、mom；统一索引后去 mom，FF5 含 mkt，CAPM 使用 mkt | E01、E05 必需；预检五表无空值 |
| factors_mega.csv / factors_large.csv / factors_small.csv | 614 月×151 / 152 / 152 个分组因子 | E02 尺寸附录，提前获取 |
| 原始 CRSP/Compustat / JKP 历史微观版本 | E01 从派生面板进入，证券级数据权益、历史快照、构造字段未确认 | E04 原始数据重建另行申请 |

数据的回测可知窗口以月 t 截至 t 结束为训练终点，t+1 月收益归因。供应商真实即时发布时间、证券层历史成员、个券退市或公司行为、价格和借券状态不由派生输入充分公开。作者包不需要联网抓取微观数据。证据 evidence/archive_contents.csv 逐文件提供路径、hash、对照分组和数据角色。稳定下载安装用 execution/fetch_and_verify_inputs.sh。版本和所有五个面板已实际核验。

## 2. 目标函数和作者源代码

设训练样本 X 的每行是 153 个因子的月收益列向量转置，T=120。因子均值 m=X'1/T，未中心化二阶矩 S=X'X/T。岭基组合资产权重 p_j=(S+z_j I)^(-1)m，z_j=10^i，i=-10…-1。每次删除 t 行，论文定义 m_(-t)=∑_{s≠t} X_s/(T−1)，S_(-t)=∑_{s≠t} X_s X_s'/(T−1)，据此得到各 z 的留一收益矩阵 A，其中 A_tj=X_t' (S_(-t)+z_j I)^(-1)m_(-t)。计算 u=A'1/T，Q=A'A/T。

求 W*=arg max_{W∈ℝ_+^10} (W'u−0.5W'QW)。W 是 10 个基组合暴露的非负混合系数。约束是逐项 W_j≥0。最终 153 维因子持仓为各 p_j 的加权和，再按本文说明做有效特征值迹归一化。用于 Fig. 7/9 的份额图才把 W 除以它的总和。最终因子持仓和原始研究样本内的 10% 事后风险缩放都独立于该 QP 约束。

NBER §3 式 (15)–(17)，以及 RFS §2.2 Definition 2、Eq. (9)–(10)、Lemma 2、footnote 2 给出矩与目标。RFS §3.1 和 NBER §4.1 报告月频、120 个月和完整惩罚网格。作者源码对应 paths：

- src/upsa.py:39–56 的权重和 trace 缩放、约 69–85 行的 QP 输入，约 93–129 行的 LOO 平滑器，145–153 行的 cvxopt QP。传入 P=Q、q=−u、G=−I、h=0，等式参数缺省。
- scripts/compute_main_figures.py 中 Z_GRID 和 120；src/portfolios.py:41–74、92–124 的滚动切分、UPSA/Ridge/LW/PCA/FF5/CAPM 与 t+1 会计。FF5 基准用 np.cov 的中心化样本协方差，对 UPSA 未中心化二阶矩无替代关系。
- src/plotting.py:321–350 的作图份额归一化；src/pricing.py:16–65 的总体及分主题定价。
- RFS 主文脚注 19 指出 Sharpe、alpha 是交易费前。Fig. 8 为因子持仓换手，不能推出逐股费用或净收益。按 src/metrics.py 以相邻目标持仓绝对变动和除以前期总绝对持仓的一半，首月 0，不做收益漂移后重权。

### 2.1 已查实的论文与作者实现差异

论文 LOO 留一估计在因子样本矩上用 T−1。原作者平滑器从以 T 为分母的 H=X(X'X/T+zI)^(-1)X'/T 做 rank-one 删除，z 未重标。代数上留一惩罚在 Gram 矩阵尺度为 T·z，论文直接重拟合用 (T−1)·z。如在平滑器的留一环节单独换成 z×(T−1)/T，数学上才对齐论文同 z；最终全窗 portfolio basis 仍使用原始 z。这一差异在 P006-PREFLIGHT-03 实测于第一窗的 3 个被留观测和 10 个 z。z≥10^-7 时作者与直接 T 公式最大差约 1.57×10^-8，和直接 T−1 公式最大差约 0.002662，都是月收益小数。极小 z=10^-10 的实现与直接 T 也可差 0.014314，显示 P>T 的数值敏感性或消去误差，不能归作分母差。

E01、E05 作为指定作者包重跑，参数与算法不改。预先报告冲突 P006-B07，并保留包含源码差异的审批范围。精确采用印刷公式的重实现为 E06，分别报告表现差异。禁止以修正后模型替代 E01 与 E05 来追数。

另一个展示口径差异是 Fig. 3/5 的 pre/post-2000 标签。作者代码以 pandas 年度切片，1981-11–2000-12 共 230 月，与 2000-01–2022-12 共 276 月，交集 12 月。两种切分下的结果不可合并归因为样本外互斥测试。E01/E05 跟随交付代码。互斥分期比较仅登记 E03。

## 3. 版本化目标、准则和缓存

| 办理顺序 | version_id / experiment_id | 复现类型与边界 |
| --- | --- | --- |
| 1 | P006-RFS-20261119 / P006-E01 | AUTHOR_CODE_RERUN。主审仅需批准 Fig. 3（全样本 6 数值与代码定义的两个子样本参考）、Fig. 5、Fig. 6 六散点面板、Table 1 的 84 格及 Fig. 8 |
| 2 | P006-NBER-20260521 / P006-E05 | AUTHOR_CODE_RERUN。完全同样输入与范围，工作稿的 Fig.3 三个面板 18 个已印数值独立核对。若要求 PDF 可核验时优先用本版本，不据此宣称 RFS 已跑 |
| 3 | P006-RFS-20261119 / P006-E02 | AUTHOR_CODE_RERUN。预留完整图表与三项模拟扩展审批，本轮仅到图表和配置映射，超出数值 pilot |
| 4 | P006-RFS-20261119 / P006-E03 | IMPLEMENTATION_AUDIT。分别评估分段边界、LW 环境漂移和原文分母；方法替换的行标 APPROXIMATE_VALIDATION，另行审批 |
| 5 | P006-RFS-20261119 / P006-E06 | INDEPENDENT_FAITHFUL。仅正式例示明示公式的研究，单报作者实现差异。E04 的原始数据工作单列，研究扩展另设 E07 |

target_alignment.csv 是唯一目标记录，按版本、实验、细粒度 result_id 关联。version_figure_crosswalk.csv 对照 61 个包文件，1 个主文表和 1 个附录表。主文 16 个编号图，17 个附录编号图，展开后 59 个图片面板。RFS 附录按 C.1–C.2、D.1–D.3、E.1–E.8、F.1–F.4 排版，Table E.1 对 NBER Table 2，也对归档 Table A1。另保留旧 ID 翻译表。正式账簿保留原文值、正式复算值、单位、绝对差、非零参考适用时相对差、事前容差、数值和经济判断、差异解释。执行前复算值及误差均空，result_status NOT_RUN，两个 verdict NOT_ASSESSED。

- Fig. 3 已印目标各格按两位见 ±0.005，原始四舍五入为首判。NBER 与随包 JPG 的全部 18 个值已核对。RFS 文本明确报告全域 6 值，当前未另行提取 RFS 子样本图标签，这 12 格单独用同作者缓存留存的参照。
- Fig. 5 的全域 UPSA 对 Ridge 年化 alpha 4.46 个百分点、t=3.72，各自绝对半单位 0.005。另核 15 条子样本/基准组合的 alpha、95% 区间；作者旧缓存派生的未舍入数值只作辅助，逐个报告误差和各显著性是否过零。图注为 HAC 5，10% 波动为每个评价区间事后缩放。
- Fig. 6 实际横轴与预测纵轴是 153 个因子的年化夏普。逐点对齐因子键、单位和相同 OOS 日期。底稿用已有作者缓存，默认逐点参考容差 5×10^-6 Sharpe 单位，超出则报告为参考底稿偏差。正式发表的六个散点面板 R² 取与 Table 1 All 同样的显示口径。总体纵轴定价评分、R² 排序与精确对齐分开。
- Table 1 及附录 E.1 各 84 格，单位为无量纲 R²，按两位显示半单位 0.005。作者 README 的 0.6652 与 0.6649 差 0.0003。实际读取随包两份既有输出重新算统计量得到 0.6652235373546274 和 0.6649162636104179，相差 0.0003072737442094686。跨舍入边界的单元如再出现，则注明数值 PARTIAL 与可能不变的经济结论，保持 原印 0.67。LW 最大既有差异为主表 Low Risk 0.09455062490342447 和附录 Value 0.1270977784513092，不能归为舍入。全部单元留存，不能因为总体排序相同判数值通过。
- Fig. 8 月均换手 UPSA 12.4%、Ridge 16.3%，一位小数 ±0.05 个百分点；12 月滚动的底稿日期和两策略逐点误差另外比较，辅助参照阈值 1×10^-5 个百分点。平均低和三分之二以上月份低不是相同结论，原文指出 Ridge 月份更常较低，均值与尾部更高。
- 本轮不在正式比较栏填入作者缓存的数值为 rerun_value。缓存诊断独立归档，并区分 manuscript_author_cache 与 regenerated_author_cache。

## 4. 可执行流程、环境与预检

建两个工作目录。证据目录保留已验归档完全不变。冷运行仅复制源码、配置和五个 CSV。冷目录的 outputs/computed/ 及 outputs/figures/ 起始为空，初始化 computed 目录供作者脚本写入。仅当主审批准时执行：

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
python run_all.py --main --compute
```

普通不带 --compute 的重绘目录读取随包 author result pickles，只能验证重绘管线。compute_main(force=True) 在确实跑 rolling engine 后对原目录 main_bundle.p 以 wb 写入，实际不保留原稿缓存。_is_vs_oos(force=True) 同样覆盖。全量 --all --compute 中模拟和附录 job 被强制重算，compute_appendix 内部 compute_main(force=False) 读的是该次先前生成的 main_bundle.p。单独 --appendix --compute 不能作为全量冷计算。预检逐源码核查 run_all.py branches、各 compute_* 函数及 finalizer；由新输出目录校验清单、mtime、日志和哈希，避免旧文件被误计为输出。仅靠 JPG 文件逐字节相等不作为判据。

本轮在云端实装 CPython 3.9.6 与 9 个作者直接依赖，25 个总包通过 uv pip check。numpy/scipy/cvxopt 及 BLAS 版本、架构、线程记录已附。resolved_packages.txt 是已安装版本清单，未建立全部 wheel 哈希跨平台锁。CVXOPT 1.3.3 采用默认 abstol 1e-7、reltol 1e-6、feastol 1e-7、maxiters 100。预检捕获诊断只在可逆 wrapper 中，正式需留存不改变数学的报告层。非 optimal、NaN、漏月、旧结果加载均保留失败日志。原程序未主动检查 status，审计用无侵入包装记录。作者的 25–35 分钟是 12 核 Apple Silicon 完整系统估计，本次未测全系统时长。

| 诊断 | 本轮真实动作与结果 | 正式状态 |
| --- | --- | --- |
| P006-PREFLIGHT-01 | 冷目录只用实际输入，从头执行首个 120 月滚动窗，1×6 六模型有限数值，样本外首月 1981-11。QP 7 次 optimal、gap 7.01e-8，混合系数总和 1.063331637。无结果缓存文件 | E01、E05 NOT_RUN |
| P006-PREFLIGHT-02 | 只读取两份作者已经产出的 main bundle 给统计量建参照。比较 Table 1/E.1 两个预先计算输出并导出图底稿，未估计策略 | E01、E05 NOT_RUN |
| P006-PREFLIGHT-03 | 对首个训练窗三个 LOO 行和十个 z 做直接方程代数诊断，证实 T/T−1 冲突及最小 z 的敏感性，不修改作者代码 | 全期审计和 E06 NOT_RUN |

本轮执行脚本、环境与 stdout/stderr 见 execution。审批之后完整窗口有 494 OOS 个月。仿真不是本轮 E01 数值目标，另外按 source 固定 seeds 0…N−1 和各 DGP。RFS 版 PDF 文件本身未获，网页版本已可锁定复现参照。若本轮必须提供纸质 PDF SHA，主审可批准这次已核的 NBER 源作为备用 E05。若审批规则要求文章中精确 T−1 而非指定作者代码，改送 E06 并保留 split-method 预检证据。
