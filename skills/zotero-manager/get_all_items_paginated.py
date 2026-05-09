#!/usr/bin/env python3
import os
import requests
import json
import time
from pathlib import Path

# 从 .env 加载配置
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value

ZOTERO_USER_ID = os.getenv('ZOTERO_USER_ID')
ZOTERO_API_KEY = os.getenv('ZOTERO_API_KEY')
base_url = "https://api.zotero.org"

headers = {
    'Zotero-API-Version': '3',
    'Zotero-API-Key': ZOTERO_API_KEY,
}

collection_key = "LPTS9LWZ"
limit = 100

print(f"正在获取 collection {collection_key} 的所有条目...")
print(f"注意：每页最多获取 {limit} 条\n")

all_items = []
page = 0

while True:
    start = page * limit
    
    for attempt in range(3):
        try:
            url = f"{base_url}/users/{ZOTERO_USER_ID}/collections/{collection_key}/items"
            params = {
                'limit': limit,
                'start': start,
                'format': 'json'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            
            items = response.json()
            print(f"第 {page + 1} 页：获取到 {len(items)} 条 (累计 {len(all_items) + len(items)} 条)")
            
            if not items:
                print("\n所有条目获取完成！")
                # 跳出两层循环
                page = -1
                break
                
            all_items.extend(items)
            page += 1
            break
            
        except Exception as e:
            print(f"第 {attempt + 1} 次尝试失败：{e}")
            if attempt < 2:
                time.sleep(2)
            else:
                print(f"第 {page + 1} 页获取失败，跳过...")
                break
    
    if page == -1:
        break

print(f"\n总共获取到 {len(all_items)} 个条目\n")

no_doi_items = []
journal_count = 0

for item in all_items:
    data = item.get('data', {})
    item_type = data.get('itemType', 'unknown')
    
    if item_type == 'journalArticle':
        journal_count += 1
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

print(f"总条目数: {len(all_items)}")
print(f"journalArticle 数量: {journal_count}")
print(f"无 DOI 的 journalArticle 数量: {len(no_doi_items)}")

with open('/tmp/no_doi_items_all.json', 'w', encoding='utf-8') as f:
    json.dump(no_doi_items, f, ensure_ascii=False, indent=2)

print(f"\n结果已保存到 /tmp/no_doi_items_all.json")
