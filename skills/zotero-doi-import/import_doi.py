#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zotero DOI Import Tool
Import papers by DOI into Zotero and organize them into collections.
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Optional

# 从同级 .env 文件加载配置
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value

sys.path.insert(0, str(Path(__file__).parent))
from cli import ZoteroManager


class DOIImporter:
    """DOI 导入管理器"""

    def __init__(self, user_id: str = None, api_key: str = None):
        self.zotero = ZoteroManager(user_id, api_key)
        self._collection_cache: Dict[str, str] = {}

    def import_doi(self, doi: str, delay: float = 0.5) -> Optional[str]:
        """
        通过 DOI 导入文献到 Zotero

        Returns:
            成功返回 item_key，失败返回 None
        """
        doi = doi.strip()
        if not doi:
            return None

        print(f"📥 正在导入 DOI: {doi}")
        url = f"{self.zotero.base_url}/users/{self.zotero.user_id}/items"
        payload = [{"itemType": "journalArticle", "DOI": doi}]

        try:
            response = self.zotero.session.post(
                url, headers=self.zotero.headers, json=payload, timeout=self.zotero.timeout
            )
            response.raise_for_status()
            result = response.json()

            if result.get("successful"):
                success = result["successful"]
                first_key = list(success.keys())[0]
                created = success[first_key]
                item_key = created.get("key", "")
                title = created.get("data", {}).get("title", "无标题")
                print(f"  ✅ 导入成功: {title} (key: {item_key})")
                time.sleep(delay)
                return item_key
            elif result.get("failed"):
                failed = result["failed"]
                first_key = list(failed.keys())[0]
                error = failed[first_key]
                print(f"  ❌ 导入失败: {error}")
                return None
            else:
                print(f"  ❌ 未知响应: {result}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"  ❌ 请求失败: {e}")
            return None

    def find_collection(self, name: str) -> Optional[str]:
        """按名称查找 collection，返回 collection_key"""
        if name in self._collection_cache:
            return self._collection_cache[name]

        collections = self.zotero.get_collections()
        for coll in collections:
            if coll["data"]["name"] == name:
                key = coll["data"]["key"]
                self._collection_cache[name] = key
                return key

        return None

    def create_collection(self, name: str, parent_name: str = None) -> Optional[str]:
        """
        创建 collection，支持嵌套（Parent/Child）

        Returns:
            成功返回 collection_key，失败返回 None
        """
        if parent_name:
            parent_key = self.find_collection(parent_name)
            if not parent_key:
                print(f"  ❌ 父分类不存在: {parent_name}")
                return None
            collection_data = {"name": name, "parentCollection": parent_key}
        else:
            collection_data = {"name": name, "parentCollection": ""}

        result = self.zotero.create_collection(collection_data)
        if result:
            key = result.get("key", "")
            self._collection_cache[name] = key
            return key
        return None

    def resolve_collection_path(self, path: str, create_if_missing: bool = False) -> Optional[str]:
        """
        解析 collection 路径，支持嵌套（如 "RF/LNA"）

        Args:
            path: 路径，如 "RF Amplifiers" 或 "RF/LNA"
            create_if_missing: 不存在时是否创建

        Returns:
            collection_key 或 None
        """
        parts = [p.strip() for p in path.split("/")]

        current_parent_key = None
        last_key = None

        for i, part_name in enumerate(parts):
            key = self.find_collection(part_name)

            if not key:
                if create_if_missing:
                    parent_key = current_parent_key if i > 0 else None
                    parent_display = parts[i - 1] if i > 0 else None
                    key = self.create_collection(part_name, parent_name=parent_display)
                    if not key:
                        print(f"  ❌ 无法创建分类: {part_name}")
                        return None
                    print(f"  📂 已创建分类: {part_name}")
                else:
                    print(f"  ❌ 分类不存在: {part_name}")
                    return None

            current_parent_key = key
            last_key = key

        return last_key

    def add_to_collection(self, item_key: str, collection_key: str) -> bool:
        """将文献添加到 collection"""
        return self.zotero.add_item_to_collection(item_key, collection_key)

    def import_and_organize(
        self,
        dois: List[str],
        collection_path: str,
        create_collection: bool = False,
        delay: float = 0.5,
    ) -> Dict[str, int]:
        """
        批量导入 DOI 并分配到指定 collection

        Returns:
            统计信息 {"success": N, "failed": N, "total": N}
        """
        stats = {"success": 0, "failed": 0, "total": len(dois)}

        # 解析或创建 collection
        print(f"📂 目标分类: {collection_path}")
        collection_key = self.resolve_collection_path(collection_path, create_if_missing=create_collection)
        if not collection_key:
            print("❌ 无法获取目标分类，中止导入")
            return stats

        print(f"\n🚀 开始导入 {len(dois)} 篇文献...\n")

        for i, doi in enumerate(dois, 1):
            print(f"[{i}/{len(dois)}]", end=" ")
            item_key = self.import_doi(doi, delay=delay)

            if item_key:
                success = self.add_to_collection(item_key, collection_key)
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    print(f"  ⚠️ 添加到分类失败")
            else:
                stats["failed"] += 1

        print(f"\n{'='*40}")
        print(f"导入完成: 成功 {stats['success']}/{stats['total']}, 失败 {stats['failed']}")
        return stats


def main():
    parser = argparse.ArgumentParser(description="Zotero DOI 导入工具")
    parser.add_argument("--doi", action="append", help="DOI（可多次使用）")
    parser.add_argument("--file", help="包含 DOI 列表的文本文件（每行一个）")
    parser.add_argument("--collection", required=True, help="目标分类名称（支持嵌套: Parent/Child）")
    parser.add_argument("--create-collection", action="store_true", help="分类不存在时自动创建")
    parser.add_argument("--delay", type=float, default=0.5, help="请求间隔秒数（默认 0.5）")
    parser.add_argument("--user-id", help="Zotero 用户 ID（或设置 ZOTERO_USER_ID）")
    parser.add_argument("--api-key", help="Zotero API Key（或设置 ZOTERO_API_KEY）")

    args = parser.parse_args()

    # 收集 DOI
    dois = []
    if args.doi:
        dois.extend(args.doi)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    dois.append(line)

    if not dois:
        print("❌ 请提供 DOI（--doi 或 --file）")
        sys.exit(1)

    # 检查认证
    if not os.getenv("ZOTERO_USER_ID") and not args.user_id:
        print("❌ 请设置 ZOTERO_USER_ID 环境变量或传入 --user-id")
        sys.exit(1)
    if not os.getenv("ZOTERO_API_KEY") and not args.api_key:
        print("❌ 请设置 ZOTERO_API_KEY 环境变量或传入 --api-key")
        sys.exit(1)

    importer = DOIImporter(args.user_id, args.api_key)
    stats = importer.import_and_organize(
        dois=dois,
        collection_path=args.collection,
        create_collection=args.create_collection,
        delay=args.delay,
    )

    if stats["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
