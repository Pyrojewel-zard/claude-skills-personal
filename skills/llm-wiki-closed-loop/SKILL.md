---
name: llm-wiki-closed-loop
description: Use when capturing, compiling, refining, or deduplicating knowledge into the Obsidian LLM Wiki across paper, project, experiment, course, and conversation workflows.
---

# LLM Wiki Closed Loop

## 目标

把低密度材料稳定落到 `raw/`，把高密度材料编译成可读 wiki 页面，只在确有价值时再提炼 typed knowledge。

对用户暴露的心智模型固定为三入口：

`wiki-capture -> wiki-compile -> wiki-refine`

底层编译引擎仍然是 `/wiki-ingest`，候选审阅仍然是 `/wiki-crystallize`。

## 适用场景

- Claude Code / Codex 对话提炼
- 项目推进与阶段性总结
- Virtuoso 仿真记录与经验沉淀
- 论文阅读、PDF 入库与方法提炼
- 课程学习、讲义整理与概念归纳

## 统一流程

```
capture low-density material
-> compile stable material into readable page
-> optionally refine into typed nodes
-> optionally review candidates and relations
```

### 1. `/wiki-capture`

用于低密度、尚未稳定、先留痕再说的材料：

- 对话洞见
- 项目碎片
- 单次仿真观察
- 课程片段
- 临时论文线索

原则：

- 只落 `raw/`
- append-only
- 不直接写 accepted wiki
- 不默认创建 claim / procedure / entity

### 2. `/wiki-compile`

用于已经足够稳定、可以直接整理成完整可读页面的材料：

- 完整 session 汇总
- 项目阶段总结
- 完整仿真记录
- 论文 DOI / URL / PDF / Markdown
- 课程讲演录与章节总结

原则：

- 先做 Obsidian Smart Search 查重
- 再做 `duplicate / update / new` 判断
- 默认产出完整可读 wiki 页面
- typed 抽取是可选增强，不是强制目标

### 3. `/wiki-refine`

只在用户明确要求、且证据足够时使用：

- 从论文提炼方法、论断、概念
- 从仿真日志提炼稳定经验
- 从项目推进记录提炼可复用流程
- 从课程笔记提炼概念卡、学习指南

原则：

- 保守升格
- claim 必须具备 evidence
- procedure / entity 只在确实可复用时创建

## 查重与合并规则

编译前必须先执行 `search_vault_smart`，覆盖：

- `wiki/sources`
- `wiki/entities`
- `wiki/procedures`
- `wiki/claims`
- `wiki/topics`
- `wiki/synthesis`
- `wiki/queries`
- `wiki/_registry`

每次编译都要显式报告：

- 搜索关键词
- candidate hits
- dedupe decision：`duplicate` / `update` / `new`

是否合并到同一 project/source，不靠 Smart Search 单独决定，而是：

`smart search recall + typed fingerprint + LLM judgment`

## 底层闭环

1. Capture
   - 先写入 `raw/`。
2. Retrieve
   - Smart Search 查重，结合 registry / fingerprint 判断是否已有节点。
3. Compile
   - 通过 `/wiki-ingest` 生成或更新可读 source / synthesis / typed node。
4. Registry
   - 更新 `wiki/_registry/{nodes,edges,fingerprints,compile_log}`。
5. Refine
   - 仅在确有结构化价值时提炼 typed node。
6. Discover
   - 需要时再运行 `/wiki-graph --candidates` 发现潜在关系。
7. Review
   - 通过 `/wiki-crystallize --scan` 审核候选并决定是否升格。

## 论文专项流程（推荐）

1. 论文原文与笔记先落 `raw/pdfs/` + `raw/notes/papers/`。
2. 执行 `/wiki-compile raw/notes/papers/{paper_id}.md --intent "论文入库"`。
3. 若形成可验证论断或可复用流程，执行 `/wiki-refine raw/notes/papers/{paper_id}.md --intent "提炼论文方法与论断"`。
4. 若需挖掘潜在关联，执行 `/wiki-graph --candidates`，候选经审核再入 accepted edges。

## 关键约束

- 不直接复制 raw 正文到 `wiki/sources/` 当最终知识。
- 不手工维护长链接阵列，关系以 registry 为准。
- graphify 是发现层，不是事实层；必须 candidate-first。
- claim 必须具备 evidence edge。
- stable ID 可带冒号，但文件名和页面名不能带 `* " \\ / < > : | ?`。
- `entity:slug`、`procedure:slug`、`claim:slug`、`topic:slug` 只用于 frontmatter/registry，不直接作为正文双链目标。
- 禁止输出 `[[entity:...]]`、`[[procedure:...]]` 这类 typed-id 伪双链。
- 目标页存在时用合法双链；目标页不存在时用反引号保留 stable ID。
- raw 中已有 Obsidian 双链必须保留，尤其 `![[...]]` 图片引用不得改写为 `![](...)`。
- source 如果需要引用 raw 图片/附件，优先使用原始 Obsidian 双链格式。
