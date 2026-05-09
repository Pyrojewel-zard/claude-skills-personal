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

# 需要更新的DOI列表（包括之前未成功的）
items_to_update = [
    # 之前提取但未成功更新的
    {'key': '78J62DMT', 'doi': '10.1109/TMTT.2022.3162209'},
    {'key': 'QV2M24GA', 'doi': '10.1109/PAWR46754.2020.9035999'},
    {'key': 'UW239YCJ', 'doi': '10.1109/TCSI.2022.3189389'},
    {'key': 'REUN8YHV', 'doi': '10.1109/TMTT.2024.3328472'},
    {'key': 'C2INSDYR', 'doi': '10.1109/TMTT.2024.3390834'},
    {'key': 'HZ8CLTX3', 'doi': '10.1109/TMTT.2024.3430893'},
    {'key': 'X2KI77VP', 'doi': '10.1109/TMTT.2024.3176818'},
    {'key': 'J2UPMPLX', 'doi': '10.1109/MWSYM.2010.5517561'},
    {'key': 'ZD2T2HYF', 'doi': '10.1109/LMWC.2019.2915998'},
    {'key': 'KF2NJSCN', 'doi': '10.1109/TMTT.2023.3279879'},
    {'key': 'WVF487YT', 'doi': '10.1109/TMTT.2024.3328472'},
    {'key': 'T8KNPCQL', 'doi': '10.1109/TCSI.2022.2869905'},
]

print(f"准备更新 {len(items_to_update)} 个条目的 DOI...\n")

success_count = 0
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
                success_count += 1
                break
            else:
                print(f"  ❌ 失败: {response.status_code} - {response.text[:100]}")
                if attempt < 2:
                    time.sleep(2)
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            if attempt < 2:
                time.sleep(2)
    
    # 每次更新后稍作延迟
    time.sleep(1)

print(f"\n更新完成！成功: {success_count}/{len(items_to_update)}")
