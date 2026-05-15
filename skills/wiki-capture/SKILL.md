---
name: wiki-capture
description: |
  Use when the material is still low-density or provisional and should first be appended into raw notes before any compile or typed knowledge promotion.
  Triggers on: "capture", "记录到raw", "碎片记录", "临时笔记", "quick note", "append to raw".
user_invocable: true
---

# wiki-capture

运行 `/wiki-capture <material-or-text> --intent "<一句话意图>"`。

## 目标

把低密度输入先落到正确的 `raw/` 入口，不直接写 accepted wiki。

这是三入口 flow 的第一步：

`wiki-capture -> wiki-compile -> wiki-refine`

## 默认适用

- Claude Code / Codex 对话洞见
- 项目推进碎片
- Virtuoso 仿真截图与单次观察
- 课程片段
- 论文相关性提醒

## 执行步骤

### Step 1: 解析输入

1. 识别输入类型：文本、文件路径、截图、URL
2. 提取关键信息：主题、项目、日期
3. 判断意图：记录、追踪、提醒

### Step 2: 确定路由

| 输入类型 | 默认路由 |
|----------|----------|
| 项目/session/仿真 | `raw/notes/projects/{project}/logs/YYYY-MM-DD-{project}-log.md` |
| 独立课程/讲演录片段 | `raw/notes/courses/{course}/` |
| 论文相关性提醒 | `raw/notes/papers/{paper-id}.md` |
| 工具经验碎片 | `raw/notes/tools/{tool}/` |
| 未归类 | `raw/notes/_shared/YYYY-MM-DD-{slug}.md` |

### Step 3: 执行写入

1. 检查目标文件是否存在
2. 若存在：追加到末尾（append-only）
3. 若不存在：创建新文件，添加标准 frontmatter

### Step 4: 确认结果

报告写入路径和内容摘要。

---

## ⚠️ Capture Checkpoint（重要）

**在写入前，确认路由决策：**

当输入涉及多个可能路由或用户意图不明确时，暂停并询问：

```
Capture 路由决策：

| 输入 | 建议路由 | 原因 |
|------|----------|------|
| "LNA 增益下降调试" | raw/notes/projects/lna-design/logs/2026-05-15-lna-design-log.md | 项目日志 |
| "Virtuoso 报错" | raw/notes/tools/virtuoso/ | 工具经验 |

确认路由？或指定其他路径？
```

**跳过检查点条件：**
- 单一明确路由
- 用户已指定完整路径
- 紧急记录（用户明确说"快速记录"）

---

## 路由规则

- 项目 / session / 仿真 -> `raw/notes/projects/{project}/logs/YYYY-MM-DD-{project}-log.md`
- 独立课程 / 讲演录片段 -> `raw/notes/courses/`
- 若材料已经足够稳定，不继续 capture，改走 `/wiki-compile`

## 规则

- append-only
- 只写 `raw/`
- 不默认创建 `claim / procedure / entity`
- 不直接写 accepted edges
- 保留原始上下文，不在 capture 阶段过度总结

## Obsidian 格式保留

### 双链引用

**必须保留的双链格式**：
- `[[页面名]]` — 标准双链
- `[[页面名|显示文本]]` — 带别名的双链
- `[[目录/页面名]]` — 带路径的双链

**禁止**：
- 将 `[[页面名]]` 转换为 `[页面名](url)` 格式
- 删除或修改已有的双链

### 图片处理

**必须保留的图片格式**：
- `![[image.png]]` — Obsidian 内部图片
- `![[目录/image.png]]` — 带路径的内部图片

**禁止**：
- 将 `![[image.png]]` 转换为 `<img>` 标签
- 修改图片的显示尺寸参数

## 后续

- 当同一主题已经形成阶段性总结、完整记录、或足够稳定的材料时，转到 `/wiki-compile`
- 只有在确有明确知识提炼价值时，才进一步使用 `/wiki-refine`

---

## Tools to Use

| Tool | Purpose | When | 完整路径 |
|------|---------|------|----------|
| `Read` | 读取现有 raw 文件 | Step 3 | `/mnt/c/obsidian_wiki/raw/notes/projects/<project>/logs/<file>` |
| `Edit` | 追加到现有 raw 文件 | Step 3 | `/mnt/c/obsidian_wiki/raw/...` |
| `Write` | 创建新 raw 文件 | Step 3 | `/mnt/c/obsidian_wiki/raw/...` |
| `Glob` | 查找项目目录 | Step 2 | `/mnt/c/obsidian_wiki/raw/notes/projects/*/` |
| `mcp__obsidian-mcp-tools__search_vault_smart` | 查找相关 raw | Step 2 | 见下方调用示例 |

### search_vault_smart 调用示例

```json
mcp__obsidian-mcp-tools__search_vault_smart({
  "query": "<项目名或关键词>",
  "filter": {
    "folders": ["raw/notes/projects/", "raw/notes/courses/", "raw/notes/papers/"],
    "limit": 10
  }
})
```

**⚠️ 重要**：`filter` 必须是 JSON 对象，不能是字符串。

---

## 边界条件处理

| 情况 | 处理方式 |
|------|----------|
| 项目目录不存在 | 创建目录结构 |
| 文件已存在且较大（>50KB） | 提示用户是否拆分 |
| 输入包含图片引用 | 保留原格式，验证图片存在 |
| frontmatter 损坏 | 修复或重建 |
| 输入为空 | 报告错误，不写入 |

---

## 相关 Skill

| Skill | 路径 | 用途 |
|-------|------|------|
| wiki-compile | `/home/holmes/.cc-switch/skills/wiki-compile/SKILL.md` | 稳定材料编译 |
| wiki-refine | `/mnt/c/obsidian_wiki/.claude/commands/wiki-refine.md` | 高价值知识提炼 |
| inbox-prepare | `/home/holmes/.claude/skills/inbox-prepare/SKILL.md` | inbox 预处理 |
