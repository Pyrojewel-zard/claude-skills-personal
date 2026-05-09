#!/usr/bin/env python3
"""
从 zotero-mcp 搜索结果中提取文献信息
然后批量查询详情获取 abstractNote
"""

import json
import csv
from pathlib import Path

def main():
    # 读取搜索结果
    base_path = Path("/home/holmes/.claude/projects/-mnt-d-obsidian-wiki/da4dba44-1ad4-41bd-9a6d-540e981c194e/tool-results")

    all_results = []

    # 读取三批搜索结果
    for filename in ["call_3db6c4b9a87b4dd5ab8b1674.json",
                     "call_675037fb5e8e482e901ad336.json",
                     "call_ada9e9e7514c46d496e51283.json"]:
        filepath = base_path / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                data = json.load(f)
            text = data[0]['text']
            result = json.loads(text)
            all_results.extend(result.get('results', []))

    print(f"总共加载 {len(all_results)} 条文献")

    # 筛选有 PDF 附件的文献
    has_pdf = []
    no_pdf = []

    for item in all_results:
        key = item.get('key', '')
        title = item.get('title', '')
        attachments = item.get('attachments', [])

        # 检查是否有 PDF
        pdf_attachments = [a for a in attachments if a.get('contentType') == 'application/pdf']

        if pdf_attachments:
            has_pdf.append({
                'key': key,
                'title': title,
                'attachment_key': pdf_attachments[0].get('key', ''),
                'filename': pdf_attachments[0].get('filename', '')
            })
        else:
            no_pdf.append({
                'key': key,
                'title': title
            })

    print(f"\n有 PDF 附件: {len(has_pdf)}")
    print(f"无 PDF 附件: {len(no_pdf)}")

    # 保存结果
    output_dir = Path(__file__).parent

    if has_pdf:
        output_file = output_dir / "items_with_pdf.csv"
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["key", "title", "attachment_key", "filename"])
            writer.writeheader()
            writer.writerows(has_pdf)
        print(f"\n有 PDF 的文献已保存到: {output_file}")

    # 输出前 20 个
    print("\n前 20 个有 PDF 的文献:")
    for i, item in enumerate(has_pdf[:20]):
        print(f"  [{i+1}] {item['key']}: {item['title'][:50]}...")

    # 保存所有 key 列表，用于后续批量查询 abstractNote
    keys_file = output_dir / "all_keys.txt"
    with open(keys_file, 'w') as f:
        for item in all_results:
            f.write(item.get('key', '') + '\n')
    print(f"\n所有文献 key 已保存到: {keys_file}")

if __name__ == "__main__":
    main()
