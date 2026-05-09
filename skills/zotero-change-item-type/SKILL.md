---
name: zotero-change-item-type
description: 批量修改 Zotero collection 中文献的 itemType。当用户说"把某个分类的文献改成会议论文"、"批量修改文献类型"、"将 collection X 的所有 journalArticle 改成 conferencePaper"时使用。支持按 collection 名称或 key 定位，自动分页获取所有条目，批量修改并报告进度。
---

# Zotero 批量修改文献类型

批量修改指定 Zotero collection 中所有文献的 `itemType` 字段。

## 使用场景

- 用户想把某个 collection 的所有期刊论文改成会议论文
- 批量修正文献类型错误
- 统一某个分类下的文献类型

## 支持的 itemType

可修改的文献类型（非 attachment）：
- `journalArticle` → 期刊论文
- `conferencePaper` → 会议论文
- `book` → 书籍
- `bookSection` → 书籍章节
- `thesis` → 学位论文
- `report` → 报告
- `preprint` → 预印本
- `webpage` → 网页

**不可修改**: `attachment`（PDF 附件）无法转换为文献类型。

## 工作流程

1. **定位 collection**: 按名称或 key 找到目标 collection
2. **分页获取所有条目**: Zotero API 单次最多返回 100 条，需要循环分页
3. **筛选可修改条目**: 排除 `attachment` 和已是目标类型的条目
4. **批量修改**: 使用 PATCH 请求逐条修改 `itemType`
5. **报告进度**: 显示成功/失败统计

## 调用脚本

使用 `scripts/change_item_type.py` 执行批量修改：

```bash
cd /path/to/zotero-change-item-type
python3 scripts/change_item_type.py <collection_name_or_key> <target_item_type>
```

参数：
- `collection_name_or_key`: 分类名称（如"重复")或 key（如"ETYYFTEF")
- `target_item_type`: 目标类型（如 `conferencePaper`、`journalArticle`）

脚本会：
- 自动分页获取所有条目（不限数量）
- 显示当前类型分布
- 筛选需要修改的条目
- 逐条修改并显示进度
- 最终报告成功/失败数

## 示例用法

用户说："把'重复'这个 collection 的所有文献改成会议论文"

执行：
```bash
python3 scripts/change_item_type.py "重复" conferencePaper
```

用户说："将 collection ETYYFTEF 的 journalArticle 都改成 conferencePaper"

执行：
```bash
python3 scripts/change_item_type.py ETYYFTEF conferencePaper
```

## 注意事项

- 修改不可逆，建议先确认
- API 有速率限制，脚本已内置 0.3s 延迟
- `attachment` 类型无法修改，会自动跳过
- 已是目标类型的条目会跳过
