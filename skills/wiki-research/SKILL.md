---
name: wiki-research
description: |
  Fill knowledge gaps from web sources and save results back into the wiki.
  Use this skill whenever the user wants to research a topic, the wiki is missing
  information, or external sources need to be consulted. Triggers on phrases like
  "research", "look up online", "find information", "deep research", "web search",
  "研究", "查找", "搜索", or when wiki-query returns gaps that need to be filled.
---

# wiki-research

Fill knowledge gaps from web sources and save results back to wiki. This skill is
**fully self-contained** — follow these instructions to execute the complete workflow.

## Overview

```
Topic → [wiki-research] → wiki/queries/research-<topic>-<date>.md
              ↓
       - Web search
       - Synthesize results
       - Save to wiki
       - Auto-ingest (optional)
```

**Pipeline position:** Can be triggered by gaps in wiki-query, or directly by user.

---

## Execution Steps

### Step 1: Prepare Search Queries

#### 1a. Extract Key Terms

From research topic:
- Main subject
- Technical terms
- Domain keywords

#### 1b. Generate Query Variations

Create 3-5 search queries:

| Variation | Example |
|-----------|---------|
| Direct topic | "attention mechanism" |
| "What is" form | "what is attention mechanism" |
| Acronym (if applicable) | "NLP attention" |
| Technical form | "attention mechanism neural network" |
| Comparison (if applicable) | "attention vs self-attention" |

---

### Step 2: Execute Web Search

#### 2a. Call Search API

Use available web search tool:

```
WebSearch or mcp__exa__web_search_exa

Parameters:
- query: <search query>
- max_results: 5 per query
```

#### 2b. Collect Results

For each query:
- Execute search
- Collect results (title, URL, snippet, source)
- Track which query found each result

#### 2c. Deduplicate

Remove duplicate URLs:
- Normalize URLs (lowercase, remove trailing slash)
- Keep first occurrence
- Merge query sources

---

### Step 3: Read Wiki Context

#### 3a. Read Wiki Index

Read `wiki/index.md` to understand existing pages.

#### 3b. Identify Cross-References

Find existing wiki pages that should be referenced in the research:
- Entities mentioned in research topic
- Concepts related to topic
- Procedures that might apply

**Why:** Research should link to existing wiki content with `[[wikilinks]]`.

---

### Step 4: Synthesize Results

#### 4a. Build Synthesis Prompt

```
You are a research assistant synthesizing web search results into a wiki page.

Topic: <research topic>

Web Results:
[1] Title: <title>
Source: <source>
<snippet>

[2] Title: <title>
Source: <source>
<snippet>
...

Existing Wiki Pages (link to these with [[wikilink]]):
- [[existing-page-1]]
- [[existing-page-2]]
...

Create a comprehensive wiki page that:
1. Synthesizes information from all sources
2. Uses [N] citations for web sources
3. Uses [[wikilink]] for existing wiki concepts
4. Notes contradictions or gaps
5. Suggests additional sources
6. Is written in neutral, encyclopedic tone
7. Matches the language of the topic (Chinese/English)
```

#### 4b. Generate Synthesis

Use LLM to generate comprehensive synthesis.

---

### Step 4.5: ⚠️ Research Direction Checkpoint (IMPORTANT)

**Before finalizing research, confirm with user:**

When research scope is large or findings are unexpected, pause and ask:

```
Research Preview for: <topic>

Key findings so far:
- <finding 1>
- <finding 2>
- <finding 3>

Sources: N results from web search

Continue with full synthesis? Or adjust focus?
```

**Why this checkpoint matters:**
- Prevents wasting time on wrong research direction
- Allows user to narrow or expand scope based on preview
- Ensures research aligns with user's actual need

**Skip checkpoint only when:**
- Single focused query (auto-proceed)
- User explicitly requested "research and save"
- Research is filling a specific gap from wiki-query

---

### Step 5: Build Research Page

#### 5a. Generate Frontmatter

```yaml
---
type: query
title: "Research: <topic>"
created: YYYY-MM-DD
origin: deep-research
tags: [research, <domain>]
---
```

#### 5b. Format Content

```markdown
---
type: query
title: "Research: <topic>"
created: YYYY-MM-DD
origin: deep-research
tags: [research, <domain>]
---

# Research: <topic>

<synthesized content with [N] citations>

## Key Findings

- <finding 1> [1]
- <finding 2> [2]

## Gaps Remaining

- <information not found>

## References

1. [<title 1>](<url>) — <source>
2. [<title 2>](<url>) — <source>
```

#### 5c. Clean Thinking Blocks

Remove any `<tool_call>` or `<thinking>` blocks from LLM output.

---

### Step 6: Save to Wiki

#### 6a. Generate Filename

```
wiki/queries/research-<slug>-<date>.md
```

**Slug:** Topic lowercase, spaces→hyphens, remove special chars, limit 50 chars.

#### 6b. Write File

Create file at determined path.

---

### Step 7: Auto-Ingest (Optional)

Trigger `wiki-compile` on the research result:
- Extract entities and concepts
- Generate cross-references
- Update wiki graph

**Note:** This is optional but recommended for full integration.

---

### Step 8: Report Results

```markdown
# Research Complete

**Topic:** <topic>
**Saved to:** wiki/queries/research-<topic>-<date>.md

## Summary

<brief summary of findings>

## Sources Used

- [<title 1>](<url>)
- [<title 2>](<url>)

## Cross-References Created

- [[existing-wiki-page-1]]
- [[existing-wiki-page-2]]

## Next Steps

- Run `/wiki-compile` to extract entities and concepts
- Or review and edit the research page manually
```

