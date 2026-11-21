# P002 第三轮补证 summary

## 关闭了什么

1. **D01–D03 真实输入入口问题（部分关闭，结论为 NOT_FOUND）**：实际尝试 Ken French、JKP、ReplicationCrisis 三条公开入口，并在本地全部挂载点按精确文件名检索。`usa.csv` / `usa_dsf.csv` / `world_ret_monthly.csv` 均 `NOT_FOUND`，确认需 WRDS Global Factor Data 权限或作者提供，非公开可得。证据：`code/verify_data_entry.py`、`results/data_entry_manifest.json`、`logs/verify_data_entry.stdout.log`、克隆的 `data/ReplicationCrisis_repo/`（commit `67174c7f...`）。
2. **D07 公开代理取得**：Ken French FF3 monthly ZIP 实取，13078 B / SHA256 `b03d39e4...`，1203 月（192607–202609）；登记为 `APPROXIMATE_VALIDATION` 的 RF 代理，不冒充原 vintage 输入。
3. **静态核对完成**：逐行核对 I21（净收益方差）、I22（财富递推）、I23（训练/投资宇宙）、I24（缺失值筛选）、I25（路径字面值），写入 `static_audit.md`，每条含论文原句、作者原码行、对照边界与状态；**未宣称作者错误**。
4. **E01/E21 关系厘清**：E21 是 E01 的精化/扩展，同 Table 2；建议 E01 作历史别名合并追踪，正式只保留 E21 99 单元，E28 为平行审计分支（需主审确认）。

## 实际下载 / 运行了什么

- `curl` 下载 Ken French FF3 monthly ZIP（HTTP 200，13078 B）。
- `git clone --depth 1 https://github.com/bkelly-lab/ReplicationCrisis.git`（commit `67174c7f170bf8b952b3c86876f187fd9970b5ba`）。
- JKP `https://www.jkpfactor.com/data/` 尝试失败（curl 35 SSL_ERROR_SYSCALL，HTTP 000）。
- 用 Python 3.9.6 运行 `verify_data_entry.py`，生成 manifest 与日志（exit 0，无 stderr）。
- 未运行任何 R 脚本、未训练、未回测。

## 剩余阻塞

- D01–D03 需 WRDS 授权或作者提供快照（硬阻塞，非本 agent 可解决）。
- I21/I22 需在真实数据上做运行时 AUM 路径比率与净/毛方差分解审计（P002-E28），当前 `NOT_RUN`。
- R 4.3.0 + 依赖 + HPC/SLURM 环境未搭建；I25 路径补丁仅在运行时处理。
- P002-E21 99 单元维持 `REQUEST_EVIDENCE` / `NOT_RUN`；主审须确认 E01→E21 合并与方差口径归属。

## 写入路径

`.../revision-v3/executions/support/P002/`
- `code/verify_data_entry.py`
- `results/data_entry_manifest.json`
- `logs/verify_data_entry.stdout.log`、`logs/verify_data_entry.stderr.log`
- `data/F-F_Research_Data_Factors_CSV.zip`、`data/jkp_landing.html`（0 B）、`data/ReplicationCrisis_repo/`
- `static_audit.md`、`summary.md`、`sha256sums.txt`

数据文件 `data/` 下的大体积克隆目录不逐文件计入 sha256sums；仅对脚本/配置/日志/结果/报告计数。
