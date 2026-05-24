---
name: wiki-lint
description: |
  Health-check the wiki for structural and semantic issues. Find contradictions,
  missing pages, broken links, duplicates, and stale structures. Use this skill
  whenever the user wants to audit wiki quality, says "lint wiki", "check health",
  "audit wiki", "find issues", "validate wiki", "健康检查", "审计", "检查wiki".
---

# wiki-lint

Health-check the wiki for issues and generate maintenance suggestions. This skill is
**fully self-contained** — follow these instructions to execute the complete workflow.

## Overview

```
wiki/ → [wiki-lint] → Lint Report
              ↓
       - Structural issues (orphan pages, broken links)
       - Semantic issues (contradictions, stale content)
       - Maintenance suggestions
       - Crystallization candidates
```

---

## Execution Steps

### Step 1: Scan Wiki Structure

#### 1a. List All Pages

Use `Glob` to scan `wiki/` recursively.

Collect all `.md` files, excluding:
- `index.md` (index page, but must check existence and format)
- `log.md` (activity log, but must check existence and recent date)
- `hot.md` (cache page, but must check existence and <500 chars)

#### 1b. Build Page Index

For each page:
- Read content
- Extract frontmatter (type, title, created, tags)
- Extract wikilinks `[[link]]`
- Record file path

---

### Step 2: Structural Lint

#### 2a. Check Orphan Pages

Find pages with no inbound links:

```
For each page P:
  inbound_count = count of pages that link to P
  if inbound_count == 0:
    report orphan
```

**Note:** Case-insensitive matching for wikilinks.

#### 2b. Check Broken Links

Find wikilinks to non-existent pages:

```
For each page P:
  for each wikilink L in P:
    if L.target does not exist:
      report broken link in P
```

#### 2c. Check Connectivity

Find pages with no outbound links:

```
For each page P:
  if P has no wikilinks:
    report no-outlinks
```

---

### Step 3: Semantic Lint

#### 3a. Frontmatter 检查（必检）

| 检查项 | 适用类型 | 规则 |
|--------|----------|------|
| id 格式 | 所有 | 必须为 `type:slug` 格式 |
| type 字段 | 所有 | 必须为 source/entity/concept/procedure/claim 之一 |
| created_at | 所有 | 必须存在且为有效日期 |
| sources | entity/concept/claim | 必须引用至少 1 个 source |
| entities | concept | 必须引用至少 2 个 entity |
| claim_type | claim | 必须为 insight/decision/constraint |
| evidence_type | claim | 必须为 experimental/constraint/precedent/gap |
| raw_ref | source | 必须指向存在的 raw 文件 |

#### 3b. 页面长度检查（必检）

| 类型 | 下限 | 上限 |
|------|------|------|
| entity | 100 行 | 300 行 |
| concept | 50 行 | 200 行 |
| claim | 50 行 | 200 行 |
| procedure | 50 行 | 300 行 |
| source | 100 行 | 300 行 |

#### 3c. LLM 矛盾检测（可选）

需要 LLM。跳过条件：LLM 不可用或页面数 <5。

#### 3a. Build Page Summaries

For each page:
- Extract frontmatter
- Take first 500 characters
- Create summary: `### <path>\n<preview>`

#### 3b. LLM Analysis

Prompt:
```
You are a wiki quality analyst. Review the following wiki page summaries and identify issues.

For each issue, output:
---LINT: type | severity | Short title---
Description of the issue.
PAGES: page1.md, page2.md
---END LINT---

Types:
- contradiction: conflicting claims
- stale: outdated information
- missing-page: heavily referenced but no dedicated page
- suggestion: question or source worth adding

Severities:
- warning: should be addressed
- info: nice to have

Only report genuine issues. Do not invent problems.

## Wiki Pages

<page summaries>
```

#### 3c. Parse LLM Results

Extract `---LINT---` blocks and parse:
- type
- severity
- title
- description
- affected pages

---

### Step 4: Generate Report

#### 4a. Group by Type

Organize issues:

