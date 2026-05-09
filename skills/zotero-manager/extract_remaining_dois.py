#!/usr/bin/env python3
"""
批量提取剩余条目的DOI
使用zotero MCP工具
"""
import json
import re
import subprocess
import sys
import os

# 读取待处理列表
remaining = []
with open('/tmp/no_doi_items_all.json', 'r', encoding='utf-8') as f:
    all_items = json.load(f)
    for item in all_items:
        key = item['key']
        # 检查是否已经找到DOI（从之前手动检查的6个）
        if key in ['IA8KHQZD', '3P68Z8RP', '827GEYRR', '78J62DMT', '7GWP8NCY', 'PQQPI8TA']:
            continue  # 跳过已处理的
        remaining.append(item)

print(f"准备处理 {len(remaining)} 个条目...")
print(f"注意：由于需要逐个调用Zotero MCP工具，这会需要较长时间")
print(f"每个条目大约需要3-5秒，预计总时间约 {len(remaining) * 4} 秒 = {len(remaining) * 4 / 60:.0f} 分钟")
print(f"请耐心等待...\n")

# 调用zotero MCP工具提取DOI的函数
def extract_doi_from_content(content):
    """从PDF内容中提取DOI"""
    doi_patterns = [
        r'(?:DOI|doi)[:]\s*\s*(10\.\d{4,9}/[^\s<>\)]+)',
        r'Digital Object Identifier\s+(10\.\d{4,9}/[^\s<>\)]+)',
        r'(?:https?://doi\.org/)?(10\.\d{4,9}/[^\s<>\)]+)',
    ]

    for pattern in doi_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(0)
    return None

# 逐个处理条目
results = []
for idx, item in enumerate(remaining, 1):
    key = item['key']
    title = item['title'][:60]

    print(f"[{idx}/{len(remaining)}] 正在提取 {key} 的 DOI...")

    try:
        # 调用zotero MCP工具获取PDF内容
        cmd = [
            'node', '-p', '~/.claude/scripts/zotero-mcp-client.mjs',
            'get-content', '--itemKey', key,
            '--mode', 'complete',
            '--include', '{"pdf": true, "attachments": true}'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print(f"  ❌ MCP调用失败")
            # 写入错误信息
            results.append({'key': key, 'title': title, 'error': f"MCP调用失败: {result.returncode}"})
            continue

        # 解析输出
        mcp_output = result.stdout
        doi = extract_doi_from_content(mcp_output)

        if doi:
            print(f"  ✓ DOI: {doi}")
        else:
            print(f"  ✗ 未找到 DOI")

        results.append({
            'key': key,
            'title': title,
            'doi': doi if doi else None
        })

        # 每处理20个条目后暂停一下，避免API限流
        if idx % 20 == 0 and idx > 0:
            print(f"  已处理 {idx} 个条目，暂停3秒...")
            import time
            time.sleep(3)

# 保存结果
with open('/tmp/dois_extraction_remaining.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n完成！结果已保存到 /tmp/dois_extraction_remaining.json")

# 统计
found_count = sum(1 for r in results if 'doi' in r and r['doi'])
not_found_count = sum(1 for r in results if 'doi' in r and not r['doi'])

print(f"\n提取结果统计:")
print(f"  成功提取 DOI: {found_count}")
print(f" 未能提取: {not_found_count}")
print(f"  总计: {len(results)} 个条目")