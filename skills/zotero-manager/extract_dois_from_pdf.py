#!/usr/bin/env python3
import os
import sys
import json
import re
sys.path.insert(0, '.')
sys.path.insert(0, './lib')
from zotero_api import ZoteroManager

# 读取无DOI列表
with open('/tmp/no_doi_items_all.json', 'r', encoding='utf-8') as f:
    no_doi_items = json.load(f)

print(f"找到 {len(no_doi_items)} 个无DOI条目，开始提取...\n")

manager = ZoteroManager()

# 暂时文件保存结果
results = []

# 逐一处理
for idx, item in enumerate(no_doi_items):
    key = item['key']
    title = item['title'][:70]
    
    print(f"[{idx + 1}/{len(no_doi_items)}] 正在提取 {key} 的 DOI...")
    
    try:
        # 使用Zotero MCP获取PDF内容
        url = f"{manager.base_url}/users/{manager.user_id}/items/{key}"
        response = manager.session.get(url, headers=manager.headers, timeout=30)
        if response.status_code != 200:
            print(f"  ❌ 获取失败")
            continue
        
        item_data = response.json()
        data = item_data.get('data', {})
        
        # 检查PDF内容
        if 'attachments' in data:
            attachments = data['attachments']
            doi_found = None
            
            for att in attachments:
                if att.get('type') == 'pdf' and 'content' in att:
                    content = att['content']
                    # 查找DOI - 多种模式
                    
                    # 模式1: 标准DOI格式
                    doi_match = re.search(r'(?:DOI|doi)[:]\s*\s*(10\.\d{4,9}/[^\s/]+[\w-/.-]?\d{1,4}[^\s/]*\d)', content, re.IGNORECASE)
                    if doi_match:
                        doi = doi_match.group(1)
                        print(f"  ✓ 找到DOI (模式1): {doi}")
                        doi_found = doi
                        break
                    
                    # 模式2: IEEE DOI format with prefix
                    if not doi_found:
                        doi_match = re.search(r'Digital Object Identifier\s+10\.\d{4,9}/[^\s/]+', content)
                        if doi_match:
                            doi = doi_match.group(0)
                            print(f"  ✓ 找到DOI (模式2): {doi}")
                            doi_found = doi
                            break
                    
                    # 模式3: arXiv DOI format
                    if not doi_found:
                        doi_match = re.search(r'arXiv:\d{4}/\.\d{4}', content)
                        if doi_match:
                            doi = doi_match.group(0)
                            print(f"  ✓ 找到DOI (模式3): {doi}")
                            doi_found = doi
                            break
                    
                    # 模式4: 直接DOI数字格式
                    if not doi_found:
                        doi_match = re.search(r'(?:https?://doi\.org/)?10\.\d{4,9}/[A-Za-z0-9]+', content)
                        if doi_match:
                            doi = re.search(r'10\.\d{4,9}/[A-Za-z0-9]+', doi_match.group(0)).group(0)
                            print(f"  ✓ 找到DOI (模式4): {doi}")
                            doi_found = doi
                            break
        
        results.append({
            'key': key,
            'title': title,
            'doi_found': doi_found if doi_found else None
        })
        
        # 避免请求过快，稍作延迟
        if idx % 5 == 4:
            print(f"  已处理 {idx + 1}/{len(no_doi_items)} 个条目，稍作延迟...")
            import time
            time.sleep(1)
    
    except Exception as e:
        print(f"  ❌ 处理{key}时出错：{e}")
        results.append({'key': key, 'title': title, 'error': str(e)})

# 保存结果
with open('/tmp/doi_extraction_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n\n完成！结果已保存到 /tmp/doi_extraction_results.json")
