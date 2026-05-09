#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zotero 通用管理工具
基于 Zotero Web API，提供完整的文献/分类/标签管理能力。
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# 从同级 .env 加载配置
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from zotero_api import ZoteroManager


def cmd_status(args):
    """显示库信息和统计"""
    z = ZoteroManager()
    if not z.user_id:
        sys.exit(1)

    info = z.get_library_info()
    if info:
        print(f"\n📚 库信息")
        print(f"  用户: {info.get('username', 'N/A')} (ID: {z.user_id})")
        access = info.get('access', {})
        user_perm = access.get('user', {})
        print(f"  权限: 读写={user_perm.get('write', False)}, 文件={user_perm.get('files', False)}")

    items = z.get_items(limit=1)
    collections = z.get_collections()
    tags = z.get_tags()

    # 估算总文献数（Zotero API 单次最多100条）
    print(f"\n📊 统计")
    print(f"  分类数: {len(collections)}")
    print(f"  标签数: {len(tags)}")
    print(f"  文献: 至少 {len(items)} 篇（API 单次上限 100）")


def cmd_list_items(args):
    """列出文献"""
    z = ZoteroManager()
    items = z.get_items(limit=args.limit)
    if items:
        z.display_items(items, limit=args.limit)


def cmd_list_collections(args):
    """列出分类（树形）"""
    z = ZoteroManager()
    collections = z.get_collections()
    if collections:
        z.display_collections(collections)


def cmd_list_tags(args):
    """列出标签"""
    z = ZoteroManager()
    tags = z.get_tags()
    if tags:
        z.display_tags(tags, limit=args.limit)


def cmd_search(args):
    """搜索文献"""
    z = ZoteroManager()
    items = z.search_items(args.query, limit=args.limit)
    if items:
        z.display_items(items, limit=args.limit)


def cmd_collection_items(args):
    """查看某分类下的文献"""
    z = ZoteroManager()
    items = z.get_items_by_collection(args.collection_key, limit=args.limit)
    if items:
        z.display_items(items, limit=args.limit)


def cmd_item_detail(args):
    """查看文献详情"""
    z = ZoteroManager()
    item = z.get_item_detail(args.item_key)
    if item:
        data = item.get('data', {})
        print(f"\n标题: {data.get('title', 'N/A')}")
        print(f"类型: {data.get('itemType', 'N/A')}")
        creators = data.get('creators', [])
        authors = []
        for c in creators:
            if 'firstName' in c:
                authors.append(f"{c.get('firstName','')} {c.get('lastName','')}")
            elif 'name' in c:
                authors.append(c['name'])
        print(f"作者: {', '.join(authors)}")
        print(f"日期: {data.get('date', 'N/A')}")
        print(f"DOI: {data.get('DOI', 'N/A')}")
        print(f"摘要: {data.get('abstractNote', 'N/A')[:200]}")
        coll_keys = data.get('collections', [])
        if coll_keys:
            all_colls = z.get_collections()
            coll_map = {c['data']['key']: c['data']['name'] for c in all_colls}
            print(f"分类: {', '.join(coll_map.get(k, k) for k in coll_keys)}")
        tags = data.get('tags', [])
        if tags:
            print(f"标签: {', '.join(t.get('tag','') for t in tags)}")


def cmd_create_collection(args):
    """创建分类"""
    z = ZoteroManager()

    parent_key = ""
    if args.parent:
        # 按名称查找父分类
        all_colls = z.get_collections()
        for c in all_colls:
            if c['data']['name'] == args.parent:
                parent_key = c['data']['key']
                break
        if not parent_key:
            print(f"❌ 父分类 '{args.parent}' 不存在")
            sys.exit(1)

    result = z.create_collection({"name": args.name, "parentCollection": parent_key})
    if result:
        print(f"✅ 已创建: {args.name} (key: {result.get('key', '')})")
    else:
        print("❌ 创建失败")
        sys.exit(1)


def cmd_delete_collection(args):
    """删除分类"""
    z = ZoteroManager()
    ok = z.delete_collection(args.collection_key)
    if not ok:
        sys.exit(1)


