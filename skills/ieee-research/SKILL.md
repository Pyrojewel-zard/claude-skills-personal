---
name: ieee-research
description: Systematic IEEE literature research agent. Searches venues, extracts full content from papers, analyzes relevance, and archives findings. Use for comprehensive literature surveys across multiple journals/conferences.
argument-hint: "[venue, keywords, year range]"
---

# IEEE Research Agent

Systematic literature research across IEEE Xplore venues. Combines search, full-content extraction, and relevance analysis.

## Overview

This agent orchestrates the complete research workflow:
1. Search IEEE Xplore for papers matching criteria
2. Extract full content from high-relevance papers using `ieee-paper-fullcontent`
3. Analyze and score relevance
4. Archive findings to knowledge base

## Required Sub-Skills

- `ieee-search` - For initial paper discovery
- `ieee-paper-fullcontent` - For deep content extraction (NOT `ieee-paper-detail`)
- `ieee-export` - For citation export (optional)

## Workflow

### Phase 1: Search Papers

Use `ieee-search` to find papers in target venue:

```
navigate_page({
  url: "https://ieeexplore.ieee.org/xpl/conhome.jsp?punumber=1234567", // Conference/journal home
  initScript: "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

// Use ieee-search skill with venue-specific keywords
```

**Search Strategy per Venue:**

| Venue | Keywords | Time Range |
|-------|----------|------------|
| TCAD | "machine learning" AND "analog" AND "design" | 2024-2026 |
| DAC | "AI" AND "EDA" AND "analog" | 2024-2026 |
| ICCAD | "generative" AND "circuit" | 2024-2026 |
| MLCAD | "LLM" AND "CAD" | 2024-2026 |
| T-MTT | "mm-wave" AND "passive" | 2024-2026 |
| RFIC | "mm-wave LNA" | 2024-2026 |
| JSSC | "mm-wave" AND "LNA" | 2024-2026 |

### Phase 2: Extract Full Content

For each high-relevance paper, use `ieee-paper-fullcontent`:

**REQUIRED:** Use full content extraction, not just detail extraction.

```
// From ieee-paper-fullcontent skill:
navigate_page({
  url: "https://ieeexplore.ieee.org/document/{arnumber}",
  initScript: "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

// Scroll to trigger lazy loading
evaluate_script(async () => {
  window.scrollTo(0, document.body.scrollHeight);
  await new Promise(r => setTimeout(r, 1000));
  window.scrollTo(0, 0);
  return { scrolled: true };
})

// Extract full content
evaluate_script(function() {
  // ... (full extraction code from ieee-paper-fullcontent)
})
```

### Phase 3: Relevance Analysis

Score each paper on these criteria:

| Criterion | Weight | Questions |
|-----------|--------|-----------|
| **Technical Relevance** | 40% | Does it directly address your research topic? |
| **Methodology Value** | 30% | Can the method be adapted/extended? |
| **Novelty** | 20% | Is the approach new or incremental? |
| **Reproducibility** | 10% | Are code/data available? |

**Relevance Scoring:**
- 8-10: Must read - directly applicable
- 6-7: Should read - relevant but needs adaptation
- 4-5: Optional - tangentially relevant
- 0-3: Skip - not relevant

### Phase 4: Archive Findings

Save results to knowledge base:

```markdown
---
title: "{Venue} Literature Search - {Date}"
date: YYYY-MM-DD
venue: {venue}
keywords: [{keywords}]
total_papers: N
high_relevance: M
---

## Search Parameters
- Venue: {venue}
- Keywords: {keywords}
- Time Range: {years}

## High Relevance Papers (Score >= 7)

| # | Title | Authors | Year | Score | DOI | Full Text Summary |
|---|-------|---------|------|-------|-----|-------------------|
| 1 | ... | ... | ... | 8.5 | ... | Key findings... |

## Medium Relevance (Score 5-6)

| # | Title | Authors | Year | Score | DOI |
|---|-------|---------|------|-------|-----|
| ... | ... | ... | ... | ... | ... |

## Key Insights

- [Insight 1 from full-text analysis]
- [Insight 2 from full-text analysis]

## Figure URLs for Multi-Modal Analysis

- [Paper 1 Fig 1]({url}) - Circuit schematic
- [Paper 1 Fig 2]({url}) - Layout diagram
```

## Rate Limiting

**CRITICAL:** IEEE Xplore has rate limits. Follow these rules:

1. **Wait 30 seconds between requests**
2. **Wait 60 seconds if 429 error**
3. **Process papers serially, NOT in parallel**
4. **Limit to 50 papers per session**

## Implementation Template

```javascript
// Main research function
async function researchPapers(venue, keywords, years) {
  const results = [];

  // 1. Search
  const papers = await searchIEEE(venue, keywords, years);

  // 2. Process each paper serially
  for (const paper of papers.slice(0, 50)) {
    // Extract full content
    const fullText = await extractFullContent(paper.arnumber);

    // Score relevance
    const score = analyzeRelevance(fullText, keywords);

    // Store if relevant
    if (score >= 5) {
      results.push({ ...paper, fullText, score });
    }

    // Rate limiting
    await sleep(30000);
  }

  // 3. Archive
  await archiveResults(results, venue);

  return results;
}
```

## Key Differences from ieee-paper-detail

| Feature | ieee-paper-detail | ieee-research (with fullcontent) |
|---------|-------------------|----------------------------------|
| Content | Metadata only | **Full text + sections + figures** |
| Analysis | Limited | **Deep - can analyze circuits** |
| Figures | Count only | **URLs extracted for screenshot** |
| Equations | ❌ | **✅ Extracted and counted** |
| Multi-modal | ❌ | **✅ Can analyze schematics** |
| Use case | Quick lookup | **Systematic research** |

## Error Handling

| Condition | Action |
|-----------|--------|
| No full text | Skip and note "PDF only" |
| Subscription required | Log DOI for later access |
| Rate limit (429) | Wait 60s, retry |
| Extraction timeout | Skip, mark as failed |

## Output Format

Final output should include:

1. **Summary Statistics**
   - Total papers searched
   - High/medium/low relevance counts
   - Processing time

2. **Ranked Paper List**
   - Sorted by relevance score
   - Include full-text summaries for top papers

3. **Knowledge Base Archive**
   - Path to saved markdown file
   - Links to extracted figures
   - Zotero collection (if exported)

## Example Usage

```
User: "Research TCAD 2024-2026 for machine learning analog design papers"

Agent:
1. Search TCAD with keywords "machine learning" AND "analog" AND "design"
2. For top 20 results:
   - Extract full content using ieee-paper-fullcontent
   - Score relevance (0-10)
   - Extract figure URLs
3. Archive papers with score >= 7
4. Generate summary report
```

## Notes

- Always use **serial processing** to respect rate limits
- Full content extraction enables **circuit analysis** via screenshots
- Archive results immediately - don't wait for all papers
- Use Obsidian MCP to save to knowledge base
- Consider Zotero export for bibliography management
