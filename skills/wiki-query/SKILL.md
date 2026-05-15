---
name: wiki-query
description: |
  Answer questions from compiled wiki knowledge with grounded citations.
  Prioritize reuse of previously solved problems and existing procedures.
  Use this skill whenever the user asks a question that should be answered from
  wiki content, says "search wiki", "query knowledge", "find in wiki", "what does
  the wiki say", or any question that should leverage the knowledge base.
---

# wiki-query

Answer questions from compiled wiki knowledge with grounded citations. This skill is
**fully self-contained** — follow these instructions to execute the complete workflow.

## Overview

```
User question → [wiki-query] → Grounded answer with citations
                     ↓
              - Search wiki pages
              - Expand via wikilinks
              - Generate answer
              - (Optional) Save query
```

**Pipeline position:** `capture → inbox-prepare → compile → crystallize → query`

---

## Execution Steps

### Step 1: Parse Query

#### 1a. Understand Intent

Identify the question type:

| Type | Indicators | Approach |
|------|------------|----------|
| **Factual** | "What is", "Define", "Explain" | Find definition pages |
| **Procedural** | "How to", "How do I", "Steps for" | Find procedure pages |
| **Troubleshooting** | "Error", "Problem", "Fix", "Not working" | Find troubleshooting pages |
| **Exploratory** | "Why", "Compare", "Difference" | Find related concepts |

#### 1b. Extract Key Concepts

Identify:
- Main topic/subject
- Technical terms
- Domain keywords
- Project names

**Example:** "How do I deploy the React app to production?"
- Main topic: deploy
- Technical terms: React, production
- Domain: deployment, frontend

---

### Step 2: Perform Search

#### 2a. Token Search

Extract tokens from query:

```
1. Lowercase query
2. Split by whitespace and punctuation
3. Remove stop words
4. For CJK: add bigrams + individual chars
```

**Stop words:**
```
的, 是, 了, 什么, 在, 有, 和, 与, 对, 从
the, is, a, an, what, how, are, was, were, do, does, did
```

#### 2b. Semantic Search (if available)

Use `mcp__obsidian-mcp-tools__search_vault_smart`:

```json
{
  "query": "<key concepts>",
  "filter": {
    "folders": ["wiki/"],
    "limit": 20
  }
}
```

#### 2c. Combine Results

Use Reciprocal Rank Fusion (RRF):

```
score(page) = Σ 1/(K + rank) for each result list
K = 60 (standard constant)
```

---

### Step 3: Score Results

Calculate relevance score:

| Signal | Weight |
|--------|--------|
| Filename exact match | +200 |
| Phrase in title | +50 |
| Phrase in content (per occurrence) | +20, max 10 |
| Token in title | +5 |
| Token in content | +1 |

**Example scoring:**
- Query: "React hooks"
- Page: `wiki/concepts/react-hooks.md`
  - Filename match: +200
  - Title contains "React hooks": +50
  - Total: 250

---

### Step 4: Graph Expansion

Expand results by following wikilinks:

#### 4a. Extract Wikilinks

From top results, extract `[[wikilink]]` references.

#### 4b. Add Related Pages

Include highly-connected related pages:
- Pages linked by multiple results
- Pages that link to results

#### 4c. Build Context Window

Assemble context for answer generation:
- Top 5-10 matched pages
- Key related pages
- Total: ~4000 characters

---

### Step 5: Generate Answer

#### 5a. Assemble Context

```markdown
## Search Results

### react-hooks
Path: wiki/concepts/react-hooks.md
React Hooks are functions that let you use state and other React features...

### use-state
Path: wiki/entities/use-state.md
useState is a Hook that adds state to functional components...

### use-effect
Path: wiki/entities/use-effect.md
useEffect is a Hook for side effects in functional components...
```

#### 5b. Generate Response

Use LLM to generate grounded answer:

