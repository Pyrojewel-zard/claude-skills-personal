import sys
sys.path.insert(0, '.')
sys.path.insert(0, './lib')
from zotero_api import ZoteroManager
import json

manager = ZoteroManager()

# 没有 DOI 的条目
items_no_doi = [
    'IS2C3EUY', 'IA8KHQZD', '3P68Z8RP', '827GEYRR'
]

for item_key in items_no_doi:
    item = manager.get_item_detail(item_key)
    if not item:
        print(f"无法获取 {item_key}")
        continue
    
    data = item.get('data', {})
    print(f"\n=== {item_key} ===")
    print(f"标题: {data.get('title', 'N/A')}")
    print(f"类型: {data.get('itemType', 'N/A')}")
    
    # 检查附件
    children = item.get('children', [])
    print(f"子条目数: {len(children)}")
    
    for child in children:
        child_data = child.get('data', {})
        child_type = child_data.get('itemType', 'unknown')
        if child_type == 'attachment':
            link_mode = child_data.get('linkMode', 'unknown')
            content_type = child_data.get('contentType', 'unknown')
            filename = child_data.get('filename', 'N/A')
            print(f"  附件: {filename} (类型: {content_type}, 链接模式: {link_mode})")
            print(f"    Key: {child.get('key')}")
