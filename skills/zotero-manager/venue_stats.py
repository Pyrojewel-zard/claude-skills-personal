#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计 Zotero 库中各期刊/会议按年份的论文数量
"""

import os
import sys
import csv
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

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

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from zotero_api import ZoteroManager


def extract_year(date_str: str) -> str:
    """从日期字符串中提取年份"""
    if not date_str:
        return "未知年份"

    # 尝试匹配 4 位年份
    match = re.search(r'\b(19|20)\d{2}\b', str(date_str))
    if match:
        return match.group()

    return "未知年份"


def normalize_venue(venue: str) -> str:
    """标准化期刊/会议名称"""
    if not venue:
        return "未知期刊/会议"

    # 去除前后空格
    venue = venue.strip()

    # 常见缩写标准化
    venue_map = {
        "IEEE J. Solid-State Circuits": "JSSC",
        "IEEE Journal of Solid-State Circuits": "JSSC",
        "JSSC": "JSSC",
        "IEEE International Solid-State Circuits Conference": "ISSCC",
        "ISSCC": "ISSCC",
        "IEEE Transactions on Microwave Theory and Techniques": "TMTT",
        "IEEE Trans. Microw. Theory Techn.": "TMTT",
        "TMTT": "TMTT",
        "IEEE Radio Frequency Integrated Circuits Symposium": "RFIC",
        "RFIC": "RFIC",
        "IEEE Custom Integrated Circuits Conference": "CICC",
        "CICC": "CICC",
        "IEEE Asian Solid-State Circuits Conference": "A-SSCC",
        "A-SSCC": "A-SSCC",
        "ASSCC": "A-SSCC",
    }

    # 检查是否匹配已知缩写
    for full_name, abbr in venue_map.items():
        if full_name.lower() in venue.lower():
            return abbr

    return venue


def get_all_items(z: ZoteroManager) -> List[Dict[str, Any]]:
    """获取所有文献（分页）"""
    all_items = []
    start = 0
    limit = 100

    while True:
        items = z.get_items(limit=limit, start=start)
        if not items:
            break
        all_items.extend(items)
        if len(items) < limit:
            break
        start += limit
        print(f"已获取 {len(all_items)} 条文献...")

    return all_items


def main():
    print("=== Zotero 期刊/会议统计 ===\n")

    # 连接 Zotero
    z = ZoteroManager()
    if not z.user_id:
        sys.exit(1)

    # 获取所有文献
    print("\n正在获取所有文献...")
    items = get_all_items(z)
    print(f"共获取 {len(items)} 条文献记录\n")

    # 统计
    stats = defaultdict(int)
    venue_year_items = defaultdict(list)

    for item in items:
        data = item.get('data', {})

        # 只统计 journalArticle 和 conferencePaper
        item_type = data.get('itemType', '')
        if item_type not in ['journalArticle', 'conferencePaper']:
            continue

        # 获取期刊/会议名称
        venue = data.get('publicationTitle', '') or data.get('conferenceName', '') or data.get('bookTitle', '')
        venue = normalize_venue(venue)

        # 获取年份
        date_str = data.get('date', '')
        year = extract_year(date_str)

        # 组合键
        key = f"{venue}{year}"
        stats[key] += 1
        venue_year_items[key].append(data.get('title', '无标题')[:50])

    # 输出结果
    if not stats:
        print("未找到期刊/会议论文")
        return

    # 按数量排序
    sorted_stats = sorted(stats.items(), key=lambda x: (-x[1], x[0]))

    # 输出到 CSV
    output_file = Path(__file__).parent / "venue_year_stats.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['期刊/会议+年份', '论文数量'])

        for key, count in sorted_stats:
            writer.writerow([key, count])

    print(f"统计结果已保存到: {output_file}\n")

    # 打印前 30 条
    print("=== 统计结果（前 30 条）===\n")
    print(f"{'期刊/会议+年份':<40} {'数量':>6}")
    print("-" * 50)
    for key, count in sorted_stats[:30]:
        print(f"{key:<40} {count:>6}")

    print(f"\n共 {len(sorted_stats)} 个期刊/会议+年份组合")


if __name__ == "__main__":
    main()
