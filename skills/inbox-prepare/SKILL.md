---
name: inbox-prepare
description: |
  Transform inbox content into high-quality raw files with intelligent deduplication.
  Use this skill whenever the user mentions "process inbox", "prepare raw", "move to raw",
  "deduplicate", "organize inbox", or when inbox items need processing. Also trigger
  when the user has captured content that needs to enter the knowledge pipeline.
  This is the critical intake layer for knowledge quality.
---

# inbox-prepare

Transform `inbox/` content into high-quality `raw/` entries through intelligent
deduplication and type classification. This skill is **fully self-contained** —
follow these instructions to execute the complete workflow.

## Overview

```
inbox/*.md → [inbox-prepare] → raw/<type>/*.md
                    ↓
         Decision: existing | append | new
```

**Pipeline position:** `capture → inbox-prepare → compile → crystallize → query`

---

## Processed Files Registry

### Registry Location

`raw/.inbox-processed.jsonl`

每行记录一个已处理的 inbox 文件：

```json
{"inbox_path": "inbox/2026-05-12-docker-volume-backup.md", "raw_path": "raw/procedure/docker-volume-backup.md", "sha256": "abc123...", "processed_at": "2026-05-12T13:15:00", "decision": "new"}
{"inbox_path": "inbox/2026-05-12-lna-gain-drop-experiment.md", "raw_path": "raw/notes/projects/lna-design/logs/2026-05-12-lna-design-log.md", "sha256": "def456...", "processed_at": "2026-05-12T14:00:00", "decision": "append"}
```

### Incremental Check

**Step 0: 增量检查（新增）**

在扫描 inbox 前，先检查哪些文件需要处理：

```
1. 读取 raw/.inbox-processed.jsonl（如不存在则创建空文件）
2. 扫描 inbox/ 目录
3. 对比：
   - 新文件：不在 registry 中 → 需要处理
   - 已处理文件：在 registry 中且 sha256 匹配 → 跳过
   - 变更文件：在 registry 中但 sha256 不匹配 → 标记为变更，需重新处理
4. 输出增量报告
```

### Incremental Report Format

```markdown
## Inbox Incremental Check

**Total inbox files:** 50
**Already processed:** 45
**New files:** 3
**Changed files:** 2

### New Files (need processing)
- inbox/2026-05-15-new-experiment.md
- inbox/2026-05-15-docker-notes.md
- inbox/notes/projects/new-project/

### Changed Files (need re-processing)
- inbox/2026-05-12-lna-gain-drop-experiment.md (content modified)
- inbox/2026-05-12-docker-volume-backup.md (content modified)

### Skipped (already processed, unchanged)
- inbox/2026-05-10-old-note.md → raw/note/old-note.md
- ... (45 files)
```

### Registry Update

处理完成后，更新 registry：

```
1. 对于 new/append 决策：追加新记录到 raw/.inbox-processed.jsonl
2. 对于 changed 文件：更新对应记录的 sha256 和 processed_at
3. 保持 registry 按时间排序
```

---

## Execution Steps

### Step 0: Incremental Check

**检查已处理文件清单：**

1. 读取 `raw/.inbox-processed.jsonl`（如不存在则创建空文件）
2. 扫描 `inbox/` 目录获取所有 `.md` 文件
3. 计算每个文件的 sha256
4. 对比 registry：
   - **New**: 不在 registry 中 → 需要处理
   - **Processed**: 在 registry 中且 sha256 匹配 → 跳过
   - **Changed**: 在 registry 中但 sha256 不匹配 → 标记为变更

5. 输出增量报告

**Tool:** `Read` 读取 registry，`Glob` 扫描 inbox，`Bash` 计算 sha256

---

### Step 1: Scan Inbox

List all files in `inbox/` directory. For each `.md` file:

1. Read the file content
2. Parse frontmatter (YAML between `---` markers)
3. Extract: `type`, `source`, `created`, `project`, `tags`

**Tool:** Use `listDirectory` then `readFile` for each file.

---

### Step 2: Analyze Each Inbox Entry

For each inbox file, perform content analysis:

#### 2a. Extract Title

Priority order:
1. First `# heading` in content
2. `title:` from frontmatter
3. First 50 characters of content

