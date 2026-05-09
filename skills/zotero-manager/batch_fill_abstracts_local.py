#!/usr/bin/env python3
"""
批量处理无摘要有 PDF 的文献 - 直接读取本地 PDF
从 PDF 内容中提取摘要并更新到 Zotero

流程：
1. 读取 no_abstract_with_pdf.csv
2. 对每条文献，直接从 Zotero storage 读取 PDF
3. 从 PDF 内容中提取摘要
4. 使用 Zotero Web API 更新摘要
5. 记录处理结果
"""

import os
import re
import csv
import time
import json
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
BASE_URL = f"https://api.zotero.org/users/{ZOTERO_USER_ID}"
ZOTERO_STORAGE = "/mnt/c/Users/28956/Zotero/storage"

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

def extract_text_from_pdf(pdf_path):
    """从 PDF 提取文本（使用 pdftotext）"""
    try:
        result = subprocess.run(
            ["pdftotext", "-l", "3", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except Exception:
        pass

    # 回退：使用 python 的 PyPDF2
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages[:3]:
                text += page.extract_text() or ""
            return text
    except Exception:
        pass

    return None

def extract_abstract_from_text(text):
    """从 PDF 文本中提取摘要"""
    if not text:
        return None

    # 清理文本
    text = re.sub(r'\s+', ' ', text)

    # 常见的摘要模式
    patterns = [
        # IEEE 格式：Abstract—... 或 Abstract: ...
        r'Abstract[—–:\s]+([^.]+(?:\.[^.]+)*?)\s*(?:Index Terms|Keywords|I\.\s|1\.\s|Introduction)',
        # 通用格式
        r'Abstract[—–:\s]+([^.]+(?:\.[^.]+)*?)\s*(?:In this paper|This paper|We present|We propose)',
        # 从开头提取第一段有意义的文字
        r'((?:This letter|This paper|This article|We present|We propose|This work)[^.]+(?:\.[^.]+)*?\.)',
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
    print("批量处理无摘要有 PDF 的文献 (本地PDF版)")
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
        "no_pdf_file": 0,
        "error": 0
    }

    for i, item in enumerate(items):
        key = item['key']
        title = item['title'][:50]
        att_key = item['attachment_key']
        filename = item['filename']

        # 先检查 Zotero 是否已有摘要
        check_url = f"{BASE_URL}/items/{key}"
        check_resp = make_request(check_url)
        if check_resp:
            existing = check_resp.json().get('data', {}).get('abstractNote', '')
            if existing and existing.strip():
                print(f"  [{i+1}/{len(items)}] SKIP {key}: Already has abstract")
                stats["no_abstract_found"] += 1  # reuse counter
                continue

        # 构建 PDF 路径
        pdf_dir = Path(ZOTERO_STORAGE) / att_key
        pdf_path = pdf_dir / filename

        # 如果文件名不匹配，尝试目录下任意 PDF
        if not pdf_path.exists():
            pdfs = list(pdf_dir.glob("*.pdf"))
            if pdfs:
                pdf_path = pdfs[0]
            else:
                print(f"  [{i+1}/{len(items)}] SKIP {key}: PDF not found in {pdf_dir}")
                stats["no_pdf_file"] += 1
                continue

        # 提取 PDF 文本
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"  [{i+1}/{len(items)}] SKIP {key}: Cannot extract text")
            stats["error"] += 1
            continue

        # 提取摘要
        abstract = extract_abstract_from_text(text)
        if not abstract:
            print(f"  [{i+1}/{len(items)}] SKIP {key}: No abstract found in text")
            stats["no_abstract_found"] += 1
            continue

        # 更新到 Zotero
        success = update_abstract(key, abstract)
        if success:
            print(f"  [{i+1}/{len(items)}] OK   {key}: {title}...")
            stats["updated"] += 1
        else:
            print(f"  [{i+1}/{len(items)}] FAIL {key}: Update failed")
            stats["error"] += 1

        time.sleep(0.5)  # 限速

    print(f"\n{'='*60}")
    print(f"处理完成!")
    print(f"  更新成功: {stats['updated']}")
    print(f"  未找到摘要: {stats['no_abstract_found']}")
    print(f"  PDF不存在: {stats['no_pdf_file']}")
    print(f"  错误: {stats['error']}")

if __name__ == "__main__":
    main()
