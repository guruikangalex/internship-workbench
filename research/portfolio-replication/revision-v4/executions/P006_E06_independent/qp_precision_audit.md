# 任务 D：QP 精度审计（阈值 1e-7，不放宽）

run_id：`P006-E06-R4-AUDIT-001`。证据：`results/qp_highprecision.json`、`history/qp_diagnostics_*_v3_backup.json`。
原配置结果（B0 max 2.105e-7 / B1 max 1.555e-7）**原样保留**，未改 `config.json`/阈值。

## 残差定义与 status 含义

- 残差定义与 `independent_upsa.py:137-141` 一致：乘子自由 KKT
  `max( max(0,-W), max(0, u-QW), max|W·(QW-u)| )`，隐含乘子 λ = QW−u ≥ 0。
- `cvxopt status='optimal'` 只说明其内部 `abstol/reltol/feastol`（默认 1e-7）满足，**不等于**本 KKT 测度通过。
- 实测：494/494 窗 status 均为 `optimal`，但 B0 有 **14/494**、B1 有 **15/494** 窗 KKT > 1e-7。
  该现象被确认，不能因 status=optimal 就判为通过。

## 高精度诊断（同一批 u,Q，494 窗逐窗重解）

| 求解器 / 设置 | B0 max KKT | B1 max KKT | B0 n>1e-7 | B1 n>1e-7 |
| --- | --- | --- | --- | --- |
| cvxopt 默认（原配置，复算一致） | 2.105e-07 | 1.555e-07 | 14 | 15 |
| cvxopt 高精度（abstol=reltol=feastol=1e-12, maxiters=1e4） | **8.11e-13** | **9.20e-13** | 0 | 0 |
| cvxopt 高精度 + Q 缩放（objective 同除以 mean(diag Q)） | **2.96e-12** | **2.89e-12** | 0 | 0 |
| scipy SLSQP（ftol=1e-14, maxiter=2000） | 1.757e-07 | 2.138e-07 | 8 | 5 |

## 结论

- QP 可行，无 infeasible 窗；KKT 残差超阈值是 **cvxopt 默认容差（1e-7）** 的直接结果，
  不是病态矩阵导致求解失败：把容差收紧到 1e-12 后残差降到 ~1e-12，全部通过。
- 缩放 Q 在高精度下效果与不缩放相当（均 ~1e-12），说明病态不是主因；默认设置下略微超线是容差边界效应。
- 残留 KKT 与本环境 matmul FP 标志告警（任务 E）无关，两者机理不同。
- **处理**：保留原配置结果和 1e-7 阈值不放宽；高精度结果作为诊断记录于
  `qp_highprecision.json`。原摘要称"MARGINAL 而非失败"的量级判断与本次高精度诊断一致，
  但本审计将其明确为"容差限制、非可行性问题"。