#### 2b. Detect Content Type

Analyze content to determine type:

| Type | Indicators | File Pattern |
|------|------------|--------------|
| **session-log** | Filename matches `*-session.md`, has `session_id` frontmatter | Use `session-log-crystallizer` skill |
| **log** | Date patterns (`YYYY-MM-DD`), project context, chronological entries | `raw/notes/projects/<project>/logs/YYYY-MM-DD-<project>-log.md` |
| **procedure** | Numbered steps, "how to", "步骤", "first/then/finally" | `raw/procedure/<topic>.md` |
| **troubleshooting** | Problem-solution pattern, "error", "fix", "解决", "问题" | `raw/troubleshooting/<issue>.md` |
| **note** | Short content, no clear structure, miscellaneous | `raw/note/YYYY-MM-DD-<slug>.md` |

**Session Log Special Handling:**

When a file matches `*-session.md` pattern:
1. **Invoke `session-log-crystallizer` skill** instead of normal processing
2. The skill will:
   - Use smart search to find existing project documentation
   - Extract work products, decisions, and learning points
   - Track direction evolution (从哪来 → 到哪去 → 为什么)
   - Merge into existing project docs (NOT create standalone files)
3. Output paths (created/updated by session-log-crystallizer):
   - `raw/notes/projects/<project>/logs/YYYY-MM-DD-<project>-log.md` — 项目日志
   - `raw/notes/projects/<project>/timeline.md` — 演进时间线
4. Skip the normal type detection and deduplication steps
5. session-log-crystallizer handles user confirmation internally

**Detection heuristics:**

```
IF filename matches "*-session.md" AND has session_id frontmatter
  → type = session-log → invoke session-log-crystallizer skill
ELSE IF content has date pattern AND (project name OR "项目")
  → type = log
ELSE IF content has numbered steps AND NOT problem keywords
  → type = procedure
ELSE IF content has (problem keywords AND solution keywords)
  → type = troubleshooting
ELSE
  → type = note
```

#### 2c. Generate Slug

Convert title to URL-safe slug:
1. Lowercase
2. Replace spaces with hyphens
3. Remove special characters (keep alphanumeric, CJK, hyphens)
4. Limit to 50 characters

**Example:** "React Hooks 使用指南" → `react-hooks-使用指南`

---

### Step 3: Search for Similar Content

**Critical step for deduplication.** Use Obsidian semantic search:

```
mcp__obsidian-mcp-tools__search_vault_smart(
  query: "<main keywords from content>",
  filter: {
    folders: ["raw/", "wiki/sources/", "wiki/entities/"],
    limit: 10
  }
)
```

**Extract keywords:**
- Title words (excluding stop words)
- Key technical terms
- Project names
- Main concepts

**Stop words to exclude:**
```
的, 是, 了, 什么, 在, 有, 和, 与, 对, 从
the, is, a, an, what, how, are, was, were, do, does, did
```

---

### Step 4: Make Decision

Based on search results, decide for each inbox entry:

#### Decision Matrix

| Condition | Decision | Action |
|-----------|----------|--------|
| No similar results found | `new` | Create new raw file |
| Similar result with >85% topic overlap | `existing` | Skip, log as duplicate |
| Similar result with 50-85% overlap | `append` | Append to existing file |
| Multiple partial matches | `new` | Create new, link to related |

**Similarity assessment:**

Compare the inbox content with each search result:
- **Title similarity:** Do titles refer to the same topic?
- **Content overlap:** Do they cover the same information?
- **Type match:** Are they the same content type?

**Conservative principle:** When in doubt, prefer `new` over `existing`. False duplicates are worse than missed duplicates.

**⚠️ Index cache validation:** Search results may include stale cached entries. Before deciding `existing`, verify the target file actually exists using `readFile`. If file not found, treat as `new`.

---

### Step 5: Enforce Granularity

Check content size against targets:

| Type | Min | Target | Max | Action if too small |
|------|-----|--------|-----|---------------------|
| **session-log** | - | - | - | Handled by session-log-crystallizer (分层摘要) |
| **log** | 800 | 1500 | 3000 | Consider merging with related log |
| **procedure** | 800 | 1200 | 2000 | Expand with context or merge |
| **troubleshooting** | 800 | 1200 | 2000 | Add more context |
| **note** | 500 | 800 | 1500 | Merge with existing note |

