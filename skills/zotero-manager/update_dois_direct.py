#!/usr/bin/env python3
import sys
import os
import requests
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

# 需要更新 DOI 的条目
items_to_update = [
    {'key': 'IS2C3EUY', 'doi': '10.1109/TMTT.2025.3609399'},
    {'key': 'IA8KHQZD', 'doi': '10.1109/TMTT.2022.3219404'},
    {'key': '3P68Z8RP', 'doi': '10.1109/JSSC.2022.3163080'},
    {'key': '827GEYRR', 'doi': '10.1109/TMTT.2021.3134653'},
]

for item in items_to_update:
    print(f"正在更新 {item['key']} 的 DOI: {item['doi']}")
    
    # 先获取当前版本号
    url = f"{base_url}/users/{ZOTERO_USER_ID}/items/{item['key']}"
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code != 200:
        print(f"  ❌ 获取当前版本失败: {response.status_code}")
        continue
    
    current_data = response.json()
    version = current_data.get('version', 0)
    
    # 更新 DOI
    current_data['data']['DOI'] = item['doi']
    
    # 使用 PATCH 更新
    url = f"{base_url}/users/{ZOTERO_USER_ID}/items/{item['key']}"
    headers_patch = headers.copy()
    headers_patch['If-Unmodified-Since-Version'] = str(version)
    
    response = requests.patch(url, json={'DOI': item['doi']}, headers=headers_patch, timeout=30)
    
    if response.status_code in [200, 204]:
        print(f"  ✅ 成功")
    else:
        print(f"  ❌ 失败: {response.status_code} - {response.text[:200]}")

print("\n所有 DOI 更新完成！")
