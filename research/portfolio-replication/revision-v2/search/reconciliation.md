# 二次送审检索对账

批次 CO-REP-20261120-02。截止 2026-11-20（北京时间）。执行 E 组。全部候选建议待主审，新增三条方法线索的实验仍为 NOT_RUN。

## 旧线索与计数

原批次首页记录“约 90 条候选/线索（8 个 agent 报告累计；含重复与排除项）”，未附完整命中清单和逐条去重原账。该数字保留为原报告自报口径。已从原 A/B/C 搜索件恢复全部 **36 张编号发现卡**（A 12、B 8、C 16），将 A-12、C-12、C-16 内分组显示的条目拆成原件可验证的单条（7、5、4 条），记录 **49 条卡内来源轨迹**。另登记原报告明确识别的 **23 条**查询、排除、消歧和方法参考线索，原轮合计 **72 条可恢复来源轨迹**。其中 54 条记录种类为 PAPER，另有 6 非论文、4 实体或主题噪声、4 人物线索、2 题名未恢复、2 仅作参考。72 条为来源记录数，包含不同机构重复发现或版本别名。

原 X01–X15 的 15 个排除组全部有明确 ledger 反向索引。分组项可对应多条轨迹，X15/P005 在主表保留为理论背景，数量不另增。原轮 10 个主表 ID 全部追溯至编号卡。后来已有的 P018/P020/P021 亦返回原 C 组卡。部分老命中只留有题名片段、机构名、作者、合并排除或数量描述，不能恢复其具体篇名、顺序、重复状态和合格性。由于“90”为近似总数且定义不同，不能把 90 减 72 直接认作精确缺失条数。原 B 自报 24 条同时包括 8 张编号卡及若干消歧、排除与观察线索，未声称额外 16 条均为逐篇文章。恢复的源段落标清出处，保留不可重建损失。

更早提交的 v1.1 主表有 21 个稳定 ID。来源台账对其中 15 个找到原包线索（13 个编号卡加 P015/P016 引文线索）；其余 6 个加入单列 v1.1 记录。二次送审新检索新增 9 条需明确记录的例示去重/排除轨迹。以上合计 **87 条**来源台账，当前率先移交的 21 个主表论文 ID 与其独立于源记录总量。主表计数以合并后的 canonical 为准。

历史 A/B/C 有 73 条可见查询/取证操作（21+31+21）；此次执行 42 条网页查询及 12 条 Crossref ISSN/机构元数据查询，合计 54 条。查询次数不计入论文数量。原件保存在 history，表 search_queries.csv 与 crossref_queries.json 提供旧页定位、实际新检索式、检索返回、用于消歧的分辨证据。

## 两个交接空档

Citadel J2/J3/J4 的 JFQA、Review of Finance、FAJ、JPM、JOIM、Operations Research、Mathematical Finance、Quantitative Finance 各有独立查询链和期刊级覆盖行。Citadel 现职或更早履历与论文版本署名分开。实例包括 Costa 的 QF 正式署 Millennium、Lopez de Prado 的 HRP 工作稿 Guggenheim/LBNL 署名，以及 The Citadel 军校作者对 SSRN 和 JPM 命中的干扰。以已查到的来源计，无新增核实通过的合格论文。具体筛查和链接见 ledger E-NEW-02 至 E-NEW-06 与 CE 系列查询。

Millennium 的 JF/JFE/RFS/Management Science 分别按期刊域、实体关键词及作者线索检索。JF 2016 的 Millennium 出现在 Cohn/Gillan/Hartzell 附录样本中，不是作者或雇主。Crossref 给 JF、JFE、RFS、MS 四条独立请求，前两者本次主题与机构查询为零命中，RFS 三个命中均无目标文字作者署名，MS 返回 429；MS 的期刊域、关键词和作者链搜索正常执行。JPM 和 Mathematical Finance 的 Crossref 查询也返回 429，网页及直接书目路径仍有记录。检索覆盖修复针对指定的交接和可追溯记录。Crossref 筛选是相关性检索，出版方历史元数据未必包含作者单位，结果不能解释为该机构所有论文的穷尽清单。

## 原 C 组三条方法线索

| 原卡 | 稳定 ID | 版本与身份 | 条件性复现 |
|---|---|---|---|
| C-04 | P020 | Journal of Optimization Theory and Applications 189:364–383，2021，DOI 10.1007/s10957-021-01823-0；Moehle（BlackRock AI Labs）和 Ang（BlackRock Factor-Based Strategies Group）正式作者栏。J4 方法池。 | Table 1 744 个历史案例的 0.05 bp 内 678/646 计数和 Figure 4。核得 arXiv v3，作者代码在列明渠道中未发现。历史股价/税盘批次、随机取整配置、市场数据授权和 CPLEX 12.9 是目标级条件。 |
| C-05 | P021 | Optimization and Engineering 24:1667–1687，2023 卷期，2022-11-11 online，DOI 10.1007/s11081-022-09748-x；Moehle/Gindi 的 BlackRock AI Labs 作者署名。J4 方法池。 | Fig 4/5 的 692 个真实税务约束实例与运行时间。作者 Julia package 已实际取得、解包并审阅，Apache-2.0，commit de3ab66772ddacbad37595da7bf52093266f173d。其公开测试含简单或随机生成的通用优化算例。原始 692 算例、经济仿真入口、历史项目环境均未见于该快照，尚未运行。 |
| C-06 | P018 | arXiv:2604.22625v1，2026-04-24，Yilun Jiang 署 Point72 Asset Management，作为工作稿登记 STAFF_AT_RESEARCH；声明系个人研究，未使用 Point72 专有信息。W 工作稿。 | Table 1 对照以 21 个实例、指定阈值和硬件，经 JAX/H100 对比 MOSEK/CPU，报告计数及 1 秒平移几何均值。完整 GPU 源码和实例文件在此次列明渠道未找到；CRSP/OptionMetrics 等历史数据许可未确认。 |

同题名跨版本去重，保持 P020 与 P021 独立。两篇共享税务应用思想但目标、求解器、DOI 不同。D. E. Shaw 等现职线索不能移作 P020/P021 出版署名。三个 PDF 指纹、访问路径、可交付源代码归档见 evidence_manifest.csv 与 supplementary_metadata.json。审查未运行三个项目，也未对其复现结果给出验收结论。

## 存档格式检查

原包名为 P001_accepted_manuscript.pdf 的字节是 HTML（SHA-256 c7c7ce2c13337012bf18ced52273bf0654750571443991f2529c192f7eba9a7b），证据索引应移除其 PDF 身份。原包另有 32 页真实 PDF P001_DynamicTrading.pdf（SHA-256 b9b01f48bd7ff0ce0431615d88b76f8a076b6593cc1d7765bd6ec2eb617473ab），应由 P001 负责组使用并在最终清单中登记。P020/P021 本次通过网页读取正式 PDF 文本，执行环境对部分 Stanford 地址直连返回短错误文本，错误件以 .txt 单列。另从 arXiv 实得预印本并核指纹。三个预印本均通过原始地址回查，避免将其指纹用于正式版。
