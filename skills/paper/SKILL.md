---
name: paper
description: "统一论文阅读入口。粗读+精读+Zotero collection 管理+认知碰撞。用法：/paper \"title\" [--deep] [--force]"
user_invocable: true
---

# Unified Paper Workflow

统一论文阅读入口，整合粗读、精读、Zotero collection 管理和认知碰撞功能。

## 命令

```
/paper "title|keyword|DOI" [--deep] [--force]
```

| 参数 | 说明 |
|------|------|
| `title|keyword|DOI` | 论文标题、关键词或 DOI |
| `--deep` | 强制执行 Stage 1 + Stage 2 |
| `--force` | 强制重新生成 raw 笔记（覆盖幂等性检查） |

---

## 两阶段流程

```
/paper "title|keyword|DOI" [--deep] [--force]
  │
  ├──▶ Stage 0: 同步验证（自动执行）
  │      ├── 读取 wiki/_registry/zotero-collections.md 获取文档记录的 collection 结构
  │      ├── 调用 CLI list-collections 获取 Zotero 实际 collection 树
  │      ├── 对比两者，检测不一致
  │      └── 若不一致：提示用户并询问是否同步更新文档
  │
  ├──▶ Stage 1: Discovery
  │      ├── Zotero 语义检索 → 多结果消歧 → 确认唯一论文
  │      ├── 添加 _Reading 标签
  │      ├── 快速认知评估（delta 检测）
  │      ├── 生成 raw 笔记（raw/notes/papers/{paper_id}.md）
  │      ├── /wiki-compile raw/notes/papers/{paper_id}.md --intent "论文入库"
  │      ├── 添加 wiki-ingest-pending 标签
  │      ├── wiki-compile 成功后 → wiki-ingest-pending → wiki-ingested
  │      ├── Zotero collection 建议（L2 映射）
  │      ├── 精读评分
  │      ├── 移除 _Reading，添加 _Read
  │      └── 评分 ≥ 7 时提示 Stage 2
  │
  └──▶ Stage 2: Deep（用户确认后触发）
         ├── 读取 Stage 1 产物（复用，不重复生成）
         ├── 深度方法提取 → procedure 候选
         ├── 对抗阅读 → 认知碰撞卡片（ASCII art）
         ├── Claim 验证 → evidence 边
         ├── 写入 raw/notes/papers/deep/{paper_id}-deep.md
         ├── /wiki-compile raw/notes/papers/deep/{paper_id}-deep.md --intent "论文精读入库"
         └── /wiki-refine raw/notes/papers/deep/{paper_id}-deep.md --intent "提炼论文方法与论断"
```

---

## Stage 0: 同步验证

**目的：** 确保 `wiki/_registry/zotero-collections.md` 与 Zotero 实际 collection 保持同步。

**执行时机：** 每次 `/paper` 调用时自动执行（静默，仅在检测到不一致时提示）。

**验证逻辑：**

1. 读取 `wiki/_registry/zotero-collections.md`，解析"当前 Collection 结构"表格，提取所有 collection path
2. 调用 `python3 zotero_manager.py list-collections`，获取 Zotero 实际 collection 树
3. 对比两者：
   - **文档有但 Zotero 无** → 标记为"Zotero 中已删除"
   - **Zotero 有但文档无** → 标记为"新增 collection"
   - **两者都有但状态不一致** → 标记为"状态冲突"

**不一致时的用户提示：**

```
⚠️ 检测到 Zotero Collection 与文档不同步：

新增（Zotero 有，文档无）：
  - Papers/AI-for-IC-Design/inverse-design/

已删除（文档有，Zotero 无）：
  - Papers/EDA-Tools/virtuoso/

是否同步更新 wiki/_registry/zotero-collections.md？
  - `y` — 自动同步（添加新增，移除已删除）
  - `n` — 跳过同步，继续执行
  - `view` — 查看详细差异后决定
```

**自动同步操作：**

- 新增 collection：在文档表格中添加条目，状态标记为 🟢 active
- 已删除 collection：将状态改为 🔴 deprecated 或移除条目
- 更新文档的 `updated` 字段为当前日期

---

## paper_id 生成规则

