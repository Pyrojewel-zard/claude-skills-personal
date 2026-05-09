#!/usr/bin/env python3
"""
批量处理无摘要有 PDF 的文献
从 PDF 内容中提取摘要并更新到 Zotero

流程：
1. 读取 no_abstract_with_pdf.csv
2. 对每条文献，使用 zotero-mcp get_content 获取 PDF 内容
3. 从 PDF 内容中提取摘要
4. 使用 zotero-mcp write_metadata 更新摘要
5. 记录处理结果

注意：此脚本需要配合 Claude Code 使用，因为需要调用 MCP 工具
"""

import os
import re
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

def make_request(url, params=None, method="get", json_data=None):
    """带重试的请求"""
    headers = {"Zotero-API-Key": ZOTERO_API_KEY}
    for i in range(5):
        try:
            if method == "get":
                resp = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == "patch":
                headers["If-Match"] = json_data.get("version", "")
                resp = requests.patch(url, headers=headers, json=json_data.get("data", {}), timeout=30)
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

def get_item_version(item_key):
    """获取文献当前版本"""
    url = f"{BASE_URL}/items/{item_key}"
    resp = make_request(url)
    if resp:
        return resp.headers.get("ETag", "").strip('"')
    return None

def update_abstract(item_key, abstract):
    """更新文献摘要"""
    url = f"{BASE_URL}/items/{item_key}"

    # 获取当前版本和数据
    resp = make_request(url)
    if not resp:
        return False

    version = resp.headers.get("ETag", "").strip('"')
    data = resp.json()

    # 更新摘要
    data["abstractNote"] = abstract

    # 提交更新
    headers = {
        "Zotero-API-Key": ZOTERO_API_KEY,
        "If-Match": version
    }

    for i in range(5):
        try:
            resp = requests.patch(url, headers=headers, json=data, timeout=30)
            if resp.status_code == 204:
                return True
            if resp.status_code == 429:
                time.sleep(2 ** i)
                continue
            if resp.status_code == 412:
                # 版本冲突，重新获取并重试
                time.sleep(1)
                resp = make_request(url)
                if resp:
                    version = resp.headers.get("ETag", "").strip('"')
                    data = resp.json()
                    data["abstractNote"] = abstract
                    headers["If-Match"] = version
                    continue
            return False
        except Exception as e:
            if i < 4:
                time.sleep(2 ** i)
            else:
                return False
    return False

def extract_abstract_from_text(text):
    """从 PDF 文本中提取摘要"""
    if not text:
        return None

    # 清理文本
    text = re.sub(r'\s+', ' ', text)

    # 常见的摘要模式
    patterns = [
        # IEEE 格式：Abstract—... 或 Abstract: ...
        r'Abstract[—–:\s]*([^.]+(?:\.[^.]+)*?)\s*(?:Index Terms|Keywords|I\.\s|1\.\s|Introduction)',
        # 通用格式
        r'Abstract[—–:\s]*([^.]+(?:\.[^.]+)*?)\s*(?:In this paper|This paper|We present|We propose)',
        # 从开头提取第一段有意义的文字
        r'(?:This letter|This paper|This article|We present|We propose|This work)[^.]+(?:\.[^.]+)*?\.',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            # 清理
            abstract = re.sub(r'Authorized licensed use limited.*?IEEE Xplore\.', '', abstract)
            abstract = re.sub(r'Downloaded on.*?IEEE Xplore\.', '', abstract)
            abstract = re.sub(r'Restrictions apply\.', '', abstract)
            abstract = abstract.strip()
            if len(abstract) > 100 and len(abstract) < 2000:
                return abstract

    return None

def main():
    print("=" * 60)
    print("批量处理无摘要有 PDF 的文献")
    print("=" * 60)

    # 读取待处理文献列表
    csv_file = Path(__file__).parent / "no_abstract_with_pdf.csv"
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        items = list(reader)

    print(f"总共 {len(items)} 条文献待处理")

    # 结果记录
    results = []
    stats = {
        "total": len(items),
        "updated": 0,
        "no_abstract_found": 0,
        "error": 0
    }

    # 输出待处理的文献 key 列表（供 Claude Code 使用）
    print("\n待处理的文献 Key 列表:")
    for i, item in enumerate(items[:20]):
        print(f"  [{i+1}] {item['key']}: {item['title'][:50]}...")

    print(f"\n完整列表已保存到: {csv_file}")
    print("\n请使用 Claude Code 的 MCP 工具批量处理这些文献:")
    print("  1. 使用 mcp__zotero-mcp__get_content 获取 PDF 内容")
    print("  2. 从 PDF 内容中提取摘要")
    print("  3. 使用 mcp__zotero-mcp__write_metadata 更新摘要")

if __name__ == "__main__":
    main()
