#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筛选出2021年及更早的DOI
"""

import csv
import re
from pathlib import Path

def extract_year_from_doi(doi):
    """从DOI中提取年份，支持IEEE格式"""
    # 匹配IEEE DOI格式中的年份: 10.1109/XXX.2021.XXXXXX
    match = re.search(r'\.(\d{4})\.\d+$', doi)
    if match:
        return int(match.group(1))

    # 其他格式尝试匹配4位年份
    match = re.search(r'/(20\d{2})/', doi)
    if match:
        return int(match.group(1))

    # 从标题或其他字段提取年份（如果DOI里没有）
    return None

def extract_year_from_title(title):
    """从标题中尝试提取年份"""
    match = re.search(r'\b(20\d{2})\b', title)
    if match:
        return int(match.group(1))
    return None

def main():
    input_csv = Path("/tmp/nopdf_collection_dois.csv")
    output_csv = Path("/tmp/doi_2021_and_earlier.csv")

    with open(input_csv, 'r', encoding='utf-8') as f_in, open(output_csv, 'w', newline='', encoding='utf-8') as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)
        writer.writerow(reader.fieldnames)

        total = 0
        filtered = 0

        for row in reader:
            total += 1
            doi = row['DOI'].strip()
            title = row['Title']

            year = extract_year_from_doi(doi)
            if not year:
                year = extract_year_from_title(title)

            if year and year <= 2021:
                writer.writerow([row[field] for field in reader.fieldnames])
                filtered += 1
                print(f"[{filtered}] {year} | {doi} | {title[:50]}...")

    print(f"\n筛选完成！")
    print(f"总DOI数: {total}")
    print(f"2021及更早的DOI数: {filtered}")
    print(f"筛选结果已保存到: {output_csv}")

if __name__ == "__main__":
    main()
