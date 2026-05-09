#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从CSV中的DOI批量下载PDF，使用sci-hub.ru
"""

import os
import csv
import time
import requests
import re
from pathlib import Path
from urllib.parse import quote, urljoin

# 配置
SCI_HUB_URL = "https://sci-hub.ru"
OUTPUT_DIR = Path("/tmp/scihub_downloads")
DELAY_BETWEEN_REQUESTS = 3  # 秒，避免被封
TIMEOUT = 30  # 秒

# 模拟浏览器请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

def sanitize_filename(doi):
    """将DOI转换为合法的文件名"""
    return doi.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_') + ".pdf"

def init_session(session):
    """初始化会话，处理DDoS-Guard验证"""
    try:
        # 先访问首页获取cookie
        response = session.get(SCI_HUB_URL, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        time.sleep(1)
        return True
    except Exception as e:
        print(f"初始化会话失败: {e}")
        return False

def get_pdf_url_from_scihub(doi, session):
    """从sci-hub获取PDF的下载链接"""
    try:
        url = f"{SCI_HUB_URL}/{quote(doi)}"
        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        content = response.text

        # 新的Sci-Hub页面结构解析
        # 方式1: 查找window.location路径
        location_match = re.search(r'window\.location\s*=\s*"([^"]+)"', content)
        if location_match:
            pdf_url = location_match.group(1)
        # 方式2: 查找embed或iframe的src
        else:
            embed_match = re.search(r'<embed[^>]+src=["\']([^"\']+\.pdf[^"\']*)["\']', content, re.IGNORECASE)
            if embed_match:
                pdf_url = embed_match.group(1)
            else:
                iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+\.pdf[^"\']*)["\']', content, re.IGNORECASE)
                if iframe_match:
                    pdf_url = iframe_match.group(1)
                else:
                    # 方式3: 查找直接的下载按钮链接
                    button_match = re.search(r'<a[^>]+href=["\']([^"\']+\.pdf[^"\']*)["\'][^>]*>.*?download', content, re.IGNORECASE)
                    if button_match:
                        pdf_url = button_match.group(1)
                    else:
                        # 方式4: 查找#article按钮的onclick
                        onclick_match = re.search(r"onclick\s*=\s*[\"\']location\.href\s*=\s*'([^']+)'[\"\']", content)
                        if onclick_match:
                            pdf_url = onclick_match.group(1)
                        else:
                            return None

        # 处理相对URL和转义
        pdf_url = pdf_url.replace('\\', '')
        if not pdf_url.startswith('http'):
            if pdf_url.startswith('//'):
                pdf_url = 'https:' + pdf_url
            else:
                pdf_url = urljoin(SCI_HUB_URL, pdf_url)

        return pdf_url
    except Exception as e:
        print(f"获取PDF链接失败 {doi}: {str(e)[:50]}...")
        return None

def download_pdf(pdf_url, output_path, session):
    """下载PDF文件"""
    try:
        # 下载时用stream避免大文件内存问题
        response = session.get(pdf_url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        response.raise_for_status()

        # 检查内容是否是PDF
        content_type = response.headers.get('Content-Type', '')
        if 'application/pdf' not in content_type and 'octet-stream' not in content_type:
            print(f"下载的内容不是PDF: {content_type}")
            return False

        # 检查文件大小，太小的可能是错误页面
        content_length = int(response.headers.get('Content-Length', 0))
        if content_length < 10240:  # 小于10KB的肯定不是正常PDF
            print(f"文件太小，不是有效PDF: {content_length} bytes")
            return False

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 验证下载后的文件大小
        if os.path.getsize(output_path) < 10240:
            os.remove(output_path)
            return False

        return True
    except Exception as e:
        print(f"下载PDF失败: {str(e)[:50]}...")
        return False

def main():
    csv_path = Path("/tmp/nopdf_collection_dois.csv")
    if not csv_path.exists():
        print(f"错误：CSV文件 {csv_path} 不存在")
        return

    # 创建输出目录
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    failed_log = OUTPUT_DIR / "failed_downloads.csv"
    success_count = 0
    failed_count = 0
    skipped_count = 0

    session = requests.Session()
    if not init_session(session):
        print("无法连接到Sci-Hub，退出")
        return

    with open(csv_path, 'r', encoding='utf-8') as f_csv, open(failed_log, 'w', newline='', encoding='utf-8') as f_failed:
        reader = csv.DictReader(f_csv)
        writer = csv.writer(f_failed)
        writer.writerow(['DOI', 'Title', 'Item Key', 'Reason'])

        total = sum(1 for _ in reader)
        f_csv.seek(0)
        next(reader)  # 跳过表头
        print(f"开始下载，共 {total} 个DOI")

        for i, row in enumerate(reader, 1):
            doi = row['DOI'].strip()
            title = row['Title']
            item_key = row['Item Key']

            if not doi:
                skipped_count += 1
                continue

            filename = sanitize_filename(doi)
            output_path = OUTPUT_DIR / filename

            # 如果文件已经存在，跳过
            if output_path.exists():
                print(f"[{i}/{total}] 已存在，跳过: {doi}")
                skipped_count += 1
                continue

            print(f"[{i}/{total}] 正在处理: {doi} | {title[:60]}...")

            # 获取PDF链接，最多重试2次
            pdf_url = None
            for retry in range(2):
                pdf_url = get_pdf_url_from_scihub(doi, session)
                if pdf_url:
                    break
                time.sleep(1)

            if not pdf_url:
                print(f"❌ 找不到PDF: {doi}")
                writer.writerow([doi, title, item_key, "找不到PDF链接"])
                failed_count += 1
                time.sleep(DELAY_BETWEEN_REQUESTS)
                continue

            print(f"找到PDF链接: {pdf_url[:80]}...")

            # 下载PDF，最多重试2次
            download_success = False
            for retry in range(2):
                if download_pdf(pdf_url, output_path, session):
                    download_success = True
                    break
                time.sleep(1)

            if download_success:
                print(f"✅ 下载成功: {filename}")
                success_count += 1
            else:
                print(f"❌ 下载失败: {doi}")
                writer.writerow([doi, title, item_key, "下载失败"])
                failed_count += 1

            # 延迟
            time.sleep(DELAY_BETWEEN_REQUESTS)

            # 每下载50个打印一次进度统计
            if i % 50 == 0:
                print(f"\n===== 进度 {i}/{total} | 成功: {success_count} | 失败: {failed_count} | 跳过: {skipped_count} =====\n")

    print(f"\n\n✅ 全部下载完成！")
    print(f"总DOI数: {total}")
    print(f"成功下载: {success_count}")
    print(f"失败: {failed_count}")
    print(f"跳过: {skipped_count}")
    print(f"成功率: {success_count / total * 100:.1f}%")
    print(f"PDF保存目录: {OUTPUT_DIR}")
    print(f"失败记录: {failed_log}")

if __name__ == "__main__":
    main()
