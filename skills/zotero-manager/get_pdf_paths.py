#!/usr/bin/env python3
"""
批量获取 Zotero 文献的 PDF 路径
使用 zotero-mcp 获取文献详情，提取 PDF 附件路径
"""

import os
import csv
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
BASE_URL = f"https://api.zotero.org/users/{ZOTERO_USER_ID}"

def make_request(url, params=None):
    """带重试的请求"""
    headers = {"Zotero-API-Key": ZOTERO_API_KEY}
    for i in range(5):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            if resp.status_code == 429:
                time.sleep(2 ** i)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if i < 4:
                time.sleep(2 ** i)
            else:
                print(f"请求失败: {e}")
                return None
    return None

def get_item_with_attachments(item_key):
    """获取文献及其附件信息"""
    # 获取子项（附件）
    url = f"{BASE_URL}/items/{item_key}/children"
    children = make_request(url)

    attachments = []
    if children:
        for child in children:
            data = child.get("data", {})
            if data.get("itemType") == "attachment" and data.get("contentType") == "application/pdf":
                attachments.append({
                    "key": child.get("key"),
                    "filename": data.get("filename", ""),
                    "url": data.get("url", ""),
                    "md5": data.get("md5", ""),
                    "size": data.get("size", 0)
                })
    return attachments

def main():
    print("=" * 60)
    print("批量获取 PDF 路径")
    print("=" * 60)

    # 读取未找到匹配的文献
    csv_file = Path(__file__).parent / "abstract_fill_results.csv"
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        not_found = [r for r in reader if r['status'] == 'not_found' and r['doi']]

    print(f"\n未找到匹配且有 DOI 的文献: {len(not_found)}")

    results = []
    has_pdf_count = 0

    for i, item in enumerate(not_found):
        item_key = item['key']
        title = item['title']
        doi = item['doi']

        if (i + 1) % 50 == 0:
            print(f"  处理进度: {i+1}/{len(not_found)}")

        # 获取附件信息
        attachments = get_item_with_attachments(item_key)

        if attachments:
            has_pdf_count += 1
            for att in attachments:
                results.append({
                    "item_key": item_key,
                    "title": title,
                    "doi": doi,
                    "attachment_key": att["key"],
                    "filename": att["filename"],
                    "url": att["url"],
                    "md5": att["md5"],
                    "status": "has_pdf"
                })
        else:
            results.append({
                "item_key": item_key,
                "title": title,
                "doi": doi,
                "attachment_key": "",
                "filename": "",
                "url": "",
                "md5": "",
                "status": "no_pdf"
            })

        time.sleep(0.2)  # 避免请求过快

    # 保存结果
    output_file = Path(__file__).parent / "pdf_paths.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item_key", "title", "doi", "attachment_key", "filename", "url", "md5", "status"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n有 PDF 附件的文献: {has_pdf_count}")
    print(f"结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