**Session-log granularity:**
- Large session (>50000 tokens): 分层摘要（段摘要 → 全局摘要）
- Normal session: 直接提取核心内容
- Output granularity: 合并到项目日志，形成时间线

**For content > max:** Split into logical chunks, each with context.

**For content < min:** Strongly prefer `append` over `new`.

---

### Step 5.5: ⚠️ Decision Confirmation Checkpoint (IMPORTANT)

**Before writing files, confirm decisions with user:**

When processing multiple inbox entries (≥3) or making significant decisions, pause and ask:

```
Inbox Prepare Decisions:

| Inbox File | Decision | Target |
|------------|----------|--------|
| session-1.md | new | raw/procedure/react-patterns.md |
| debug-log.md | append | raw/troubleshooting/memory-leak.md |
| duplicate.md | existing | (skip - 90% overlap) |

Proceed with all decisions? Or adjust specific ones?
```

**Why this checkpoint matters:**
- Prevents incorrect deduplication decisions
- Allows user to override `existing` → `new` when needed
- Catches type misclassifications before writing
- Ensures granularity decisions are appropriate

**Skip checkpoint only when:**
- Single inbox entry (auto-proceed)
- User explicitly requested "process all inbox"
- Running in automated/batch mode with prior approval

---

### Step 6: Write Raw Files

#### 6a. For `new` Decision

Create new file at determined path with this structure:

```markdown
---
type: <log|procedure|troubleshooting|note>
title: "<inferred title>"
created: YYYY-MM-DD
project: <project-name>  # Only for logs
tags: [<auto-detected-tags>]
sources: ["inbox/<original-filename>"]
---

# <title>

<processed content>

<!-- Prepared from: inbox/<original-filename> -->
<!-- Prepared on: YYYY-MM-DD -->
```

#### 6b. For `append` Decision

Read existing file, then append:

```markdown
---

## <YYYY-MM-DD> — <source description>

<new content>

<!-- Appended from: inbox/<original-filename> -->
<!-- Appended on: YYYY-MM-DD -->
```

**Important:** Preserve existing content exactly. Only append new section.

#### 6c. For `existing` Decision

Do not write. Log the decision with reason.

---

### Step 7: Generate Decision Log

After processing all inbox entries, output a summary:

```markdown
# Inbox Prepare Report

**Processed:** YYYY-MM-DD HH:mm

## Decisions

| Inbox File | Decision | Type | Raw Target | Reason |
|------------|----------|------|------------|--------|
| inbox/session-1.md | new | procedure | raw/procedure/react-patterns.md | No similar content found |
| inbox/debug-log.md | append | troubleshooting | raw/troubleshooting/memory-leak.md | Extends existing troubleshooting |
| inbox/duplicate.md | existing | - | raw/note/same-topic.md | Already exists with 90% overlap |

## Statistics

- Total processed: 3
- New files created: 1
- Files appended: 1
- Duplicates skipped: 1

## Handoff

Ready for `wiki-compile`:
- raw/procedure/react-patterns.md
- raw/troubleshooting/memory-leak.md (updated)
```

---

### Step 8: Update Registry

**更新已处理文件清单：**

1. 读取 `raw/.inbox-processed.jsonl`
2. 对于每个处理的文件，追加或更新记录：
   ```json
   {"inbox_path": "inbox/xxx.md", "raw_path": "raw/xxx.md", "sha256": "...", "processed_at": "YYYY-MM-DDTHH:MM:SS", "decision": "new|append|existing"}
   ```
3. 写回 registry 文件

**Tool:** `Read` 读取 registry，`Edit` 追加记录

---

## File Structure Reference

### Inbox Entry Format (Input)

```markdown
---
type: log | note | procedure | troubleshooting  # Optional hint
source: chat | file | snippet | command
created: YYYY-MM-DD
project: <project-name>  # Optional
tags: [tag1, tag2]  # Optional
---

# <title>

<content>
```

### Raw File Format (Output)

