#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
sys.path.insert(0, './lib')
from zotero_api import ZoteroManager
import json

manager = ZoteroManager()

collection_key = "LPTS9LWZ"
all_items = []
start = 0
limit = 100

print(f"正在获取 collection {collection_key} 的所有条目...")

# 分页获取所有条目
while True:
    items = manager.get_items_by_collection(collection_key, limit=limit, start=start)
    if not items:
        break
    all_items.extend(items)
    print(f"  已获取 {len(items)} 条 (累计 {len(all_items)} 条)")
    if len(items) < limit:
        break
    start += limit

print(f"\n总共获取到 {len(all_items)} 个条目\n")

no_doi_items = []

for item in all_items:
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
                                for c in data.get('creators', [])[:3]])
        })
        print(f"❌ 无 DOI: {title[:60]}... (ID: {key})")

journal_count = sum(1 for item in all_items if item.get('data', {}).get('itemType') == 'journalArticle')
print(f"\n\n总条目数: {len(all_items)}")
print(f"journalArticle 数量: {journal_count}")
print(f"无 DOI 的 journalArticle 数量: {len(no_doi_items)}")

# 保存到文件
with open('/tmp/no_doi_items_full.json', 'w', encoding='utf-8') as f:
    json.dump(no_doi_items, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存到 /tmp/no_doi_items_full.json")
