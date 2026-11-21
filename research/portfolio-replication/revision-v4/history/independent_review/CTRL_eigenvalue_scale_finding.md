# 总控独立复核：E06 特征值/ trace 尺度不一致（2026-11-21）

## 独立发现（不依赖 Agent C 结论）
对照 executions/P006_E01_author/cold_run/src/upsa.py 与
executions/P006_E06_independent/independent_upsa.py 源码：

- 作者 smart_eigenvalue_decomposition_covariance (upsa.py:132-140) 返回
  covariance = X X' / T 的特征值 lam_author（P>T 分支）。
- 作者 get_upsa_weights (upsa.py:47-53) 用 inv_eigs = W @ 1/(lam_author + z)，
  scale = sum(1/inv_eigs)/sum(lam_author)，两处尺度一致（均为 /T 特征值 + z）。
- 作者 w_and_lambda 的 ridge smoother 用 1/(lam_author+z)，原 T 分母约定。

- E06 eig_K (independent_upsa.py:65-70) 返回 K = X X' 的特征值 lam = T·lam_author（未除 T）。
- E06 prepare_full_basis (line 73-80) 用 invT = 1/(lam + T*z)，
  因 lam + T*z = T·(lam_author + z)，与作者 eff_port 只差整体因子 T（被归一化吸收），尺度正确。
- **E06 asset_weights (line 168-176) 用 inv_eigs = W @ 1/(lam + z)**，
  此处 lam 是未除 T 的 XX' 特征值，但 z 是作者网格（对应 lam_author 尺度）。
  与作者的 1/(lam_author+z) 相差 T 倍（T=120）。这会导致：
  (1) inv_eigs 量级错，scale = sum(1/inv_eigs)/sum(lam) 受影响；
  (2) pi = eff_port @ W * scale 的最终资产权重可能整体错误。

## 待 Agent C 数值确认
此发现是源码级推理，非定论。要求 Agent C 在 eigenvalue_trace_audit 中：
- 数值比较 E06 的 pi 与作者 pi（逐元素），确认是否整体差 T 倍或经 scale 后是否抵消；
- 判断 eff_port 的 T 因子与 asset_weights 的缺失 T 是否恰好抵消（若 eff_port 也少/多 T，可能抵消）；
- 修正或用实验证明无需修正；保留旧结果，新 run_id。
