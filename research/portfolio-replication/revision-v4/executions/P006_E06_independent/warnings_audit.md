# 任务 E：数值警告与环境审计

run_id：`P006-E06-R4-AUDIT-001`。证据：`results/audit_E_warnings.json`。

## 警告定位（不直接宣布无害）

`run_full.log` / `run_first_window.log` 中 `RuntimeWarning: divide/overflow/invalid encountered in matmul`
出现在 `independent_upsa.py` 的以下计算点（行号来自旧日志路径，对应本目录同名文件行号）：

| 行 | 计算 | 复现的警告数 | 输出是否有限 |
| --- | --- | --- | --- |
| 67 | `K = X @ X.T` | 3 | 是 |
| 79/81/82 | `Vt1`、`g1`、`eff_port = X.T @ g1` | 12 | 是 |
| 92/93 | `stable_loo` 的 `g1`、`dg` | 18 | 是 |
| 326 | `u = A.mean(0)`, `Q = A.T@A/T` | 21 | 是 |

日志计数：`run_full.log` 30 条、`run_first_window.log` 69 条、`run_metrics.log` 3 条、`run_compare.log` 0 条。

## 影响范围（逐窗全扫描，494 窗）

- 输入数据 `factors_main.csv`（614×153）：NaN=0、Inf=0，全有限。
- 全扫描 494 窗、每窗 6 个关键中间量：发出 14820 条 numpy 警告，但
  **非有限中间量的窗口数 = 0**，**实际 FloatingPointError 窗口数 = 0**。
- 所有最终输出（494 月收益、153 维权重）经 `full_run_summary.json` 有限性检查全部为 True。

## 警告性质（关键控制实验，不能只说"无害"）

- 对 `X @ X.T` 施加 `np.errstate(divide='raise', over='raise', invalid='raise')`：
  **确实抛出** `FloatingPointError('divide by zero encountered in matmul')` —— FP 状态标志被真实置位，
  不是 numpy 的误报文案。
- 但用**纯随机有限数组** `rng.standard_normal((120,153)) @ .T` 复现：同样 3 条警告、输出仍有限；
  而 `(4,4)` 小矩阵无警告、`errstate` 不抛异常。
- **结论**：这是本环境 numpy 2.0.2 + 底层 BLAS 在**较大矩阵 matmul**时置位 FP 标志的
  库/硬件 quirk（数据无关，随机矩阵也触发）；它不改变任何数值结果（所有中间量与输出有限）。
  精确表述：FP 标志为真、结果有限、无逐月/逐行/逐列的选择性损坏；
  不应笼统写"全部无害而不影响"，而应写"警告在本环境可被控制实验复现、输出经全窗验证有限"。
- 该 quirk 与任务 D 的 QP KKT 残差是**不同问题**：后者是 cvxopt 容差，不是 FP 标志告警。

## 依赖与环境可重建性

- `requirements.txt` 当前内容：numpy==2.0.2 / scipy==1.13.1 / pandas==2.3.3 / cvxopt==1.3.3 /
  statsmodels==0.14.6 / **python==3.9.6**。
- **问题**：`python==3.9.6` 不是 pip 包，`pip install -r requirements.txt` 会尝试拉取不存在的
  `python` 分发包而失败。直接依赖应只含 5 个库，Python 版本归入 `environment.json`。
- `environment.json` 已记录 python 3.9.6、numpy/scipy/pandas/cvxopt/statsmodels 版本与
  cvxopt 选项、commit、独立实现声明；**但缺 pip 版本**。本环境实测：`pip 26.0.1`（python3.9），
  Python 可执行文件 `.../env_py396/bin/python`。
- 建议：从 requirements.txt 移除 `python==3.9.6`；在 environment.json 增补 pip 版本；
  传递依赖不锁（已由完整 pip freeze + 冻结 env 捕获）。
