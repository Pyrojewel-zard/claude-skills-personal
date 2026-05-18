---
name: darwin-skill
description: "Darwin Skill (达尔文.skill): autonomous skill optimizer inspired by Karpathy's autoresearch. Evaluates SKILL.md files using an 8-dimension rubric (structure + effectiveness), runs hill-climbing with git version control, validates improvements through test prompts, and generates visual result cards. Use when user mentions \"优化skill\", \"skill评分\", \"自动优化\", \"auto optimize\", \"skill质量检查\", \"达尔文\", \"darwin\", \"帮我改改skill\", \"skill怎么样\", \"提升skill质量\", \"skill review\", \"skill打分\"."
---

# Darwin Skill

> 借鉴 Karpathy autoresearch 的自主实验循环，对 skills 进行持续优化。
> 核心理念：**评估 → 改进 → 实测验证 → 人类确认 → 保留或回滚 → 生成成果卡片**
> GitHub: https://github.com/alchaincyf/darwin-skill

---

## TL;DR

darwin-skill 用于自动优化其他 skills：
1. **评估**：8维度打分（结构60分 + 效果40分）
2. **改进**：针对最低维度提出方案
3. **验证**：用测试 prompt 跑一遍
4. **决策**：改进则保留，退步则回滚

触发词：优化skill、skill评分、达尔文、darwin、auto optimize

---

## 设计哲学

autoresearch 的精髓：
1. **单一可编辑资产** — 每次只改一个 SKILL.md
2. **双重评估** — 结构评分（静态分析）+ 效果验证（跑测试看输出）
3. **棘轮机制** — 只保留改进，自动回滚退步
4. **独立评分** — 评分用子agent，避免「自己改自己评」的偏差
5. **人在回路** — 每个skill优化完后暂停，用户确认再继续

与纯结构审查的区别：不只看 SKILL.md 写得规不规范，更看改完后**实际跑出来的效果是否更好**。

---

## 评估 Rubric（8维度，总分100）

### 结构维度（60分）— 静态分析

| # | 维度 | 权重 | 评分标准 |
|---|------|------|---------|
| 1 | Frontmatter质量 | 8 | name规范、description包含做什么+何时用+触发词、≤1024字符 |
| 2 | 工作流清晰度 | 15 | 步骤明确可执行、有序号、每步有明确输入/输出 |
| 3 | 边界条件覆盖 | 10 | 处理异常情况、有fallback路径、错误恢复 |
| 4 | 检查点设计 | 7 | 关键决策前有用户确认、防止自主失控 |
| 5 | 指令具体性 | 15 | 不模糊、有具体参数/格式/示例、可直接执行 |
| 6 | 资源整合度 | 5 | references/scripts/assets引用正确、路径可达 |

### 效果维度（40分）— 需要实测

| # | 维度 | 权重 | 评分标准 |
|---|------|------|---------|
| 7 | 整体架构 | 15 | 结构层次清晰、不冗余不遗漏、与花叔生态一致 |
| 8 | 实测表现 | 25 | 用测试prompt跑一遍，输出质量是否符合skill宣称的能力 |

### 评分规则

- 维度1-7：每个维度打 1-10 分，乘以权重得到该维度得分
- 维度8（实测表现）：跑2-3个测试prompt，按输出质量打1-10分
- **总分 = Σ(维度分 × 权重) / 10**，满分100
- 改进后总分必须 **严格高于** 改进前才保留

### 实测表现评分方式

```
1. 为每个skill设计2-3个典型用户prompt（见 test-prompts.json）
2. 用子agent执行：
   - with_skill: 带着SKILL.md执行测试prompt
   - baseline: 不带skill执行同一prompt
3. 对比两组输出，从以下角度打分：
   - 输出是否完成了用户意图？
   - 相比baseline，质量提升明显吗？
   - 有没有skill引入的负面影响？
```

如果子agent不可用，进入**干跑验证**模式（见 `docs/exceptions.md`）。

---

## 优化流程

### Phase 0: 初始化

```
1. 确认优化范围：
   - 全部skills → 扫描 .claude/skills/*/SKILL.md
   - 指定skills → 用户指定列表
2. 创建 git 分支：auto-optimize/YYYYMMDD-HHMM
   - 不在git仓库 → 用文件备份代替
3. 初始化 results.tsv（如不存在）
4. 为每个skill设计测试prompt（见 Phase 0.5）
```

### Phase 0.5: 测试Prompt设计

为每个skill设计测试prompt，保存到 `skill目录/test-prompts.json`：

```json
[
  {"id": 1, "prompt": "用户会说的话", "expected": "期望输出的简短描述", "category": "场景类型"},
  {"id": 2, "prompt": "...", "expected": "...", "category": "..."}
]
```

**测试prompt覆盖：**
- 最典型的使用场景（happy path）
- 一个稍复杂或有歧义的场景

展示所有测试prompt给用户，**确认后再进入评估**。

### Phase 1: 基线评估

```
for each skill in 优化范围:
  # 结构评分
  1. 读取 SKILL.md 全文
  2. 按维度1-7逐项打分（附简短理由）

  # 效果评分（用子agent）
  3. 对每个测试prompt，spawn子agent：
     - with_skill: 带着SKILL.md执行
     - baseline: 不带skill执行
  4. 对比输出，打维度8的分

  # 汇总
  5. 计算加权总分
  6. 记录到 results.tsv
```

