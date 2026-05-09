#!/usr/bin/env python3
"""
批量获取 Zotero 文献详情并筛选无摘要有 PDF 的文献
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
                print(f"请求失败: {e}")
                return None
    return None

def get_all_items():
    """获取所有文献"""
    url = f"{BASE_URL}/items"
    params = {"limit": 100, "start": 0}
    all_items = []

    while True:
        resp = make_request(url, params)
        if not resp:
            break

        items = resp.json()
        if not items:
            break

        all_items.extend(items)
        print(f"已获取 {len(all_items)} 条文献...")

        if len(items) < 100:
            break

        params["start"] += 100
        time.sleep(0.3)

    return all_items

def main():
    print("=" * 60)
    print("批量获取 Zotero 文献详情")
    print("=" * 60)

    # 获取所有文献
    items = get_all_items()
    print(f"\n总共获取 {len(items)} 条文献")

    # 筛选：没有摘要但有 PDF 附件
    no_abstract_with_pdf = []
    no_abstract_no_pdf = []
    has_abstract = 0
    not_journal = 0

    for item in items:
        data = item.get("data", {})

        # 只处理期刊文章和会议论文
        item_type = data.get("itemType", "")
        if item_type not in ["journalArticle", "conferencePaper", "preprint", "thesis"]:
            not_journal += 1
            continue

        key = data.get("key", "")
        title = data.get("title", "")
        abstract = data.get("abstractNote", "")
        doi = data.get("DOI", "")
        date = data.get("date", "")

        # 获取附件信息
        attachments = item.get("links", {}).get("attachment", {})
        if isinstance(attachments, dict):
            # 单个附件
            has_pdf = attachments.get("attachmentType") == "application/pdf"
            pdf_count = 1 if has_pdf else 0
        elif isinstance(attachments, list):
            # 多个附件
            pdf_count = sum(1 for a in attachments if a.get("attachmentType") == "application/pdf")
            has_pdf = pdf_count > 0
        else:
            has_pdf = False
            pdf_count = 0

        if abstract and abstract.strip():
            has_abstract += 1
        else:
            if has_pdf:
                no_abstract_with_pdf.append({
                    "key": key,
                    "title": title,
                    "doi": doi,
                    "date": date,
                    "item_type": item_type,
                    "pdf_count": pdf_count
                })
            else:
                no_abstract_no_pdf.append({
                    "key": key,
                    "title": title,
                    "doi": doi,
                    "date": date,
                    "item_type": item_type
                })

    print(f"\n统计结果:")
    print(f"  有摘要: {has_abstract}")
    print(f"  无摘要有PDF: {len(no_abstract_with_pdf)}")
    print(f"  无摘要无PDF: {len(no_abstract_no_pdf)}")
    print(f"  非期刊/会议: {not_journal}")

    # 保存结果
    output_dir = Path(__file__).parent

    # 保存无摘要有PDF的文献
    if no_abstract_with_pdf:
        output_file = output_dir / "no_abstract_with_pdf.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["key", "title", "doi", "date", "item_type", "pdf_count"])
            writer.writeheader()
            writer.writerows(no_abstract_with_pdf)
        print(f"\n无摘要有PDF的文献已保存到: {output_file}")

    # 保存无摘要无PDF的文献
    if no_abstract_no_pdf:
        output_file = output_dir / "no_abstract_no_pdf.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["key", "title", "doi", "date", "item_type"])
            writer.writeheader()
            writer.writerows(no_abstract_no_pdf)
        print(f"无摘要无PDF的文献已保存到: {output_file}")

    # 输出前10个需要处理的文献
    if no_abstract_with_pdf:
        print(f"\n前10个需要处理的文献:")
        for i, item in enumerate(no_abstract_with_pdf[:10]):
            print(f"  [{i+1}] {item['key']}: {item['title'][:60]}...")

if __name__ == "__main__":
    main()
