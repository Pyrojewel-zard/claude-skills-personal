---
name: wiki-crystallize
description: |
  Use when reviewing candidates, graphify suggestions, or reusable summaries that may deserve promotion into accepted claim, procedure, entity, or synthesis nodes.
  Triggers on: "crystallize", "结晶", "提升", "promote", "candidate review", "审核候选".
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

## 执行步骤

### Step 1: 收集候选

| 来源 | 路径 |
|------|------|
| graphify 候选 | `wiki/candidates/graphify/` |
| raw 候选 | `raw/notes/candidates/` |
| 项目候选 | `raw/notes/projects/*/candidates/` |
| session 洞见 | 已编译 session / digest 中的 reusable insight |

### Step 2: 智能检索

**必须调用 `search_vault_smart` 检索 accepted wiki：**

```json
mcp__obsidian-mcp-tools__search_vault_smart({
  "query": "<候选关键词>",
  "filter": {
    "folders": ["wiki/sources", "wiki/entities", "wiki/concepts", "wiki/procedures", "wiki/claims", "wiki/topics"],
    "limit": 10
  }
})
```

### Step 3: 复用或计算 fingerprint

检查 `wiki/_registry/fingerprints.jsonl` 是否已有相同指纹。

### Step 4: 判断 promotion target

| 候选类型 | 目标路径 |
|----------|----------|
| 可测试论断 | `wiki/claims/{status}/` |
| 可复用流程/工具经验 | `wiki/procedures/` |
| 稳定概念/解释对象 | `wiki/entities/` |
| 跨材料综合 | `wiki/synthesis/` |
| 仅任务性记录 | archive，不升格 |

### Step 5: 创建或更新 accepted node

写入目标页面，添加标准 frontmatter。

### Step 6: 更新 Registry

- `wiki/_registry/edges.jsonl`
- `wiki/_registry/nodes.jsonl`
- `wiki/_registry/fingerprints.jsonl`

### Step 7: 写回 candidate 状态

更新 candidate 文件的 `review_status` 字段。

### Step 8: 刷新 query_pack

更新 `wiki/_registry/query_pack.md`。

### Step 9: 维护 hot/index/log

**必须执行**（任何 wiki 页面写入后）：

1. **hot.md** (`wiki/hot.md`)：更新前 500 字近期上下文，含本次 crystallize 摘要
2. **index.md** (`wiki/index.md`)：确认提升后的节点在对应 type 分区有入口
3. **log.md** (`wiki/log.md`)：prepend 操作记录

```
log.md prepend 模板：
**YYYY-MM-DDTHH:MM** | crystallize | {操作} | {节点ID} | {一句话说明}
```

---

## ⚠️ Crystallization Checkpoint（重要）

**在提升候选前，确认决策：**

```
Crystallization 审核决策：

| 候选 | 类型 | 决策 | 目标 |
|------|------|------|------|
| candidates/graphify/xxx.md | INFERRED 边 | promote | wiki/claims/supported/ |
| candidates/graphify/yyy.md | EXTRACTED 边 | reject | 证据不足 |

候选内容摘要：
- xxx: "LNA 噪声系数与增益呈负相关" (confidence: 0.92)
- yyy: "匹配网络影响稳定性" (confidence: 0.65)

确认提升决策？或调整？
```

**跳过检查点条件：**
- 单一候选且置信度高（>0.9）
- 用户已明确指定决策
- 批量审核模式（用户已批准批量策略）

---

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

## Obsidian 格式保留

### 双链引用

**必须保留的双链格式**：
- `[[页面名]]` — 标准双链
- `[[页面名|显示文本]]` — 带别名的双链

**禁止**：
- 输出 typed-id 伪双链（如 `[[entity:xxx]]`）
- 将双链转换为 Markdown 链接格式

### 图片处理

**必须保留的图片格式**：
- `![[image.png]]` — Obsidian 内部图片

**禁止**：
- 将 `![[image.png]]` 转换为 `<img>` 标签

## 边界

- 不是日常默认入口
- 不替代 `wiki-compile`
- 不对低密度碎片直接做升格

---

## Tools to Use

| Tool | Purpose | When | 完整路径 |
|------|---------|------|----------|
| `Read` | 读取候选文件 | Step 1 | `/mnt/c/obsidian_wiki/wiki/candidates/graphify/*.md` |
| `Write` | 创建 accepted node | Step 5 | `/mnt/c/obsidian_wiki/wiki/<type>/*.md` |
| `Edit` | 更新 candidate 状态 | Step 7 | `/mnt/c/obsidian_wiki/wiki/candidates/graphify/*.md` |
| `mcp__obsidian-mcp-tools__search_vault_smart` | 检索 accepted wiki | Step 2 | 见上方调用示例 |

### search_vault_smart 调用示例

```json
mcp__obsidian-mcp-tools__search_vault_smart({
  "query": "<候选关键词>",
  "filter": {
    "folders": ["wiki/sources", "wiki/entities", "wiki/concepts", "wiki/procedures", "wiki/claims", "wiki/topics"],
    "limit": 10
  }
})
```

**⚠️ 重要**：`filter` 必须是 JSON 对象，不能是字符串。

---

## 边界条件处理

| 情况 | 处理方式 |
|------|----------|
| 候选文件损坏 | 跳过，记录错误 |
| fingerprint 冲突 | 提示用户选择合并或拒绝 |
| 目标页面已存在 | 用 Edit 补充而非覆盖 |
| Registry 文件损坏 | 修复或重建 |
| 候选列表为空 | 报告"无待审核候选"，不执行后续 |
| 提升目标涉及不存在的节点 | 标记 `orphan` 暂搁 |
| 用户拒绝提升 | 标记 `rejected`，保留候选 |
| hot/index/log 更新失败 | 记录错误但不阻断主流程 |

---

## 相关 Skill

| Skill | 路径 | 用途 |
|-------|------|------|
| wiki-compile | `/home/holmes/.cc-switch/skills/wiki-compile/SKILL.md` | 稳定材料编译 |
| wiki-graph | `/mnt/c/obsidian_wiki/.claude/commands/wiki-graph.md` | graphify 运行 |
| wiki-digest | `/mnt/c/obsidian_wiki/.claude/commands/wiki-digest.md` | 主题综合 |
