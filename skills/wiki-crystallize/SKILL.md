---
name: wiki-crystallize
description: Use when reviewing candidates, graphify suggestions, or reusable summaries that may deserve promotion into accepted claim, procedure, entity, or synthesis nodes.
user_invocable: true
---

# wiki-crystallize

运行 `/wiki-crystallize [candidate|path|--scan]`。

## 目标

把 candidate 审核为 accepted knowledge，或明确拒绝 / 归档。

这是简化版 `llm_wiki` flow 里的可选审核层：

`wiki-capture -> wiki-compile -> wiki-refine -> wiki-crystallize`

其中前三步是主流程，`wiki-crystallize` 只在确有候选需要审阅时使用。

## 适用场景

- `wiki/candidates/graphify/` 下有待审核候选
- `raw/notes/candidates/` 或 project candidates 已沉淀出稳定知识
- 某个 summary / session insight 需要判断是否值得升格
- 需要把 candidate 明确标记为 accepted / rejected / archived

## 候选来源

- `wiki/candidates/graphify/`
- `raw/notes/candidates/`
- `raw/notes/projects/*/candidates/`
- 已编译 session / digest 里提炼出的 reusable insight

## 审核流程

1. 读取 candidate。
2. 用 `search_vault_smart` 检索 accepted wiki。
3. 复用或计算 fingerprint。
4. 判断 promotion target。
5. 创建或更新 accepted node。
6. 更新 `wiki/_registry/edges.jsonl`。
7. 写回 candidate `review_status`。
8. 刷新 `wiki/_registry/query_pack.md`。

## Promotion Targets

- 可测试论断 -> `wiki/claims/{status}/`
- 可复用流程 / 工具经验 -> `wiki/procedures/`
- 稳定概念 / 解释对象 -> `wiki/entities/`
- 跨材料综合 -> `wiki/synthesis/`
- 仅任务性记录 -> archive，不升格

## 规则

- candidate-first，不能把 graphify 推断直接当 accepted facts
- claim 必须具备 evidence
- `INFERRED` 候选默认更保守，通常只升格为较弱关系或 synthesis
- typed-id 不直接作为正文双链目标
- 审核结果至少要说明：candidate path、promotion decision、accepted node path、added edges 或 reject reason

## 边界

- 不是日常默认入口
- 不替代 `wiki-compile`
- 不对低密度碎片直接做升格
