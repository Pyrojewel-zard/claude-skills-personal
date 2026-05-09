---
name: inspectional-reading
description: Use when guiding inspectional reading of a book or theory material and turning the result into raw notes, a compiled readable wiki page, and optionally refined concepts or claims.
user_invocable: true
---

# 检视阅读引导 (Inspectional Reading)

**核心使命**：通过多轮对话，引导用户完成《如何阅读一本书》中的检视阅读笔记。

**原则**：
- 分块引导，每完成一块再进入下一块
- 分类问题用选择题，描述问题用开放题
- 不催促，等待用户阅读和反馈

## 约束

### Markdown 语法

- 加粗用 `**bold**`（双星号）
- 标题层级从 `#` 开始，不跳级
- 代码块用 triple backticks

## 四阶段流程

### 阶段 1: 略读执行清单

引导用户确认是否完成以下检查：
- [ ] 看书名、副标题、作者
- [ ] 看目录结构
- [ ] 看出版信息（年份、版本）
- [ ] 看序言/前言/作者自述
- [ ] 快速翻阅全书，留意章节标题和图表

### 阶段 2: 结构笔记

引导用户记录：
- 这本书整体在谈什么（一句话概括）
- 书的架构（按目录分层次）
- 作者要解决的核心问题

### 阶段 3: 粗浅阅读

引导用户：
- 快速通读全书，不纠结细节
- 标记重要章节
- 记录初步感受

输出粗读卡到 `raw/notes/reading/{书名}-{YYYYMMDD}.md`

### 阶段 4: 阅读决策

引导用户判断：
- 这本书值得精读吗？（1-10 分）
- 如果精读，重点关注哪些章节？
- 哪些章节可以跳过？

### 阶段 5: 输出检视阅读笔记

最终输出到 `raw/notes/reading/{书名}-inspectional-{YYYYMMDD}.md`

```markdown
---
id: "inspectional-{书名简写}"
type: theory
created: YYYY-MM-DD
tags: [reading, inspectional]
topics: [{topic}]
raw_ref: "[[raw/notes/reading/{书名}-inspectional-{YYYYMMDD}.md]]"
raw_path: raw/notes/reading/{书名}-inspectional-{YYYYMMDD}.md
---

# {书名} — 检视阅读笔记

## 基本信息

| 字段 | 内容 |
|------|------|
| 书名 | {书名} |
| 作者 | {作者} |
| 年份 | {年份} |
| 版本 | {版本} |

## 一句话概括

{这本书在谈什么}

## 架构

{章节层次结构}

## 核心问题

{作者要解决的问题}

## 精读建议

- 推荐精读评分: {X}/10
- 重点关注: {章节}
- 可以跳过: {章节}
```

### 阶段 6: 入库（可选）

若该书与当前研究直接相关，执行：

```bash
/wiki-compile raw/notes/reading/{书名}-inspectional-{YYYYMMDD}.md --intent "检视阅读入库"
```

如果需要提炼方法、概念或明确可验证论断，再执行：

```bash
/wiki-refine raw/notes/reading/{书名}-inspectional-{YYYYMMDD}.md --intent "提炼阅读方法与论断"
```

先产出 raw，再用 `/wiki-compile` 进入编译流程。
若要提炼方法、论断或流程，再用 `/wiki-refine`。

## 与论文流程的边界

- 本 skill 面向“书籍/理论材料”的检视阅读。
- 如果输入是论文 PDF 或论文精读任务，优先使用 `marker-pdf` + `/wiki-compile`，需要时再补 `/wiki-refine`。
- 不在本 skill 内直接维护 `wiki/` 最终页面，统一通过 compile/refine 闭环。
- raw 文档里的 Obsidian 双链（尤其 `![[...]]` 图片引用）必须原样保留。
- 若 source 需要引用该 raw 的图片或附件，优先沿用 Obsidian 双链，不转换为 `![](...)`。
