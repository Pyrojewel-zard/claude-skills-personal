---
name: ieee-research
description: "IEEE Xplore 文献检索全流程。支持：基础搜索、高级搜索（字段过滤）、期刊浏览、论文详情提取、全文提取、PDF 下载。触发词：ieee、IEEE Xplore、检索、下载、详情。"
argument-hint: "[搜索关键词或操作描述]"
user_invocable: true
---

# IEEE Research: IEEE Xplore 文献检索全流程

一站式 IEEE 文献检索：搜索 → 详情/全文 → 下载。

## 模式

根据 `$ARGUMENTS` 自动选择模式：

| 模式 | 触发条件 | 操作 |
|------|----------|------|
| **search** | 提供关键词 | 搜索论文 |
| **advanced** | 包含过滤条件（作者、期刊、年份） | 高级搜索 |
| **browse** | "浏览期刊"、"browse journal" | 期刊/会议浏览 |
| **detail** | 提供 DOI 或 article number | 提取论文详情 |
| **fulltext** | "全文"、"fulltext" | 提取全文内容 |
| **download** | "下载"、"download" | 下载 PDF |

## 常量

- **BASE_URL** = `https://ieeexplore.ieee.org`
- **MAX_RESULTS** = 25（单页结果数）
- **RATE_LIMIT** = 30s（请求间隔，避免 429）

---

## Phase 1: 搜索

### 1.1 基础搜索

```javascript
// 构造 URL
const url = `${BASE_URL}/search/searchresult.jsp?newsearch=true&queryText=${encodeURIComponent(QUERY)}`;

// 导航
navigate_page({ url, initScript: "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})" })

// 提取结果（单次 evaluate_script，内置等待）
async () => {
  for (let i = 0; i < 30; i++) {
    if (document.querySelectorAll('.List-results-items .result-item').length > 0) break;
    await new Promise(r => setTimeout(r, 500));
  }

  const items = document.querySelectorAll('.List-results-items .result-item');
  const papers = [];

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const titleLink = item.querySelector('h3 a[href*="/document/"]');
    const authors = [...item.querySelectorAll('.author a[href*="/author/"]')].map(a => a.textContent.trim());
    const pubLink = item.querySelector('.description a[href*="/xpl/"]');
    const infoText = item.querySelector('.publisher-info-container')?.textContent?.trim() || '';
    const yearMatch = infoText.match(/Year:\s*(\d{4})/);
    const docNumber = titleLink?.href?.match(/\/document\/(\d+)/)?.[1] || '';
    const citedByMatch = item.textContent.match(/Cited by:.*?(\d+)/);

    papers.push({
      rank: i + 1,
      title: titleLink?.textContent?.trim() || '',
      arnumber: docNumber,
      authors,
      publication: pubLink?.textContent?.trim() || '',
      year: yearMatch ? yearMatch[1] : '',
      citedBy: citedByMatch ? citedByMatch[1] : ''
    });
  }

  const resultCount = document.querySelector('.Dashboard-header span')?.textContent?.trim() || '';
  return { papers, resultCount, url: location.href };
}
```

### 1.2 高级搜索（字段过滤）

IEEE 支持布尔命令搜索：

| 字段 | 语法 | 示例 |
|------|------|------|
| 标题 | `"Document Title":term` | `"Document Title":transformer` |
| 作者 | `"Authors":name` | `"Authors":Hinton` |
| 期刊 | `"Publication Title":name` | `"Publication Title":IEEE Access` |
| 摘要 | `"Abstract":term` | `"Abstract":neural network` |
| DOI | `"DOI":value` | `"DOI":10.1109/TPAMI.2024.1234567` |
| 年份 | `ranges=2020_2025_Year` | URL 参数 |

**布尔组合**：
```
("Document Title":deep learning AND "Authors":LeCun)
("Abstract":transformer OR "Abstract":attention) AND "Publication Title":IEEE TPAMI
```

**URL 构造**：
```
{BASE_URL}/search/searchresult.jsp?action=search&matchBoolean=true&queryText={BOOLEAN_QUERY}&ranges={YEAR_RANGE}&contentType={TYPE}
```

### 1.3 期刊浏览

```javascript
// 导航到期刊首页
navigate_page({ url: `${BASE_URL}/xpl/RecentIssue.jsp?punumber=${PUNUMBER}` })

// 或浏览期刊列表
navigate_page({ url: `${BASE_URL}/xpl/topAccessedArticles.jsp` })
```

---

## Phase 2: 详情/全文提取

### 2.1 论文详情（元数据）

