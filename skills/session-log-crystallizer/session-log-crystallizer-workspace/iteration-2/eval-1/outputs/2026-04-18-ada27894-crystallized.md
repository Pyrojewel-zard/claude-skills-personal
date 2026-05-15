---
type: crystallized-session
session_id: ada27894-21fa-42af-a907-818832682b49
project: andrej-karpathy-skills
created: 2026-04-18
crystallized_at: 2026-05-14
tags: [session, crystallized, skill-extraction, hook-design, karpathy-guidelines]
sources: ["inbox/notes/projects/andrej-karpathy-skills/logs/2026-04-18-ada27894-session.md"]
related_plans: ["inbox/notes/tools/Codex/sessions/2026-04-18-019da0a8-I-need-your-analysis-on-how-to-make-behavioral-gui.md"]
---

# Session 结晶: Karpathy Guidelines 的 Skill/Hook 模式提取与持久化方案

## 工作成果

### 完成的任务

1. 分析 `andrej-karpathy-skills` 项目，提取可复用的 skill/hook 模式
2. 与 Codex 讨论并确定 "Karpathy Guidelines" 在所有上下文中反复声明的方案
3. 编写实现计划（后因用户切换到 Innovus 综合任务而中断）
4. 完成 1to450 SIPO Innovus 综合脚本创建（Codex 审核 D 级，全部修正）

### 核心产出：可复用的 Skill/Hook 模式

#### 1. 可独立为 Skill 的模式

| 模式 | 来源 | 复用价值 |
|------|------|---------|
| Goal-Driven Execution | karpathy-guidelines | 可独立为 `/goal-driven` skill，将任何任务转为「验证标准 -> 循环直到通过」的工作流 |
| Surgical Changes | karpathy-guidelines | 可独立为 `/surgical` skill，作为代码修改前的约束检查 |
| Simplicity First | karpathy-guidelines | 可独立为 `/simplify` skill，核心逻辑：200行能50行就重写 |
| Think Before Coding | karpathy-guidelines | 可独立为 `/think-first` skill，在 `EnterPlanMode` 前强制列出假设和歧义 |

#### 2. 可提取为 Hook 的模式

| Hook | 触发点 | 作用 |
|------|--------|------|
| surgical-changes-reminder | `PreToolUse` -> `Edit`/`Write` | 提醒「只改必须改的行，不改相邻代码风格」 |
| simplicity-check | `PostToolUse` -> `Write` | 检查新文件行数，超过阈值时警告 |
| assumption-surfacing | `PreToolUse` -> `EnterPlanMode` | 强制在方案中列出假设和替代解读 |

## 决策记录

| 决策 | 依据 | 替代方案 |
|------|------|----------|
| 使用 CLAUDE.md + 2 个轻量 Hook 而非纯 Skill 方案 | Skill 是按需加载，但 Karpathy Guidelines 需要始终生效 | 纯 Skill 方案（不推荐，需要显式调用） |
| 使用 CLAUDE.md + 2 个轻量 Hook 而非全套 Hook 方案 | 个人使用时维护成本 > 收益 | Codex 建议的 5 层 hook 体系（适合团队/企业场景） |

### 最小有效方案

**CLAUDE.md（法典）+ 2 个 hook（执法）：**

```json
{
  "UserPromptSubmit": [{
    "hooks": [{
      "type": "command",
      "command": "echo 'Clarify first. Smallest fix. Only requested lines. Verify before done.'"
    }]
  }],
  "PreToolUse": [{
    "matcher": "Edit|Write",
    "hooks": [{
      "type": "command",
      "command": "echo 'Surgical: only change lines directly required by the request.'"
    }]
  }]
}
```

**不加的 hook 及原因：**

| Hook | 为什么不加 |
|------|-----------|
| PostToolUse 检测 | 启发式检测误报高，不如 `/simplify` skill 手动触发 |
| Stop hook | `/simplify` 已经在做完成前检查 |
| Hookify 规则 | 维护成本高于收益，regex 检测太脆弱 |

## 学习要点

### 技术技巧

1. **Mantra 压缩原则**：将行为准则压缩为一行 mantra（~15 token），便于高频注入而不浪费 token
   - 长版：`Clarify first. Smallest fix. Only requested lines. Verify before done.`
   - 短版：`Clarify. Simplify. Be surgical. Verify.`

2. **Hook vs Skill 的选择依据**：
   - Skill：按需加载的知识，适合 API 用法、配置参考
   - Hook：需要始终生效的行为约束，适合编码规范、质量检查

3. **Hook 热路径优化**：
   - `UserPromptSubmit` 和 `PreToolUse` 是热路径
   - 避免在热路径上用 LLM hook，用廉价 shell 命令注入短文本
   - `PostToolUse` 只做客观代理检测（行数、关键词），不做模糊哲学判断

4. **Codex 审核流程**：计划完成后可交给 Codex 审核，获取评级和修正建议

### 避坑指南

1. **Hook ID 命名约定**：必须遵循 `{事件}:{工具}:{功能}` 格式
2. **辅助类 hook 必须失败开放**：inject-rule.js 出错时应 exit 0，不阻塞主流程
3. **Hook 注入内容应尽量短**：规范要求注入内容尽量短，防止 token 浪费

## 与项目计划的关联

- 相关 Codex Session: [[inbox/notes/tools/Codex/sessions/2026-04-18-019da0a8-I-need-your-analysis-on-how-to-make-behavioral-gui.md]]
- 推进状态: 方案已确定，实现计划已编写，但被 Innovus 综合任务中断

## 下一步建议

1. **完成 Karpathy Guidelines 持久化方案实现**：
   - 创建 `~/.claude/rules/karpathy.md`（1 行 mantra）
   - 在 `settings.json` 中添加 2 个 hook
   - 在 `CLAUDE.md` 中添加引用

2. **将本结晶提取的模式应用到其他项目**：
   - Goal-Driven Execution 可整合到 plan 流程
   - Surgical Changes 可转为 hookify 规则

<!-- Crystallized from: inbox/notes/projects/andrej-karpathy-skills/logs/2026-04-18-ada27894-session.md -->
<!-- Crystallized on: 2026-05-14 -->
