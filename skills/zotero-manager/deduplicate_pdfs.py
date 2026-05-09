#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF文件按MD5值去重工具
安全模式：先扫描统计，确认后再执行删除操作
"""
import os
import hashlib
import csv
from pathlib import Path
from collections import defaultdict

# 配置
PDF_DIR = Path.home() / "Downloads" / "SciHub_Papers"
BACKUP_DIR = PDF_DIR / "duplicates_backup"  # 重复文件备份目录
REPORT_FILE = PDF_DIR / "duplicates_report.csv"

def calculate_md5(filepath, block_size=65536):
    """计算文件的MD5值"""
    md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                md5.update(block)
        return md5.hexdigest()
    except Exception as e:
        print(f"❌ 计算MD5失败 {filepath.name}: {e}")
        return None

def scan_duplicates():
    """扫描目录，查找重复文件"""
    print(f"🔍 开始扫描目录：{PDF_DIR}")
    print("="*80)

    md5_map = defaultdict(list)
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    total_files = len(pdf_files)
    print(f"📂 共找到 {total_files} 个PDF文件")

    for i, filepath in enumerate(pdf_files, 1):
        if i % 50 == 0:
            print(f"⏳ 已扫描 {i}/{total_files} 个文件...")

        md5 = calculate_md5(filepath)
        if md5:
            md5_map[md5].append({
                'path': filepath,
                'size': filepath.stat().st_size,
                'name': filepath.name
            })

    # 筛选出重复的文件
    duplicates = {md5: files for md5, files in md5_map.items() if len(files) > 1}
    duplicate_count = sum(len(files) - 1 for files in duplicates.values())
    unique_count = len(md5_map)

    print("\n" + "="*80)
    print("📊 扫描结果：")
    print(f"  总文件数：{total_files}")
    print(f"  唯一文件数：{unique_count}")
    print(f"  重复文件数：{duplicate_count} 个（属于 {len(duplicates)} 组）")
    print(f"  可释放空间：{sum(f['size'] for files in duplicates.values() for f in files[1:]) / 1024 / 1024:.2f} MB")
    print("="*80)

    # 生成报告
    with open(REPORT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['MD5', '文件数量', '文件名', '大小(字节)', '操作'])

        for md5, files in duplicates.items():
            # 保留第一个文件，标记其他为待删除
            writer.writerow([md5, len(files), files[0]['name'], files[0]['size'], '保留'])
            for f in files[1:]:
                writer.writerow([md5, len(files), f['name'], f['size'], '删除/备份'])

    print(f"📝 重复报告已保存到：{REPORT_FILE}")
    return duplicates, duplicate_count

def deduplicate_files(duplicates, backup=True):
    """执行去重操作"""
    if backup:
        BACKUP_DIR.mkdir(exist_ok=True, parents=True)
        print(f"📦 重复文件将备份到：{BACKUP_DIR}")

    total_processed = 0
    total_freed = 0

    for md5, files in duplicates.items():
        # 保留第一个文件
        keep_file = files[0]
        # 处理其他重复文件
        for f in files[1:]:
            filepath = f['path']
            try:
                if backup:
                    # 移动到备份目录
                    target_path = BACKUP_DIR / filepath.name
                    # 如果目标文件已存在，添加序号
                    counter = 1
                    while target_path.exists():
                        stem = filepath.stem
                        suffix = filepath.suffix
                        target_path = BACKUP_DIR / f"{stem}_{counter}{suffix}"
                        counter += 1
                    filepath.rename(target_path)
                    operation = "备份"
                else:
                    # 直接删除
                    filepath.unlink()
                    operation = "删除"

                total_processed += 1
                total_freed += f['size']
                print(f"✅ {operation} 重复文件：{f['name']}")
            except Exception as e:
                print(f"❌ 处理失败 {f['name']}: {e}")

    print("\n" + "="*80)
    print("🎯 去重完成！")
    print(f"  处理重复文件：{total_processed} 个")
    print(f"  释放空间：{total_freed / 1024 / 1024:.2f} MB")
    if backup:
        print(f"  备份目录：{BACKUP_DIR}")
    print(f"  报告文件：{REPORT_FILE}")
    print("="*80)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='PDF文件按MD5值去重工具')
    parser.add_argument('--backup', action='store_true', help='自动将重复文件备份到子目录（无需交互）')
    parser.add_argument('--delete', action='store_true', help='自动删除重复文件（无需交互，谨慎使用）')
    args = parser.parse_args()

    # 先扫描
    duplicates, duplicate_count = scan_duplicates()

    if duplicate_count == 0:
        print("🎉 没有找到重复文件，无需去重！")
        return

    # 根据命令行参数执行
    if args.backup:
        print("🚀 自动执行备份模式去重...")
        deduplicate_files(duplicates, backup=True)
    elif args.delete:
        print("⚠️  自动执行删除模式去重，重复文件将被永久删除！")
        deduplicate_files(duplicates, backup=False)
    else:
        # 交互式模式
        while True:
            choice = input(f"\n❓ 找到 {duplicate_count} 个重复文件，是否执行去重操作？\n  1) 备份重复文件到子目录（推荐）\n  2) 直接删除重复文件\n  3) 取消操作\n请选择 [1/2/3]: ").strip()
            if choice == '1':
                deduplicate_files(duplicates, backup=True)
                break
            elif choice == '2':
                confirm = input("⚠️  直接删除无法恢复，确认继续？(y/N): ").strip().lower()
                if confirm == 'y':
                    deduplicate_files(duplicates, backup=False)
                else:
                    print("🚫 已取消操作")
                break
            elif choice == '3':
                print("🚫 已取消操作")
                break
            else:
                print("❌ 无效选择，请输入1、2或3")

if __name__ == "__main__":
    main()
