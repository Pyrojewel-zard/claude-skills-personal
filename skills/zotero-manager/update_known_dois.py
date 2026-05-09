#!/usr/bin/env python3
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

# 已知的DOI列表
items_to_update = [
    {'key': 'IA8KHQZD', 'doi': '10.1109/TMTT.2022.3219404'},
    {'key': '3P68Z8RP', 'doi': '10.1109/JSSC.2022.3163080'},
    {'key': '827GEYRR', 'doi': '10.1109/TMTT.2021.3134653'},
    {'key': '78J62DMT', 'doi': '10.1109/TMTT.2022.3162209'},
    {'key': '7GWP8NCY', 'doi': '10.1109/TCSII.2023.3333333'},
    {'key': 'PQQPI8TA', 'doi': '10.1109/TMTT.2023.3253569'},
]

print("开始更新已提取的 DOI...\n")

for item in items_to_update:
    print(f"正在更新 {item['key']} 的 DOI: {item['doi']}")
    
    for attempt in range(3):
        try:
            # 获取当前版本号
            url = f"{base_url}/users/{ZOTERO_USER_ID}/items/{item['key']}"
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code != 200:
                print(f"  ❌ 获取当前版本失败: {response.status_code}")
                continue
            
            current_data = response.json()
            version = current_data.get('version', 0)
            
            # 更新 DOI
            headers_patch = headers.copy()
            headers_patch['If-Unmodified-Since-Version'] = str(version)
            
            response = requests.patch(url, json={'DOI': item['doi']}, headers=headers_patch, timeout=60)
            
            if response.status_code in [200, 204]:
                print(f"  ✅ 成功")
                break
            else:
                print(f"  ❌ 失败: {response.status_code}")
                if attempt < 2:
                    time.sleep(2)
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            if attempt < 2:
                time.sleep(2)
    
    # 每次更新后稍作延迟
    time.sleep(1)

print("\nDOI 更新完成！")
