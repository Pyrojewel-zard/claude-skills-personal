#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试下载前3篇IEEE论文，验证流程
"""
import csv
import subprocess
from pathlib import Path

# 配置
INPUT_CSV = Path("/tmp/ieee_dois_2022_2026.csv")
TEST_COUNT = 3

def read_first_n_dois(n):
    """读取前n个DOI"""
    dois = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= n:
                break
            doi = row['doi'].strip()
            if doi and doi.startswith('10.1109'):
                dois.append({
                    'doi': doi,
                    'title': row['title'],
                    'year': row['year']
                })
    return dois

def test_download(doi, title, index, total):
    """测试单篇下载"""
    print(f"\n{'='*80}")
    print(f"📝 测试 [{index}/{total}]：{doi}")
    print(f"📄 标题：{title[:100]}...")
    print(f"🔍 开始调用ieee-download...")

    try:
        # 直接调用ieee-download，显示完整输出
        result = subprocess.run(
            ['/home/holmes/.local/bin/claude', 'skill', 'run', 'ieee-download', doi],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )

        print(f"🔹 返回码：{result.returncode}")
        if result.stdout:
            print(f"🔹 标准输出：\n{result.stdout[:500]}..." if len(result.stdout) > 500 else f"🔹 标准输出：\n{result.stdout}")
        if result.stderr:
            print(f"🔹 标准错误：\n{result.stderr[:500]}..." if len(result.stderr) > 500 else f"🔹 标准错误：\n{result.stderr}")

        if result.returncode == 0:
            print(f"✅ 第{index}篇下载成功！")
            return True
        else:
            print(f"❌ 第{index}篇下载失败！")
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ 下载超时（5分钟）")
        return False
    except Exception as e:
        print(f"❌ 调用异常：{str(e)}")
        return False

def main():
    dois = read_first_n_dois(TEST_COUNT)
    print(f"🚀 开始测试下载前{len(dois)}篇IEEE论文...")

    success = 0
    for i, item in enumerate(dois, 1):
        if test_download(item['doi'], item['title'], i, len(dois)):
            success += 1

    print(f"\n{'='*80}")
    print(f"📊 测试结果：{success}/{len(dois)} 篇下载成功")
    if success == len(dois):
        print("✅ 全部测试成功，可以开始批量下载！")
    else:
        print("⚠️  部分测试失败，请检查问题后再批量下载")

if __name__ == "__main__":
    main()
