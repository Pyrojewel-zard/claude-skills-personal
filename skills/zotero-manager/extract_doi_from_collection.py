#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取指定collection中的文献DOI，保存到CSV
"""

import os
import csv
import time
from pathlib import Path

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

from zotero_api import ZoteroManager

def main():
    collection_key = "3IAWNQYQ"  # Nopdf collection ID
    output_file = Path("/tmp/nopdf_collection_dois.csv")

    z = ZoteroManager()
    if not z.user_id:
        return

    print(f"开始提取collection {collection_key} 中的文献DOI，保存到 {output_file}")

    seen_item_keys = set()  # 去重
    start = 0
    limit = 100
    total_processed = 0
    has_doi_count = 0

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['DOI', 'Title', 'Item Key'])

        while True:
            print(f"正在获取第 {start+1} - {start+limit} 条文献...")
            items = z.get_items_by_collection(collection_key, limit=limit, start=start)

            if not items:
                break

            # 去重
            new_items = [item for item in items if item['data']['key'] not in seen_item_keys]
            if not new_items:
                print("没有新的条目了，结束")
                break

            for item in new_items:
                item_key = item['data']['key']
                seen_item_keys.add(item_key)
                total_processed += 1

                data = item.get('data', {})
                title = data.get('title', '无标题')
                doi = data.get('DOI', '').strip()

                if doi:
                    has_doi_count += 1
                    writer.writerow([doi, title, item_key])
                    print(f"提取到DOI: {doi} | {title[:50]}...")

            # 如果返回的条目数小于limit，说明已经到最后一页
            if len(items) < limit:
                break

            start += limit
            # 避免API限流
            time.sleep(0.2)

    print(f"\n处理完成！")
    print(f"总处理文献数: {total_processed}")
    print(f"有DOI的文献数: {has_doi_count}")
    print(f"DOI列表已保存到: {output_file}")

if __name__ == "__main__":
    main()
