import os
from dotenv import load_dotenv
import requests
from pathlib import Path
import json

env_path = Path('.env')
load_dotenv(env_path)

ZOTERO_USER_ID = os.getenv('ZOTERO_USER_ID')
ZOTERO_API_KEY = os.getenv('ZOTERO_API_KEY')
base_url = 'https://api.zotero.org'
headers = {
    'Zotero-API-Key': ZOTERO_API_KEY,
    'Zotero-API-Version': '3'
}

# 获取"导入"集合的key
print("获取导入集合的key...")
url = f'{base_url}/users/{ZOTERO_USER_ID}/collections'
params = {'limit': 100}
response = requests.get(url, headers=headers, params=params, timeout=30)
collections = response.json()

collection_key = None
for collection in collections:
    if collection['data']['name'] == '导入':
        collection_key = collection['key']
        break

if not collection_key:
    print("找不到'导入'集合")
    exit(1)

print(f"导入集合key: {collection_key}")

# 分页获取所有条目
print("获取所有条目...")
items = []
start = 0
limit = 100

while True:
    url = f'{base_url}/users/{ZOTERO_USER_ID}/collections/{collection_key}/items'
    params = {'limit': limit, 'start': start, 'format': 'json'}
    response = requests.get(url, headers=headers, params=params, timeout=60)

    if response.status_code != 200:
        print(f"获取条目失败: {response.status_code}")
        break

    batch = response.json()
    if not batch:
        break

    items.extend(batch)
    start += limit
    print(f"已获取 {len(items)} 个条目...")

print(f"总条目数: {len(items)}")

# 筛选出没有DOI的条目
no_doi_items = []
for item in items:
    data = item['data']
    # 排除笔记、附件等非文献条目
    if data['itemType'] in ['note', 'attachment']:
        continue
    if not data.get('DOI') or data['DOI'].strip() == '':
        no_doi_items.append({
            'key': data['key'],
            'title': data['title'],
            'date': data.get('date', ''),
            'authors': ', '.join([f"{a.get('lastName', '')} {a.get('firstName', '')}" for a in data.get('creators', [])])
        })

print(f"无DOI的条目数: {len(no_doi_items)}")

# 保存到文件
with open('/tmp/no_doi_items_all.json', 'w', encoding='utf-8') as f:
    json.dump(no_doi_items, f, ensure_ascii=False, indent=2)

print(f"结果已保存到 /tmp/no_doi_items_all.json")