**Prompt template:**
```
You are answering a question from wiki knowledge.

Question: <user query>

Context from wiki:
<assembled context>

Answer the question:
1. Be concise and direct
2. Cite sources using [[page-name]] syntax
3. Quote relevant sections when helpful
4. Acknowledge if information is missing
5. Suggest related topics

Format:
## Answer
<direct answer>

## Sources
- [[page-1]] — <relevant excerpt>
- [[page-2]] — <relevant excerpt>

## Related
- [[related-topic-1]]
- [[related-topic-2]]

## Gaps (if any)
- <information not found in wiki>
```

---

### Step 5.5: ⚠️ Knowledge Gap Checkpoint

**When search returns insufficient results:**

If answer has significant gaps (missing key information), inform user:

```
⚠️ Knowledge Gap Detected

Wiki lacks sufficient information on: <topic>

Options:
1. Proceed with partial answer (current)
2. Research and compile new knowledge (triggers wiki-research)
3. Save as review item for later investigation

What would you like to do?
```

**Why this checkpoint matters:**
- Prevents giving misleading incomplete answers
- Enables proactive knowledge base growth
- Allows user to decide research priority

**Skip checkpoint when:**
- Answer is complete with 2+ sources
- User explicitly requested quick/partial answer
- Gap is minor and doesn't affect core answer

---

### Step 6: Evaluate Save-Back

Determine if query should be saved:

**Save if:**
- Query is substantive (not trivial)
- Answer has 2+ sources
- Answer is >200 characters
- Query type is informational or procedural

**Don't save if:**
- Trivial query ("what is X")
- Single source
- Very short answer

---

### Step 7: Save Query (Optional)

If saving, create `wiki/queries/<date>-<slug>.md`:

```markdown
---
type: query
title: "Q: <question summary>"
created: YYYY-MM-DD
tags: [query, <domain>]
---

# Q: <question>

<full question text>

## Answer

<generated answer>

## Sources

- [[source-1]]
- [[source-2]]
```

---

### Step 8: Report Results

```markdown
## Answer

<generated answer>

## Sources
- [[react-hooks]] — "React Hooks are functions that..."
- [[use-state]] — "useState adds state to..."

## Related
- [[use-effect]]
- [[custom-hooks]]

## Gaps
- No specific information on: performance optimization
```

---

## Tools to Use

| Tool | Purpose |
|------|---------|
| `mcp__obsidian-mcp-tools__search_vault_smart` | Semantic search |
| `readFile` | Read matched pages |
| `listDirectory` | Scan wiki structure |
| LLM API | Generate answer |

---

## Search Algorithm Details

### Token Extraction

```python
def tokenize_query(query):
    tokens = []
    raw = query.lower().split(/[\s,，。！？、；：""''（）()\-_/\\]+/)
    
    for token in raw:
        if len(token) <= 1: continue
        if token in STOP_WORDS: continue
        
        if has_cjk(token) and len(token) > 2:
            # Add bigrams
            chars = list(token)
            for i in range(len(chars) - 1):
                tokens.append(chars[i] + chars[i+1])
            # Add individual chars
            tokens.extend(chars)
            # Add original
            tokens.append(token)
        else:
            tokens.append(token)
    
    return unique(tokens)
```

### RRF Fusion

```python
def reciprocal_rank_fusion(lists, k=60):
    scores = {}
    for lst in lists:
        for rank, item in enumerate(lst):
            path = item.path
            rrf_score = 1 / (k + rank + 1)
            scores[path] = scores.get(path, 0) + rrf_score
    return scores
```

---

## Examples

### Example 1: Factual Query

**Query:** "What is attention mechanism?"

**Process:**
1. Type: Factual
2. Search: "attention mechanism"
3. Results: `wiki/concepts/attention-mechanism.md`
4. Expand: `wiki/entities/transformer.md`, `wiki/concepts/self-attention.md`
5. Generate answer with citations

**Output:**
```markdown
## Answer

Attention mechanism is a technique that allows models to focus on relevant
parts of the input when producing output. It computes weighted importance
scores for different input positions.

## Sources
- [[attention-mechanism]] — Core definition and explanation
- [[transformer]] — Architecture using attention

## Related
- [[self-attention]]
- [[multi-head-attention]]
```

### Example 2: Procedural Query

**Query:** "How do I deploy the application?"

