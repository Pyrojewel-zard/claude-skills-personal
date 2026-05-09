#!/usr/bin/env python3
"""
筛选 Zotero 库中不含摘要但有 PDF 附件的文献
"""

import json
import csv
from pathlib import Path

def load_search_results(json_path):
    """加载搜索结果"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 提取 text 字段中的 JSON
    if isinstance(data, list) and len(data) > 0:
        text = data[0].get("text", "")
        return json.loads(text)
    return data

def main():
    # 加载三批搜索结果
    base_path = Path(__file__).parent.parent.parent.parent / "da4dba44-1ad4-41bd-9a6d-540e981c194e/tool-results"

    all_results = []

    for filename in ["call_3db6c4b9a87b4dd5ab8b1674.json",
                     "call_675037fb5e8e482e901ad336.json",
                     "call_ada9e9e7514c46d496e51283.json"]:
        filepath = base_path / filename
        if filepath.exists():
            data = load_search_results(filepath)
            all_results.extend(data.get("results", []))

    print(f"总共加载 {len(all_results)} 条文献")

    # 筛选：没有摘要但有 PDF 附件
    no_abstract_with_pdf = []
    no_abstract_no_pdf = []
    has_abstract = 0

    for item in all_results:
        key = item.get("key", "")
        title = item.get("title", "")
        abstract = item.get("abstractNote", "")
        attachments = item.get("attachments", [])

        # 检查是否有 PDF 附件
        has_pdf = any(att.get("contentType") == "application/pdf" for att in attachments)

        if abstract and abstract.strip():
            has_abstract += 1
        else:
            if has_pdf:
                pdf_info = [att for att in attachments if att.get("contentType") == "application/pdf"][0]
                no_abstract_with_pdf.append({
                    "key": key,
                    "title": title,
                    "attachment_key": pdf_info.get("key", ""),
                    "filename": pdf_info.get("filename", ""),
                    "doi": item.get("DOI", ""),
                    "date": item.get("date", ""),
                    "creators": item.get("creators", "")
                })
            else:
                no_abstract_no_pdf.append({
                    "key": key,
                    "title": title,
                    "doi": item.get("DOI", ""),
                    "date": item.get("date", "")
                })

    print(f"\n统计结果:")
    print(f"  有摘要: {has_abstract}")
    print(f"  无摘要有PDF: {len(no_abstract_with_pdf)}")
    print(f"  无摘要无PDF: {len(no_abstract_no_pdf)}")

    # 保存结果
    output_dir = Path(__file__).parent

    # 保存无摘要有PDF的文献
    if no_abstract_with_pdf:
        output_file = output_dir / "no_abstract_with_pdf.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["key", "title", "attachment_key", "filename", "doi", "date", "creators"])
            writer.writeheader()
            writer.writerows(no_abstract_with_pdf)
        print(f"\n无摘要有PDF的文献已保存到: {output_file}")

    # 保存无摘要无PDF的文献
    if no_abstract_no_pdf:
        output_file = output_dir / "no_abstract_no_pdf.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["key", "title", "doi", "date"])
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
