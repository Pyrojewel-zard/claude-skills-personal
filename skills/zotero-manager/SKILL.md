---
name: zotero-manager
description: "Zotero 文献库管理全流程。支持：库浏览、搜索、分类管理、DOI 导入、标签管理、字段更新。触发词：zotero、文献库、导入、分类。"
argument-hint: "[命令和参数]"
user_invocable: true
version: "2.0.0"
---

# Zotero Manager: 文献库管理全流程

一站式 Zotero Web API 管理：浏览 → 搜索 → 导入 → 组织。

## 前置条件

设置环境变量：
```bash
export ZOTERO_USER_ID='your_user_id'
export ZOTERO_API_KEY='your_api_key'
```

---

## 命令总览

| 命令 | 描述 | 示例 |
|------|------|------|
| `status` | 库信息和统计 | `status` |
| `list-items` | 列出文献 | `list-items -n 50` |
| `list-collections` | 列出分类（树形） | `list-collections` |
| `list-tags` | 列出标签 | `list-tags -n 50` |
| `search` | 搜索文献 | `search "LNA design"` |
| `import` | DOI 导入 | `import --doi 10.1109/... --collection "LNA"` |
| `create-collection` | 创建分类 | `create-collection "毫米波电路"` |
| `add-to-collection` | 添加文献到分类 | `add-to-collection "LNA" KEY1 KEY2` |
| `remove-from-collection` | 从分类移除 | `remove-from-collection "LNA" KEY1` |
| `add-tag` | 添加标签 | `add-tag KEY1 "重要"` |
| `remove-tag` | 移除标签 | `remove-tag KEY1 "待读"` |
| `update` | 更新字段/itemType | `update KEY1 itemType=journalArticle` |
| `delete-item` | 删除文献 | `delete-item KEY1` |

---

## 浏览与搜索

### status - 库信息

```bash
python3 zotero_manager.py status
```

输出：
```
Library: User Library
Items: 1234
Collections: 56
Tags: 789
Storage: 2.3 GB / 3 GB
```

### list-items - 列出文献

```bash
python3 zotero_manager.py list-items [-n 50] [--collection NAME]
```

### list-collections - 列出分类

```bash
python3 zotero_manager.py list-collections
```

输出树形结构：
```
📁 LNA设计 (WNGWPD4I)
  📁 噪声优化 (ABC12345)
  📁 宽带匹配 (DEF67890)
📁 毫米波电路 (XYZ12345)
```

### search - 搜索文献

```bash
python3 zotero_manager.py search "关键词" [-n 50]
```

---

## 导入（DOI）

### 单篇导入

```bash
python3 zotero_manager.py import --doi "10.1109/TMTT.2023.1234567" --collection "RF Amplifiers"
```

### 批量导入

```bash
# 多个 DOI
python3 zotero_manager.py import --doi "10.1109/TMTT.2023.111" --doi "10.1109/TMTT.2023.222" --collection "RF Filters"

# 从文件导入
python3 zotero_manager.py import --file dois.txt --collection "LNA Design"
```

### 创建分类并导入

```bash
python3 zotero_manager.py import --doi "10.xxxx/xxx" --collection "新分类/子分类" --create-collection
```

**工作原理**：
1. 使用 Zotero Web API `POST /users/{userId}/items` 创建 `journalArticle` 条目
2. Zotero 自动解析 DOI 获取元数据
3. 查找或创建分类
4. 将文献添加到分类

---

## 分类管理

### create-collection - 创建分类

```bash
# 顶级分类
python3 zotero_manager.py create-collection "太赫兹电路"

# 子分类
python3 zotero_manager.py create-collection "滤波器" --parent "太赫兹电路"
```

### add-to-collection - 添加文献到分类

```bash
# 按名称
python3 zotero_manager.py add-to-collection "LNA设计" KEY1 KEY2 KEY3

# 搜索并批量添加
python3 zotero_manager.py add-by-search "noise figure" --collection "LNA设计"
```

### remove-from-collection - 从分类移除

```bash
python3 zotero_manager.py remove-from-collection "LNA设计" KEY1
```

---

## 标签管理

### add-tag - 添加标签

```bash
python3 zotero_manager.py add-tag KEY1 "重要"
python3 zotero_manager.py add-tag KEY1 "2026必读"
```

### remove-tag - 移除标签

```bash
python3 zotero_manager.py remove-tag KEY1 "待读"
```

---

## 字段更新

### update - 更新字段/itemType

```bash
# 更新标题
python3 zotero_manager.py update KEY1 title="New Title"

# 更新 itemType（批量修改文献类型）
python3 zotero_manager.py update KEY1 KEY2 KEY3 itemType=journalArticle

# 更新多个字段
python3 zotero_manager.py update KEY1 title="Title" date="2024" publicationTitle="IEEE TMTT"
```

**支持的 itemType**：
- `journalArticle` - 期刊论文
- `conferencePaper` - 会议论文
- `book` - 书籍
- `thesis` - 学位论文
- `report` - 报告
- `preprint` - 预印本

---

## 删除

### delete-item - 删除文献

```bash
python3 zotero_manager.py delete-item KEY1
```

### delete-collection - 删除分类

```bash
python3 zotero_manager.py delete-collection COLLECTION_KEY
```

---

## 典型工作流

```bash
# 1. 查看现有分类
python3 zotero_manager.py list-collections

# 2. 创建新分类
python3 zotero_manager.py create-collection "太赫兹电路"

# 3. 创建子分类
python3 zotero_manager.py create-collection "滤波器" --parent "太赫兹电路"

# 4. 搜索相关文献
python3 zotero_manager.py search "terahertz filter" -n 50

# 5. 搜索并批量添加到分类
python3 zotero_manager.py add-by-search "terahertz" --collection "太赫兹电路"

# 6. 或直接指定文献 key 添加
python3 zotero_manager.py add-to-collection "太赫兹电路" KEY1 KEY2 KEY3

# 7. 添加标签
python3 zotero_manager.py add-tag KEY1 "2026必读"

# 8. 验证结果
python3 zotero_manager.py collection-items <太赫兹电路的key>
```

---

## API 细节

```python
from cli import ZoteroManager

zotero = ZoteroManager()

# 导入 DOI
url = f"{zotero.base_url}/users/{zotero.user_id}/items"
payload = [{
    "itemType": "journalArticle",
    "DOI": "10.xxxx/xxx"
}]
response = zotero.session.post(url, headers=zotero.headers, json=payload)

# 获取所有分类
collections = zotero.get_collections()

# 创建分类
zotero.create_collection({"name": "New Collection", "parentCollection": ""})

# 添加文献到分类
zotero.add_item_to_collection(item_key, collection_key)
```

---

## 限流说明

- Zotero API：匿名用户 200 请求/5 分钟，认证用户更高
- 默认重试：5 次，指数退避
- 批量导入时建议间隔 0.5 秒

---

## 注意事项

- DOI 导入依赖 Zotero 的元数据解析，部分 DOI 可能无法解析
- 导入后建议检查元数据
- 分类名称区分大小写
- 子分类需要父分类已存在（使用 `Parent/Child` 语法 + `--create-collection`）

---

## 快速示例

\`\`\`
/zotero-manager status                          # 库信息
/zotero-manager search "LNA"                    # 搜索
/zotero-manager import --doi 10.1109/...        # 导入
/zotero-manager create-collection "新分类"      # 创建分类
/zotero-manager add-tag KEY1 "重要"             # 添加标签
/zotero-manager update KEY1 itemType=journalArticle  # 修改类型
\`\`\`