| Type | Severity | Description |
|------|----------|-------------|
| orphan | info | No inbound links |
| broken-link | warning | Link to non-existent page |
| no-outlinks | info | No outbound links |
| contradiction | warning | Conflicting claims |
| stale | info | Outdated information |
| missing-page | info | Referenced but no page |
| suggestion | info | Worth adding |

#### 4b. Sort by Severity

Warnings first, then info.

#### 4c. Add Recommendations

For each issue type, suggest action:

| Issue | Recommendation |
|-------|----------------|
| orphan | Add links from related pages, or consider removing |
| broken-link | Create missing page or fix link |
| no-outlinks | Add links to related concepts |
| contradiction | Review and resolve conflict |
| missing-page | Create page or use `/wiki-crystallize` |
| suggestion | Consider adding to wiki |

---

### Step 5: Identify Crystallization Candidates

From lint results, identify content ready for crystallization:

- `missing-page` items → candidates for creation
- Repeated concepts in suggestions → formalize
- Orphan procedures → integrate or remove

---

### Step 5.5: ⚠️ Lint Action Checkpoint (IMPORTANT)

**Before outputting final report, confirm with user:**

When lint finds significant issues (≥5 warnings or ≥10 total issues), pause and ask:

```
Lint Scan Complete

Found:
- W warnings (broken links, contradictions)
- I info items (orphans, missing pages)
- C crystallization candidates

Priority actions:
1. <most critical issue>
2. <second critical issue>
3. <third critical issue>

Proceed with full report? Or focus on specific issue type?
```

**Why this checkpoint matters:**
- Prevents overwhelming user with too many issues at once
- Allows prioritizing critical fixes first
- Enables focused cleanup sessions

**Skip checkpoint only when:**
- Few issues found (<5 total)
- User explicitly requested "full lint report"
- Running in automated maintenance mode

---

### Step 6: Output Report

```markdown
# Wiki Lint Report

**Generated:** YYYY-MM-DD HH:mm
**Pages scanned:** N
**Issues found:** M (W warnings, I info)

---

## Warnings

### Broken Links

| Source | Broken Link | Action |
|--------|-------------|--------|
| wiki/entities/foo.md | [[missing-concept]] | Create page or fix link |
| wiki/concepts/bar.md | [[typo-pgae]] | Fix typo |

### Contradictions

| Issue | Affected Pages |
|-------|----------------|
| "API limit is 100/min" vs "API limit is 1000/min" | wiki/entities/api.md, wiki/concepts/rate-limit.md |

---

## Info

### Orphan Pages

| Page | Suggestion |
|------|------------|
| wiki/entities/unused.md | Add links from related pages |

### Missing Pages

| Referenced As | Reference Count | Suggestion |
|---------------|-----------------|------------|
| attention-mechanism | 5 | Create concept page |

### No Outbound Links

| Page | Suggestion |
|------|------------|
| wiki/queries/research-x.md | Add links to related concepts |

---

## Crystallization Candidates

- `attention-mechanism` — referenced 5 times, consider creating
- `deployment-process` — mentioned in 3 logs, consider formalizing

---

## Statistics

| Metric | Count |
|--------|-------|
| Total pages | N |
| Orphan pages | O |
| Broken links | B |
| Contradictions | C |
| Missing pages | M |

## Next Steps

1. Fix broken links (warnings)
2. Resolve contradictions (warnings)
3. Create missing pages
4. Run `/wiki-crystallize` on candidates
```

---

## Tools to Use

| Tool | Purpose | When | 完整路径 |
|------|---------|------|----------|
| `Glob` | 扫描 wiki 结构 | Step 1 | `/mnt/c/obsidian_wiki/wiki/**/*.md` |
| `Read` | 读取页面内容 | Step 1b | `/mnt/c/obsidian_wiki/wiki/...` |
| `mcp__obsidian-mcp-tools__search_vault_smart` | 搜索相关页面 | Step 2 | 见下方调用示例 |

### search_vault_smart 调用示例

```json
mcp__obsidian-mcp-tools__search_vault_smart({
  "query": "<页面关键词>",
  "filter": {
    "folders": ["wiki/"],
    "limit": 20
  }
})
```

