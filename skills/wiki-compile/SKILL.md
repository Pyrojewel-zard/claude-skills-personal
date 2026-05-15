---
name: wiki-compile
description: |
  Use when raw notes or external material are stable enough to be compiled into a readable wiki page with deduplication, registry updates, and optional later refinement.
  Triggers on: "compile", "编译", "入库", "ingest", "process raw", "处理raw", "convert to wiki".
user_invocable: true
---

# wiki-compile

运行 `/wiki-compile <path|url|file> --intent "<一句话意图>"`。

## 目标

把稳定 raw 或外部材料编译成完整可读 wiki 页面。

这是三入口 flow 的主入口：

`wiki-capture -> wiki-compile -> wiki-refine`

## 默认适用

- 完整 session 汇总
- 项目阶段总结
- 完整仿真记录
- 论文 DOI / URL / PDF / Markdown
- 课程讲演录与章节总结

## 执行步骤

### Step 1: 识别输入类型

| 输入类型 | 处理方式 |
|----------|----------|
| `raw/` 文件 | 直接读取并编译 |
| URL / DOI | 获取内容后编译 |
| PDF / Markdown | 转换后编译 |
| 目录 | 逐文件处理 |

### Step 2: 智能搜索去重

**必须调用 `search_vault_smart`：**

```json
mcp__obsidian-mcp-tools__search_vault_smart({
  "query": "<核心标题/关键词>",
  "filter": {
    "folders": ["wiki/sources", "wiki/entities", "wiki/procedures", "wiki/claims", "wiki/topics"],
    "limit": 10
  }
})
```

### Step 3: 判断去重决策

报告搜索关键词、candidate hits、dedupe decision：

| 决策 | 条件 | 行为 |
|------|------|------|
| `duplicate` | fingerprint 相同或标题完全匹配 | 更新现有节点 |
| `update` | 高度相似（>70% 关键词重叠） | 补充新内容 |
| `new` | 无匹配或部分相似（<30%） | 创建新页面 |

### Step 4: 调用 wiki-ingest

执行底层编译流程，生成完整可读 wiki 页面。

### Step 5: 更新 Registry

更新：
- `wiki/_registry/nodes.jsonl`
- `wiki/_registry/edges.jsonl`
- `wiki/_registry/fingerprints.jsonl`
- `wiki/_registry/compile_log.jsonl`
- `wiki/_registry/query_pack.md`

---

## ⚠️ Compile Checkpoint（重要）

**在写入 wiki 前，确认编译决策：**

当材料涉及多个可能目标或去重判断复杂时，暂停并询问：

```
Compile 编译决策：

| 输入 | 搜索结果 | 决策 | 目标 |
|------|----------|------|------|
| raw/session-2026-05-15.md | 2 个相似页面 | update | wiki/sources/projects/lna-design/ |
| raw/paper-xxx.md | 无匹配 | new | wiki/sources/papers/lna-design/ |

关键词：LNA 增益、匹配网络、调试
相似页面：
- wiki/sources/projects/lna-design/session-2026-05-14.md (70% 重叠)
- wiki/entities/matching-network.md (相关实体)

确认决策？或调整？
```

**跳过检查点条件：**
- 单一明确目标
- 无相似页面
- 用户已指定完整路径

---

## 规则

- 默认输出完整可读 wiki 页面
- typed 抽取是可选增强，不是强制目标
- 是否合并到已有 project/source，不靠 Smart Search 单独决定，而是 `smart search + fingerprint + LLM judgment`
- stable ID 可带冒号，但文件名和页面名不能带 `* " \\ / < > : | ?`
- 禁止输出 `[[entity:...]]`、`[[procedure:...]]` 这类 typed-id 伪双链
- 目标页存在时使用合法双链；目标页不存在时用反引号保留 stable ID

## Obsidian 格式保留

### 双链引用

**必须保留的双链格式**：
- `[[页面名]]` — 标准双链
- `[[页面名|显示文本]]` — 带别名的双链
- `[[目录/页面名]]` — 带路径的双链

**禁止**：
- 将 `[[页面名]]` 转换为 `[页面名](url)` 格式
- 输出 typed-id 伪双链（如 `[[entity:xxx]]`）

### 图片处理

**必须保留的图片格式**：
- `![[image.png]]` — Obsidian 内部图片
- `![[目录/image.png]]` — 带路径的内部图片
- `![](url)` — 外部图片链接

**禁止**：
- 将 `![[image.png]]` 转换为 `<img>` 标签
- 修改图片的显示尺寸参数

## 边界

- 不直接处理纯碎片输入
- 不把 marker 输出或 raw 正文直接当最终事实页
- 不默认升格 claim / procedure / entity

---

## Tools to Use

| Tool | Purpose | When | 完整路径 |
|------|---------|------|----------|
| `Read` | 读取 raw 文件 | Step 1 | `/mnt/c/obsidian_wiki/raw/...` |
| `Write` | 创建 wiki 页面 | Step 4 | `/mnt/c/obsidian_wiki/wiki/...` |
| `Edit` | 更新现有 wiki 页面 | Step 4 | `/mnt/c/obsidian_wiki/wiki/...` |
| `mcp__obsidian-mcp-tools__search_vault_smart` | 智能搜索去重 | Step 2 | 见上方调用示例 |
| `Skill` | 调用 wiki-ingest | Step 4 | `wiki-ingest` |

### search_vault_smart 调用示例

```json
mcp__obsidian-mcp-tools__search_vault_smart({
  "query": "<核心标题/关键词>",
  "filter": {
    "folders": ["wiki/sources", "wiki/entities", "wiki/procedures", "wiki/claims", "wiki/topics"],
    "limit": 10
  }
})
```

**⚠️ 重要**：`filter` 必须是 JSON 对象，不能是字符串。

---

## 边界条件处理

| 情况 | 处理方式 |
|------|----------|
| 搜索结果包含过期缓存 | 用 Read 验证文件存在 |
| 多个相似页面冲突 | 提示用户选择合并策略 |
| Registry 文件损坏 | 修复或重建 |
| 输入文件损坏 | 报告错误，跳过 |
| 并发写入冲突 | 使用 Edit 而非 Write |

---

## 相关 Skill

| Skill | 路径 | 用途 |
|-------|------|------|
| wiki-capture | `/home/holmes/.cc-switch/skills/wiki-capture/SKILL.md` | 低密度捕获 |
| wiki-ingest | `/mnt/c/obsidian_wiki/.claude/commands/wiki-ingest.md` | 底层编译引擎 |
| wiki-refine | `/mnt/c/obsidian_wiki/.claude/commands/wiki-refine.md` | 高价值提炼 |
| wiki-crystallize | `/home/holmes/.cc-switch/skills/wiki-crystallize/SKILL.md` | candidate 审核 |
