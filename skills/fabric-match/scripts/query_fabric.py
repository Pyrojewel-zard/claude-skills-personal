#!/usr/bin/env python3
"""
面料匹配查询脚本
输入：面料类型、米数、尺码
输出：所有匹配的款式列表
"""

import json
import re
import sys
from pathlib import Path

# 数据源
DATA_PATH = Path("/home/DataTransfer/Pyrojewel/01_lab/excel_deal/extracted/styles.json")

def load_data():
    """加载纸样数据"""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_fabric(fabric_str):
    """标准化面料名称"""
    if not fabric_str:
        return []
    # 分割多种面料
    fabrics = fabric_str.replace('、', ',').replace('，', ',').split(',')
    return [f.strip().lower() for f in fabrics if f.strip()]

def match_fabric(user_fabric, suggestion):
    """判断面料是否匹配"""
    if not suggestion:
        return False
    user_fabric = user_fabric.lower().strip()
    suggested = normalize_fabric(suggestion)
    
    # 模糊匹配：用户面料在建议面料中
    for s in suggested:
        if user_fabric in s or s in user_fabric:
            return True
    return False

def get_usage_for_size(usage_dict, size):
    """获取指定尺码的面料用量"""
    if not usage_dict:
        return None
    size = size.upper()
    # 处理尺码格式
    size_map = {
        'XS': 'XS', 'S': 'S', 'M': 'M', 'L': 'L',
        'XL': 'XL', '2XL': '2XL', '3XL': '3XL', '4XL': '4XL',
        'XXL': '2XL', 'XXXL': '3XL', 'XXXXL': '4XL'
    }
    normalized_size = size_map.get(size, size)
    usage = usage_dict.get(normalized_size)
    if usage:
        # 提取数值
        match = re.search(r'(\d+\.?\d*)', str(usage))
        if match:
            return float(match.group(1))
    return None

def safe_get(d, key, default=None):
    """安全获取字典值"""
    if d is None:
        return default
    return d.get(key, default)

def query(fabric_type, meters, size='M'):
    """
    查询匹配的款式
    
    Args:
        fabric_type: 面料类型，如"棉麻"
        meters: 米数，如2.0
        size: 尺码，如"M"
    
    Returns:
        list: 匹配的款式列表
    """
    data = load_data()
    records = data['records']
    
    matched = []
    not_enough = []
    wrong_fabric = []
    
    for r in records:
        extracted = r.get('llm_extracted', {})
        if extracted is None:
            continue
        
        fabric = safe_get(extracted, 'fabric', {})
        if fabric is None:
            fabric = {}
        
        # 获取款号
        style_id = r.get('excel_text', '')
        style_id_match = re.search(r'款号[：:]\s*([^\n]+)', style_id)
        display_id = style_id_match.group(1).strip() if style_id_match else f"Row{r['row']}"
        
        style_type = safe_get(extracted, 'style_type') or ''
        
        # 面料匹配
        suggestion = safe_get(fabric, 'suggestion')
        if not match_fabric(fabric_type, suggestion):
            wrong_fabric.append({
                'id': display_id,
                'type': style_type,
                'suggestion': suggestion
            })
            continue
        
        # 米数判断
        usage_dict = safe_get(fabric, 'usage', {})
        usage = get_usage_for_size(usage_dict, size)
        
        lining_obj = safe_get(extracted, 'lining', {})
        lining_usage = safe_get(lining_obj, 'usage', {}) if lining_obj else {}
        
        accessories = safe_get(extracted, 'accessories', [])
        
        if usage is None:
            # 没有用量数据，但有面料匹配
            matched.append({
                'id': display_id,
                'type': style_type,
                'usage': None,
                'enough': True,
                'remaining': None,
                'lining': lining_usage,
                'accessories': accessories,
                'width': safe_get(fabric, 'width')
            })
        elif meters >= usage:
            matched.append({
                'id': display_id,
                'type': style_type,
                'usage': usage,
                'enough': True,
                'remaining': meters - usage,
                'lining': lining_usage,
                'accessories': accessories,
                'width': safe_get(fabric, 'width')
            })
        else:
            not_enough.append({
                'id': display_id,
                'type': style_type,
                'usage': usage,
                'short': usage - meters,
                'suggestion': suggestion
            })
    
    return {
        'matched': matched,
        'not_enough': not_enough[:5],  # 只显示前5个差一点够的
        'wrong_fabric_count': len(wrong_fabric),
        'total': len(records)
    }

def format_result(result, fabric_type, meters, size):
    """格式化输出结果"""
    lines = []
    lines.append(f"## 匹配结果")
    lines.append(f"\n**你的面料**：{fabric_type} {meters}米")
    lines.append(f"**目标尺码**：{size}码")
    lines.append(f"\n找到 **{len(result['matched'])}** 款可制作（共{result['total']}款）")
    
    if result['matched']:
        lines.append("\n### ✅ 可制作的款式")
        for i, m in enumerate(result['matched'][:20], 1):  # 最多显示20个
            usage_str = f"{m['usage']}米" if m['usage'] else "用量未知"
            remaining_str = f"（剩余{m['remaining']:.1f}米）" if m['remaining'] else ""
            
            lines.append(f"\n**{i}. {m['id']}** - {m['type']}")
            lines.append(f"- 面料用量：{size}码需 {usage_str} {remaining_str}")
            
            if m['width']:
                lines.append(f"- 幅宽要求：{m['width']}")
            
            # 里布
            lining = m.get('lining')
            if lining:
                lining_usage = get_usage_for_size(lining, size)
                if lining_usage:
                    lines.append(f"- ⚠️ 里布需求：{lining_usage}米（需另备）")
            
            # 辅料
            accessories = m.get('accessories', [])
            if accessories:
                acc_str = ', '.join([f"{a['name']}({a.get('usage', '')})" for a in accessories])
                lines.append(f"- 辅料：{acc_str}")
    
    # 差一点够的
    if result['not_enough']:
        lines.append("\n### ⚠️ 米数不够，差一点")
        for m in result['not_enough']:
            lines.append(f"- **{m['id']}** - {m['type']}：需{m['usage']}米，差{m['short']:.1f}米")
    
    # 不匹配面料数量
    lines.append(f"\n### ❌ 面料不匹配")
    lines.append(f"共 {result['wrong_fabric_count']} 款建议面料不是{fabric_type}")
    
    return '\n'.join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python query_fabric.py <面料类型> <米数> [尺码]")
        print("示例: python query_fabric.py 棉麻 2 M")
        sys.exit(1)
    
    fabric_type = sys.argv[1]
    meters = float(sys.argv[2])
    size = sys.argv[3] if len(sys.argv) > 3 else 'M'
    
    result = query(fabric_type, meters, size)
    print(format_result(result, fabric_type, meters, size))
