#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zotero 批量修改文献类型

用法:
    python3 change_item_type.py <collection_name_or_key> <target_item_type>

示例:
    python3 change_item_type.py "重复" conferencePaper
    python3 change_item_type.py ETYYFTEF journalArticle
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# 从同级 .env 加载配置
_env_path = Path(__file__).parent.parent / ".env"
if not _env_path.exists():
    # 尝试 zotero-manager 的 .env
    _env_path = Path(__file__).parent.parent.parent / "zotero-manager" / ".env"

if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value

# 添加 zotero-manager 的 lib 路径
_lib_paths = [
    Path(__file__).parent.parent.parent / "zotero-manager" / "lib",
    Path(__file__).parent / "lib",
]
for _lib_path in _lib_paths:
    if _lib_path.exists():
        sys.path.insert(0, str(_lib_path))
        break

try:
    from zotero_api import ZoteroManager
except ImportError:
    print("错误: 无法导入 zotero_api，请确保 zotero-manager skill 存在")
    sys.exit(1)


# 可修改的文献类型
MODIFIABLE_TYPES = {
    'journalArticle': '期刊论文',
    'conferencePaper': '会议论文',
    'book': '书籍',
    'bookSection': '书籍章节',
    'thesis': '学位论文',
    'report': '报告',
    'preprint': '预印本',
    'webpage': '网页',
    'manuscript': '手稿',
    'document': '文档',
}


def get_all_collection_items(z: ZoteroManager, collection_key: str) -> List[Dict[str, Any]]:
    """分页获取 collection 的所有条目"""
    all_items = []
    start = 0
    limit = 100

    while True:
        url = f"{z.base_url}/users/{z.user_id}/collections/{collection_key}/items"
        params = {'limit': limit, 'start': start, 'format': 'json'}
        resp = z.session.get(url, headers=z.headers, params=params, timeout=z.timeout)
        resp.raise_for_status()
        items = resp.json()

        if not items:
            break

        all_items.extend(items)

        if len(items) < limit:
            break

        start += limit
        time.sleep(0.2)

    return all_items


def resolve_collection(z: ZoteroManager, name_or_key: str) -> Optional[str]:
    """按名称或 key 解析 collection"""
    collections = z.get_collections()

    # 先尝试 key 匹配
    for c in collections:
        if c['data']['key'] == name_or_key:
            return name_or_key

    # 再尝试名称匹配
    for c in collections:
        if c['data']['name'] == name_or_key:
            return c['data']['key']

    return None


def change_item_type(z: ZoteroManager, item_key: str, target_type: str, version: int) -> bool:
    """修改单个条目的类型"""
    url = f"{z.base_url}/users/{z.user_id}/items/{item_key}"
    headers = z.headers.copy()
    headers['If-Unmodified-Since-Version'] = str(version)

    try:
        resp = z.session.patch(url, headers=headers, json={"itemType": target_type}, timeout=z.timeout)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"  ❌ 修改失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="批量修改 Zotero collection 中文献的类型",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
支持的目标类型:
  {chr(10).join(f'  {k}: {v}' for k, v in MODIFIABLE_TYPES.items())}

示例:
  python3 change_item_type.py "重复" conferencePaper
  python3 change_item_type.py ETYYFTEF journalArticle
"""
    )
    parser.add_argument("collection", help="分类名称或 key")
    parser.add_argument("target_type", help="目标 itemType")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将要修改的条目，不实际修改")
    parser.add_argument("--delay", type=float, default=0.3, help="API 请求间隔（秒）")
    parser.add_argument("-y", "--yes", action="store_true", help="跳过确认，直接执行")

    args = parser.parse_args()

    if args.target_type not in MODIFIABLE_TYPES:
        print(f"错误: 不支持的目标类型 '{args.target_type}'")
        print(f"支持的类型: {', '.join(MODIFIABLE_TYPES.keys())}")
        sys.exit(1)

    # 初始化
    z = ZoteroManager()
    if not z.user_id:
        sys.exit(1)

    # 解析 collection
    collection_key = resolve_collection(z, args.collection)
    if not collection_key:
        print(f"错误: 找不到分类 '{args.collection}'")
        sys.exit(1)

    # 获取 collection 名称
    collections = z.get_collections()
    collection_name = args.collection
    for c in collections:
        if c['data']['key'] == collection_key:
            collection_name = c['data']['name']
            break

    print(f"\n目标分类: {collection_name} (key: {collection_key})")
    print(f"目标类型: {args.target_type} ({MODIFIABLE_TYPES[args.target_type]})")

    # 获取所有条目
    print(f"\n正在获取所有条目...")
    all_items = get_all_collection_items(z, collection_key)
    print(f"共 {len(all_items)} 条")

    # 统计类型分布
    type_count = {}
    for item in all_items:
        t = item.get('data', {}).get('itemType', 'unknown')
        type_count[t] = type_count.get(t, 0) + 1

    print(f"\n当前类型分布:")
    for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
        type_name = MODIFIABLE_TYPES.get(t, t)
        print(f"  {t} ({type_name}): {c}")

    # 筛选需要修改的条目
    items_to_modify = [
        item for item in all_items
        if item.get('data', {}).get('itemType') in MODIFIABLE_TYPES
        and item.get('data', {}).get('itemType') != args.target_type
    ]

    # attachment 等不可修改的条目
    unmodifiable_count = sum(
        1 for item in all_items
        if item.get('data', {}).get('itemType') not in MODIFIABLE_TYPES
    )

    # 已是目标类型的条目
    already_target_count = type_count.get(args.target_type, 0)

    print(f"\n需要修改: {len(items_to_modify)} 条")
    print(f"已是目标类型: {already_target_count} 条")
    print(f"不可修改 (attachment 等): {unmodifiable_count} 条")

    if not items_to_modify:
        print("\n没有需要修改的条目")
        return

    if args.dry_run:
        print(f"\n[Dry-run] 将修改以下 {len(items_to_modify)} 条:")
        for i, item in enumerate(items_to_modify[:20]):
            data = item.get('data', {})
            print(f"  [{i+1}] [{data.get('itemType')}] {data.get('title', 'N/A')[:60]}")
        if len(items_to_modify) > 20:
            print(f"  ... 还有 {len(items_to_modify) - 20} 条")
        return

    # 确认
    print(f"\n即将修改 {len(items_to_modify)} 条文献的类型为 {args.target_type}")
    if not args.yes:
        confirm = input("确认执行？(y/N): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return

    # 批量修改
    print(f"\n开始修改...")
    success = 0
    failed = 0

    for i, item in enumerate(items_to_modify):
        data = item.get('data', {})
        item_key = data.get('key')
        title = data.get('title', 'N/A')[:50]
        version = item.get('version', 0)

        ok = change_item_type(z, item_key, args.target_type, version)
        if ok:
            success += 1
            print(f"[{i+1}/{len(items_to_modify)}] ✅ {title}")
        else:
            failed += 1

        time.sleep(args.delay)

    print(f"\n完成: 成功 {success}, 失败 {failed}")

    # 显示最终类型分布
    print(f"\n正在验证...")
    all_items = get_all_collection_items(z, collection_key)
    type_count = {}
    for item in all_items:
        t = item.get('data', {}).get('itemType', 'unknown')
        type_count[t] = type_count.get(t, 0) + 1

    print(f"\n最终类型分布:")
    for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
        type_name = MODIFIABLE_TYPES.get(t, t)
        print(f"  {t} ({type_name}): {c}")


if __name__ == "__main__":
    main()
