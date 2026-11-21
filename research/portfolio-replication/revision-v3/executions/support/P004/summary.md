# P004 第三轮补证 summary

## 关闭了什么
1. **版本映射**：`version_map.md` 统一 QF2023_VOR_CANDIDATE、arXiv v1、代码快照 commit b5e299a 与 R05(Exp4/Table 9)/R06(Exp5/Table 11/Fig 7) 的映射；明确 QF 版编号未核、R05/R06 非论文数值证据。
2. **DGP/窗口/初始化材料**：逐行给出 DataLoad.synthetic_exp、SlidingWindow、e2e_net 的源码证据与实测（perf_period=13→14 未来收益、seed 123/2000/3000/4000、γ/δ 初值）。
3. **梯度预检实跑**：用作者未改代码对六个 Exp5 配置各做一次 forward/backward/Adam step，六项全 PASS（梯度有限、更新非零、权重和≈1），记录 stdout/stderr 与 JSON。

## 实际下载 / 运行了什么
- 使用已克隆 P004_repo commit b5e299ad；在 p004_venv 中补装 pandas_datareader/alpha_vantage/statsmodels/psutil 以导入作者模块（未改算法）。
- Python 3.13.12 / torch 2.15.0 运行 `gradient_preflight.py`：exit 0，OVERALL PASS，stderr 空。首轮因缺 pandas_datareader 失败（已记录），补装后成功。
- 未读作者 cache/*.pkl，未跑 CV/roll_test，未运行 Table 11/Fig 7。

## 剩余阻塞
- 正式 QF 版合成实验正文/附录 403 NOT_READ，与 arXiv v1 的 Table 10/11/Fig 7 编号和数值尚未核验 (I02/I03/I04 开放)。
- 训练完整 Table 11/Fig 7 需专门审批；结论 NOT_ASSESSED。
- 依赖版本与原文（Py3.8.5/PyTorch 1.10/cvxpylayers 0.1.4）数值等效性无证据。

## 写入路径
`.../revision-v3/executions/support/P004/`
- `code/gradient_preflight.py`
- `results/gradient_preflight.json`、`results/grad_cache/`（作者 init_state 落点，非结果缓存）
- `logs/gradient_preflight.stdout.log`、`logs/gradient_preflight.stderr.log`
- `version_map.md`、`summary.md`、`sha256sums.txt`