**Process:**
1. Type: Procedural
2. Search: "deploy application"
3. Results: `wiki/procedures/deploy-application.md`
4. Generate step-by-step answer

**Output:**
```markdown
## Answer

To deploy the application:

1. Build the production bundle: `npm run build`
2. Upload to server: `scp dist/ server:/app`
3. Restart the service: `systemctl restart app`

## Sources
- [[deploy-application]] — Full deployment procedure

## Related
- [[rollback-procedure]]
- [[monitoring-setup]]
```

### Example 3: Troubleshooting Query

**Query:** "Memory leak in worker process"

**Process:**
1. Type: Troubleshooting
2. Search: "memory leak worker"
3. Results: `wiki/troubleshooting/fix-memory-leak-worker.md`
4. Generate solution-focused answer

**Output:**
```markdown
## Answer

The memory leak is likely caused by unclosed database connections.

**Solution:** Always close connections in `finally` blocks:

```javascript
try {
  const conn = await getConnection();
  // ... work
} finally {
  conn?.close();
}
```

## Sources
- [[fix-memory-leak-worker]] — Complete troubleshooting guide

## Related
- [[connection-pooling]]
- [[worker-configuration]]
```

---

## Quality Principles

1. **Always cite sources** — Answers must be grounded
2. **Acknowledge gaps** — Be honest about missing information
3. **Prefer procedures** — For how-to questions
4. **Use graph expansion** — Find related but not directly matched content
5. **Save valuable queries** — Enable future reference

---

## Error Handling

| Error | Action |
|-------|--------|
| No results found | Report "No information found", suggest research |
| Search tool unavailable | Fall back to filename matching |
| Cannot read page | Skip, continue with other results |
| LLM generation fails | Return raw search results |

---

## Completion Checklist

- [ ] Query parsed and understood
- [ ] Search performed
- [ ] Results scored and ranked
- [ ] Graph expansion completed
- [ ] Answer generated with citations
- [ ] Save-back evaluated
- [ ] Results reported to user

---

## Tools to Use

| Tool | Purpose | When | 完整路径 |
|------|---------|------|----------|
| `mcp__obsidian-mcp-tools__search_vault_smart` | 语义搜索 wiki | Step 2b | 见下方调用示例 |
| `Read` | 读取匹配的 wiki 页面 | Step 4 | `/mnt/c/obsidian_wiki/wiki/<type>/<file>` |
| `Glob` | 扫描 wiki 目录结构 | Step 2a | `/mnt/c/obsidian_wiki/wiki/**/*.md` |
| `Write` | 保存高价值查询 | Step 7 | `/mnt/c/obsidian_wiki/wiki/queries/<date>-<slug>.md` |

### search_vault_smart 调用示例

```json
mcp__obsidian-mcp-tools__search_vault_smart({
  "query": "<关键词>",
  "filter": {
    "folders": ["wiki/sources/", "wiki/entities/", "wiki/procedures/", "wiki/claims/", "wiki/topics/", "wiki/synthesis/", "wiki/queries/", "wiki/_registry/", "wiki/candidates/graphify/"],
    "limit": 20
  }
})
```

**⚠️ 重要**：`filter` 必须是 JSON 对象，不能是字符串。

---

## Obsidian 格式保留规则

### 双链引用输出

**必须使用合法双链格式**：
- `[[页面名]]` — 标准双链
- `[[页面名|显示文本]]` — 带别名的双链
- `[[目录/页面名]]` — 带路径的双链

**禁止**：
- 输出 typed-id 伪双链（如 `[[entity:xxx]]`、`[[procedure:xxx]]`）
- 将双链转换为 Markdown 链接格式 `[文本](url)`

### 稳定 ID 处理

当引用的节点有稳定 ID（如 `entity:s-parameters`）但对应页面不存在时：
- 使用反引号保留稳定 ID：`` `entity:s-parameters` ``
- 不生成伪双链

### 图片引用

**保留原图片格式**：
- `![[image.png]]` — Obsidian 内部图片
- `![](url)` — 外部图片链接

**禁止**：
- 将 `![[image.png]]` 转换为 `<img>` 标签
- 修改图片的显示尺寸参数
