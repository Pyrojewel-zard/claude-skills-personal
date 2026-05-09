---
name: wiki-refine
description: Use when the user explicitly wants to distill high-value knowledge from existing raw notes or wiki pages into conservative claim, procedure, or entity nodes.
user_invocable: true
---

# wiki-refine

运行 `/wiki-refine <path|node|topic> --intent "<一句话意图>"`。

## 目标

只在用户明确要求时，保守提炼 `claim / procedure / entity`。

这是三入口 flow 的可选第三步：

`wiki-capture -> wiki-compile -> wiki-refine`

## 默认适用

- 从论文粗读笔记提炼方法或论断
- 从仿真日志提炼稳定设置经验
- 从项目 / session 总结提炼可复用流程
- 从课程笔记提炼概念卡或学习指南

## 行为

1. 读取已有 raw 或 wiki 页面。
2. 判断是否值得升格。
3. 仅在证据充分时创建或更新 typed node。
4. 需要时使用 `/wiki-crystallize` 做候选审阅或提升。

## 规则

- 不是默认入口
- claim 必须有 evidence
- procedure / entity 只在确实可复用时创建
- stable ID 主要用于 frontmatter / registry，不直接作为正文双链目标
- 若目标页面不存在，优先保留反引号 stable ID，而不是输出非法伪双链

## 边界

- 不直接处理低密度碎片
- 不绕过 compile 直接大规模造 typed node
