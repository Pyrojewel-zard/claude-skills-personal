#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__)) + '/lib'))

from zotero_api import ZoteroManager
import json

manager = ZoteroManager()

# 需要更新 DOI 的条目
items_to_update = [
    {'key': 'IS2C3EUY', 'doi': '10.1109/TMTT.2025.3609399'},
    {'key': 'IA8KHQZD', 'doi': '10.1109/TMTT.2022.3219404'},
    {'key': '3P68Z8RP', 'doi': '10.1109/JSSC.2022.3163080'},
    {'key': '827GEYRR', 'doi': '10.1109/TMTT.2021.3134653'},
]

for item in items_to_update:
    print(f"正在更新 {item['key']} 的 DOI: {item['doi']}")
    result = manager.update_item_field(item['key'], 'DOI', item['doi'])
    if result:
        print(f"  ✅ 成功")
    else:
        print(f"  ❌ 失败")

print("\n所有 DOI 更新完成！")
