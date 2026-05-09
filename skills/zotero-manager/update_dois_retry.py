#!/usr/bin/env python3
import sys
import os
import requests
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
    'Content-Type': 'application/json',
}

# 只更新剩余的条目（IS2C3EUY 已经成功）
items_to_update = [
    {'key': 'IA8KHQZD', 'doi': '10.1109/TMTT.2022.3219404'},
    {'key': '3P68Z8RP', 'doi': '10.1109/JSSC.2022.3163080'},
    {'key': '827GEYRR', 'doi': '10.1109/TMTT.2021.3134653'},
]

def update_item(item_key, doi):
    for attempt in range(3):
        try:
            print(f"  [尝试 {attempt + 1}] 获取当前版本...")
            url = f"{base_url}/users/{ZOTERO_USER_ID}/items/{item_key}"
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code != 200:
                print(f"  ❌ 获取当前版本失败: {response.status_code}")
                return False
            
            current_data = response.json()
            version = current_data.get('version', 0)
            print(f"  当前版本: {version}")
            
            print(f"  [尝试 {attempt + 1}] 更新 DOI...")
            headers_patch = headers.copy()
            headers_patch['If-Unmodified-Since-Version'] = str(version)
            
            response = requests.patch(url, json={'DOI': doi}, headers=headers_patch, timeout=60)
            
            if response.status_code in [200, 204]:
                print(f"  ✅ 成功")
                return True
            else:
                print(f"  ❌ 失败: {response.status_code} - {response.text[:100]}")
                if attempt < 2:
                    time.sleep(2)
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            if attempt < 2:
                time.sleep(2)
    return False

for item in items_to_update:
    print(f"正在更新 {item['key']} 的 DOI: {item['doi']}")
    success = update_item(item['key'], item['doi'])

print("\n更新完成！")
