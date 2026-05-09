#!/usr/bin/env python3
"""
检查 Zotero API 返回的附件信息结构
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
BASE_URL = f"https://api.zotero.org/users/{ZOTERO_USER_ID}"

def make_request(url, params=None):
    headers = {"Zotero-API-Key": ZOTERO_API_KEY}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp

def main():
    # 获取前10条文献，检查结构
    url = f"{BASE_URL}/items"
    params = {"limit": 10, "start": 0}
    resp = make_request(url, params)
    items = resp.json()

    for item in items:
        data = item.get("data", {})
        key = data.get("key", "")
        title = data.get("title", "")[:50]
        item_type = data.get("itemType", "")
        abstract = data.get("abstractNote", "")

        # 检查附件信息
        links = item.get("links", {})
        print(f"\n{'='*60}")
        print(f"Key: {key}")
        print(f"Title: {title}...")
        print(f"Type: {item_type}")
        print(f"Has Abstract: {bool(abstract)}")
        print(f"Links structure: {json.dumps(links, indent=2)[:500]}")

        # 获取子项（附件）
        if "attachment" in links:
            attachment_link = links.get("attachment", {})
            print(f"Attachment link: {attachment_link}")

if __name__ == "__main__":
    main()
