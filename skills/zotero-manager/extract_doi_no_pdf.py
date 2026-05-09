#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取没有PDF附件的文献的DOI，保存到CSV
"""

import os
import csv
import time
from pathlib import Path

# 从同级 .env 加载配置
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value

from zotero_api import ZoteroManager

def get_item_attachments(z, item_key):
    """获取文献的附件列表"""
    try:
        url = f"{z.base_url}/users/{z.user_id}/items/{item_key}/children"
        params = {
            'format': 'json'
        }
        response = z.session.get(url, headers=z.headers, params=params, timeout=z.timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取文献 {item_key} 附件失败: {e}")
        return []

def has_pdf_attachment(z, item_key):
    """检查文献是否有PDF附件"""
    attachments = get_item_attachments(z, item_key)
    for att in attachments:
        data = att.get('data', {})
        if data.get('itemType') == 'attachment' and data.get('contentType') == 'application/pdf':
            return True
    return False

def main():
    z = ZoteroManager()
    if not z.user_id:
        return

    output_file = Path("/tmp/nopdf_dois.csv")
    print(f"开始提取没有PDF附件的文献DOI，保存到 {output_file}")

    # 遍历所有文献
    all_items = []
    start = 0
    limit = 100
    total_processed = 0
    no_pdf_count = 0
    has_doi_count = 0

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['DOI', 'Title', 'Item Key'])

        while True:
            print(f"正在获取第 {start+1} - {start+limit} 条文献...")
            items = z.get_items(limit=limit, start=start)
            if not items:
                break

            for item in items:
                total_processed += 1
                data = item.get('data', {})
                item_key = data.get('key')
                title = data.get('title', '无标题')
                doi = data.get('DOI', '').strip()

                # 跳过附件类型的条目
                if data.get('itemType') == 'attachment':
                    continue

                # 检查是否有PDF附件
                if not has_pdf_attachment(z, item_key):
                    no_pdf_count += 1
                    if doi:
                        has_doi_count += 1
                        writer.writerow([doi, title, item_key])
                        print(f"找到无PDF且有DOI的文献: {title[:50]}... DOI: {doi}")

            start += limit
            # 避免API限流
            time.sleep(0.5)

    print(f"\n处理完成！")
    print(f"总处理文献数: {total_processed}")
    print(f"无PDF附件的文献数: {no_pdf_count}")
    print(f"其中有DOI的文献数: {has_doi_count}")
    print(f"DOI列表已保存到: {output_file}")

if __name__ == "__main__":
    main()
