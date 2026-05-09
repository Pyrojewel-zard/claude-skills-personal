---
name: wiki-compile
description: Use when raw notes or external material are stable enough to be compiled into a readable wiki page with deduplication, registry updates, and optional later refinement.
user_invocable: true
---

# wiki-compile

运行 `/wiki-compile <path|url|file> --intent "<一句话意图>"`。

## 目标

把稳定 raw 或外部材料编译成完整可读 wiki 页面。

这是三入口 flow 的主入口：

`wiki-capture -> wiki-compile -> wiki-refine`

## 默认适用

- 完整 session 汇总
- 项目阶段总结
- 完整仿真记录
- 论文 DOI / URL / PDF / Markdown
- 课程讲演录与章节总结

## 行为

1. 先做 `search_vault_smart` 查重。
2. 报告搜索关键词、candidate hits、dedupe decision：`duplicate` / `update` / `new`。
3. 识别 raw 落点或原始材料类型。
4. 调用既有 `/wiki-ingest` 编译流程。
5. 更新 registry / fingerprint / compile_log / query_pack。

## 规则

- 默认输出完整可读 wiki 页面
- typed 抽取是可选增强，不是强制目标
- 是否合并到已有 project/source，不靠 Smart Search 单独决定，而是 `smart search + fingerprint + LLM judgment`
- stable ID 可带冒号，但文件名和页面名不能带 `* " \\ / < > : | ?`
- 禁止输出 `[[entity:...]]`、`[[procedure:...]]` 这类 typed-id 伪双链
- 目标页存在时使用合法双链；目标页不存在时用反引号保留 stable ID

## 边界

- 不直接处理纯碎片输入
- 不把 marker 输出或 raw 正文直接当最终事实页
- 不默认升格 claim / procedure / entity
