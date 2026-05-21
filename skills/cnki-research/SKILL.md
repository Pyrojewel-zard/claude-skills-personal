---
name: cnki-research
description: "CNKI 知网文献检索全流程。支持：基础搜索、高级搜索（来源类别过滤）、论文详情提取、PDF/CAJ 下载。触发词：cnki、知网、检索、下载。"
argument-hint: "[搜索关键词或操作描述]"
user_invocable: true
---

# CNKI Research: 知网文献检索全流程

一站式 CNKI 文献检索：搜索 → 详情 → 下载。

## 模式

根据 `$ARGUMENTS` 自动选择模式：

| 模式 | 触发条件 | 操作 |
|------|----------|------|
| **search** | 提供关键词 | 基础搜索 |
| **advanced** | 包含过滤条件（作者、期刊、来源类别） | 高级搜索 |
| **detail** | 提供论文 URL 或在详情页 | 提取论文详情 |
| **download** | "下载"、"download" | 下载 PDF/CAJ |

## 常量

- **BASE_URL** = `https://kns.cnki.net`
- **ADVANCED_URL** = `https://kns.cnki.net/kns/AdvSearch?classid=7NS01R8M`

---

## Phase 1: 搜索

### 1.1 基础搜索

```javascript
// 导航
navigate_page({ url: `${BASE_URL}/kns8s/search` })

// 搜索 + 提取结果（单次 evaluate_script）
async () => {
  const query = "YOUR_KEYWORDS";

  // 等待搜索框
  await new Promise((r, j) => {
    let n = 0;
    const c = () => { if (document.querySelector('input.search-input')) r(); else if (++n > 30) j('timeout'); else setTimeout(c, 500); };
    c();
  });

  // 验证码检查
  const outer = document.querySelector('#tcaptcha_transform_dy');
  if (outer && outer.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  // 填入并提交
  const input = document.querySelector('input.search-input');
  input.value = query;
  input.dispatchEvent(new Event('input', { bubbles: true }));
  document.querySelector('input.search-btn')?.click();

  // 等待结果
  await new Promise((r, j) => {
    let n = 0;
    const c = () => { if (document.body.innerText.includes('条结果')) r(); else if (++n > 30) j('timeout'); else setTimeout(c, 500); };
    c();
  });

  // 再次检查验证码
  const outer2 = document.querySelector('#tcaptcha_transform_dy');
  if (outer2 && outer2.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  // 提取结果
  const rows = document.querySelectorAll('.result-table-list tbody tr');
  const checkboxes = document.querySelectorAll('.result-table-list tbody input.cbItem');
  const results = Array.from(rows).map((row, i) => {
    const titleLink = row.querySelector('td.name a.fz14');
    const authors = Array.from(row.querySelectorAll('td.author a.KnowledgeNetLink') || []).map(a => a.innerText?.trim());
    const journal = row.querySelector('td.source a')?.innerText?.trim() || '';
    const date = row.querySelector('td.date')?.innerText?.trim() || '';
    const citations = row.querySelector('td.quote')?.innerText?.trim() || '';
    const downloads = row.querySelector('td.download')?.innerText?.trim() || '';
    return {
      n: i + 1,
      title: titleLink?.innerText?.trim() || '',
      href: titleLink?.href || '',
      exportId: checkboxes[i]?.value || '',
      authors: authors.join('; '),
      journal,
      date,
      citations,
      downloads
    };
  });

  return {
    query,
    total: document.querySelector('.pagerTitleCell')?.innerText?.match(/([\d,]+)/)?.[1] || '0',
    page: document.querySelector('.countPageMark')?.innerText || '1/1',
    results
  };
}
```

### 1.2 高级搜索（来源类别过滤）

高级搜索支持：
- **字段过滤**：主题、篇名、关键词、摘要
- **来源类别**：SCI、EI、北大核心、CSSCI、CSCD
- **时间范围**：起始年 - 结束年
- **作者/期刊**：精确匹配

```javascript
// 导航到高级检索页
navigate_page({ url: ADVANCED_URL })

// 高级搜索
async () => {
  const query = "KEYWORDS";          // 搜索词
  const fieldType = "SU";           // SU=主题, TI=篇名, KY=关键词, AB=摘要
  const sourceTypes = ["SCI", "EI"]; // 来源类别
  const startYear = "2020";
  const endYear = "2025";
  const author = "";
  const journal = "";

  // 等待表单
  await new Promise((r, j) => {
    let n = 0;
    const c = () => { if (document.querySelector('#txt_1_value1')) r(); else if (n++ > 30) j('timeout'); else setTimeout(c, 500); };
    c();
  });

  // 验证码检查
  const cap = document.querySelector('#tcaptcha_transform_dy');
  if (cap && cap.getBoundingClientRect().top >= 0) return { error: 'captcha' };

  const selects = Array.from(document.querySelectorAll('select')).filter(s => s.offsetParent !== null);

  // 来源类别
  if (sourceTypes.length > 0) {
    const gjAll = document.querySelector('#gjAll');
    if (gjAll && gjAll.checked) gjAll.click();
    for (const st of sourceTypes) {
      const cb = document.querySelector('#' + st);
      if (cb && !cb.checked) cb.click();
    }
  }

  // 字段类型 + 关键词
  selects[0].value = fieldType;
  selects[0].dispatchEvent(new Event('change', { bubbles: true }));
  const input = document.querySelector('#txt_1_value1');
  input.value = query;
  input.dispatchEvent(new Event('input', { bubbles: true }));

  // 时间范围
  if (startYear) { selects[14].value = startYear; selects[14].dispatchEvent(new Event('change', { bubbles: true })); }
  if (endYear) { selects[15].value = endYear; selects[15].dispatchEvent(new Event('change', { bubbles: true })); }

  // 作者
  if (author) {
    const auInput = document.querySelector('#au_1_value1');
    if (auInput) { auInput.value = author; auInput.dispatchEvent(new Event('input', { bubbles: true })); }
  }

  // 期刊
  if (journal) {
    const magInput = document.querySelector('#magazine_value1');
    if (magInput) { magInput.value = journal; magInput.dispatchEvent(new Event('input', { bubbles: true })); }
  }

  // 提交
  document.querySelector('div.search')?.click();

  // 等待结果
  await new Promise((r, j) => {
    let n = 0;
    const c = () => {
      if (document.body.innerText.includes('条结果')) r();
      else if (n++ > 40) j('timeout');
      else setTimeout(c, 500);
    };
    setTimeout(c, 2000);
  });

  return {
    query, fieldType, sourceTypes, startYear, endYear, author, journal,
    total: document.querySelector('.pagerTitleCell')?.innerText?.match(/([\d,]+)/)?.[1] || '0',
    page: document.querySelector('.countPageMark')?.innerText || '1/1',
    url: location.href
  };
}
```

