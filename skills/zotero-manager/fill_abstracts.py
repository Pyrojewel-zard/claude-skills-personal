#!/usr/bin/env python3
"""
Zotero Abstract 补充脚本
- 检索 Zotero 中所有 abstract 为空的文献
- 尝试从 /mnt/d/02-related_paper 中用 DOI 匹配补充 abstract
- 输出结果到 CSV
"""

import os
import re
import csv
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import requests

# 加载环境变量
load_dotenv()

ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
BASE_URL = f"https://api.zotero.org/users/{ZOTERO_USER_ID}"

# 02-related_paper 目录
PAPER_DIR = Path("/mnt/d/02-related_paper")

def make_request(url, params=None, method="get", json_data=None):
    """带重试的请求"""
    headers = {"Zotero-API-Key": ZOTERO_API_KEY}
    for i in range(5):
        try:
            if method == "get":
                resp = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == "patch":
                resp = requests.patch(url, headers=headers, json=json_data, timeout=30)
            if resp.status_code == 429:
                time.sleep(2 ** i)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.SSLError as e:
            if i < 4:
                print(f"    SSL 错误，等待重试 ({i+1}/5)...")
                time.sleep(3 ** i)
            else:
                raise e
        except Exception as e:
            if i < 4:
                time.sleep(2 ** i)
            else:
                raise e
    return None

def get_all_items():
    """获取所有文献"""
    items = []
    start = 0
    limit = 100
    while True:
        url = f"{BASE_URL}/items"
        params = {"limit": limit, "start": start}
        resp = make_request(url, params)
        if not resp:
            break
        batch = resp.json()
        if not batch:
            break
        items.extend(batch)
        if len(batch) < limit:
            break
        start += limit
        time.sleep(0.2)  # 避免请求过快
    return items

def extract_doi_from_filename(filename):
    """从文件名提取可能的 DOI（备用）"""
    # 文件名格式：20162016_CMOS_UWB_radar_sensor_for.md
    return None

def load_paper_abstracts():
    """加载 02-related_paper 中所有文件的 DOI 和 abstract"""
    paper_map = {}  # doi -> abstract

    for md_file in PAPER_DIR.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")

            # 提取 DOI
            doi_match = re.search(r'doi:\s*["\']?([^"\'\n]+)["\']?', content)
            if not doi_match:
                continue
            doi = doi_match.group(1).strip().strip('"').strip("'")

            # 提取 Abstract
            abstract_match = re.search(r'# Abstract\s*\n+(.*?)(?=\n#|\Z)', content, re.DOTALL)
            if abstract_match:
                abstract = abstract_match.group(1).strip()
                if doi and abstract:
                    paper_map[doi.lower()] = {
                        "abstract": abstract,
                        "file": md_file.name
                    }
        except Exception as e:
            print(f"  读取文件失败: {md_file.name}: {e}")

    return paper_map

def update_item_abstract(item_key, abstract):
    """更新文献的 abstract"""
    url = f"{BASE_URL}/items/{item_key}"

    # 先获取当前版本
    resp = make_request(url)
    if not resp or resp.status_code != 200:
        return False

    current_version = resp.headers.get("Last-Modified-Version")
    data = resp.json()

    # 更新 abstract
    if "data" not in data:
        data["data"] = {}
    data["data"]["abstractNote"] = abstract

    # 提交更新
    headers = {
        "Zotero-API-Key": ZOTERO_API_KEY,
        "If-Unmodified-Since-Version": current_version,
        "Content-Type": "application/json"
    }

    resp = make_request(url, method="patch", json_data=data["data"])
    return resp is not None and resp.status_code == 204

def main():
    print("=" * 60)
    print("Zotero Abstract 补充脚本")
    print("=" * 60)

    # 1. 加载 02-related_paper 中的 DOI 和 abstract
    print("\n[1/4] 加载 02-related_paper 中的文献...")
    paper_map = load_paper_abstracts()
    print(f"  已加载 {len(paper_map)} 篇文献的 abstract")

    # 2. 获取 Zotero 中所有文献
    print("\n[2/4] 获取 Zotero 文献列表...")
    items = get_all_items()
    print(f"  共获取 {len(items)} 条记录")

    # 3. 检查 abstract 为空的文献
    print("\n[3/4] 检查 abstract 为空的文献...")
    results = []

    for item in items:
        item_key = item.get("key", "")
        item_type = item.get("data", {}).get("itemType", "")
        title = item.get("data", {}).get("title", "无标题")
        doi = item.get("data", {}).get("DOI", "") or item.get("data", {}).get("doi", "")
        abstract = item.get("data", {}).get("abstractNote", "")

        # 跳过附件类型
        if item_type == "attachment":
            continue

        # 检查 abstract 是否为空
        if abstract and abstract.strip():
            continue

        result = {
            "key": item_key,
            "title": title,
            "doi": doi,
            "status": "not_found",
            "matched_file": "",
            "abstract_preview": ""
        }

        # 尝试匹配 DOI
        if doi:
            doi_lower = doi.lower()
            if doi_lower in paper_map:
                matched = paper_map[doi_lower]
                result["status"] = "matched"
                result["matched_file"] = matched["file"]
                result["abstract_preview"] = matched["abstract"][:100] + "..."

                # 更新 Zotero
                print(f"\n  匹配成功: {title[:50]}...")
                print(f"    DOI: {doi}")
                print(f"    文件: {matched['file']}")

                try:
                    if update_item_abstract(item_key, matched["abstract"]):
                        result["status"] = "updated"
                        print(f"    ✓ 已更新 abstract")
                    else:
                        result["status"] = "update_failed"
                        print(f"    ✗ 更新失败")
                except Exception as e:
                    result["status"] = "update_error"
                    result["matched_file"] = f"{matched['file']} (错误: {str(e)[:50]})"
                    print(f"    ✗ 更新出错: {e}")

                time.sleep(1.0)  # 增加延迟避免 SSL 问题

        results.append(result)

    # 4. 输出结果到 CSV
    print("\n[4/4] 输出结果到 CSV...")
    output_file = "abstract_fill_results.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["key", "title", "doi", "status", "matched_file", "abstract_preview"])
        writer.writeheader()
        writer.writerows(results)

    print(f"  结果已保存到: {output_file}")

    # 统计
    print("\n" + "=" * 60)
    print("统计结果")
    print("=" * 60)
    total_empty = len(results)
    matched = sum(1 for r in results if r["status"] in ["matched", "updated"])
    updated = sum(1 for r in results if r["status"] == "updated")
    not_found = sum(1 for r in results if r["status"] == "not_found")

    print(f"  abstract 为空的文献: {total_empty}")
    print(f"  匹配成功: {matched}")
    print(f"  更新成功: {updated}")
    print(f"  未找到匹配: {not_found}")

if __name__ == "__main__":
    main()
