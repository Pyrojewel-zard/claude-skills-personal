#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将所有非附件条目转换为会议论文类型
"""

import os
import sys
from pathlib import Path

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
        print(f"❌ 更新失败 {item_key}: {e}")
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

    # 统计类型分布
    type_counts = {}
    to_convert = []
    for item in items:
        data = item.get('data', {})
        item_type = data.get('itemType', '')
        key = data.get('key', '')
        version = item.get('version', 0)
        title = data.get('title', '')

        type_counts[item_type] = type_counts.get(item_type, 0) + 1

        # 非附件且不是会议论文的需要转换
        if item_type != 'attachment' and item_type != 'conferencePaper':
            to_convert.append((key, title, item_type, version))

    print(f"\n当前类型分布: {type_counts}")
    print(f"需要转换为会议论文的条目数量: {len(to_convert)}")

    if not to_convert:
        print("✅ 所有非附件条目已经是会议论文类型！")
        return

    # 确认转换
    confirm = input(f"\n确认要将这 {len(to_convert)} 个条目转换为会议论文类型吗？(y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消操作")
        return

    # 执行转换
    success_count = 0
    fail_count = 0
    for i, (key, title, old_type, version) in enumerate(to_convert, 1):
        print(f"\n{i}/{len(to_convert)} 处理: {title[:60]}...")
        print(f"   类型: {old_type} -> conferencePaper")
        success = _update_item(zotero, key, {"itemType": "conferencePaper"}, version)
        if success:
            success_count += 1
            print(f"   ✅ 转换成功")
        else:
            fail_count += 1
            print(f"   ❌ 转换失败")

    print(f"\n处理完成！成功转换 {success_count} 个条目，失败 {fail_count} 个")

if __name__ == "__main__":
    main()
