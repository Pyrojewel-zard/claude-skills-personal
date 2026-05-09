import sys
sys.path.insert(0, '.')
sys.path.insert(0, './lib')
from zotero_api import ZoteroManager
import json

manager = ZoteroManager()

# 检查第一个没有 DOI 的条目
item_key = 'IS2C3EUY'

# 使用底层 API 获取完整数据
url = f"{manager.base_url}/users/{manager.user_id}/items/{item_key}"
response = manager.session.get(url, headers=manager.headers, timeout=manager.timeout)
print(f"主条目状态: {response.status_code}")
if response.status_code == 200:
    item_data = response.json()
    print(f"主条目数据:")
    print(json.dumps(item_data, indent=2, ensure_ascii=False)[:2000])

# 获取子条目（附件）
url = f"{manager.base_url}/users/{manager.user_id}/items/{item_key}/children"
response = manager.session.get(url, headers=manager.headers, timeout=manager.timeout)
print(f"\n\n子条目状态: {response.status_code}")
if response.status_code == 200:
    children = response.json()
    print(f"找到 {len(children)} 个子条目")
    for child in children:
        print(f"\n子条目: {child.get('data', {}).get('title', 'N/A')}")
        print(f"类型: {child.get('data', {}).get('itemType', 'N/A')}")
        print(f"Key: {child.get('key')}")
