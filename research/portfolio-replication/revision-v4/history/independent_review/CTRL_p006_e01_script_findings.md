# 总控独立复核：P006-E01 build_comparison.py 四问题（2026-11-21）

在 Agent B 修复前，总控直接读取 R4 继承的 build_comparison.py 核验审查意见：

1. 硬编码路径：line 5-6 BASE/TARGET 均为绝对机器路径；BASE 指向 revision-v3（旧批次），
   PYBIN (line 14) 也是绝对路径。属实。
2. 数组静默截断：line 124-127 maxabs() 用 n=min(len(fa),len(fb))，长度不一致时不报错而截断。属实。
3. All-UPSA 无条件 PARTIAL：line 184-186 对 rid=="P006-T01-ALL-UPSA" 若 verdict==FAIL 一律改 PARTIAL，
   未按冻结容差规则判定。属实（0.6645123437 显示0.66 vs 印刷0.67，属舍入边界但需规则化）。
4. 硬编码解释数值：line 219-220 把 0.6652235374/0.6649162636/0.6645123437 等具体值写入解释字符串，
   非当次运行生成。属实。

结论：审查意见四点均有源码证据，Agent B 必须实质修改而非仅移动行号。
总控将在 Agent B 返回后复核修复版是否消除上述问题（尤其 min(len)、无条件PARTIAL、硬编码数值）。