| 优先级 | 来源 | 格式 |
|--------|------|------|
| 1 | DOI | `doi-<doi-kebab>`（去掉斜杠和特殊字符） |
| 2 | arXiv ID | `arxiv-<id>` |
| 3 | 标题 | `<year>-<first-author>-<title-kebab>` |
| 4 | Zotero key | `zotero-<key>` |

去重：同一篇论文无论通过哪个入口检索，最终都使用同一 paper_id。

---

## 幂等性约束

**Stage 1 执行前：**
- 检查 `raw/notes/papers/{paper_id}.md` 是否已存在
- 若存在且无 `--force`：复用已有 raw 笔记，跳过重写，直接进入 collection 建议 + 评分
- 若不存在或有 `--force`：重新执行完整 Stage 1

**Stage 2 执行前：**
- 检查 `raw/notes/papers/deep/{paper_id}-deep.md` 是否已存在
- 若存在且无 `--force`：复用已有精读笔记，提示用户追加或跳过
- 若不存在：执行完整 Stage 2

---

## 多结果消歧策略

**返回 0 条：**
1. 提示用户当前关键词无匹配
2. 自动 fallback 到 Zotero MCP `search_library` 关键词搜索
3. 若仍无结果，中止并建议用户检查关键词或手动导入论文到 Zotero

**返回 1 条：**
- 自动确认，直接进入 delta 检测

**返回多篇（≥2）：**
1. 列出前 5 条（标题 + 年份 + 第一作者 + 期刊/会议）
2. 让用户选择：输入编号 1-5，或输入 `more` 查看后续
3. 若用户输入非数字且非 `more`，视为放弃本次检索
4. 仅确认唯一论文后才进入 delta 检测

---

## Delta 检测定义

将论文核心主张/方法与 wiki 中已有同类节点（`wiki/entities/`、`wiki/claims/`、`wiki/procedures/`）做语义对比，判断是否存在认知增量。

| Delta 等级 | 标准 | 行为 |
|-----------|------|------|
| delta = 0 | 论文方法/结论与 wiki 已有节点高度重叠 | 如实标注"无显著碰撞"，不强制生成认知卡片 |
| delta > 0 | 论文提出新方法、新指标、新实验范式，或修正已有 claim | 生成认知卡片，标记相关 wiki 节点为可能需要更新 |
| delta < 0（反驳） | 论文结论与已有 claim 矛盾 | 生成张力型认知卡片，标记 claim 状态可能需要调整 |

---

## 精读评分机制

Stage 1 末尾由 LLM 自动评分，依据粗读笔记内容判定。

**评分维度（每项 0-10，加权平均）：**

| 维度 | 权重 | 评分要点 |
|------|------|---------|
| 研究相关度 | 40% | 与当前 wiki research-direction 的重合程度 |
| 方法论价值 | 30% | 技术/方法是否可迁移、可复用 |
| 写作质量 | 15% | 逻辑清晰度、实验完整性 |
| 复现价值 | 15% | 是否有代码/数据公开 |

**触发逻辑：**

| 总分 | 行为 |
|------|------|
| ≥ 8 | 强烈推荐精读，提示进入 Stage 2，添加 `_Important` |
| 7-7.9 | 推荐精读，提示是否进入 Stage 2 |
| 5-6.9 | 可选精读，添加 `_To-Read`，不主动提示 |
| < 5 | 不精读，添加 `_Read`，结束 |

---

## Zotero Collection 管理

### Collection 标准文档

**维护位置：** `/mnt/c/obsidian_wiki/wiki/_registry/zotero-collections.md`

此文档定义：
- Collection 命名规范
- 当前 Collection 结构（含状态标记）
- Wiki 映射规则
- 创建/删除流程
- 标签体系

**读取时机：** Stage 1 粗读完成后，读取此文档获取当前 collection 结构用于建议。

### Collection 层级规范（L2 映射）

| Zotero | Wiki |
|--------|------|
| `Papers/RF-IC-Design/lna-design/` | `wiki/sources/papers/rf-ic-design/lna-design/` |
| `Papers/AI-for-IC-Design/gds-generator/` | `wiki/sources/papers/ai-for-ic-design/gds-generator/` |

