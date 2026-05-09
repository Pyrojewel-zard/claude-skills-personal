import os
from dotenv import load_dotenv
import requests
from pathlib import Path
import time

env_path = Path('.env')
load_dotenv(env_path)

ZOTERO_USER_ID = os.getenv('ZOTERO_USER_ID')
ZOTERO_API_KEY = os.getenv('ZOTERO_API_KEY')
base_url = 'https://api.zotero.org'
headers = {
    'Zotero-API-Key': ZOTERO_API_KEY,
    'Zotero-API-Version': '3'
}

# 提取到的DOI列表
items = {
    '9R673P6H': '10.1109/TMTT.2024.3421558',
    'JSULJLRX': '10.1109/TMTT.2025.3610336',
    'XDKH4I2N': '10.1109/TMTT.2024.3447028',
    'CCQV48Q8': '10.1109/TMTT.2026.3654251',
    'EE436FJG': '10.1109/TMTT.2025.3647113'
}

# 获取每个条目的版本号
versions = {}
for key, doi in items.items():
    for attempt in range(3):
        try:
            url = f'{base_url}/users/{ZOTERO_USER_ID}/items/{key}'
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                data = r.json()['data']
                versions[key] = data['version']
                print(f'{key}: version={versions[key]}, DOI={doi}')
                break
            else:
                print(f'{key}: Get version failed (attempt {attempt+1}), status={r.status_code}')
                time.sleep(2)
        except Exception as e:
            print(f'{key}: Get version error (attempt {attempt+1}): {e}')
            time.sleep(2)

print("\n=== Updating DOIs ===")
headers_patch = headers.copy()
results = {}

for key, doi in items.items():
    version = versions.get(key)
    if not version:
        print(f"{key}: Skipping - no version")
        continue

    url = f'{base_url}/users/{ZOTERO_USER_ID}/items/{key}'
    headers_patch['If-Unmodified-Since-Version'] = str(version)

    for attempt in range(3):
        try:
            print(f"{key}: Updating DOI to {doi} (attempt {attempt+1})")
            r = requests.patch(url, json={'DOI': doi}, headers=headers_patch, timeout=60)
            if r.status_code == 204:
                print(f"  ✓ Success!")
                results[key] = {'status': 'success', 'doi': doi}
                break
            else:
                print(f"  ✗ Failed: {r.status_code}")
                if r.status_code == 412:
                    # Version conflict, retry getting version
                    r2 = requests.get(url, headers=headers, timeout=30)
                    if r2.status_code == 200:
                        versions[key] = r2.json()['data']['version']
                        headers_patch['If-Unmodified-Since-Version'] = str(versions[key])
                        print(f"  Refreshed version to {versions[key]}")
                        continue
                time.sleep(2)
        except Exception as e:
            print(f"  ✗ Error: {e}")
            time.sleep(2)

print("\n=== Summary ===")
success_count = 0
for key, result in results.items():
    if result['status'] == 'success':
        success_count += 1
        print(f"✓ {key}: {result['doi']}")
    else:
        print(f"✗ {key}: {result}")

print(f"\nTotal: {success_count}/{len(items)} updates successful")
