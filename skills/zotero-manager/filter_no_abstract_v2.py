#!/usr/bin/env python3
"""
使用 Zotero Web API 批量获取文献详情
筛选：无摘要但有 PDF 附件的文献
"""

import os
import csv
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

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
            return resp
        except Exception as e:
            if i < 4:
                time.sleep(2 ** i)
            else:
                return None
    return None

def get_all_item_keys():
    """获取所有文献的 key"""
    url = f"{BASE_URL}/items"
    params = {"limit": 500, "start": 0}
    all_keys = []

    while True:
        resp = make_request(url, params)
        if not resp:
            break

        items = resp.json()
        if not items:
            break

        for item in items:
            data = item.get("data", {})
            item_type = data.get("itemType", "")
            # 只处理文献类型
            if item_type in ["journalArticle", "conferencePaper", "preprint", "thesis", "report", "bookSection"]:
                all_keys.append({
                    "key": data.get("key"),
                    "title": data.get("title", "")[:100],
                    "item_type": item_type
                })

        if len(items) < 500:
            break

        params["start"] += 500
        time.sleep(0.3)

    return all_keys

def get_item_with_attachments(item_key):
    """获取文献详情和附件"""
    # 获取文献详情
    url = f"{BASE_URL}/items/{item_key}"
    resp = make_request(url)
    if not resp:
        return None, []

    item_data = resp.json()

    # 获取子项（附件）
    url = f"{BASE_URL}/items/{item_key}/children"
    resp = make_request(url)
    attachments = []

    if resp:
        children = resp.json()
        for child in children:
            data = child.get("data", {})
            if data.get("itemType") == "attachment" and data.get("contentType") == "application/pdf":
                attachments.append({
                    "key": child.get("key"),
                    "filename": data.get("filename", ""),
                    "size": data.get("size", 0)
                })

    return item_data, attachments

def main():
    print("=" * 60)
    print("批量获取 Zotero 文献详情（含附件信息）")
    print("=" * 60)

    # 获取所有文献 key
    print("\n获取文献列表...")
    item_keys = get_all_item_keys()
    print(f"总共 {len(item_keys)} 条文献")

    # 筛选
    no_abstract_with_pdf = []
    no_abstract_no_pdf = []
    has_abstract = 0
    error_count = 0

    output_dir = Path(__file__).parent

    for i, item_info in enumerate(item_keys):
        key = item_info["key"]
        title = item_info["title"]

        if (i + 1) % 100 == 0:
            print(f"  处理进度: {i+1}/{len(item_keys)}")

        # 获取详情和附件
        item_data, attachments = get_item_with_attachments(key)

        if not item_data:
            error_count += 1
            continue

        data = item_data.get("data", {})
        abstract = data.get("abstractNote", "")
        doi = data.get("DOI", "")
        date = data.get("date", "")

        has_pdf = len(attachments) > 0

        if abstract and abstract.strip():
            has_abstract += 1
        else:
            if has_pdf:
                no_abstract_with_pdf.append({
                    "key": key,
                    "title": title,
                    "doi": doi,
                    "date": date,
                    "item_type": item_info["item_type"],
                    "pdf_count": len(attachments),
                    "attachment_key": attachments[0]["key"] if attachments else ""
                })
            else:
                no_abstract_no_pdf.append({
                    "key": key,
                    "title": title,
                    "doi": doi,
                    "date": date,
                    "item_type": item_info["item_type"]
                })

        time.sleep(0.3)  # 避免请求过快

    print(f"\n统计结果:")
    print(f"  有摘要: {has_abstract}")
    print(f"  无摘要有PDF: {len(no_abstract_with_pdf)}")
    print(f"  无摘要无PDF: {len(no_abstract_no_pdf)}")
    print(f"  错误: {error_count}")

    # 保存结果
    if no_abstract_with_pdf:
        output_file = output_dir / "no_abstract_with_pdf.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["key", "title", "doi", "date", "item_type", "pdf_count", "attachment_key"])
            writer.writeheader()
            writer.writerows(no_abstract_with_pdf)
        print(f"\n无摘要有PDF的文献已保存到: {output_file}")

    if no_abstract_no_pdf:
        output_file = output_dir / "no_abstract_no_pdf.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["key", "title", "doi", "date", "item_type"])
            writer.writeheader()
            writer.writerows(no_abstract_no_pdf)
        print(f"无摘要无PDF的文献已保存到: {output_file}")

    # 输出需要处理的文献
    if no_abstract_with_pdf:
        print(f"\n需要处理的文献 (无摘要有PDF):")
        for i, item in enumerate(no_abstract_with_pdf[:20]):
            print(f"  [{i+1}] {item['key']}: {item['title'][:50]}...")

if __name__ == "__main__":
    main()
