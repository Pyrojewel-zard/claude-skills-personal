#!/usr/bin/env python3
"""
Zotero Abstract 补充脚本 - 第二阶段
- 处理未找到匹配的文献
- 检查是否有 PDF 附件
- 使用 zotero-mcp 获取 PDF 全文并提取 abstract
- 使用 zotero-manager 更新 abstract
"""

import os
import re
import csv
import time
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import requests

# 加载环境变量
load_dotenv()

ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
BASE_URL = f"https://api.zotero.org/users/{ZOTERO_USER_ID}"

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

def get_item_details(item_key):
    """获取文献详情"""
    url = f"{BASE_URL}/items/{item_key}"
    resp = make_request(url)
    if resp:
        return resp.json()
    return None

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
    resp = make_request(url, method="patch", json_data=data["data"])
    return resp is not None and resp.status_code == 204

def get_pdf_content_via_mcp(item_key):
    """使用 MCP 工具获取 PDF 内容"""
    # 这个函数需要通过 Claude 的 MCP 工具调用
    # 在脚本中我们返回 None，需要手动处理
    return None

def extract_abstract_from_pdf_content(content):
    """从 PDF 内容中提取 abstract"""
    if not content:
        return None

    # 常见的 abstract 模式
    patterns = [
        r'(?i)Abstract[—–:\s]*(.*?)(?=\n\s*(?:Keywords|Index Terms|I\.\s|1\.\s|Introduction|I\s+INTRODUCTION))',
        r'(?i)Abstract[—–:\s]*(.*?)(?=\n\n[A-Z])',
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            # 清理多余的空白和换行
            abstract = re.sub(r'\s+', ' ', abstract)
            # 移除常见的页眉页脚
            abstract = re.sub(r'Authorized licensed use limited.*?IEEE Xplore\.', '', abstract)
            abstract = abstract.strip()
            if len(abstract) > 100:  # 确保是有效的 abstract
                return abstract
    return None

def main():
    print("=" * 60)
    print("Zotero Abstract 补充脚本 - 第二阶段")
    print("处理未找到匹配但有 PDF 附件的文献")
    print("=" * 60)

    # 读取未找到匹配的文献
    csv_file = Path(__file__).parent / "abstract_fill_results.csv"
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        not_found = [r for r in reader if r['status'] == 'not_found']

    print(f"\n未找到匹配的文献: {len(not_found)}")

    # 统计
    stats = {
        "total": len(not_found),
        "no_pdf": 0,
        "has_pdf": 0,
        "updated": 0,
        "no_abstract_in_pdf": 0,
        "error": 0
    }

    results = []

    for i, item in enumerate(not_found):
        item_key = item['key']
        title = item['title']
        doi = item['doi']

        print(f"\n[{i+1}/{len(not_found)}] {title[:50]}...")
        print(f"  Key: {item_key}")

        # 获取文献详情
        details = get_item_details(item_key)
        if not details:
            print("  获取详情失败")
            stats["error"] += 1
            results.append({
                "key": item_key,
                "title": title,
                "doi": doi,
                "status": "error",
                "abstract_preview": ""
            })
            continue

        # 检查是否有 PDF 附件
        attachments = details.get("data", {}).get("attachments", [])
        pdf_attachments = [a for a in attachments if a.get("contentType") == "application/pdf"]

        if not pdf_attachments:
            print("  无 PDF 附件")
            stats["no_pdf"] += 1
            results.append({
                "key": item_key,
                "title": title,
                "doi": doi,
                "status": "no_pdf",
                "abstract_preview": ""
            })
            continue

        print(f"  找到 {len(pdf_attachments)} 个 PDF 附件")
        stats["has_pdf"] += 1

        # 标记需要通过 MCP 获取 PDF 内容
        results.append({
            "key": item_key,
            "title": title,
            "doi": doi,
            "status": "has_pdf_need_mcp",
            "abstract_preview": ""
        })

        time.sleep(0.5)  # 避免请求过快

    # 输出统计
    print("\n" + "=" * 60)
    print("统计结果")
    print("=" * 60)
    print(f"  总数: {stats['total']}")
    print(f"  无 PDF 附件: {stats['no_pdf']}")
    print(f"  有 PDF 附件: {stats['has_pdf']}")
    print(f"  错误: {stats['error']}")

    # 保存结果
    output_file = Path(__file__).parent / "abstract_fill_phase2_results.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["key", "title", "doi", "status", "abstract_preview"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n结果已保存到: {output_file}")

    # 输出需要 MCP 处理的文献列表
    need_mcp = [r for r in results if r['status'] == 'has_pdf_need_mcp']
    if need_mcp:
        print(f"\n需要通过 MCP 获取 PDF 内容的文献: {len(need_mcp)}")
        print("Keys:", [r['key'] for r in need_mcp[:20]])

if __name__ == "__main__":
    main()
