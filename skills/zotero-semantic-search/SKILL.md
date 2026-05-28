---
name: zotero-semantic-search
description: "Zotero 论文检索入口——语义搜索或标题搜索 Zotero 库，返回 item key、content.md 路径（MarkerPDF 解析产物）、PDF 路径和图片列表。合并了原 zotero-find-pdf 的 PDF 路径查找功能。当用户说 '语义搜索'、'semantic search'、'Zotero 搜论文'、'找论文'、'content.md 路径'、'论文的 markdown 在哪'、'论文图片' 时触发。也适用于用户给出研究方向或关键词需要检索 Zotero 库的场景。"
---

# Zotero Semantic Search

Zotero 论文检索的统一入口。核心价值：搜索论文 → 拿到 item key → 直接拼出 content.md 路径和图片列表，下游 skill（ljg-paper 等）可以立刻读取带图的 markdown。

## 三种模式

根据用户输入自动选择模式，不需要用户显式指定。

### 模式一：语义搜索（研究方向 / 方法关键词）

用户给的是研究方向或方法描述，不是具体论文标题。

1. `mcp__zotero-mcp__semantic_status()` — 先检查语义搜索是否可用
   - 可用 → `mcp__zotero-mcp__semantic_search(query, limit=10)`
   - 不可用 → 回退到模式二（标题搜索），告知用户语义搜索不可用
2. 对每个结果进入「路径拼接」流程

### 模式二：标题搜索

用户给的是论文标题或标题片段。

1. `mcp__zotero-mcp__search_library(q, mode="preview")`
2. 对每个结果进入「路径拼接」流程

### 模式三：按 item key 直接查询

用户直接给了 Zotero item key（如 `ZDSWBUH7`）。

1. `mcp__zotero-mcp__get_item_details(key, mode="standard")`
2. 进入「路径拼接」流程

## 路径拼接

对每条搜索结果：

1. `mcp__zotero-mcp__get_item_details(key, mode="standard")` — 获取 attachments
2. 在 attachments 中找 `contentType="application/pdf"` 的条目
   - 如果有多个，取第一个
   - 如果没有 PDF attachment，PDF 列显示 "—"
3. 拿到 attachment 的 key 作为 attachmentKey
4. 拼接路径：

```
BASE = "/mnt/c/Users/28956/Zotero/storage"
pdf_path = BASE + "/" + attachmentKey + "/" + attachment.filename
md_path  = BASE + "/" + attachmentKey + "/content.md"
```

5. 对于 linkMode=1（linked file），用 `attachment.path` 做 Windows→WSL 路径转换：
   - `C:\Users\28956\Zotero\` → `/mnt/c/Users/28956/Zotero/`

6. 验证路径：
   ```bash
   ls {md_path}     # 检查 content.md 是否存在
   ls {BASE}/{attachmentKey}/*.(jpeg|png|jpg)  # 统计图片数量
   ```

7. 如果 content.md 不存在但有 PDF：
   - 告知用户"该论文 PDF 尚未解析为 Markdown"
   - 可调用 `/zotero-pdf-parse` 将 PDF 解析为 content.md + 图片
   - 解析完成后重新验证 md_path 和图片

## 输出格式

展示搜索结果让用户选择，不要自动取第一个。用表格：

```
| # | Title | Item Key | Attachment Key | PDF | MD | Images |
|---|-------|----------|----------------|-----|----|--------|
| 1 | 论文标题1 | ABC12345 | DEF67890 | ✅ | ✅ | 12 |
| 2 | 论文标题2 | GHI11223 | JKL44556 | ✅ | — | 0 |
```

列说明：
- **PDF**: ✅ 表示 PDF 文件存在，— 表示无 PDF
- **MD**: ✅ 表示 content.md 存在（MarkerPDF 已解析），— 表示未解析
- **Images**: 数字表示目录下 jpeg/png/jpg 文件数量

输出表格后，附上关键路径供下游使用：

```
论文1 路径：
  MD: /mnt/c/.../DEF67890/content.md
  Images: /mnt/c/.../DEF67890/
```

## 注意事项

- 如果语义搜索不可用（`semantic_status` 返回未就绪），自动回退到标题搜索并告知用户
- 多条结果时让用户选择，不要自作主张取第一个
- 如果用户给了 Zotero 链接（zotero://select/...），从中提取 item key 走模式三
- content.md 是 MarkerPDF 解析产物，同目录下的 jpeg 图片是论文中的图表，markdown 中用 `![](xxx.jpeg)` 相对路径引用