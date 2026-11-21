# P006 LOO 分母配对审计（REV2-P006-09）

## 本执行做了什么
闭合 issue `REV2-P006-09`（OPEN → CONFIRMED）：在作者真实数据第一个训练窗（factors_main，T=120，P=153，1971-11 至 1981-10）上，运行配对的 LOO 分母路径，比较完整目标敏感性，**保留作者实现不修改**。

性质：**IMPLEMENTATION_AUDIT**，不是原文数值复现；不回填 P006-E01/E05 的正式结果栏（仍 NOT_RUN）。

## 三条路径
- A 作者实现：`src/upsa.py::w_and_lambda` 用 /T + w_adj/z，z 不重标；LOO=(wbar−w)/(1−w)。
- B 论文对齐：仅在 LOO 平滑器把惩罚 z→z·(T−1)/T；全窗 basis 仍用原始 z。
- C 直接 T−1（诊断对照，非论文亦非作者）：smoother /(T−1)、w_adj/(T−1)、z 不重标。

## 关键结果（真实执行，见 audit_loo_divisor_results.json）
1. **一致性自检 PASS**：path A 的 best_z=6、10 维混合系数 W 与作者 fit L2=0、153 维资产权重 π 与作者 `get_upsa_weights()` L2=0。证明 path A 忠实复现作者实现。
2. **best_z 三路径均为 6**（z=10^-5），排序稳定。
3. **A vs B（论文分母对齐）**：W 混合系数 Fro=0.00582；资产权重 π Fro=0.0689；单 z 的 LOO 月收益最大绝对差约 6.4e-3。差异小，集中在低 z。
4. **A vs C（直接换分母不重标）**：W Fro=0.239；资产权重 π Fro=12.61；低 z（1e-7）LOO 差达 144.8——**证明直接把 /T 改成 /(T−1) 而不重标 z 是错误的**，支持作者实现与协议 PREFLIGHT-03 的判断。
5. 低 z=1e-10 的 A vs B 差 3.5e-3、C 差 4.5，印证 P>T 时的数值敏感性/消去误差，不能归因于分母单一因素。

## 变量口径（审查意见强调）
- W ∈ R^L（L=10）是岭基组合的**混合系数**，约束仅 W≥0，无 sum(W)=1。
- π ∈ R^N（N=153）是最终**资产权重**。二者不得混淆；本审计分别记录。
- 二阶矩为非中心化 E[rr']，未去均值。

## 复现命令
```bash
export UPSA_PACKAGE_DIR=<作者 P006 复现包解压目录>
PY=<本机 Python 3.9.6 解释器路径>
cd <本目录>
$PY -W ignore audit_loo_divisor.py > audit_loo_divisor.log 2> audit_loo_divisor_stderr.log
```
依赖：Python 3.9.6，numpy 2.0.2，pandas 2.3.3，cvxopt 1.3.3（作者 requirements.txt）。
脚本内 `PKG` 由环境变量 UPSA_PACKAGE_DIR 提供（默认相对路径）。接收方下载 Dataverse DOI 10.7910/DVN/OHZFKD（file 14008244，MD5 b8cac94b06f22aa8bab676c0c1ec4656）解压后指向该目录。

## 文件
- audit_loo_divisor.py — 审计脚本（不改作者源码）
- audit_loo_divisor_results.json — 结果（含 hash、per_z、full_target、verdict）
- audit_loo_divisor.log / audit_loo_divisor_stderr.log — 完整 stdout/stderr