**⚠️ 重要**：`filter` 必须是 JSON 对象，不能是字符串。

---

## Obsidian 格式检查

### 双链引用检查

**合法格式**：
- `[[页面名]]` — 标准双链
- `[[页面名|显示文本]]` — 带别名的双链
- `[[目录/页面名]]` — 带路径的双链

**需要报告的问题**：
- typed-id 伪双链（如 `[[entity:xxx]]`）
- 双链转换为 Markdown 链接格式

### 图片引用检查

**合法格式**：
- `![[image.png]]` — Obsidian 内部图片
- `![](url)` — 外部图片链接

**需要报告的问题**：
- 图片引用转换为 `<img>` 标签

---

## Link Extraction

```python
def extract_wikilinks(content):
    links = []
    regex = r'\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]'
    for match in re.finditer(regex, content):
        links.append(match.group(1).strip())
    return links
```

---

## Page Existence Check

```python
def page_exists(link, slug_map):
    normalized = link.lower()
    # Check exact match
    if normalized in slug_map:
        return True
    # Check with hyphens
    if normalized.replace(' ', '-') in slug_map:
        return True
    return False
```

---

## Examples

### Example 1: Structural Lint Only

**Input:** User says "lint the wiki"

**Process:**
1. Scan all wiki pages
2. Build link graph
3. Find orphans, broken links, no-outlinks
4. Generate report

**Output:**
```markdown
# Wiki Lint Report

**Generated:** 2026-05-12 14:30
**Pages scanned:** 45
**Issues found:** 8 (2 warnings, 6 info)

## Warnings

### Broken Links

| Source | Broken Link |
|--------|-------------|
| wiki/entities/api.md | [[rate-limt]] | Typo? Should be [[rate-limit]] |

## Info

### Orphan Pages

| Page |
|------|
| wiki/entities/legacy-system.md |

### Missing Pages

| Referenced As | Count |
|---------------|-------|
| authentication-flow | 3 |
```

### Example 2: Full Lint with Semantics

**Input:** User says "check wiki health including contradictions"

**Process:**
1. Structural lint
2. LLM semantic analysis
3. Find contradictions and stale content
4. Generate comprehensive report

---

## Quality Principles

1. **Conservative on semantic issues** — Avoid false positives
2. **Actionable recommendations** — Every issue should have a suggested fix
3. **Prioritize warnings** — Address broken links and contradictions first
4. **Exclude index/log from orphan check** — These are special pages
5. **Case-insensitive links** — [[Transformer]] matches transformer.md
6. **Check persistence layer** — hot.md (<500 字), index.md (格式正确), log.md (最新条目日期 ≤7 天)

---

## Error Handling

| Error | Action |
|-------|--------|
| Cannot read page | Skip, note in report |
| Wiki directory empty | Report "No wiki pages found" |
| LLM unavailable | Skip semantic lint, do structural only |

---

## 边界条件处理

| 情况 | 处理方式 |
|------|----------|
| Wiki 目录不存在 | 报告错误，建议运行 wiki-init |
| 页面数量过多（>500） | 分批处理，每批 100 页 |
| LLM 分析超时 | 仅输出结构检查结果 |
| Registry 文件损坏 | 跳过 registry 相关检查 |

---

## Completion Checklist

- [ ] Wiki structure scanned
- [ ] Page index built
- [ ] Structural lint completed
- [ ] Semantic lint completed (if LLM available)
- [ ] Issues grouped and sorted
- [ ] Recommendations generated
- [ ] Crystallization candidates identified
- [ ] Report generated

---

## 相关 Skill

| Skill | 路径 | 用途 |
|-------|------|------|
| wiki-crystallize | `/home/holmes/.cc-switch/skills/wiki-crystallize/SKILL.md` | candidate 提升 |
| wiki-init | `/mnt/c/obsidian_wiki/.claude/commands/wiki-init.md` | 骨架初始化 |
| wiki-compile | `/home/holmes/.cc-switch/skills/wiki-compile/SKILL.md` | 编译修复 |