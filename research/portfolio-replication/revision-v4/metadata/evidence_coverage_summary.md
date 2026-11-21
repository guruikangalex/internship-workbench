# R4 证据分级覆盖率报告

批次：CO-REP-20261120-02-R4 ｜ 审核基线：`104aecfcad4c308e1044a3d15483fe2320619597` / `REVIEW-104AECF-20261121`
生成：`metadata/build_canonical_r4.py` ｜ 数据：`evidence_index.csv`（186 行，utf-8-sig）

## 口径定义（先读，避免把「ID存在」当「证据已核实」）

| 列 | 枚举 | 含义 |
|---|---|---|
| id_coverage | COVERED_CRITICAL / COVERED_EXECUTION / COVERED_CANONICAL | 该 ID 在规范主档 critical 列表 / 执行期 evidence_ids / 其余规范引用中出现 —— **仅表示 ID 可追溯** |
| source_accessibility | HTTP_200 / HTTP_202 / HTTP_403 / HTTP_000 / LOCAL_FILE_PRESENT / LOCAL_FILE_MISSING / NO_PATH | 原始 URL 在 2026-11-21 用 `curl -sL -A Mozilla/5.0 --max-time 20` 实测的 HTTP 状态；本地反引号路径按文件是否存在判定 |
| source_read_rate | READ_FULL / READ_PARTIAL / NOT_READ | 原文是否**实际阅读**。本轮只把 5 行（下表）记为 READ_FULL；403 仅见导航或仅经已存抽取物阅读的记 READ_PARTIAL；其余占位保持 NOT_READ |
| decisive_fact_verification | VERIFIED / UNVERIFIED | 决定性事实（具体数值/公式/条款）是否与原文页级定位核对 —— 只有下表 5 行为 VERIFIED |
| independent_review | DONE / NOT_DONE | 是否有第二方独立重导同一事实（reviewer 高精度计算 / 独立工作簿复算）—— 只有 2 行为 DONE |

> 可访问（可访问率分子）= HTTP_200 或 LOCAL_FILE_PRESENT。HTTP_202（Harvard Dataverse 异步受理、0 字节）、HTTP_403（Cloudflare/SSRN 拦截）、HTTP_000（连接超时）均**不计**为可访问。

## 五个率（全体 / 五个重点实验分组）

| 分组 | ID 覆盖率 | 原始来源可访问率 | 原文实际阅读率 | 决定性事实核验率 | 独立复核率 |
|---|---|---|---|---|---|
| 全体 186 行 | 186/186 = 100.0% | 42/186 = 22.6% | 59/186 = 31.7%（其中 READ_FULL 24/186 = 12.9%） | 5/186 = 2.7% | 2/186 = 1.1% |
| 五个重点实验所依赖证据（P001+P006+P008，52 行） | 52/52 = 100.0% | 24/52 = 46.2% | 29/52 = 55.8%（其中 READ_FULL 5/52 = 9.6%） | 5/52 = 9.6% | 2/52 = 3.8% |
| P001-E01（15 行） | 15/15 = 100.0% | 13/15 = 86.7% | 13/15 = 86.7%（其中 READ_FULL 3/15 = 20.0%） | 3/15 = 20.0% | 1/15 = 6.7% |
| P006-E01（P006 证据行，与 E06 共用）（32 行） | 32/32 = 100.0% | 9/32 = 28.1% | 13/32 = 40.6%（其中 READ_FULL 1/32 = 3.1%） | 1/32 = 3.1% | 0/32 = 0.0% |
| P006-E06（P006 证据行，与 E01 共用）（32 行） | 32/32 = 100.0% | 9/32 = 28.1% | 13/32 = 40.6%（其中 READ_FULL 1/32 = 3.1%） | 1/32 = 3.1% | 0/32 = 0.0% |
| P008-E01（P008 证据行，与 E03 共用）（5 行） | 5/5 = 100.0% | 2/5 = 40.0% | 3/5 = 60.0%（其中 READ_FULL 1/5 = 20.0%） | 1/5 = 20.0% | 1/5 = 20.0% |
| P008-E03（P008 证据行，与 E01 共用）（5 行） | 5/5 = 100.0% | 2/5 = 40.0% | 3/5 = 60.0%（其中 READ_FULL 1/5 = 20.0%） | 1/5 = 20.0% | 1/5 = 20.0% |

被引用证据 ID 回指覆盖（critical ∪ execution evidence_ids）：88/98 = 89.8%
未回指的 10 个为执行期产物型 ID（RUN-/SHA256-/OUT-/FIG-/P008-B02~B05/reviewer-workbook-recompute），
不是论文原文证据，保留在执行目录的 evidence_ids 字段中，不补造为原文证据行。

