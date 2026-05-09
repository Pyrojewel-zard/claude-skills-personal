#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__)) + '/lib'))

from zotero_api import ZoteroManager
import json

manager = ZoteroManager()

# 获取导入 collection 的条目
collection_key = "LPTS9LWZ"
items = manager.get_items_by_collection(collection_key, limit=100)

print(f"总共获取到 {len(items)} 个条目\n")

no_doi_items = []

for item in items:
    data = item.get('data', {})
    item_type = data.get('itemType', 'unknown')
    
    # 只处理 journalArticle 类型的条目
    if item_type != 'journalArticle':
        continue
    
    key = item.get('key', 'unknown')
    title = data.get('title', '未知标题')
    doi = data.get('DOI', '')
    
    if not doi:
        no_doi_items.append({
            'key': key,
            'title': title,
            'date': data.get('date', ''),
            'authors': ', '.join([f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() 
                                for c in data.get('creators', [])[:2]])
        })
        print(f"❌ 无 DOI: {title[:60]}... (ID: {key})")
    else:
        print(f"✅ 有 DOI: {title[:50]}... DOI: {doi}")

print(f"\n\n总计: {len(no_doi_items)} 个条目没有 DOI")
print("\n没有 DOI 的条目列表:")
for i, item in enumerate(no_doi_items, 1):
    print(f"{i}. {item['title'][:70]}")
    print(f"   ID: {item['key']}, 作者: {item['authors']}, 日期: {item['date']}")

# 保存到文件
with open('/tmp/no_doi_items.json', 'w', encoding='utf-8') as f:
    json.dump(no_doi_items, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存到 /tmp/no_doi_items.json")
