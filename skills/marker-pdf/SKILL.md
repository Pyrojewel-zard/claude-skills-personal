---
name: marker-pdf
description: Use when the user provides a PDF path or asks to convert a paper PDF into Markdown before compiling it into the LLM Wiki; this covers marker-based PDF-to-Markdown conversion and raw paper note preparation.
---

# Marker PDF — PDF 转 Markdown

**核心能力**：将 PDF 快速转换为结构化 Markdown，保留公式、表格、代码块、图片引用。

**GitHub**: https://github.com/datalab-to/marker (33k+ stars)

---

## 环境

```bash
# Conda 环境
conda activate marker

# 验证安装
marker_single --help
```

**环境路径**: `/home/holmes/miniconda3/envs/marker/bin/marker_single`

---

## 用法

### 单文件转换

```bash
conda run -n marker marker_single /path/to/input.pdf --output_dir /path/to/output
```

### 批量转换

```bash
conda run -n marker marker /path/to/pdf_folder --output_dir /path/to/output
```

### 常用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--output_dir` | 输出目录 | - |
| `--output_format` | 输出格式: markdown/json | markdown |
| `--langs` | 语言代码 (如 zh,en) | 自动检测 |
| `--page_range` | 页码范围 (如 0-10) | 全部 |
| `--disable_image_extraction` | 不提取图片 | False |
| `--batch_multiplier` | 批处理倍数 (显存不足时调小) | 2 |

### 中文 PDF 转换

```bash
conda run -n marker marker_single input.pdf --output_dir ./output --langs zh
```

---

## 输出结构

转换后每个 PDF 生成一个文件夹，包含：

```
output/
├── {pdf_name}/
│   ├── {pdf_name}.md          # Markdown 正文
│   ├── images/                 # 提取的图片
│   └── {pdf_name}.json         # JSON 元数据
```

---

## 与 obsidian_wiki 集成

### PDF 论文解析流程

```
PDF 文件 → marker 转 Markdown → raw/pdfs/ + raw/notes/papers/
  → /wiki-compile 编译为完整可读的 wiki 页面
  → /wiki-refine（必要时）提炼 method/claim/procedure/entity
  → /wiki-graph --candidates（可选）发现潜在关系
```

先产出 raw，再用 `/wiki-compile` 进入编译流程。
若要提炼方法、论断或流程，再用 `/wiki-refine`。

### 论文入库标准路径（固定）

- PDF 原件：`raw/pdfs/{paper_id}.pdf`
- 转换正文：`raw/notes/papers/{paper_id}.md`
- 精读笔记：`raw/notes/papers/deep/{paper_id}-deep.md`（可选）

### 论文 raw 笔记最小 frontmatter

```yaml
---
id: paper:{paper_id}
type: paper
title: ""
authors: []
year: 0
venue: ""
doi: ""
source_pdf: raw/pdfs/{paper_id}.pdf
---
```

### 典型用法

1. **用户给 PDF 路径**:
   ```
   帮我解析这个 PDF: /path/to/paper.pdf
   ```
   → 运行 marker 转换 → 输出到 `raw/notes/papers/{paper_id}.md`
   → 提示执行 `/wiki-compile raw/notes/papers/{paper_id}.md --intent "论文入库"`
   → 如需提炼方法或结论，提示 `/wiki-refine raw/notes/papers/{paper_id}.md --intent "提炼论文方法与论断"`

2. **批量解析**:
   ```
   把这个文件夹下的 PDF 都转成 Markdown
   ```
   → 批量运行 marker → 输出到指定目录

3. **指定页码**:
   ```
   只转换第 1-5 页
   ```
   → 使用 `--page_range 0-4` 参数

---

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| CUDA 显存不足 | 加 `--batch_multiplier 1` |
| 中文识别差 | 加 `--langs zh` 强制中文 |
| 公式丢失 | 检查 PDF 是否有可提取的文本层 |
| 扫描版 PDF | 先用 OCR 工具（如 pdfocr）处理 |

## 与当前知识库的绑定约束

- 写入前先用 `search_vault_smart` 检索：`wiki/sources, wiki/entities, wiki/procedures, wiki/claims, wiki/topics, wiki/synthesis, wiki/queries, wiki/_registry`。
- 不直接把 marker 输出当最终 wiki 事实页。
- 关系事实只认 `wiki/_registry/edges.jsonl`，graphify 结果先入 candidate。
- 若后续 raw/source 中已有 Obsidian 双链（如 `![[...]]`），必须原样保留，不改写为 Markdown 图片语法。
- source 引用 raw 图片或附件时，优先用 Obsidian 双链（`![[...]]` / `[[...]]`）。
