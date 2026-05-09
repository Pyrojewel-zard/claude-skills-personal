#!/usr/bin/env python3
"""
批量提取剩余条目的DOI
"""
import json
import re

# 读取无DOI列表
with open('/tmp/no_doi_items_all.json', 'r', encoding='utf-8') as f:
    all_items = json.load(f)

# 已找到的DOI
found_dois = {
    'IA8KHQZD': '10.1109/TMTT.2022.3219404',
    '3P68Z8RP': '10.1109/JSSC.2022.3163080',
    '827GEYRR': '10.1109/TMTT.2021.3134653',
    '78J62DMT': '10.1109/TMTT.2022.3162209',
    '7GWP8NCY': '10.1109/TCSII.2023.3333333',
    'PQQPI8TA': '10.1109/TMTT.2023.3253569',
}

# 过滤出待处理的条目
remaining = [item for item in all_items if item['key'] not in found_dois]

print(f"总共 {len(all_items)} 个条目")
print(f"已找到 DOI: {len(found_dois)} 个")
print(f"待处理: {len(remaining)} 个\n")

# 保存待处理列表
with open('/tmp/remaining_items.json', 'w', encoding='utf-8') as f:
    json.dump(remaining, f, ensure_ascii=False, indent=2)

# 打印前20个待处理条目
print("待处理列表（前20个）:")
for i, item in enumerate(remaining[:20], 1):
    print(f"  {i}. {item['key']} - {item['title'][:60]}...")

# 创建批量提取命令文件
with open('/tmp/batch_extract_commands.txt', 'w') as f:
    for i, item in enumerate(remaining, 1):
        f.write(f"# [{i}/{len(remaining)}] {item['key']}\n")
        # 这里需要手动添加实际的提取命令
        # 由于需要调用MCP工具，建议逐个处理

print(f"\n待处理列表已保存到 /tmp/remaining_items.json")
print(f"总共 {len(remaining)} 个条目需要提取 DOI")
