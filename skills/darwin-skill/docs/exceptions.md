# 异常与边界条件处理

流程假设环境理想，但实操常遇异常。以下预定义 fallback，保证优化过程不会「一跑就卡住」。

## 异常处理表

| 场景 | 触发条件 | 处理动作 |
|---|---|---|
| 不在 git 仓库 | `git rev-parse` 失败 | 提示用户「建议 git init」；若拒绝，用 `cp SKILL.md SKILL.md.bak.YYYYMMDD-HHMM` 文件备份代替 revert |
| results.tsv 缺失 | 文件不存在 | 新建并写表头行（9列：含 eval_mode） |
| results.tsv 损坏 | 列数不匹配 / 非TSV | 备份为 `.bak.YYYYMMDD-HHMM` 后重建，告知用户 |
| 分支已存在 | `git checkout -b` 失败 | 分支名末尾加 `-2` / `-3`；第3次失败则切回现有分支并询问继续还是新起 |
| `git revert` 失败 | 冲突 / 工作树脏 | 先 `git stash`，重试；仍失败则从上一个 commit 的 SKILL.md 读出覆盖当前文件手动恢复 |
| MAX_ROUNDS 触顶（默认3） | 已跑3轮仍有短板 | 展示当前最弱维度，问用户：「继续加1轮 / 进入探索性重写 / 跳过这个skill / 收工」 |
| 优化后超 150% 体积 | 新文件 > 原 × 1.5 | 拒绝提交，回到改进步骤精简（删冗余/合并重复），再评 |
| test-prompts.json 已存在 | 文件已在 skill 目录 | 默认复用并展示，问用户「复用 / 重写 / 追加」三选一 |
| SKILL.md 找不到 | 目录存在但无 SKILL.md | 该 skill 终止，results.tsv 记 `status=error`，继续下一个 |
| 分数计算规则 | 浮点精度漂移 | 总分保留 1 位小数，改进需严格 > 旧分（不靠四舍五入） |
| 子 agent 不可用 | spawn 失败 / 超时 | 进入干跑验证模式，标注 `dry_run` |

## 干跑验证流程

当子 agent 不可用时，用以下流程替代实测：

```
1. 读取目标 SKILL.md 全文
2. 选择一个测试 prompt（从 test-prompts.json）
3. 模拟执行：
   - 按 skill 定义的步骤，逐步推演
   - 记录每个步骤的预期输出
   - 标注哪些步骤顺利、哪些步骤卡住
4. 输出评估：
   - 输出是否符合 expected 描述？
   - 有没有 skill 引入的负面影响？
5. 打分：基于推演结果打 1-10 分
   - 10分：完全符合预期，流程顺畅
   - 7-9分：基本符合，有小问题
   - 4-6分：部分符合，有明显卡点
   - 1-3分：严重偏离或无法执行
```

## results.tsv 数据校验

除了列数检查，还需验证：

| 字段 | 类型 | 校验规则 |
|------|------|----------|
| timestamp | ISO8601 | 格式：YYYY-MM-DDTHH:MM |
| commit | string | 7字符 hex 或特殊值（baseline/improved/final/deleted/error） |
| skill | string | 非空，匹配现有 skill 目录名 |
| old_score | float | 0-100 或 "-"（baseline 时） |
| new_score | float | 0-100 |
| status | enum | baseline/keep/revert/deleted/error |
| dimension | string | 非空（error 时可为 "-"） |
| note | string | 非空 |
| eval_mode | enum | full_test/dry_run |

校验失败时：备份损坏文件，重建表头，告知用户。

## 原则

**异常先告知用户，再按规则处理；绝不静默跳过或静默失败。**