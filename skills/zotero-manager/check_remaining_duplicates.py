#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查剩余的重复条目
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
        key = data.get('key', '')

        # 跳过附件类型
        if item_type == 'attachment':
            continue

        if title:
            title_groups[title].append((item_type, key))

    print(f"\n找到 {len(title_groups)} 个不同的标题")

    # 找出有重复条目的标题
    duplicate_groups = {title: group for title, group in title_groups.items() if len(group) > 1}
    print(f"找到 {len(duplicate_groups)} 组重复条目")

    if not duplicate_groups:
        print("✅ 没有找到重复条目")
        return

    # 检查哪些组还有不同的类型
    print("\n=== 重复条目详情 ===")
    mixed_type_groups = []
    for i, (title, group) in enumerate(duplicate_groups.items(), 1):
        types = [t for t, _ in group]
        unique_types = set(types)
        type_counts = {t: types.count(t) for t in unique_types}

        print(f"\n{i}. {title}")
        print(f"   条目数: {len(group)}")
        print(f"   类型分布: {type_counts}")
        for t, key in group:
            print(f"   - {key}: {t}")

        if len(unique_types) > 1:
            mixed_type_groups.append((title, group))

    if mixed_type_groups:
        print(f"\n⚠️  找到 {len(mixed_type_groups)} 组仍有不同类型的重复条目")
    else:
        print("\n✅ 所有重复条目的类型已经完全统一！")

if __name__ == "__main__":
    main()
