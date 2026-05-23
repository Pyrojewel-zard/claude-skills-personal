---
name: wiki-compile
description: |
  Two-phase ingest: Phase 1 reads raw, deduplicates, writes source page, produces compile-plan manifest;
  Phase 2 creates/updates entity/concept/procedure/claim pages and maintains hot.md/index.md/log.md.
  Triggers on: "compile", "编译", "入库", "ingest", "process raw", "处理raw", "convert to wiki".
user_invocable: true
---

# wiki-compile (两阶段 Ingest)

运行 `/wiki-compile <path|url|file> --intent "<一句话意图>"`。

## 目标

将稳定 raw 或外部材料编译为完整 wiki 知识网络：1 个 source 页 + N 个 entity/concept/procedure/claim 页，并维护 hot.md/index.md/log.md。

## 两阶段架构

```
Phase 1: raw → 分析 → source 页面 → compile-plan 清单
Phase 2: compile-plan → 逐项创建/更新 entity/concept/procedure/claim → 维护 hot/index/log
```

Phase 1 和 Phase 2 可在同一 agent 会话内顺序执行。当材料特别复杂（>5 个提取项）时，Phase 2 应逐项处理避免上下文溢出。

---

## Phase 1: 分析 + Source 页面 + Compile-Plan

### Step 1: 识别输入类型

| 输入类型 | 处理方式 |
|----------|----------|
| `raw/` 文件 | 直接读取并编译 |
| URL / DOI | 获取内容后编译 |
| PDF / Markdown | 转换后编译 |
| 目录 | 逐文件处理 |

### Step 2: 智能搜索去重

**必须调用 `search_vault_smart`：**

```json
mcp__obsidian-mcp-tools__search_vault_smart({
  "query": "<核心标题/关键词>",
  "filter": {
    "folders": ["wiki/sources", "wiki/entities", "wiki/concepts", "wiki/procedures", "wiki/claims", "wiki/topics"],
    "limit": 10
  }
})
```

### Step 3: 判断去重决策

| 决策 | 条件 | 行为 |
|------|------|------|
| `duplicate` | fingerprint 相同或标题完全匹配 | 更新现有节点 |
| `update` | 高度相似（>70% 关键词重叠） | 补充新内容 |
| `new` | 无匹配或部分相似（<30%） | 创建新页面 |

### Step 4: 写 Source 页面

写入 `wiki/sources/<route>/<slug>/<slug>.md`，包含完整 frontmatter：

```yaml
id: source:<slug>
type: source
source_kind: paper|experiment|tool-note|course-note|project-log|worklog|external-article
raw_ref: "[[raw/...]]"
raw_path: raw/...
raw_sha256: "<sha256>"
compiled_at: YYYY-MM-DDTHH:MM:SS
compiler_version: llm-wiki-v2-two-phase
fingerprint: "<typed fingerprint>"
stale: false
```

Source 页面正文规则：
- 中文为主，技术术语保留英文
- 长度约束 100-300 行；超过则拆分为多个 source
- 引用已存在的 entity/concept 用 `[[页面名]]`，不存在的用反引号
- 标注矛盾和空白用 Obsidian callout：

```markdown
> [!contradiction] 标题
> 描述矛盾内容和来源

> [!gap] 标题
> 描述缺失信息和需要补充的方向
```

### Step 5: 产出 Compile-Plan 清单

Phase 1 最后产出 YAML 格式的 compile-plan，作为 Phase 2 的交接件：

```yaml
compile_plan:
  source_id: "source:<slug>"
  source_path: "wiki/sources/<route>/<slug>/<slug>.md"

  extractions:
    - type: entity          # entity | concept | procedure | claim
      action: create        # create | update | merge
      slug: vector-fitting
      name: Vector Fitting
      reason: "核心参数化方法，多篇论文引用"
      entity_type: method   # method | tool | device | material | metric

    - type: concept
      action: create
      slug: transfer-function-parameterization
      name: 传递函数参数化
      reason: "从 neuro-tf 和 vector-fitting 抽象的共同思想"

    - type: claim
      action: create
      slug: cross-process-modeling-gap
      name: 跨工艺建模是无人区
      claim_type: insight   # insight | decision | constraint
      evidence_type: gap    # experimental | constraint | precedent | gap
      reason: "所有综述均未涉及跨工艺泛化"

  contradictions:
    - description: "论文 A 的 X 结论与论文 B 的 Y 结论矛盾"
      sources: ["source:a", "source:b"]

  gaps:
    - description: "缺少 Z 方向的验证数据"
      related_entities: ["entity:xxx"]

  maintenance:
    hot_update: true
    index_update: true
    log_entry: "compile | <slug> | 新增 N entity, M concept, K claim"
```

**Compile Checkpoint**：产出 compile-plan 后，如果提取项 >5 或有 contradictions，暂停向用户确认决策后再进入 Phase 2。

---

## Phase 2: 逐项提取 + 维护持久层

### Step 6: 按 compile-plan 逐项创建/更新页面

对 compile-plan 中每个 extraction 项：

**Entity 页面** (`wiki/entities/<slug>.md`)：
```yaml
id: entity:<slug>
type: entity
entity_type: method|tool|device|material|metric
created_at: YYYY-MM-DD
sources: ["source:xxx"]
```
- 正文描述该实体的定义、核心特征、使用场景
- 与其他 entity/concept 的 `[[双链]]`
- 长度 100-300 行

