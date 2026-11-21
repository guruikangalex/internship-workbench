# P006-E01 作者原码复现审查 R4 摘要（Agent B）

Run ID `RUN-P006-E01-AUTHOR-20261121-R4`（重跑恢复冷 bundle）；比较脚本 run_id `RUN-P006-E01-AUTHOR-20261121-R4`。
冻结提交 `104aecf`；审批 `REVIEW-104AECF-20261121`。所有数字来自实际运行。

## 任务 A：真实作者代码环境核验（完成）

- ZIP `P006_upsa_reproduction_RFS_v2.zip` SHA256 = `a20c2fb…699b`（一致）、MD5 = `b8cac94b…4656`（一致），123737306 B。
- `cold_run/` 源码 + 5 个 CSV 与 ZIP 逐文件 SHA256 **30/30 完全一致**（`manifest_license_check.json`）；算法未改。
- 冷目录隔离空启动（outputs 跑前 0 文件）；`run_all.py --main --compute` 真实从 CSV 重算（stdout `computing rolling-window engine`）。
- 发现 R3 遗留问题：`cold_run/outputs/computed/main_bundle.p`（R3 日志记 `3ebba382…`）在磁盘上缺失。R4 以新 run 重跑（79 s，exit 0），新 bundle SHA256 = `3ebba382…a91`，与 R3 日志完全一致；22 产物逐项 `shasum -c` 全部 OK → 确定性复现，非读缓存。
- 口径确认：494 月（1981-11..2022-12）、月频、T=120、`z_grid=logspace(-10,-1,10)`、W≥0 无单纯形、二阶矩非中心化 `X'X/T`、`opt_port` NaN=0/Inf=0。见 `static_check.md`、`LW_diagnosis.md`。

## 任务 B：4 个脚本问题修复 + 115 行重生成（完成）

| # | v3 问题 | R4 修法（已实测） |
| --- | --- | --- |
| 1 | 第 5-16 行硬编码执行者绝对路径 | 改 `argparse`：`--base/--target/--extracted/--out/--pybin`，默认相对本文件（`HERE`、向上发现工作根）；新脚本无 `/Users/...` 硬编码。 |
| 2 | 第 124-129 行 `min(len(a),len(b))` 静默截断 | 改 `strict_maxabs()` 键控比较：缺失/多余项/长度不一致显式列出并强制 `NOT_ASSESSED`，不截断。注入测试确认（缺失 `c`、列表长度 3vs4 均被检出）。 |
| 3 | 第 185-186 行对 All-UPSA 无条件 PARTIAL | 改 `scalar_verdict()` 统一按数值+冻结容差计算，无 result_id 特判。All-UPSA `0.005488 > 0.005` → **FAIL**（原 PARTIAL 是无依据硬编码豁免）。 |
| 4 | 第 219-220 行解释文本硬编码数值 | 改 `boundary_note()`/`expl` 从当次 `fresh/manuscript/regen/paper` 生成；All-UPSA 边界分析含实时数值，无硬编码。 |

- 旧版保留为 `build_comparison_v3_backup.py`（SHA `54efa2e3…`）；新脚本 `build_comparison.py`。
- 新表 `target_comparison_r4.csv`（115 行 × 44 列，**不覆盖** R3 的 115 行 `target_comparison.csv`），新增 `author_cache_value`/`cold_run_value`/`suspected_cause`/`confirming_test`（FAIL/PARTIAL 必填）。
- **重生成 verdict 分布**：PASS 90 / FAIL 18 / PARTIAL 7 / NOT_ASSESSED 0（R3 为 90/17/8/0）。唯一变化：`P006-T01-ALL-UPSA` PARTIAL→FAIL（统一规则下无豁免）。旧 FAIL/PARTIAL 全部保留在 R3 文件与 `discrepancy_analysis.csv` 的 `verdict_r3` 列。
- 运行日志：`run_comparison_stdout.log` / `run_comparison_stderr.log`（exit 0，strict issues 0）。

## 任务 C：17 FAIL + 8 PARTIAL 逐项分析（完成）

- `discrepancy_analysis.csv`：25 行（原 17 FAIL + 8 PARTIAL 全覆盖），逐项给出 paper/author_cache/cold_run 值、absolute_error、tolerance、R3/R4 verdict、`suspected_cause`、`confirming_test`。
- **LW 家族 14 FAIL 根因**（详细见 `LW_diagnosis.md`）：源码与输入逐字节一致、冷重跑确定性复现；差异出现在数值层——作者缓存生成环境(LAPACK/BLAS、缓存时点)与本地固定环境不同，首个窗口 1981-11-30 即分叉；LW 非线性收缩对全部 120 个特征值求逆（最小 2.797e-7，逆权重 3.57e6，条件数 1.41e5），把 1e-12 级特征值差异放大到 1.67e-3 权重 / 1.6e-3 单月回报。PCA（独立特征分解）max 4.9e-11、FF5/CAPM 一致，反证非输入/时序层。
- UPSA 擦边 3 FAIL + Ridge alpha 1 FAIL：同量级数值漂移，abs 0.0055~0.0088，统一容差 0.005 下 FAIL。
- **All-UPSA**：paper 0.67 / fresh 0.664512 / manuscript 0.665224 / regen 0.664916，边界 0.6650，fresh 距边界 0.000488；abs 0.005488 稳定超 0.005 → FAIL。无无限豁免，边界分析由当次数据生成。
- 7 PARTIAL：Fig3 After-2000-UPSA（作者参考仅，abs 0.000817≤0.005 但显示跨档）+ 6 个面板逐点超冻结阈值（Fig6 5e-6 Sharpe / Fig8 1e-5 百分点），索引/长度严格一致，非实现缺失。

## 交付文件（仅本目录，未改顶层主档/其他实验目录）

- 脚本：`build_comparison.py`（修复版）、`build_comparison_v3_backup.py`（旧版）
- 比较：`target_comparison_r4.csv`（新 115 行）、`discrepancy_analysis.csv`（25 行）
- 诊断：`LW_diagnosis.md`、`lw_diagnosis_experiment.py`、`lw_diagnosis_data.json`、`lw_diagnosis_stderr.log`
- 核验：`manifest_license_check.json`、`verify_license.py`、`strict_validation_test.log`
- 日志：`run_comparison_stdout.log`、`run_comparison_stderr.log`、`run_computation_r4_stdout.log`、`run_computation_r4_stderr.log`、`run_stdout_r3.log`/`run_stderr_r3.log`（R3 备份）
- 本摘要：`summary_r4.md`、`sha256sums_r4.txt`

最终发表数值验收交主审；本轮未放宽容差、未改作者算法、未删除旧记录。