## 本轮真实读过的原文与决定性事实（VERIFIED 明细）

| evidence_id | 依据（本地原文，含页码/行号） | 决定性事实 | 独立复核 |
|---|---|---|---|
| P001-S02 | NBER w15205 原文 Eq.(9) 存在（P001_NBER_w15205.txt:289-292）；a=0.742 非原文印值，属 reviewer 计算 | VERIFIED | DONE |
| P001-S05 | 正式版全文数据/公式节可读（P001_DynamicTrading.txt）；Table II 数值见原文 | VERIFIED | NOT_DONE |
| P001-S06 | 勘误原文 p.1：A15* 替换式 + 'otherwise not'（P001_DynamicTrading_corrigendum.txt） | VERIFIED | NOT_DONE |
| P006-S10 | NBER w32004 原文 p.18：UPSA Sharpe 1.92、LW 1.31、Ridge 1.59（pypdf 抽取核对） | VERIFIED | NOT_DONE |
| P008-S01 | OA 正式版 Table4 Panel A 7.84% / Panel B 3.01%（P008_pdf_extract/content.md L1172/L1174） | VERIFIED | DONE |

## URL 实测记录（curl，2026-11-21）

| evidence_id | HTTP | bytes |
|---|---|---|
| E-P018-S11 | HTTP_200 | 383979 |
| E-P020-S11 | HTTP_200 | 590121 |
| E-P020-S12 | HTTP_200 | 478151 |
| E-P021-S11 | HTTP_200 | 520808 |
| E-P021-S12 | HTTP_200 | 263642 |
| E-P021-S13 | HTTP_200 | 259921 |
| P001-S01 | HTTP_200 | 90691 |
| P001-S03 | HTTP_200 | 42463 |
| P001-S04 | HTTP_200 | 71237 |
| P001-S07 | HTTP_200 | 354622 |
| P001-S08 | HTTP_200 | 143394 |
| P001-S09 | HTTP_200 | 53339 |
| P001-S10 | HTTP_200 | 13745 |
| P001-S11 | HTTP_200 | 235660 |
| P001-S12 | HTTP_200 | 34401 |
| P001-S13 | HTTP_200 | 180753 |
| P002-S01 | HTTP_403 | 896437 |
| P002-S02 | HTTP_200 | 316268 |
| P002-S03 | HTTP_200 | 72649 |
| P002-S05 | HTTP_000 | 0 |
| P002-S06 | HTTP_403 | 5464 |
| P002-S07 | HTTP_200 | 53545 |
| P003-S01 | HTTP_403 | 5577 |
| P003-S02 | HTTP_403 | 896437 |
| P003-S03 | HTTP_200 | 67180 |
| P003-S04 | HTTP_000 | 0 |
| P003-S05 | HTTP_200 | 211167 |
| P004-S01 | HTTP_403 | 5577 |
| P004-S02 | HTTP_200 | 500751 |
| P004-S03 | HTTP_200 | 221177 |
| P004-S04 | HTTP_200 | 40648 |
| P004-S05 | HTTP_200 | 240410 |
| P005-S02 | HTTP_403 | 5507 |
| P005-S03 | HTTP_403 | 0 |
| P006-S01 | HTTP_403 | 5570 |
| P006-S02 | HTTP_200 | 53115 |
| P006-S03 | HTTP_202 | 0 |
| P006-S04 | HTTP_200 | 9690 |
| P006-S11 | HTTP_403 | 896437 |
| P006-S12 | HTTP_200 | 53034 |
| P007-S02 | HTTP_000 | 0 |
| P007-S03 | HTTP_200 | 213002 |
| P007-S04 | HTTP_403 | 5864 |
| P008-S01 | HTTP_403 | 832981 |
| P008-S02 | HTTP_200 | 67510 |
| P008-S03 | HTTP_200 | 571367 |

## 与 R3 审查问题的对应

- R3 的 127 条 `DETAILS_NOT_IN_FROZEN_PACKAGE` 占位在本轮**仍保持 NOT_READ / UNVERIFIED / NOT_DONE**；
  补的是「可追溯 ID + 真实 HTTP 状态 + 诚实阅读等级」，不是把占位改写成「已核实」。
- 84 个 critical ID 全部在索引中（ID 覆盖 100%），但其中本轮读过原文的只有上表 5 行；
  二者必须分开报告，不能互相替代。
