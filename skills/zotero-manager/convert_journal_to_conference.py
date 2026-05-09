#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将分类下所有期刊文章转换为会议论文
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
    items = zotero.get_items_by_collection(collection_key, limit=200)

    if not items:
        print("❌ 没有找到文献")
        return

    print(f"共获取到 {len(items)} 条文献")

    # 筛选出期刊文章
    journal_items = []
    for item in items:
        data = item.get('data', {})
        item_type = data.get('itemType', '')
        if item_type == 'journalArticle':
            key = data.get('key', '')
            title = data.get('title', '')
            version = item.get('version', 0)
            journal_items.append((key, title, version))

    print(f"找到 {len(journal_items)} 篇期刊文章需要转换为会议论文")

    if not journal_items:
        print("✅ 没有需要转换的期刊文章！")
        return

    # 显示列表
    print("\n=== 待转换的期刊文章 ===")
    for i, (key, title, _) in enumerate(journal_items, 1):
        print(f"{i}. {key}: {title[:80]}")

    # 确认转换
    confirm = input(f"\n确认要将这 {len(journal_items)} 篇期刊文章转换为会议论文吗？(y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消操作")
        return

    # 执行转换
    success_count = 0
    fail_count = 0
    for i, (key, title, version) in enumerate(journal_items, 1):
        print(f"\n{i}/{len(journal_items)} 处理: {title[:70]}...")
        success = _update_item(zotero, key, {"itemType": "conferencePaper"}, version)
        if success:
            success_count += 1
            print(f"   ✅ 转换成功")
        else:
            fail_count += 1
            print(f"   ❌ 转换失败")

    print(f"\n处理完成！成功转换 {success_count} 篇，失败 {fail_count} 篇")

if __name__ == "__main__":
    main()
