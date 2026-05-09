#!/usr/bin/env python3
"""
批量查询文献详情，筛选出无摘要有 PDF 的文献
使用 Zotero Web API
"""

import os
import csv
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
BASE_URL = f"https://api.zotero.org/users/{ZOTERO_USER_ID}"

def make_request(url, params=None):
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

def get_item_details(item_key):
    """获取文献详情"""
    url = f"{BASE_URL}/items/{item_key}"
    resp = make_request(url)
    if resp:
        return resp.json()
    return None

def main():
    # 读取有 PDF 的文献列表
    csv_file = Path(__file__).parent / "items_with_pdf.csv"
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        items = list(reader)

    print(f"总共 {len(items)} 条有 PDF 的文献")

    no_abstract = []
    has_abstract = 0
    error_count = 0

    for i, item in enumerate(items):
        key = item['key']
        title = item['title']

        if (i + 1) % 50 == 0:
            print(f"  处理进度: {i+1}/{len(items)}")

        # 获取详情
        details = get_item_details(key)
        if not details:
            error_count += 1
            continue

        data = details.get('data', {})
        abstract = data.get('abstractNote', '')
        doi = data.get('DOI', '')
        date = data.get('date', '')

        if abstract and abstract.strip():
            has_abstract += 1
        else:
            no_abstract.append({
                'key': key,
                'title': title,
                'doi': doi,
                'date': date,
                'attachment_key': item.get('attachment_key', ''),
                'filename': item.get('filename', '')
            })

        time.sleep(0.3)

    print(f"\n统计结果:")
    print(f"  有摘要: {has_abstract}")
    print(f"  无摘要: {len(no_abstract)}")
    print(f"  错误: {error_count}")

    # 保存无摘要的文献
    output_dir = Path(__file__).parent

    if no_abstract:
        output_file = output_dir / "no_abstract_with_pdf.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["key", "title", "doi", "date", "attachment_key", "filename"])
            writer.writeheader()
            writer.writerows(no_abstract)
        print(f"\n无摘要有PDF的文献已保存到: {output_file}")

        print(f"\n需要处理的文献:")
        for i, item in enumerate(no_abstract[:20]):
            print(f"  [{i+1}] {item['key']}: {item['title'][:50]}...")

if __name__ == "__main__":
    main()