```
raw/
├── notes/
│   └── projects/
│       └── <project>/
│           ├── logs/
│           │   └── YYYY-MM-DD-<project>-log.md    # session-log 输出
│           └── timeline.md                         # 项目演进时间线
├── log/
│   └── YYYY-MM-DD-<project>-<topic>.md
├── procedure/
│   └── <topic-slug>.md
├── troubleshooting/
│   └── <issue-slug>.md
└── note/
    └── YYYY-MM-DD-<topic>.md
```

**Note:** session-log 类型不创建独立文件，而是合并到 `raw/notes/projects/<project>/` 下的现有文档。

---

## Tools to Use

| Tool | Purpose | When | 完整路径 |
|------|---------|------|----------|
| `Glob` | 扫描 inbox 目录 | Step 0, Step 1 | `/mnt/c/obsidian_wiki/inbox/**/*.md` |
| `Read` | 读取 registry 和 inbox 文件 | Step 0, Step 1, Step 6b | `/mnt/c/obsidian_wiki/raw/.inbox-processed.jsonl` |
| `Write` | 创建新 raw 文件 | Step 6a | `/mnt/c/obsidian_wiki/raw/<type>/<file>` |
| `Edit` | 追加到现有 raw 文件或更新 registry | Step 6b, Step 8 | `/mnt/c/obsidian_wiki/raw/<type>/<file>` |
| `Bash` + `sha256sum` | 计算文件哈希 | Step 0 | `sha256sum <file>` |
| `mcp__obsidian-mcp-tools__search_vault_smart` | 语义搜索去重 | Step 3 | 见下方调用示例 |

### search_vault_smart 调用示例

```json
mcp__obsidian-mcp-tools__search_vault_smart({
  "query": "<关键词>",
  "filter": {
    "folders": ["raw/", "wiki/sources/", "wiki/entities/"],
    "limit": 10
  }
})
```

**⚠️ 重要**：`filter` 必须是 JSON 对象，不能是字符串。

### 相关 Skill 路径

| Skill | 路径 | 用途 |
|-------|------|------|
| session-log-crystallizer | `/home/holmes/.claude/skills/session-log-crystallizer/SKILL.md` | 处理 `*-session.md` 文件 |

---

## Examples

### Example 1: New Procedure

**Input:** `inbox/2026-05-12-git-workflow.md`

```markdown
---
type: procedure
source: chat
created: 2026-05-12
---

# Git 分支管理流程

1. 从 main 创建 feature 分支
2. 开发完成后提交 PR
3. Code review 通过后合并
```

**Process:**
1. Type: procedure (has numbered steps)
2. Search: "git 分支管理 workflow" → no similar results
3. Decision: `new`
4. Write: `raw/procedure/git-分支管理流程.md`

### Example 2: Append to Troubleshooting

**Input:** `inbox/2026-05-12-memory-fix.md`

```markdown
---
type: troubleshooting
source: debug
created: 2026-05-12
---

# 内存泄漏修复

发现 Worker 进程内存持续增长，原因是连接未正确关闭。
解决方案：在 finally 块中显式关闭连接。
```

**Process:**
1. Type: troubleshooting (problem + solution)
2. Search: "内存泄漏 worker" → found `raw/troubleshooting/memory-leak.md`
3. Compare: Same issue, new solution
4. Decision: `append`
5. Append new solution section to existing file

### Example 3: Duplicate Detection

**Input:** `inbox/2026-05-12-react-hooks.md`

```markdown
# React Hooks 基础

useState 和 useEffect 是最常用的两个 Hook...
```

**Process:**
1. Type: note
2. Search: "react hooks" → found `raw/note/react-hooks.md` with 90%+ overlap
3. Decision: `existing`
4. Skip, log as duplicate

---

## Quality Principles

1. **Conservative on `existing`** — Only skip if truly redundant
2. **Prefer `append` over `new`** — Related knowledge should be together
3. **Log all decisions** — Transparency enables debugging
4. **Size targets are guidelines** — Content quality > strict limits
5. **Preserve context** — When splitting or merging, keep essential context

---

## Obsidian 格式保留规则

### 双链引用（Wikilinks）

