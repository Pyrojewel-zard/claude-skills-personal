---
name: wiki-capture
description: |
  Use when the material is still low-density or provisional and should first be appended into raw notes before any compile or typed knowledge promotion.
  Triggers on: "capture", "记录到raw", "碎片记录", "临时笔记", "quick note", "append to raw".
  Does NOT write accepted wiki directly — that is wiki-compile's job.
user_invocable: true
---

# wiki-capture

运行 `/wiki-capture <material-or-text> --intent "<一句话意图>"`。

## 目标

把低密度输入先落到正确的 `raw/` 入口，不直接写 accepted wiki。

这是三入口 flow 的第一步：

`wiki-capture -> wiki-compile -> wiki-refine`

## 执行步骤

### Step 1: 解析输入

1. 识别输入类型（按优先级匹配）：

| 信号词/模式 | 输入类型 | 路由键 |
|-------------|----------|--------|
| "仿真"、"Virtuoso"、"EMX"、"跑了一下" | 仿真/项目 | project |
| "论文"、"paper"、"DOI"、"arXiv" | 论文 | paper |
| "课程"、"lecture"、"讲义" | 课程 | course |
| "工具"、"报错"、"配置"、"安装" | 工具经验 | tool |
| 以上均不匹配 | 未归类 | shared |

2. 提取三要素：`{project}`（项目名）、`{date}`（当前日期 YYYY-MM-DD）、`{slug}`（≤30字符 kebab-case 摘要，示例：`"LNA增益在2.4GHz下降3dB"` → `lna-gain-drop-2-4ghz`）
   - project 推断：用户指定 > 从输入推断 > 留空路由到 `_shared`

3. 判断意图：记录（默认）→ 追加到已有文件；追踪/提醒 → 新建独立文件
   - `--intent` 影响：若 intent 含"追踪"/"提醒"/"TODO"，则新建独立文件而非追加

4. 多义输入：在 Checkpoint 中展示备选路由让用户确认

### Step 2: 确定路由

| 输入类型 | 默认路由 |
|----------|----------|
| 项目/session/仿真 | `raw/notes/projects/{project}/logs/YYYY-MM-DD-{project}-log.md` |
| 独立课程/讲演录片段 | `raw/notes/courses/{course}/` |
| 论文相关性提醒 | `raw/notes/papers/{paper-id}.md` |
| 工具经验碎片 | `raw/notes/tools/{tool}/` |
| 未归类 | `raw/notes/_shared/YYYY-MM-DD-{slug}.md` |

### Step 3: 执行写入

**工具调用链**：
```
search_vault_smart(相关raw) → Read(目标文件) → Edit(追加) 或 Write(新建)
```

1. 先用 `search_vault_smart` 搜索是否已有相关 raw 文件
2. 若存在且路由一致：用 `Edit` 追加到末尾（append-only）
3. 若不存在：用 `Write` 创建新文件

**新建文件的 frontmatter 模板**：
```yaml
---
type: raw-note
created_at: YYYY-MM-DDTHH:MM
project: {project}          # 可选，有明确项目时填
tags: [capture, {输入类型}]
---
```

**追加内容的分隔模板**：
```markdown
---
**YYYY-MM-DD HH:MM** | {输入类型} | {一句话摘要}

{实际内容}
```

### Step 4: 确认结果

输出格式：
```
✓ Capture 完成
  路径: raw/notes/projects/{project}/logs/YYYY-MM-DD-{project}-log.md
  操作: 追加 / 新建
  内容: {一句话摘要}
  后续: 当材料稳定后可走 /wiki-compile
```

---

## Capture Checkpoint

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
| project 名无法推断 | project 留空，路由到 `_shared/` |
| search_vault_smart 返回空 | 直接创建新文件（无需追加） |
| 多义输入匹配多个路由 | 在 Checkpoint 展示备选，让用户选择 |

---

## 相关 Skill

| Skill | 路径 | 用途 |
|-------|------|------|
| wiki-compile | `/home/holmes/.cc-switch/skills/wiki-compile/SKILL.md` | 稳定材料编译 |
| wiki-refine | `/mnt/c/obsidian_wiki/.claude/commands/wiki-refine.md` | 高价值知识提炼 |