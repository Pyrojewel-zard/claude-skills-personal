#!/usr/bin/env python3
"""
批量处理 Zotero 文献摘要补充
1. 使用 zotero-mcp 获取所有文献
2. 筛选出没有摘要但有 PDF 的文献
3. 获取 PDF 路径
4. 用 Python 读取 PDF 第一页
5. 提取摘要并更新
"""

import os
import re
import csv
import json
import subprocess
from pathlib import Path

# 输出文件
OUTPUT_FILE = Path(__file__).parent / "empty_abstract_with_pdf.csv"

def extract_abstract_from_pdf_text(text):
    """从 PDF 文本中提取摘要"""
    # 常见的摘要模式
    patterns = [
        # IEEE 格式
        r'(?i)Abstract[—–:\s]*([^\n]+(?:\n(?![A-Z][a-z]+[—–:])(?![A-Z]{2,}\s)[^\n]+)*)',
        # 通用格式
        r'(?i)Abstract[:\s]*(.*?)(?=\n\s*(?:Keywords|Index Terms|I\.\s|1\.\s|Introduction))',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            # 清理
            abstract = re.sub(r'\s+', ' ', abstract)
            abstract = re.sub(r'Authorized licensed use limited.*?IEEE Xplore\.', '', abstract)
            abstract = abstract.strip()
            if len(abstract) > 100:
                return abstract
    return None

def main():
    print("=" * 60)
    print("批量处理 Zotero 文献摘要补充")
    print("=" * 60)

    # 这个脚本需要配合 Claude 的 MCP 工具使用
    # 步骤：
    # 1. Claude 使用 mcp__zotero-mcp__search_library 获取所有文献
    # 2. 筛选出 abstractNote 为空但有 PDF 附件的文献
    # 3. Claude 使用 mcp__zotero-mcp__get_content 获取 PDF 内容
    # 4. 提取摘要
    # 5. 使用 zotero_manager.py update-field 更新

    print("""
处理流程：
1. 使用 MCP 搜索所有文献
2. 筛选：abstractNote 为空 + 有 PDF 附件
3. 获取 PDF 内容
4. 提取摘要
5. 更新到 Zotero

请使用 Claude 的 MCP 工具执行此流程。
""")

if __name__ == "__main__":
    main()
