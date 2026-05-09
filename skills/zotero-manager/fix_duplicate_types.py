#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复重复条目的类型问题
将同一标题的重复条目的类型统一为相同，以便后续合并
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

# 加载环境变量
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from zotero_api import ZoteroManager

def _update_item(zotero, item_key: str, data: dict, version: int) -> bool:
    """更新文献字段"""
    url = f"{zotero.base_url}/users/{zotero.user_id}/items/{item_key}"
    headers = zotero.headers.copy()
    headers['If-Unmodified-Since-Version'] = str(version)
    try:
        resp = zotero.session.patch(url, headers=headers, json=data, timeout=zotero.timeout)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False

def main():
    # 初始化Zotero管理器
    zotero = ZoteroManager()
    if not zotero.user_id:
        print("❌ 无法连接到Zotero库")
        return

    # "重复"分类的key
    collection_key = "ETYYFTEF"

    # 获取该分类下的所有文献
    print(f"正在获取分类 {collection_key} 下的所有文献...")
    items = zotero.get_items_by_collection(collection_key, limit=100)

    if not items:
        print("❌ 没有找到文献")
        return

    print(f"共获取到 {len(items)} 条文献")

    # 按标题分组
    title_groups = defaultdict(list)
    for item in items:
        data = item.get('data', {})
        title = data.get('title', '').strip()
        item_type = data.get('itemType', '')

        # 跳过附件类型
        if item_type == 'attachment':
            continue

        if title:
            title_groups[title].append(item)

    print(f"\n找到 {len(title_groups)} 个不同的标题")

    # 找出有重复条目的标题
    duplicate_groups = {title: group for title, group in title_groups.items() if len(group) > 1}
    print(f"找到 {len(duplicate_groups)} 组重复条目")

    if not duplicate_groups:
        print("✅ 没有找到需要处理的重复条目")
        return

    # 处理每组重复条目
    total_updated = 0
    for title, group in duplicate_groups.items():
        print(f"\n处理: {title}")
        print(f"  条目数: {len(group)}")

        # 统计该组的类型分布
        type_counts = defaultdict(int)
        for item in group:
            item_type = item.get('data', {}).get('itemType', '')
            type_counts[item_type] += 1

        print(f"  类型分布: {dict(type_counts)}")

        # 确定目标类型：优先选择数量最多的类型，如果都是1个，优先选择conferencePaper，其次journalArticle
        target_type = None
        if 'conferencePaper' in type_counts:
            target_type = 'conferencePaper'
        elif 'journalArticle' in type_counts:
            target_type = 'journalArticle'
        else:
            # 选择数量最多的类型
            target_type = max(type_counts.items(), key=lambda x: x[1])[0]

        print(f"  统一为类型: {target_type}")

        # 更新所有不是目标类型的条目
        for item in group:
            item_data = item.get('data', {})
            current_type = item_data.get('itemType', '')
            item_key = item_data.get('key', '')
            version = item.get('version', 0)

            if current_type != target_type:
                print(f"    更新条目 {item_key}: {current_type} -> {target_type}")
                success = _update_item(zotero, item_key, {"itemType": target_type}, version)
                if success:
                    total_updated += 1
                    print(f"    ✅ 更新成功")
                else:
                    print(f"    ❌ 更新失败")

    print(f"\n处理完成！共更新了 {total_updated} 个条目的类型")

if __name__ == "__main__":
    main()