def cmd_add_to_collection(args):
    """将文献添加到分类（支持批量）"""
    z = ZoteroManager()

    # 解析分类 key
    collection_key = _resolve_collection(z, args.collection)
    if not collection_key:
        print(f"❌ 分类 '{args.collection}' 不存在")
        sys.exit(1)

    success = 0
    failed = 0
    for item_key in args.item_keys:
        ok = z.add_item_to_collection(item_key, collection_key)
        if ok:
            success += 1
        else:
            failed += 1

    print(f"\n完成: 成功 {success}, 失败 {failed}")
    if failed:
        sys.exit(1)


def cmd_add_by_search(args):
    """搜索文献并批量添加到分类"""
    z = ZoteroManager()

    collection_key = _resolve_collection(z, args.collection)
    if not collection_key:
        print(f"❌ 分类 '{args.collection}' 不存在")
        sys.exit(1)

    items = z.search_items(args.query, limit=args.limit)
    if not items:
        print("❌ 未找到匹配的文献")
        sys.exit(1)

    print(f"找到 {len(items)} 篇文献，准备添加到分类...")
    z.display_items(items, limit=len(items))

    if args.confirm:
        confirm = input("\n确认添加到分类？(y/N): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return

    success = failed = 0
    for item in items:
        item_key = item['data']['key']
        ok = z.add_item_to_collection(item_key, collection_key)
        if ok:
            success += 1
        else:
            failed += 1

    print(f"\n完成: 成功 {success}, 失败 {failed}")
    if failed:
        sys.exit(1)


def cmd_remove_from_collection(args):
    """从分类中移除文献"""
    z = ZoteroManager()
    collection_key = _resolve_collection(z, args.collection)
    if not collection_key:
        print(f"❌ 分类 '{args.collection}' 不存在")
        sys.exit(1)

    success = 0
    for item_key in args.item_keys:
        ok = z.remove_item_from_collection(item_key, collection_key)
        if ok:
            success += 1
    print(f"完成: {success} 篇已从分类移除")


def cmd_delete_item(args):
    """删除文献"""
    z = ZoteroManager()
    ok = z.delete_item(args.item_key)
    if not ok:
        sys.exit(1)


def cmd_add_tag(args):
    """添加标签"""
    z = ZoteroManager()
    item = z.get_item_detail(args.item_key)
    if not item:
        sys.exit(1)

    current_tags = [t.get('tag', '') for t in item.get('data', {}).get('tags', [])]
    if args.tag in current_tags:
        print("标签已存在")
        return

    new_tags = [{'tag': t} for t in current_tags + [args.tag]]
    _update_item(z, args.item_key, {"tags": new_tags}, item.get('version', 0))
    print(f"✅ 已添加标签: {args.tag}")


def cmd_remove_tag(args):
    """移除标签"""
    z = ZoteroManager()
    item = z.get_item_detail(args.item_key)
    if not item:
        sys.exit(1)

    current_tags = [t.get('tag', '') for t in item.get('data', {}).get('tags', [])]
    if args.tag not in current_tags:
        print("标签不存在")
        return

    new_tags = [{'tag': t} for t in current_tags if t != args.tag]
    _update_item(z, args.item_key, {"tags": new_tags}, item.get('version', 0))
    print(f"✅ 已移除标签: {args.tag}")


def cmd_update_field(args):
    """更新文献字段"""
    z = ZoteroManager()
    item = z.get_item_detail(args.item_key)
    if not item:
        sys.exit(1)

    data = {}
    for kv in args.fields:
        if "=" in kv:
            k, v = kv.split("=", 1)
            data[k.strip()] = v.strip()

    if not data:
        print("❌ 请提供字段（格式: key=value）")
        sys.exit(1)

    _update_item(z, args.item_key, data, item.get('version', 0))
    print(f"✅ 已更新字段: {', '.join(data.keys())}")


def _resolve_collection(z: ZoteroManager, name_or_key: str) -> Optional[str]:
    """按名称或 key 解析分类"""
    # 先尝试直接作为 key
    collections = z.get_collections()
    for c in collections:
        if c['data']['key'] == name_or_key:
            return name_or_key
    # 再按名称匹配
    for c in collections:
        if c['data']['name'] == name_or_key:
            return c['data']['key']
    return None


def _update_item(z: ZoteroManager, item_key: str, data: dict, version: int) -> bool:
    """更新文献字段"""
    url = f"{z.base_url}/users/{z.user_id}/items/{item_key}"
    headers = z.headers.copy()
    headers['If-Unmodified-Since-Version'] = str(version)
    try:
        resp = z.session.patch(url, headers=headers, json=data, timeout=z.timeout)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Zotero 通用管理工具")
    sub = parser.add_subparsers(dest="command", help="子命令")

    # status
    sub.add_parser("status", help="库信息和统计")

    # list-items
    p = sub.add_parser("list-items", help="列出文献")
    p.add_argument("-n", "--limit", type=int, default=20, help="显示数量")

    # list-collections
    sub.add_parser("list-collections", help="列出分类（树形）")

    # list-tags
    p = sub.add_parser("list-tags", help="列出标签")
    p.add_argument("-n", "--limit", type=int, default=30)

    # search
    p = sub.add_parser("search", help="搜索文献")
    p.add_argument("query", help="搜索关键词")
    p.add_argument("-n", "--limit", type=int, default=20)

    # collection-items
    p = sub.add_parser("collection-items", help="查看分类下的文献")
    p.add_argument("collection_key", help="分类 key")
    p.add_argument("-n", "--limit", type=int, default=50)

    # item-detail
    p = sub.add_parser("item-detail", help="文献详情")
    p.add_argument("item_key", help="文献 key")

    # create-collection
    p = sub.add_parser("create-collection", help="创建分类")
    p.add_argument("name", help="分类名称")
    p.add_argument("--parent", help="父分类名称（可选）")

    # delete-collection
    p = sub.add_parser("delete-collection", help="删除分类")
    p.add_argument("collection_key", help="分类 key")

    # add-to-collection
    p = sub.add_parser("add-to-collection", help="添加文献到分类")
    p.add_argument("collection", help="分类名称或 key")
    p.add_argument("item_keys", nargs="+", help="文献 key 列表")

    # add-by-search
    p = sub.add_parser("add-by-search", help="搜索并批量添加到分类")
    p.add_argument("query", help="搜索关键词")
    p.add_argument("--collection", required=True, help="目标分类名称")
    p.add_argument("-n", "--limit", type=int, default=50)
    p.add_argument("--confirm", action="store_true", help="添加前确认（默认直接执行）")

    # remove-from-collection
    p = sub.add_parser("remove-from-collection", help="从分类移除文献")
    p.add_argument("collection", help="分类名称或 key")
    p.add_argument("item_keys", nargs="+", help="文献 key 列表")

    # delete-item
    p = sub.add_parser("delete-item", help="删除文献")
    p.add_argument("item_key", help="文献 key")

    # add-tag
    p = sub.add_parser("add-tag", help="添加标签")
    p.add_argument("item_key", help="文献 key")
    p.add_argument("tag", help="标签名称")

    # remove-tag
    p = sub.add_parser("remove-tag", help="移除标签")
    p.add_argument("item_key", help="文献 key")
    p.add_argument("tag", help="标签名称")

    # update-field
    p = sub.add_parser("update-field", help="更新文献字段")
    p.add_argument("item_key", help="文献 key")
    p.add_argument("fields", nargs="+", help="字段 key=value")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "status": cmd_status,
        "list-items": cmd_list_items,
        "list-collections": cmd_list_collections,
        "list-tags": cmd_list_tags,
        "search": cmd_search,
        "collection-items": cmd_collection_items,
        "item-detail": cmd_item_detail,
        "create-collection": cmd_create_collection,
        "delete-collection": cmd_delete_collection,
        "add-to-collection": cmd_add_to_collection,
        "add-by-search": cmd_add_by_search,
        "remove-from-collection": cmd_remove_from_collection,
        "delete-item": cmd_delete_item,
        "add-tag": cmd_add_tag,
        "remove-tag": cmd_remove_tag,
        "update-field": cmd_update_field,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
