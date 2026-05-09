---
name: code-inventory
description: Use when inventorying a code repository into the LLM Wiki so it becomes a raw project card, a compiled readable page, and optionally a refined reusable tool or procedure note.
---

# Code Inventory

## 目标

把“代码仓库”作为研究对象纳入知识库，输出可检索、可升格的结构化知识，而不是把源码全文搬进 wiki。

## 触发场景

- 新工具仓库需要登记
- 需要避免重复造轮子
- 需要把工具能力映射到实验流程/理论实体

## 工作流

1. 查重
   - 先用 `search_vault_smart` 检索 `wiki/sources|entities|procedures|claims|topics|synthesis|queries|_registry`。
   - 报告搜索关键词、candidate hits、dedupe decision：`duplicate` / `update` / `new`。
2. 提取元信息
   - 项目名、路径、语言栈、入口脚本、主要用途、适用场景、限制条件。
3. 写入 raw 项目卡
   - `raw/notes/projects/{slug}/{slug}-codebase-card.md`
4. 执行 `/wiki-compile raw/notes/projects/{slug}/{slug}-codebase-card.md --intent "项目代码盘点入库"`
5. 如形成可复用操作链，再执行 `/wiki-refine raw/notes/projects/{slug}/{slug}-codebase-card.md --intent "提炼工具能力与流程"`
6. 需要时通过 `/wiki-crystallize` 审阅候选并升格为：
   - `wiki/entities/tools/...`
   - `wiki/procedures/...`

## raw 项目卡模板

```markdown
---
id: repo-{slug}
type: project-log
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [code, tooling]
topics: []
raw_ref: "[[raw/notes/projects/{slug}/{slug}-codebase-card.md]]"
raw_path: raw/notes/projects/{slug}/{slug}-codebase-card.md
---

# {项目名称}

## 基本信息

- 路径: `{absolute_or_repo_path}`
- 语言: {python|matlab|skill|mixed}
- 入口: `{main file}`
- 目标问题: {一句话}

## 可复用能力

- 能力 1
- 能力 2

## 限制与风险

- 限制 1
- 限制 2
```

## 规则

- 不在技能中直接创建最终 `entity/procedure` 页面，统一经 `wiki-compile` / `wiki-refine` / `wiki-crystallize`。
- 不使用手工 `source_refs` 维护关系。
- 关系以 registry 为准。
- raw 中已有 Obsidian 双链必须保留，特别是 `![[...]]` 图片引用。
- source 引用 raw 图片/附件时优先使用 Obsidian 双链，禁止改写为本地 `![](...)`。