映射规则：Zotero collection path 去掉 `Papers/` 前缀，转小写，统一为 kebab-case。

跨方向论文允许同时放入多个 collection。

### 多级 Collection 创建规则

**⚠️ 重要：Zotero 不支持用路径字符串一次性创建多级 collection，必须逐级创建。**

例如要创建 `逆向综合网络/Inverse-Synthesis-Network/代理优化-Surrogate-Optimization`：

```bash
# 错误方式（不会创建父级，只会创建一个带斜杠名字的单层 collection）
python3 zotero_manager.py create-collection "逆向综合网络/Inverse-Synthesis-Network/代理优化-Surrogate-Optimization"

# 正确方式（逐级创建）
# Step 1: 创建 L1 父级
python3 zotero_manager.py create-collection "逆向综合网络"

# Step 2: 创建 L2 子级（使用 --parent 指定父级名称或 key）
python3 zotero_manager.py create-collection "Inverse-Synthesis-Network" --parent "逆向综合网络"

# Step 3: 创建 L3 子级
python3 zotero_manager.py create-collection "代理优化-Surrogate-Optimization" --parent "Inverse-Synthesis-Network"
```

**命名规范：**
- 支持中英文混合命名，如 `逆向综合网络`、`Inverse-Synthesis-Network`
- 每级命名使用 kebab-case 或明确术语
- 建议格式：`中文名-English-Name` 或纯英文 `english-name`

**创建流程：**
1. 解析目标路径，按 `/` 分割为多级
2. 从 L1 开始，逐级检查是否已存在
3. 若不存在则创建，并记录返回的 key
4. 使用上一级的 key 或名称作为 `--parent` 参数创建下一级
5. 重复直到所有层级创建完成

### Collection 建议逻辑

粗读完成后：

1. 读取当前 Zotero collection 树（CLI `list-collections`）
2. 读取 wiki `papers/` 目录树
3. 根据论文标题/摘要 + 已有的 wiki research-direction 推断最匹配的 L2
4. 推荐 1-3 个候选 collection，标注理由
5. 用户操作：
   - `y` / `yes` — 放入推荐的主 collection
   - `all` — 放入所有推荐（跨方向）
   - `1,2` — 手动选择编号
   - `new:rf-circuit-design` — 新建 collection 并放入
   - `skip` — 不操作

### 新建 Collection 自动联动

用户选择 `new:<name>` 时：

1. 创建 Zotero collection（CLI `create-collection`）
2. 创建对应 wiki 目录 `wiki/sources/papers/<l2-name>/`
3. 更新 `wiki/_registry/zotero-collections.md` 中的"当前 Collection 结构"表

---

## 系统 Collection 自动维护

| 事件 | 自动操作 |
|------|---------|
| 开始阅读 | 添加 `_Reading` |
| 标记完成粗读 | 移除 `_Reading`，添加 `_Read` |
| 评分 ≥ 8 | 添加 `_Important` |
| 评分 5-6.9 | 添加 `_To-Read` |
| 用户接受 Stage 2 提示 | 移除 `_To-Read`（如有），进入 Stage 2 |
| 缺少 PDF | 添加 `_No-PDF` |
| 计划精读（`--deep` 或接受提示） | 添加 `_Reading`（Stage 2 期间） |

---

## 标签生命周期

| 时机 | 操作 |
|------|------|
| Stage 1 开始（确认唯一论文后） | 添加 `wiki-ingest-pending` |
| Stage 1 完成（/wiki-compile 成功后） | `wiki-ingest-pending` → `wiki-ingested` |
| Stage 2 完成（/wiki-refine 成功后） | 保留 `wiki-ingested`，可选添加 `deep-read` |

---

## 接口选择（MCP vs CLI）

| 操作 | 接口 | 说明 |
|------|------|------|
| 语义检索论文 | Zotero MCP `semantic_search` | 获取论文列表 |
| 获取论文详情/内容 | Zotero MCP `get_content` / `get_item_details` | 获取元数据和 PDF |
| 列出 collection 树 | Zotero Manager CLI `list-collections` | 本地脚本 |
| 创建/删除 collection | Zotero Manager CLI `create-collection` / `delete-collection` | 本地脚本 |
| 添加论文到 collection | Zotero Manager CLI `add-to-collection` | 本地脚本 |
| 更新论文标签 | Zotero Manager CLI `add-tag` / `remove-tag` | 本地脚本 |

