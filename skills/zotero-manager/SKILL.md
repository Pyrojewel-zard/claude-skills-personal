---
name: zotero-manager
description: "Universal Zotero Web API management tool. Supports: list/search items, create/delete collections, batch add/remove items to collections, tag management, field updates. Trigger: user wants to manage Zotero library via API."
version: 0.1.0
---

# Zotero Manager Skill

Complete Zotero Web API management — browse, organize, tag, and manage your entire library from the command line.

## Quick Start

```bash
cd ~/.claude/skills/zotero-manager
python3 zotero_manager.py <command> [options]
```

## Commands

### Browse & Search

| Command | Description | Example |
|---------|-------------|---------|
| `status` | 库信息和统计 | `python3 zotero_manager.py status` |
| `list-items [-n 50]` | 列出文献 | `python3 zotero_manager.py list-items -n 50` |
| `list-collections` | 列出分类（树形） | `python3 zotero_manager.py list-collections` |
| `list-tags [-n 50]` | 列出标签 | `python3 zotero_manager.py list-tags` |
| `search "keyword"` | 搜索文献 | `python3 zotero_manager.py search "LNA design"` |
| `collection-items KEY` | 查看某分类文献 | `python3 zotero_manager.py collection-items WNGWPD4I` |
| `item-detail KEY` | 文献详情 | `python3 zotero_manager.py item-detail ABCDEFGH` |

### Collection 管理

| Command | Description | Example |
|---------|-------------|---------|
| `create-collection NAME [--parent NAME]` | 创建分类 | `python3 zotero_manager.py create-collection "毫米波电路"` |
| `create-collection NAME --parent "LNA设计"` | 创建子分类 | `python3 zotero_manager.py create-collection "噪声优化" --parent "LNA设计"` |
| `delete-collection KEY` | 删除分类 | `python3 zotero_manager.py delete-collection ABCDEFGH` |

### 文献 → 分类（批量）

| Command | Description | Example |
|---------|-------------|---------|
| `add-to-collection NAME KEY1 KEY2 ...` | 添加文献到分类 | `python3 zotero_manager.py add-to-collection "LNA设计" KEY1 KEY2 KEY3` |
| `add-by-search "query" --collection NAME` | 搜索并批量添加 | `python3 zotero_manager.py add-by-search "noise figure" --collection "LNA设计"` |
| `remove-from-collection NAME KEY1 KEY2` | 从分类移除文献 | `python3 zotero_manager.py remove-from-collection "LNA设计" KEY1` |

### 标签 & 字段

| Command | Description | Example |
|---------|-------------|---------|
| `add-tag KEY "tagname"` | 添加标签 | `python3 zotero_manager.py add-tag KEY1 "重要"` |
| `remove-tag KEY "tagname"` | 移除标签 | `python3 zotero_manager.py remove-tag KEY1 "待读"` |
| `update-field KEY key=value ...` | 更新文献字段 | `python3 zotero_manager.py update-field KEY title="New Title"` |
| `delete-item KEY` | 删除文献 | `python3 zotero_manager.py delete-item KEY1` |

## Typical Workflow: 创建分类并批量导入文献

```bash
# 1. 查看现有分类
python3 zotero_manager.py list-collections

# 2. 创建新分类
python3 zotero_manager.py create-collection "太赫兹电路"

# 3. 创建子分类
python3 zotero_manager.py create-collection "滤波器" --parent "太赫兹电路"

# 4. 搜索相关文献
python3 zotero_manager.py search "terahertz filter" -n 50

# 5. 搜索并批量添加到分类（有确认步骤）
python3 zotero_manager.py add-by-search "terahertz" --collection "太赫兹电路"

# 6. 或者直接指定文献 key 添加
python3 zotero_manager.py add-to-collection "太赫兹电路" KEY1 KEY2 KEY3

# 7. 添加标签
python3 zotero_manager.py add-tag KEY1 "2026必读"

# 8. 验证结果
python3 zotero_manager.py collection-items <太赫兹电路的key>
```

## Notes

- collection 参数支持**名称**或 **key**，自动识别
- `add-by-search` 会先显示匹配文献，要求确认后再添加
- 配置从同级 `.env` 文件读取（`ZOTERO_USER_ID`, `ZOTERO_API_KEY`）
- 带 5 次重试 + 指数退避，防 API 限流