```javascript
// 导航到论文页
navigate_page({
  url: `${BASE_URL}/document/${ARNUMBER}`,
  initScript: "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

// 提取详情
async () => {
  await new Promise(r => setTimeout(r, 2000));
  window.scrollTo(0, document.body.scrollHeight);
  await new Promise(r => setTimeout(r, 1000));

  return {
    title: document.querySelector('.document-title span')?.textContent?.trim(),
    authors: [...document.querySelectorAll('.authors span a')].map(a => a.textContent.trim()),
    abstract: document.querySelector('.abstract-text')?.textContent?.trim(),
    keywords: [...document.querySelectorAll('.keywords span a')].map(a => a.textContent.trim()),
    publication: document.querySelector('.publication-title a')?.textContent?.trim(),
    year: document.querySelector('.doc-pub-date')?.textContent?.match(/\d{4}/)?.[0],
    doi: document.querySelector('.doc-doi')?.textContent?.trim(),
    arnumber: ARNUMBER,
    citedBy: document.querySelector('.cited-by-count')?.textContent?.trim(),
    figures: document.querySelectorAll('.figure-img').length,
    url: location.href
  };
}
```

### 2.2 全文提取（深度版）

```javascript
// 滚动触发懒加载
async () => {
  window.scrollTo(0, document.body.scrollHeight);
  await new Promise(r => setTimeout(r, 2000));
  window.scrollTo(0, 0);
  await new Promise(r => setTimeout(r, 1000));

  // 提取全文
  const sections = [];
  document.querySelectorAll('.article-section').forEach(sec => {
    const heading = sec.querySelector('h2, h3')?.textContent?.trim();
    const content = sec.querySelector('.section-content')?.textContent?.trim();
    if (heading && content) {
      sections.push({ heading, content: content.substring(0, 2000) });
    }
  });

  // 提取图片 URL
  const figures = [...document.querySelectorAll('.figure-img img, .figure-container img')].map(img => ({
    url: img.src,
    alt: img.alt
  }));

  // 提取公式数量
  const equations = document.querySelectorAll('.formula, .equation, [class*="math"]').length;

  return {
    sections,
    figures,
    equations,
    fullTextLength: document.body.innerText.length
  };
}
```

---

## Phase 3: PDF 下载

### 3.1 单篇下载（优化路径：2 tool calls）

IEEE PDF URL 模式：
```
{BASE_URL}/stampPDF/getPDF.jsp?tp=&arnumber={ARNUMBER}&ref=
```

**直接导航到 PDF**：

```javascript
// 1. 导航到 PDF
navigate_page({
  url: `${BASE_URL}/stampPDF/getPDF.jsp?tp=&arnumber=${ARNUMBER}&ref=`,
  initScript: "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

// 2. 触发下载
(arnumber, title) => {
  if (document.contentType === 'application/pdf') {
    const safeName = (title || '').replace(/[^\w\s-]/g, '').replace(/\s+/g, '_').substring(0, 60);
    const filename = arnumber + (safeName ? '-' + safeName : '') + '.pdf';
    const a = document.createElement('a');
    a.href = window.location.href;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    return { downloaded: true, filename };
  }
  return { downloaded: false, error: 'Not a PDF. Access may be denied.' };
}
```

### 3.2 批量下载

```javascript
// 顺序下载，间隔 3 秒
for (const arnumber of arnumbers) {
  await downloadPaper(arnumber);
  await new Promise(r => setTimeout(r, 3000));
}
```

---

## Phase 4: 结果归档

输出格式：

```markdown
## IEEE 检索结果

**查询**: {query}
**结果数**: {total}
**时间**: {timestamp}

### 高相关论文

| # | 标题 | 作者 | 期刊 | 年份 | 引用 |
|---|------|------|------|------|------|
| 1 | ... | ... | ... | ... | ... |

### 详情提取

- **DOI**: ...
- **摘要**: ...
- **关键词**: ...
```

---

## 错误处理

| 条件 | 处理 |
|------|------|
| 验证码 | 告知用户在浏览器中完成验证 |
| 无权限 | 告知用户检查机构登录状态 |
| 429 限流 | 等待 60 秒后重试 |
| 页面超时 | 跳过并记录 |

---

## 注意事项

- **必须使用 initScript** 绕过 webdriver 检测
- **请求间隔 30 秒** 避免 429 错误
- **串行处理** 论文，不要并行
- **单次最多 50 篇**，超过需分批

---

## 快速示例

\`\`\`
/ieee-research deep learning                    # 基础搜索
/ieee-research author:LeCun deep learning       # 高级搜索
/ieee-research browse TCAD                      # 浏览 TCAD 期刊
/ieee-research detail 10.1109/TPAMI.2024.123    # 详情（DOI）
/ieee-research fulltext 8876906                 # 全文提取
/ieee-research download 8876906                 # 下载 PDF
\`\`\`
