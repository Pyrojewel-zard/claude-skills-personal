#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取Nopdf collection中2022-2026年论文的DOI和网址
"""
import os
import csv
import re
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
from zotero_api import ZoteroManager

# 配置
COLLECTION_KEY = "3IAWNQYQ"  # Nopdf分类的key
OUTPUT_FILE = Path("/tmp/nopdf_2022_2026_doi_url.csv")
YEAR_RANGE = range(2022, 2027)  # 2022-2026

def extract_year(date_str):
    """从各种日期格式中提取4位年份"""
    if not date_str:
        return None
    # 匹配20xx格式的年份
    match = re.search(r'\b(20\d{2})\b', str(date_str))
    if match:
        return int(match.group(1))
    return None

def main():
    zotero = ZoteroManager()
    if not zotero.user_id:
        print("❌ Zotero配置错误")
        return

    print(f"🔍 开始获取Nopdf分类（key: {COLLECTION_KEY}）的所有文献...")
    all_items = []
    start = 0
    limit = 100

    # 分页获取所有条目
    while True:
        items = zotero.get_items_by_collection(COLLECTION_KEY, limit=limit, start=start)
        if not items:
            break
        all_items.extend(items)
        start += limit
        print(f"⏳ 已获取 {len(all_items)} 条文献...")

    print(f"\n📚 共获取 {len(all_items)} 条文献，开始筛选2022-2026年的条目...")

    # 筛选并提取字段
    result = []
    for item in all_items:
        data = item.get('data', {})
        item_key = data.get('key')
        title = data.get('title', '无标题')
        date = data.get('date', '')
        doi = data.get('DOI', '').strip()
        url = data.get('url', '').strip()

        # 提取年份
        year = extract_year(date)
        if not year or year not in YEAR_RANGE:
            continue

        result.append({
            'year': year,
            'doi': doi,
            'url': url,
            'title': title,
            'item_key': item_key
        })

    # 保存到CSV
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['year', 'doi', 'url', 'title', 'item_key'])
        writer.writeheader()
        writer.writerows(result)

    # 统计
    year_count = {}
    for row in result:
        year = row['year']
        year_count[year] = year_count.get(year, 0) + 1

    print("\n🎉 提取完成！")
    print("="*80)
    print(f"📊 2022-2026年论文总数：{len(result)} 篇")
    for year in sorted(year_count.keys()):
        print(f"  {year}年：{year_count[year]} 篇")
    print(f"  有DOI的条目：{sum(1 for r in result if r['doi'])} 篇")
    print(f"  有URL的条目：{sum(1 for r in result if r['url'])} 篇")
    print("="*80)
    print(f"📝 结果已保存到：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