---

## Phase 2: 详情提取

```javascript
// 导航到论文页（直接用 URL，不要点击链接）
navigate_page({ url: PAPER_URL })

// 提取详情
async () => {
  await new Promise((r, j) => {
    let n = 0;
    const c = () => { if (document.querySelector('.brief h1')) r(); else if (++n > 30) j('timeout'); else setTimeout(c, 500); };
    c();
  });

  const title = document.querySelector('.brief h1')?.innerText?.trim()?.replace(/\s*网络首发\s*$/, '') || '';
  const authors = Array.from(document.querySelectorAll('.author a') || []).map(a => a.innerText?.trim());
  const journal = document.querySelector('.source a')?.innerText?.trim() || '';
  const date = document.querySelector('.date')?.innerText?.trim() || '';
  const keywords = Array.from(document.querySelectorAll('.keyword a') || []).map(a => a.innerText?.trim());
  const abstract = document.querySelector('.abstract-text')?.innerText?.trim() || '';

  return { title, authors, journal, date, keywords, abstract, url: location.href };
}
```

---

## Phase 3: PDF/CAJ 下载

```javascript
// 在论文详情页下载
async () => {
  const format = "pdf"; // "pdf" 或 "caj"

  // 验证码检查
  const cap = document.querySelector('#tcaptcha_transform_dy');
  if (cap && cap.getBoundingClientRect().top >= 0) {
    return { error: 'captcha', message: '请在 Chrome 中完成验证码' };
  }

  // 检查下载链接
  const pdfLink = document.querySelector('#pdfDown') || document.querySelector('.btn-dlpdf a');
  const cajLink = document.querySelector('#cajDown') || document.querySelector('.btn-dlcaj a');

  // 检查登录状态
  const notLogged = document.querySelector('.downloadlink.icon-notlogged') || document.querySelector('[class*="notlogged"]');
  if (notLogged) {
    return { error: 'not_logged_in', message: '请先登录知网账号' };
  }

  const title = document.querySelector('.brief h1')?.innerText?.trim()?.replace(/\s*网络首发\s*$/, '') || '';

  if (format === 'pdf' && pdfLink) {
    pdfLink.click();
    return { status: 'downloading', format: 'PDF', title };
  } else if (format === 'caj' && cajLink) {
    cajLink.click();
    return { status: 'downloading', format: 'CAJ', title };
  } else if (pdfLink) {
    pdfLink.click();
    return { status: 'downloading', format: 'PDF', title };
  } else if (cajLink) {
    cajLink.click();
    return { status: 'downloading', format: 'CAJ', title };
  }

  return { error: 'no_download', message: '未找到下载链接' };
}
```

---

## 翻页（内部函数）

```javascript
// 下一页
async () => {
  const nextBtn = document.querySelector('.pager-next-cell a');
  if (nextBtn) {
    nextBtn.click();
    await new Promise(r => setTimeout(r, 2000));
    return { success: true, page: document.querySelector('.countPageMark')?.innerText };
  }
  return { success: false, message: '已是最后一页' };
}
```

---

## 验证码检测

检查 `#tcaptcha_transform_dy` 元素的 `getBoundingClientRect().top >= 0`。

腾讯验证码 SDK 预加载时 `top: -1000000px`（不可见），只有 `top >= 0` 时才是真正激活。

---

## 选择器速查

| 元素 | 选择器 |
|------|--------|
| 搜索输入框 | `input.search-input` |
| 搜索按钮 | `input.search-btn` |
| 结果行 | `.result-table-list tbody tr` |
| 标题链接 | `td.name a.fz14` |
| 作者 | `td.author a.KnowledgeNetLink` |
| 期刊 | `td.source a` |
| 日期 | `td.date` |
| 引用数 | `td.quote` |
| 下载量 | `td.download` |
| PDF 下载 | `#pdfDown` |
| CAJ 下载 | `#cajDown` |
| 来源类别 SCI | `#SCI` |
| 来源类别 EI | `#EI` |
| 来源类别 北大核心 | `#hx` |
| 来源类别 CSSCI | `#CSSCI` |

---

## 快速示例

\`\`\`
/cnki-research 深度学习                        # 基础搜索
/cnki-research SCI EI 深度学习 2020-2025       # 高级搜索（SCI/EI）
/cnki-research detail [URL]                    # 详情提取
/cnki-research download [URL]                  # 下载 PDF
\`\`\`
