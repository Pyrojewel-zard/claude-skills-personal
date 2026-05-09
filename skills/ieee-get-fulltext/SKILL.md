---
name: ieee-get-fulltext
description: Use when extracting the complete full text of IEEE papers from IEEE Xplore. Simple approach - navigate, wait 20s for dynamic content, then extract body text.
---

# IEEE Get Full Text (Simple & Reliable)

## Overview

Extract complete full text from IEEE Xplore papers using Chrome DevTools MCP. **Simple rule**: Navigate → Wait 20s → Extract body content.

## When to Use

- Fetching complete paper content from IEEE Xplore
- Static tools return only navigation/footer
- Previous attempts failed due to dynamic loading

## When NOT to Use

- Paper without institutional access
- Only abstract/metadata needed (use `ieee-paper-detail`)
- Non-IEEE sources

## Core Pattern

```
IEEE ARN → Navigate → Wait 20s → Extract Body → Validate → Save
```

## Implementation

### Step 1: Navigate to Paper

```javascript
mcp__chrome-devtools__navigate_page({
  url: "https://ieeexplore.ieee.org/document/{arnumber}",
  initScript: "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})
```

### Step 2: Wait & Check Access

```javascript
async () => {
  // Wait for Angular dynamic content to load
  await new Promise(r => setTimeout(r, 20000));

  const bodyText = document.body.innerText;

  // Check access barriers
  const hasLoginWall = /Sign in to access|Institutional Access|Please sign in/i.test(bodyText);
  const hasPaywall = /Purchase|Buy Now|USD \$|Price:/i.test(bodyText);

  // Check for fulltext indicators
  const hasIntroduction = /SECTION\s+I|INTRODUCTION|Introduction/i.test(bodyText);
  const hasConclusion = /CONCLUSION|Conclusion|ACKNOWLEDGMENT/i.test(bodyText);
  const hasFigures = /Fig\.\s*\d|Figure\s+\d/i.test(bodyText);
  const hasCitations = /\[\d+\]|\(\d+\)/.test(bodyText);

  const canAccess = hasIntroduction && !hasLoginWall && !hasPaywall;

  return {
    canAccess,
    hasLoginWall,
    hasPaywall,
    indicators: { hasIntroduction, hasConclusion, hasFigures, hasCitations },
    bodyLength: bodyText.length
  };
}
```

**Decision:**
- `canAccess: true` → Proceed to Step 3
- `canAccess: false` → Stop and report access issue

### Step 3: Extract Full Text

```javascript
async () => {
  // Clean body content
  const body = document.body.cloneNode(true);

  // Remove non-content elements
  const selectorsToRemove = [
    'nav', 'header', 'footer', '.sidebar', '.related-articles',
    '.ads', '.promo', 'script', 'style', 'iframe', 'noscript',
    '.access-provided-by', '.document-banner', '.pdf-container'
  ];

  selectorsToRemove.forEach(sel => {
    body.querySelectorAll(sel).forEach(el => el.remove());
  });

  // Get clean text
  let content = body.innerText
    .replace(/\n{3,}/g, '\n\n')     // Collapse multiple newlines
    .replace(/^\s+|\s+$/g, '')      // Trim
    .trim();

  // Extract metadata from page
  const title = document.querySelector('.document-title span')?.textContent?.trim() ||
                document.querySelector('h1')?.textContent?.trim() || '';

  const authors = [...document.querySelectorAll('.authors-info a[href*="/author/"]')]
    .map(a => a.textContent.trim()).filter(Boolean);

  const doi = document.querySelector('a[href*="doi.org"]')?.textContent?.trim() || '';

  const year = document.body.innerText.match(/\b(20\d{2})\b/)?.[0] || '';

  // Extract sections
  const sections = [...document.querySelectorAll('h1, h2, h3, .section-title')]
    .map(h => h.innerText.trim())
    .filter(t => t && t.length < 200 && t.length > 5)
    .slice(0, 20);

  return {
    content,
    length: content.length,
    title,
    authors,
    doi,
    year,
    sections,
    success: content.length > 3000  // Minimum threshold
  };
}
```

### Step 4: Validate & Save

```javascript
async function saveFullText(arnumber) {
  // Step 1: Navigate
  await navigate(arnumber);

  // Step 2: Check access
  const access = await checkAccess();
  if (!access.canAccess) {
    return {
      success: false,
      error: access.hasLoginWall ? "需要登录访问全文" :
             access.hasPaywall ? "需要机构订阅" : "无法访问全文"
    };
  }

  // Step 3: Extract
  const data = await extractContent();

  if (!data.success) {
    return {
      success: false,
      error: `提取失败，内容长度 ${data.length} 太短`
    };
  }

  // Step 4: Format & Save
  const output = formatFullText(data, arnumber);

  return {
    success: true,
    arnumber,
    content: output,
    metadata: {
      title: data.title,
      authors: data.authors,
      year: data.year,
      doi: data.doi,
      length: data.length
    }
  };
}
```

## Output Format

```markdown
---
title: "{title}"
authors: {authors}
year: "{year}"
doi: "{doi}"
arnumber: "{arnumber}"
source: "IEEE Xplore"
extracted_date: "{timestamp}"
content_length: {length}
---

# {title}

**Authors**: {authors}
**DOI**: {doi}
**ARN**: {arnumber}

---

## Full Text

{content}

---

*Extracted from IEEE Xplore on {timestamp}*
```

## Troubleshooting

| 问题 | 原因 | 解决 |
|------|------|------|
| "需要登录访问全文" | 会话过期 | 在浏览器中重新登录 |
| "需要机构订阅" | 无访问权限 | 通过机构VPN访问 |
| 内容太短 (< 3000字符) | 页面未完全加载 | 等待时间可能不足 |

## Key Principle

> **简单可靠**: 不依赖特定CSS选择器，而是等待20秒后提取整个body内容，然后清理非内容元素。

## Related Skills

- `ieee-paper-detail` - Extract metadata only
- `ieee-paper-markdown` - Format structured notes
- `ieee-download` - Direct PDF download

---

*Simple and reliable full text extraction - navigate, wait, extract*