展示评分卡，**暂停等用户确认**：

```
┌──────────────────────────┬───────┬──────────────┬──────────────┐
│ Skill                    │ Score │ 结构短板      │ 效果短板      │
├──────────────────────────┼───────┼──────────────┼──────────────┤
│ inbox-prepare            │ 72    │ 边界条件      │ 测试prompt2  │
│ session-log-crystallizer │ 66    │ 指令具体性    │ baseline持平  │
└──────────────────────────┴───────┴──────────────┴──────────────┘
```

### Phase 2: 优化循环

按基线分数从低到高排序，先优化最弱的。

```
for each skill:
  round = 0
  while round < MAX_ROUNDS (默认3):
    round += 1

    # Step 1: 诊断
    找出得分最低的维度

    # Step 2: 提出改进方案
    针对最低维度，生成改进方案：
      - 改什么（具体段落/行）
      - 为什么改（对应rubric哪条）
      - 预期提升多少分

    # Step 3: 执行改进
    编辑 SKILL.md
    git commit（格式见下方）

    # Step 4: 重新评估
    - 结构维度：主agent重新打分
    - 效果维度：spawn子agent重跑测试prompt

    # Step 5: 决策
    if 新总分 > 旧总分:
      status = "keep"，更新旧总分
    else:
      status = "revert"
      git revert HEAD
      记录失败尝试，break

    # Step 6: 日志
    results.tsv 追加行

  # 人类检查点
  展示改动摘要，等用户确认
```

**git commit message 格式：**
```
optimize {skill-name}: {dimension} - {brief note}

Example:
optimize session-log-crystallizer: 边界条件 - 添加session_id判重规则
```

### Phase 2.5: 探索性重写（可选）

当 hill-climbing 连续2个skill都在 round 1 就 break 时，提议「探索性重写」：

```
1. 选一个瓶颈skill
2. git stash 保存当前最优版本
3. 从头重写SKILL.md（重新组织结构和表达方式）
4. 重新评估
5. if 重写版 > stash版: 采用重写版
   else: git stash pop 恢复
```

**必须征得用户同意后才执行。**

### Phase 3: 汇总报告

```
## 优化报告

### 总览
- 优化skills数：N
- 总实验次数：M
- 保留改进：X（Y%）
- 回滚次数：Z

### 分数变化
┌──────────────────────────┬────────┬────────┬────────┐
│ Skill                    │ Before │ After  │ Δ      │
├──────────────────────────┼────────┼────────┼────────┤
│ inbox-prepare            │ 72     │ 83     │ +11    │
│ session-log-crystallizer │ 66     │ 86     │ +20    │
└──────────────────────────┴────────┴────────┴────────┘
```

生成成果卡片（见 `docs/result-card.md`）。

---

## 优化策略库

按优先级排序，每轮只做最高优先级的一个：

### P0: 效果问题（实测发现的）
- 测试输出偏离用户意图 → 检查skill是否有误导性指令
- 带skill比不带还差 → skill可能过度约束，考虑精简
- 输出格式不符合预期 → 补充明确的输出模板

### P1: 结构性问题
- Frontmatter缺少触发词 → 补充中英文触发词
- 缺少Phase/Step结构 → 重组为线性流程
- 缺少用户确认检查点 → 在关键决策处插入

### P2: 具体性问题
- 步骤模糊（"处理图片"）→ 改为具体操作和参数
- 缺少输入/输出规格 → 补充格式、路径、示例
- 缺少异常处理 → 补充 "如果X失败，则Y"

### P3: 可读性问题
- 段落过长 → 拆分+用表格
- 重复描述 → 合并去重
- 缺少速查 → 添加TL;DR

---

## 约束规则

1. **不改变skill的核心功能和用途** — 只优化"怎么写"和"怎么执行"
2. **不引入新依赖** — 不添加skill原本没有的scripts或references
3. **每轮只改一个维度** — 避免多个变更导致无法归因
4. **保持文件大小合理** — 优化后SKILL.md不应超过原始大小的150%
5. **尊重花叔风格** — 中文为主、简洁为上
6. **可回滚** — 所有改动在git分支上，用git revert而非reset --hard
7. **评分独立性** — 效果维度必须用子agent或干跑验证

---

## 使用方式

| 命令 | 流程 |
|------|------|
| "优化所有skills" | Phase 0-3 完整流程 |
| "优化 xxx 这个skill" | Phase 0.5-2 单个优化 |
| "评估 xxx 的质量" | Phase 0.5-1 仅评估不改 |
| "看看优化历史" | 读取并展示 results.tsv |

---

## 设计灵感

> "You write the goals and constraints in program.md; let an agent generate and test code deltas indefinitely; keep only what measurably improves the objective."
> — Karpathy, autoresearch

对应关系：
- **program.md** → 本文件（评估rubric和约束规则）
- **train.py** → 每个SKILL.md
- **val_bpb** → 8维加权总分
- **git ratchet** → 只保留有改进的commit
- **test set** → test-prompts.json

区别：增加了人在回路，以及双重评估机制（结构+效果）。

---

## 相关文档

- `docs/exceptions.md` — 异常与边界条件处理
- `docs/result-card.md` — 成果卡片生成
- `test-prompts.json` — 本 skill 的测试 prompt 集
- `results.tsv` — 优化历史记录