**Concept 页面** (`wiki/concepts/<slug>.md`)：
```yaml
id: concept:<slug>
type: concept
created_at: YYYY-MM-DD
sources: ["source:xxx", "source:yyy"]
entities: ["entity:aaa", "entity:bbb"]
```
- 正文描述抽象思想、从哪些 entity 提炼、适用范围
- 长度 50-200 行

**entity vs concept 判定规则**：
- 有具体出处可引用（论文、工具、器件）= entity
- 从多个 entity 抽象出的思想/模式 = concept

**Procedure 页面** (`wiki/procedures/<slug>.md`)：
```yaml
id: procedure:<slug>
type: procedure
created_at: YYYY-MM-DD
sources: ["source:xxx"]
```
- 正文包含可复用的工程步骤

**Claim 页面** (`wiki/claims/<slug>.md`)：
```yaml
id: claim:<slug>
type: claim
claim_type: insight|decision|constraint
evidence_type: experimental|constraint|precedent|gap
created_at: YYYY-MM-DD
sources: ["source:xxx"]
```
- claim_type:decision 用于工程决策，evidence 回答"为什么不选替代方案"
- 正文包含主张、证据、反驳风险

**去重检查**：每个 extraction 执行前，必须 `search_vault_smart` 搜索是否已存在同类页面。已存在则 action 改为 update。

### Step 7: 更新 Registry

更新：
- `wiki/_registry/nodes.jsonl` — 所有新/更新节点
- `wiki/_registry/edges.jsonl` — source→entity/concept/claim 关系
- `wiki/_registry/fingerprints.jsonl` — 去重指纹
- `wiki/_registry/compile_log.jsonl` — 编译日志
- `wiki/_registry/query_pack.md` — 查询上下文

### Step 8: 维护 hot.md / index.md / log.md

**任何 skill 写入 wiki 页面后，必须同步更新以下三个文件。**

**hot.md** (`wiki/hot.md`)：
- 更新 `updated` 时间戳
- 更新 "Key Recent Facts" 和 "Recent Changes"
- 更新 "Active Threads"
- 总长度 < 500 字

**index.md** (`wiki/index.md`)：
- 在对应 type 分区添加新条目
- 格式：`- [[slug]] — 一句话描述`
- 更新 `updated` 日期

**log.md** (`wiki/log.md`)：
- prepend 新条目（新条目在顶部）
- 格式：`## [YYYY-MM-DD] compile | <slug>`
- 列出本次创建/更新的所有页面

---

## ⚠️ Compile Checkpoint

**在 Phase 1 → Phase 2 之间，如果满足以下任一条件，暂停确认：**

- 提取项 > 5
- 存在 contradictions
- 去重决策不明确（update vs merge）
- 用户未指定完整路径且目标不唯一

**跳过检查点条件：**
- 单一明确目标，提取项 ≤ 3
- 无相似页面
- 用户已指定完整路径

---

## 规则

- Source 页面必须完整可读，不退化成 raw 副本或纯 bullet 摘要
- 每个编译页面可追溯、可重建、可审计
- typed 抽取是 Phase 2 的核心目标，不是可选增强
- stable ID 只用于 frontmatter/registry，文件名用 kebab-case
- 禁止 `[[entity:...]]` typed-id 伪双链
- 目标页存在用 `[[页面名]]`，不存在用反引号
- Page 长度约束 100-300 行，超过则拆分
- 必须维护 hot.md / index.md / log.md

## Obsidian 格式保留

- `[[页面名]]` 标准双链，`[[页面名|显示文本]]` 带别名
- `![[image.png]]` 内部图片
- 禁止转换为 `[text](url)` 或 `<img>` 格式
- `> [!contradiction]` 和 `> [!gap]` callout 标注矛盾和空白

## 边界

- 不直接处理纯碎片输入（用 wiki-capture）
- 不把 raw 正文直接当最终事实页
- Phase 2 不创建 topic/synthesis/query（这些由专门 skill 处理）

---

## Tools to Use

| Tool | Purpose | When |
|------|---------|------|
| `Read` | 读取 raw 文件 | Phase 1 Step 1 |
| `Write` | 创建 wiki 页面 | Phase 1 Step 4, Phase 2 Step 6 |
| `Edit` | 更新现有 wiki 页面 | Phase 2 Step 6 |
| `mcp__obsidian-mcp-tools__search_vault_smart` | 智能搜索去重 | Phase 1 Step 2, Phase 2 Step 6 |
| `mcp__obsidian-mcp-tools__create_vault_file` | 创建新 vault 文件 | Phase 2 Step 6, 8 |
| `mcp__obsidian-mcp-tools__patch_vault_file` | 增量编辑 | Phase 2 Step 8 |

### search_vault_smart 调用规范

`filter` 必须是 JSON 对象，不能是字符串。

---

## 相关 Skill

| Skill | 用途 |
|-------|------|
| wiki-capture | 低密度捕获 → raw |
| wiki-refine | 高价值提炼 → claim/procedure/entity（用户明确要求时） |
| wiki-crystallize | candidate 审核与提升 |
| wiki-lint | 健康检查（含 hot/index/log） |
| wiki-query | hot → index → pages 三步查询 |