---

## Zotero Manager CLI 调用指南

**CLI 路径：** `~/.claude/skills/zotero-manager/zotero_manager.py`

### Stage 1 流程中的 CLI 调用

**1. 列出当前 collection 树（用于建议）：**

```bash
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py list-collections
```

**2. 添加论文到 collection：**

```bash
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-to-collection "collection-name" <ITEM_KEY>
```

- `collection-name` 支持 collection 名称或 key，自动识别
- 跨方向论文可多次调用，添加到多个 collection

**3. 新建 collection：**

```bash
# 创建 L1 领域
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py create-collection "Papers/RF-IC-Design"

# 创建 L2 方向（带父级）
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py create-collection "lna-design" --parent "Papers/RF-IC-Design"
```

**4. 标签管理：**

```bash
# 添加标签
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag <ITEM_KEY> "_Reading"

# 移除标签
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py remove-tag <ITEM_KEY> "_Reading"

# 常用系统标签
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag <ITEM_KEY> "_Read"
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag <ITEM_KEY> "_Important"
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag <ITEM_KEY> "_To-Read"
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag <ITEM_KEY> "wiki-ingest-pending"
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag <ITEM_KEY> "wiki-ingested"
```

**5. 搜索文献（fallback）：**

```bash
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py search "keyword" -n 20
```

**6. 获取文献详情：**

```bash
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py item-detail <ITEM_KEY>
```

### 完整 Stage 1 CLI 调用序列示例

```bash
# 1. 获取 collection 树（用于建议）
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py list-collections

# 2. 添加 _Reading 标签（开始阅读）
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag ABCDEFGH "_Reading"

# 3. 添加 wiki-ingest-pending 标签
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag ABCDEFGH "wiki-ingest-pending"

# 4. 添加论文到 collection（用户确认后）
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-to-collection "lna-design" ABCDEFGH

# 5. 更新标签状态（完成粗读）
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py remove-tag ABCDEFGH "_Reading"
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag ABCDEFGH "_Read"
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py remove-tag ABCDEFGH "wiki-ingest-pending"
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag ABCDEFGH "wiki-ingested"

# 6. 评分 ≥ 8 时添加 _Important
cd ~/.claude/skills/zotero-manager && python3 zotero_manager.py add-tag ABCDEFGH "_Important"
```

---

## Stage 2 数据流

Stage 2 的所有分析产物统一写入 `raw/notes/papers/deep/{paper_id}-deep.md`（frontmatter: `type: deep-read`）。

文件结构：
```
# 深度方法提取
...
# 对抗阅读 — 认知碰撞卡片
...
# Claim 验证
...
```

`/wiki-compile` 先把此文件编译为完整可读页面；如需要稳定抽象，再由 `/wiki-refine` 提炼：
- `procedure` 节点（来自深度方法提取）
- `synthesis` 节点（来自认知碰撞卡片）
- `claim` 节点及 evidence 边（来自 claim 验证）

---

## 输出规范

| 产物 | 路径 |
|------|------|
| Stage 1 粗读笔记 | `raw/notes/papers/{paper_id}.md` |
| Stage 2 精读笔记 | `raw/notes/papers/deep/{paper_id}-deep.md` |
| wiki 已入库 | 由 `/wiki-compile` 生成/更新 |
| Zotero 标签 | `wiki-ingest-pending` / `wiki-ingested` |

---

## 依赖

- Zotero MCP 服务器
- Zotero Manager CLI（`~/.claude/skills/zotero-manager/zotero_manager.py`）
- `/wiki-compile` 与 `/wiki-refine`
- wiki `papers/` 目录结构

---

## 被替换的旧 Skill

| 旧 Skill | 替换方式 |
|----------|---------|
| 旧粗读入口 | `/paper` Stage 1 覆盖 |
| 旧精读入口 | `/paper --deep` 或 Stage 1 评分后触发覆盖 |
| `/pyrojewel-paper-zotero` | `/paper` Stage 2 对抗阅读和认知卡片覆盖 |
