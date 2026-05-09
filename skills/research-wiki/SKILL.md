---
name: research-wiki
description: Karpathy 风格 research wiki 闭环：capture -> compile readable page -> optional refine -> candidate review -> query。
argument-hint: [subcommand: init|ingest|query|update|lint|stats]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, mcp__obsidian-mcp-tools__search_vault_smart
---

# research-wiki

Subcommand: **$ARGUMENTS**

## Architecture

以 `raw` 为证据层，以 `wiki/_registry/*` 为关系事实层，以 typed nodes 为内容层。

核心节点：
- `source`
- `entity`
- `procedure`
- `claim`
- `topic`
- `synthesis`
- `graph_candidate`

## Subcommands

### `init`

创建或校验：
- `wiki/_registry/{nodes,edges,fingerprints,compile_log}.jsonl`
- `wiki/_registry/query_pack.md`
- typed 目录骨架

### `ingest <raw_path_or_dir>`

兼容旧术语。对用户优先暴露 `/wiki-compile`，底层仍可通过既有 `/wiki-ingest` 引擎执行。

要求：
- 先查重
- 后编译为完整可读页面
- 再注册
- smart search 目录使用：`wiki/sources, wiki/entities, wiki/procedures, wiki/claims, wiki/topics, wiki/synthesis, wiki/queries, wiki/_registry, wiki/candidates/graphify`

### `query "<question>"`

检索顺序：
1. `wiki/_registry/query_pack.md`
2. accepted registry edges + typed nodes
3. graphify candidate（标注为候选）
4. raw（仅在前 3 层不足时）

### `update <node_id> --field value`

更新节点后必须：
- 写 `compile_log`
- 刷新 `query_pack`
- 必要时将关系变更降级为 candidate 等待审核

### `lint`

检查：
- orphan node
- stale claim
- duplicate fingerprint
- edge without evidence
- candidate backlog
- raw status：`unprocessed/current/stale/partial/orphaned`

Raw status 只通过 registry/source 证据判断：
- `current`：`raw_path` 已注册，且 `raw_sha256` 等于当前文件哈希。
- `stale`：`raw_path` 已注册，但 `raw_sha256` 与当前文件哈希不同。
- `partial`：source、fingerprint、compile_log 证据不完整。
- `unprocessed`：没有任何 registry/source 证据。
- `orphaned`：registry/source 指向的 raw 文件不存在。

不要依赖 raw 正文里的 `processed_date` 或手写标记。

### `stats`

输出：
- typed node 数量
- accepted edge 数量
- candidate 数量
- claim 状态分布

## Graphify Integration

- graphify 是 discovery layer，不是 truth layer。
- 所有 `INFERRED` 关系必须先写 candidate，再由 `/wiki-refine` 或候选审核决定是否升格。
- 高置信路径可触发 digest/comparison 建议，但不能跳过审核。

## Non-Negotiables

- 不手工维护页面长链接阵列。
- 不把 page connections 当成事实来源。
- 事实关系只认 registry accepted edges。
- raw 处理状态只认 registry/source 的 `raw_path + raw_sha256`。
