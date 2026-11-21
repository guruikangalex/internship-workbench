# 总控复核：P006-E01 All-UPSA verdict 变化（2026-11-21）

Agent B 按审查意见修复 build_comparison.py 后，R4 verdict 相对 R3 有一处实质变化：
- P006-T01-ALL-UPSA：R3 PARTIAL → R4 FAIL。
- 原因：R3 脚本 line 184-186 对 rid=="P006-T01-ALL-UPSA" 无条件把 FAIL 改 PARTIAL，属无依据硬编码豁免；
  R4 改为统一 scalar_verdict() 按数值+冻结容差判定，fresh 0.6645123437 显示 0.66 vs 印刷 0.67，
  绝对误差 0.005488 > 冻结容差 0.005 → FAIL。
- 总控核对：target_comparison.csv(R3, 90/17/8) 保留未动；target_comparison_r4.csv(R4, 90/18/7) 独立新文件；
  discrepancy_analysis.csv 25 行含 verdict_r3/verdict_r4 双列，变化可追溯。
结论：该变化是"取消无依据豁免"而非"放宽/收紧容差追数"，符合主审原则 2/10。最终验收交主审。
