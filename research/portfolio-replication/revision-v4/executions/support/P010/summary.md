# P010 第三轮补证 summary

## 关闭了什么
1. **TRACE 路线协议**：`trace_protocol.md` 严格与 ICE 分离，明确输入快照（TRACE 归档 hash/面板形状/206月×8759/2003-08…2020-09）、成本（tcost=0.00189=19bps，毛波动分母）、样本/信息时点、结果 ID（R06/R07 方向+量级验收）与验收量；明确禁止用零占位 MAT 和不同 ICE 表格数值判 TRACE。
2. **官方代码包审计**：`code_audit.md` 记录从 sethpruitt.net/research 实取两个 Dropbox 归档，归档/成员 hash 与 v2 逐字节一致；静态阅读 Table_3/4/8、JF2_pubdata 入口、成本与 ALS 规则；确认 `zeroedoutdata.mat` 为全零占位、原 ICE 未释放。

## 实际下载 / 运行了什么
- `curl` 下载 sethpruitt 研究页（57,563 B）；下载官方 ICE 代码包 ZIP（955,004,837 B，SHA-256 `43bf7bcd...bb09`，与 v2 一致）；下载 TRACE 公开数据 ZIP（491,720,701 B，SHA-256 `681725ee...5991`，与 v2 一致）。
- Python 读 ZIP 重算官方 12 个关键成员 + TRACE 6 个成员 hash，全部与 v2 `input_audit.json` 一致（`results/official_member_hash.json`、`results/trace_member_hash.json`）。
- 未运行任何 MATLAB / IPCA / 组合 / 成本计算。

## 剩余阻塞
- ICE 原研究成员快照仍 ENTITLEMENT_UNCONFIRMED（P010-B01），ICE 忠实路线 BLOCKED；Wiley SI 403、Internet Appendix 全文未读（P010-B04）。
- MATLAB 版本/运行环境未锁定；所有目标 `NOT_RUN` / `NOT_ASSESSED`，主审 PENDING；TRACE 仅 APPROXIMATE_VALIDATION。

## 写入路径
`.../revision-v3/executions/support/P010/`
- `data/sethpruitt_research.html`、`data/official_code_archive.zip`、`data/trace_public_archive.zip`
- `results/official_member_hash.json`、`results/trace_member_hash.json`
- `code_audit.md`、`trace_protocol.md`、`summary.md`、`sha256sums.txt`

大体积 ZIP 不逐字节计入 sha256sums；仅对脚本/报告/结果 JSON 计数。
