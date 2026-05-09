---
name: wiki-compile-merged
description: 强制去重合并的编译流程。raw → source 是多对1关系，相似内容合并、互相补充。
---

# wiki-compile-merged

## 核心原则

**raw → source 是多对1关系**，不是 1:1 转换。

- 相似内容合并到一个 source 页面
- 不同 raw 互相补充同一主题
- 通过 smart search 强制去重

## 编译流程

### Step 1: 收集待编译文件

```
列出 raw 目录下所有待处理文件
按主题/项目/时间分组
```

### Step 2: 对每个主题组执行

```python
for group in topic_groups:
    # 2.1 先搜索是否已有相关 source
    results = search_vault_smart(
        query=group.keywords,
        filter={"folders": ["wiki/sources"], "limit": 10}
    )

    # 2.2 判断合并策略
    if results.exact_match:
        # 更新现有 source，补充新内容
        target = results.matched_page
        action = "merge"
    elif results.similar_pages:
        # 多个相关页面，考虑合并
        target = merge_or_create(results.similar_pages)
        action = "merge_or_create"
    else:
        # 创建新 source
        target = new_page
        action = "create"

    # 2.3 读取所有 raw 文件内容
    raw_contents = [read(f) for f in group.files]

    # 2.4 合并编译
    compiled_content = compile_and_merge(raw_contents, target, action)

    # 2.5 写入
    write_vault_file(target, compiled_content)
```

### Step 3: 更新 Registry

```
更新 nodes.jsonl（记录合并的 raw_refs）
更新 fingerprints.jsonl（每个 raw 一个指纹）
更新 edges.jsonl（raw → source 关系）
```

## 合并规则

### Session Logs 合并

| 场景 | 处理方式 |
|------|----------|
| 同一项目同一天的多个 session | 合并成一个 source，按时间线组织 |
| 同一主题跨多天的 session | 合并成主题聚合页，保留时间戳 |
| 不同项目但相似方法 | 提取方法到 procedure，source 互相引用 |

### 项目文档合并

| 场景 | 处理方式 |
|------|----------|
| 设计规范 + 实施计划 | 合并成项目总览页 |
| 多份周报 | 合并成项目演进时间线 |
| 需求 + 验证报告 | 合并成需求追踪页 |

### 论文笔记合并

| 场景 | 处理方式 |
|------|----------|
| 同一论文的多份笔记 | 合并成一个 source，标注来源 |
| 同一主题的多篇论文 | 保持独立 source，创建 topic 聚合 |
| 论文 + 相关代码笔记 | 在 source 中添加实现部分 |

## Smart Search 强制调用

**每次写入前必须调用：**

```
mcp__obsidian-mcp-tools__search_vault_smart(
    query="<主题关键词>",
    filter={
        "folders": ["wiki/sources", "wiki/entities", "wiki/procedures"],
        "limit": 10
    }
)
```

**判断标准：**

1. **完全匹配**：标题相同或 fingerprint 相同 → 更新现有页面
2. **高度相似**（>70% 关键词重叠）→ 合并到现有页面
3. **部分相似**（30-70%）→ 创建新页面，添加双向链接
4. **无匹配** → 创建新页面

## Fingerprint 去重

每个 raw 文件生成独立 fingerprint：

```json
{
    "id": "raw:session-2026-04-18-automodel",
    "fingerprint": "session:automodel:2026-04-18:abc123",
    "fingerprint_type": "session",
    "raw_sha256": "...",
    "compiled_to": "source:automodel-project-overview"
}
```

一个 source 可以对应多个 raw fingerprint：

```json
{
    "id": "source:automodel-project-overview",
    "raw_refs": [
        "raw:session-2026-04-18-automodel",
        "raw:session-2026-04-19-automodel",
        "raw:learning-roadmap-pca-nn"
    ]
}
```

## 输出模板

### 合并后的 Source 页面

```markdown
---
id: source:<slug>
type: source
source_kind: project-log | paper | tool-note | ...
title: <合并后的标题>
created_at: <最早 raw 日期>
updated_at: <最新 raw 日期>
raw_refs:
  - "[[raw/path1.md]]"
  - "[[raw/path2.md]]"
raw_paths:
  - raw/path1.md
  - raw/path2.md
fingerprint: <合并后的 fingerprint>
---

# <标题>

> **一句话总结**：...

## 来源

本页面合并自以下 raw：
- [[raw/path1.md]] (2026-04-18)
- [[raw/path2.md]] (2026-04-19)

## 内容

（合并重组后的完整内容）

## 提取的方法

- `procedure:xxx`

## 提取的实体

- `entity:xxx`

## 提取的主张

- `claim:xxx`
```

## 禁止

- ❌ 不调用 smart search 直接写入
- ❌ 1:1 复制 raw 到 source
- ❌ 忽略已存在的相似页面
- ❌ 不记录 raw_refs 来源