---

## Tools to Use

| Tool | Purpose | When | 完整路径 |
|------|---------|------|----------|
| `WebSearch` | Web 搜索 | Step 2 | 内置工具 |
| `Read` | 读取 wiki index | Step 3 | `/mnt/c/obsidian_wiki/wiki/index.md` |
| `Write` | 保存研究页面 | Step 6 | `/mnt/c/obsidian_wiki/wiki/queries/research-*.md` |
| `Glob` | 扫描 wiki 结构 | Step 3 | `/mnt/c/obsidian_wiki/wiki/**/*.md` |
| `mcp__obsidian-mcp-tools__search_vault_smart` | 搜索相关 wiki | Step 3 | 见下方调用示例 |

### search_vault_smart 调用示例

```json
mcp__obsidian-mcp-tools__search_vault_smart({
  "query": "<研究主题关键词>",
  "filter": {
    "folders": ["wiki/sources", "wiki/entities", "wiki/procedures", "wiki/claims", "wiki/topics"],
    "limit": 10
  }
})
```

**⚠️ 重要**：`filter` 必须是 JSON 对象，不能是字符串。

---

## Obsidian 格式保留

### 双链引用

**必须使用合法双链格式**：
- `[[页面名]]` — 标准双链
- `[[页面名|显示文本]]` — 带别名的双链

**禁止**：
- 输出 typed-id 伪双链（如 `[[entity:xxx]]`）
- 将双链转换为 Markdown 链接格式

### 图片引用

**保留原图片格式**：
- `![[image.png]]` — Obsidian 内部图片
- `![](url)` — 外部图片链接

---

## Search Query Generation Heuristics

```python
def generate_search_queries(topic):
    queries = [topic]
    
    # Add "what is" variation
    if not topic.lower().startswith("what is"):
        queries.append(f"what is {topic}")
    
    # Add acronym if detected
    words = topic.split()
    acronym = "".join(w[0].upper() for w in words if w[0].isupper())
    if 2 <= len(acronym) <= 5:
        queries.append(acronym)
    
    # Add technical context
    if any(tech in topic.lower() for tech in ["model", "network", "algorithm"]):
        queries.append(f"{topic} machine learning")
    
    return queries[:5]
```

---

## Examples

### Example 1: Technical Research

**Topic:** "Transformer architecture"

**Process:**
1. Queries: ["Transformer architecture", "what is Transformer", "Transformer neural network"]
2. Web search: Collect 10-15 results
3. Read wiki index: Found [[attention-mechanism]], [[neural-network]]
4. Synthesize with cross-references
5. Save: `wiki/queries/research-transformer-architecture-2026-05-12.md`

**Output:**
```markdown
---
type: query
title: "Research: Transformer Architecture"
created: 2026-05-12
origin: deep-research
tags: [research, deep-learning, nlp]
---

# Research: Transformer Architecture

The Transformer is a neural network architecture introduced in "Attention Is All You Need" [1]. Unlike recurrent architectures, Transformers use self-attention to process sequences in parallel.

## Key Components

- **Self-Attention**: Computes relationships between all positions simultaneously. See [[attention-mechanism]].
- **Positional Encoding**: Adds position information to embeddings.
- **Feed-Forward Networks**: Applied to each position independently.

## Key Findings

- Transformers enable parallel processing of sequences [1]
- Self-attention scales as O(n²) in sequence length [2]
- Foundation for models like BERT and GPT [3]

## References

1. [Attention Is All You Need](https://arxiv.org/...) — arXiv
2. [Transformer Architecture Explained](https://...) — Blog
```

### Example 2: Gap-Filling Research

**Trigger:** wiki-query returned "No information found on attention mechanisms"

**Process:**
1. Topic: "attention mechanism in deep learning"
2. Search and synthesize
3. Save research
4. Auto-ingest to create [[attention-mechanism]] concept page

---

## Quality Principles

1. **Cite all sources** — Use [N] notation consistently
2. **Cross-reference wiki** — Link to existing concepts
3. **Acknowledge gaps** — Note what wasn't found
4. **Neutral tone** — Encyclopedic, not promotional
5. **Prefer authoritative sources** — Papers, docs over blogs

---

## Error Handling

| Error | Action |
|-------|--------|
| No web results | Report "No results found", suggest refining topic |
| Search API fails | Report error, suggest manual search |
| Cannot save file | Report error, provide content for manual save |
| LLM synthesis fails | Return raw search results |

---

## 边界条件处理

| 情况 | 处理方式 |
|------|----------|
| 研究主题过于宽泛 | 提示用户缩小范围 |
| 搜索结果过多（>50） | 筛选前 10 个最相关 |
| 搜索结果过少（<3） | 扩展查询词或报告不足 |
| Wiki index 不存在 | 跳过交叉引用步骤 |

---

## Completion Checklist

- [ ] Search queries generated
- [ ] Web searches executed
- [ ] Results deduplicated
- [ ] Wiki context read
- [ ] Synthesis generated
- [ ] Research page formatted
- [ ] File saved to wiki
- [ ] Report provided to user
- [ ] Auto-ingest triggered (optional)

---

## 相关 Skill

| Skill | 路径 | 用途 |
|-------|------|------|
| wiki-query | `/home/holmes/.cc-switch/skills/wiki-query/SKILL.md` | 知识库查询 |
| wiki-compile | `/home/holmes/.cc-switch/skills/wiki-compile/SKILL.md` | 编译研究结果 |
| wiki-lint | `/home/holmes/.cc-switch/skills/wiki-lint/SKILL.md` | 健康检查 |
