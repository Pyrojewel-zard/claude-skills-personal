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

items = {
    'KF2NJSCN': '10.1109/TMTT.2025.3648363',
    'WVF487YT': '10.1109/TMTT.2025.3627331',
    'T8KNPCQL': '10.1109/TCSI.2023.3338056',
    'REUN8YHV': '10.1109/TMTT.2023.3284268',
    'Q7DFJ4Y5': '10.1109/TMTT.2025.3610420'
}

versions = {}
for key, doi in items.items():
    url = f'{base_url}/users/{ZOTERO_USER_ID}/items/{key}'
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code == 200:
        data = r.json()['data']
        versions[key] = data['version']
        print(f'{key}: version={versions[key]}, DOI={doi}')
    else:
        print(f'{key}: FAILED - {r.status_code}')

print(f"\nUpdate data:")
for key, doi in items.items():
    print(f"'{key}': {{'doi': '{doi}', 'version': {versions.get(key, 'N/A')}}}")

# Now update
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
for key, result in results.items():
    if result['status'] == 'success':
        print(f"✓ {key}: {result['doi']}")
    else:
        print(f"✗ {key}: {result}")

print(f"\nTotal: {len(results)} updates attempted")