#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量调用/ieee-download下载IEEE论文，每隔1分钟下载一篇
"""
import csv
import time
import subprocess
from pathlib import Path

# 配置
INPUT_CSV = Path("/tmp/ieee_dois_2022_2026.csv")
DOWNLOAD_INTERVAL = 60  # 间隔60秒（1分钟）
LOG_FILE = Path("/tmp/ieee_download_log.csv")

def read_ieee_dois():
    """读取IEEE DOI列表"""
    dois = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doi = row['doi'].strip()
            if doi and doi.startswith('10.1109'):
                dois.append({
                    'doi': doi,
                    'title': row['title'],
                    'year': row['year']
                })
    return dois

def call_ieee_download(doi):
    """调用/ieee-download技能下载论文"""
    print(f"📥 开始下载：{doi}")
    try:
        # 调用claude的/ieee-download命令，不设置超时
        result = subprocess.run(
            ['/home/holmes/.local/bin/claude', 'run', 'ieee-download', doi],
            capture_output=True,
            text=True,
            timeout=None  # 不设置超时
        )
        if result.returncode == 0:
            print(f"✅ 下载成功：{doi}")
            return True, result.stdout
        else:
            print(f"❌ 下载失败：{doi}，错误：{result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ 调用失败：{doi}，异常：{str(e)}")
        return False, str(e)

def main():
    # 初始化日志
    log_exists = LOG_FILE.exists()
    with open(LOG_FILE, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not log_exists:
            writer.writerow(['time', 'doi', 'title', 'year', 'status', 'message'])

    dois = read_ieee_dois()
    total = len(dois)
    print(f"📚 共找到 {total} 篇IEEE论文，将每隔 {DOWNLOAD_INTERVAL} 秒下载一篇，预计总耗时：{total / 60:.1f} 小时")

    for i, item in enumerate(dois, 1):
        doi = item['doi']
        title = item['title']
        year = item['year']
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n⏳ 进度：{i}/{total} ({i/total*100:.1f}%) | {current_time}")
        print(f"📄 {year}年 | {title[:60]}...")

        # 调用下载
        success, message = call_ieee_download(doi)

        # 记录日志
        with open(LOG_FILE, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                current_time,
                doi,
                title,
                year,
                'success' if success else 'failed',
                message[:200]  # 只记录前200字符错误信息
            ])

        # 不是最后一篇的话，等待1分钟
        if i < total:
            print(f"⏰ 等待 {DOWNLOAD_INTERVAL} 秒后下载下一篇...")
            time.sleep(DOWNLOAD_INTERVAL)

    print(f"\n🎉 全部下载任务完成！")
    print(f"📝 下载日志已保存到：{LOG_FILE}")

if __name__ == "__main__":
    main()
