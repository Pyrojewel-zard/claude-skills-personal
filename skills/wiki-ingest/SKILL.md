---
name: wiki-ingest
description: raw 证据入库 + typed 编译 + registry 更新。用于把论文/实验/工具/理论/日志素材转为可查询的 LLM Wiki 节点。
---

# wiki-ingest

## Role

`/wiki-ingest` 是底层编译引擎入口。对用户优先暴露 `/wiki-compile`，但底层仍执行同一套入库流程：

1. raw capture 校验
2. smart search 去重
3. typed node 编译
4. registry 更新
5. query_pack 刷新

禁止旧模式：
- 不直接复制 raw 正文到 `wiki/sources/`。
- 不手工维护长 `source_refs`。
- 不绕过 candidate 审核直接写入推断关系。

## Inputs

- `raw/` 下的文件或目录
- 新文本（先落地到 `raw/`）
- URL/PDF（先转为 raw 笔记）

## Pipeline

1. Classify
   - `paper | experiment | procedure | theory | project-log | worklog | candidate`
2. Retrieve
   - 在 `wiki/sources|entities|procedures|claims|topics|synthesis|queries|_registry|candidates/graphify` 做 smart search。
3. Fingerprint
   - 基于类型 + 关键词 + 目标对象生成去重 key。
4. Compile
   - 生成或更新 typed node：
     - `source` -> `wiki/sources/...`
     - `entity` -> `wiki/entities/...`
     - `procedure` -> `wiki/procedures/...`
     - `claim` -> `wiki/claims/{status}/...`
     - `synthesis` -> `wiki/synthesis/...`
5. Register
   - 更新：
     - `wiki/_registry/nodes.jsonl`
     - `wiki/_registry/edges.jsonl`
     - `wiki/_registry/fingerprints.jsonl`
     - `wiki/_registry/compile_log.jsonl`
6. Refresh
   - 刷新 `wiki/_registry/query_pack.md`。

## Rules

- Claim 必须可测试，且带 evidence edge。
- graphify 发现关系先入 `wiki/candidates/graphify/`，再经 `/wiki-refine` 或候选审核决定是否升格。
- 问题导向检索优先读 `query_pack` 和 accepted registry。
- 论文标准输入路径优先：`raw/pdfs/{paper_id}.pdf` + `raw/notes/papers/{paper_id}.md`。
- 稳定 ID 可以带冒号，但文件名和页面名不能带 Windows/Obsidian 非法字符：`* " \\ / < > : | ?`。
- 不要把 `entity:<slug>`、`procedure:<slug>`、`claim:<slug>` 直接当成文件名；文件名应使用 `kebab-case`。
- `entity:<slug>`、`procedure:<slug>`、`claim:<slug>`、`topic:<slug>` 等稳定 ID 只用于 frontmatter/registry，不直接作为正文双链目标。
- 禁止输出把 `entity:slug`、`procedure:slug`、`claim:slug`、`topic:slug` 直接塞进 Obsidian 双链目标位置的“typed-id 伪双链”。
- 目标页存在时使用合法双链；目标页不存在时使用反引号保留稳定 ID。
- 在 `提取的方法`、`提取的实体`、`提取的主张` 这类列表中，默认输出反引号包裹的稳定 ID，例如 ``procedure:pso-inverse-synthesis``、``entity:inverse-request``、``claim:pca-baseline-ceiling``。
- 只有目标页面已经真实存在时，才把这些列表项升级成合法双链。
- source frontmatter 中 `raw_ref` 使用 Obsidian 双链格式：`"[[raw/...]]"`；同时写 `raw_path: "raw/..."` 供脚本、fingerprint、registry 使用。
- registry JSONL 中的 `raw_ref`/`raw_refs` 保持纯路径，不写双链。
- 判断 raw 是否已处理时，只看 `wiki/_registry/fingerprints.jsonl`、`wiki/_registry/compile_log.jsonl` 和 `wiki/sources` 的 `raw_path + raw_sha256` 证据；不要依赖 raw 正文里的 `processed_date` 或手写标记。
- 状态模型固定为 `unprocessed/current/stale/partial/orphaned`。PDF、图片、Markdown、CSV 等 raw 文件都使用同一套哈希判定。