**必须保留的双链格式**：
- `[[页面名]]` — 标准双链
- `[[页面名|显示文本]]` — 带别名的双链
- `[[目录/页面名]]` — 带路径的双链

**处理规则**：

| 情况 | 处理方式 |
|------|----------|
| 目标页面存在 | 保留原双链，不做修改 |
| 目标页面不存在 | 保留原双链（Obsidian 会显示为灰色） |
| typed-id 格式 `[[entity:xxx]]` | 转换为反引号 `` `entity:xxx` `` 或合法双链 `[[xxx]]` |

**禁止**：
- 将 `[[页面名]]` 转换为 `[页面名](url)` 格式
- 删除或修改已有的双链
- 输出 `[[entity:...]]`、`[[procedure:...]]` 这类 typed-id 伪双链

### 图片处理

**必须保留的图片格式**：
- `![[image.png]]` — Obsidian 内部图片
- `![[目录/image.png]]` — 带路径的内部图片
- `![](url)` — 外部图片链接

**图片路径处理**：

| 情况 | 处理方式 |
|------|----------|
| 图片在 `Assets/` 目录 | 保留原路径，不修改 |
| 图片在同级目录 | 保留原路径 |
| 图片路径包含中文/空格 | 保留原路径，不做 URL 编码 |
| 外部图片 URL | 保留原 URL |

**图片迁移规则**：

当 inbox 文件包含图片时：

1. **检查图片是否存在**：
   - 读取 inbox 文件中的图片路径
   - 验证图片文件是否存在

2. **图片路径转换**：
   - 原路径：`![[image.png]]`（相对于 inbox 文件）
   - 新路径：`![[Assets/image.png]]`（相对于 raw 文件）
   - 或保持原路径不变（如果图片已在正确位置）

3. **图片文件处理**：
   - 不复制图片文件（假设图片已在 vault 中）
   - 只更新 markdown 中的图片引用路径

**禁止**：
- 删除图片引用
- 将 `![[image.png]]` 转换为 `<img>` 标签
- 修改图片的显示尺寸参数（如 `![[image.png|300]]`）

### 其他 Obsidian 元素

**保留的元素**：
- 标签：`#tag`、`#嵌套/标签`
- 代码块：` ```language ... ``` `
- 行内代码：`` `code` ``
- 数学公式：`$...$`、`$$...$$`
- Callouts：`> [!note] ...`
- 表格
- 任务列表：`- [ ] task`、`- [x] done`

**禁止修改**：
- 标签格式（不添加 `#` 或删除 `#`）
- 代码块语言标识
- 数学公式的 LaTeX 语法

---

## Error Handling

| Error | Action |
|-------|--------|
| Inbox directory not found | Create it, report empty inbox |
| Cannot read inbox file | Log error, skip file, continue |
| Cannot write to raw | Log error, report failure |
| Search tool unavailable | Fall back to filename comparison |
| Existing raw file corrupted | Log warning, create new file |

---

## Completion Checklist

- [ ] Incremental check performed (Step 0)
- [ ] Registry file read/created
- [ ] New/changed files identified
- [ ] All pending inbox files processed
- [ ] Decision made for each entry
- [ ] Raw files written (new or appended)
- [ ] Decision log generated
- [ ] Registry updated (Step 8)
- [ ] Original inbox files remain (do not delete)
- [ ] Report provided to user

---

## Registry File Format

`raw/.inbox-processed.jsonl` 格式：

```jsonl
{"inbox_path": "inbox/2026-05-12-docker-volume-backup.md", "raw_path": "raw/procedure/docker-volume-backup.md", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "processed_at": "2026-05-12T13:15:00Z", "decision": "new"}
{"inbox_path": "inbox/2026-05-12-lna-gain-drop-experiment.md", "raw_path": "raw/notes/projects/lna-design/logs/2026-05-12-lna-design-log.md", "sha256": "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592", "processed_at": "2026-05-12T14:00:00Z", "decision": "append"}
```

**字段说明**：
- `inbox_path`: inbox 文件的相对路径
- `raw_path`: 输出 raw 文件的相对路径
- `sha256`: inbox 文件内容的 SHA256 哈希
- `processed_at`: 处理时间（ISO 8601 格式）
- `decision`: 处理决策（new | append | existing）
