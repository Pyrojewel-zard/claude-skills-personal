#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IEEE PDF 下载任务执行器
读取 download_tasks.json，返回下一篇待下载的论文信息
"""

import json
import sys
from pathlib import Path
from datetime import datetime

TASKS_FILE = Path(__file__).parent / 'download_tasks.json'

def get_next_task():
    """获取下一篇待下载的论文（自动跳过重复的 arnumber）"""
    if not TASKS_FILE.exists():
        print("ERROR: download_tasks.json 不存在")
        sys.exit(1)

    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    # 收集已完成的 arnumber
    completed_arnumbers = set()
    for paper in tasks['papers']:
        if paper.get('status') == 'completed':
            completed_arnumbers.add(paper.get('arnumber'))

    # 查找下一篇 pending 的论文，跳过重复
    skipped = 0
    for i, paper in enumerate(tasks['papers']):
        if paper.get('status') == 'pending':
            # 如果 arnumber 已完成，标记为跳过
            if paper.get('arnumber') in completed_arnumbers:
                paper['status'] = 'completed'
                paper['downloaded_at'] = 'skipped-duplicate'
                skipped += 1
                continue
            return {
                'index': i,
                'arnumber': paper['arnumber'],
                'title': paper['title'],
                'key': paper['key'],
                'url': paper['url'],
                'total': tasks['total'],
                'completed': tasks['completed'],
                'remaining': tasks['total'] - tasks['completed'] - tasks['failed']
            }

    # 如果跳过了重复，更新计数并保存
    if skipped > 0:
        tasks['completed'] = sum(1 for p in tasks['papers'] if p['status'] == 'completed')
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

    return None  # 没有待下载的论文

def mark_completed(index, success=True, error_msg=''):
    """标记论文下载状态"""
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    paper = tasks['papers'][index]
    if success:
        paper['status'] = 'completed'
        paper['downloaded_at'] = datetime.now().isoformat()
        tasks['completed'] += 1
    else:
        paper['status'] = 'failed'
        paper['error'] = error_msg
        tasks['failed'] += 1

    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    return tasks

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'next':
            task = get_next_task()
            if task:
                print(f"NEXT_DOWNLOAD:")
                print(f"  index: {task['index']}")
                print(f"  arnumber: {task['arnumber']}")
                print(f"  title: {task['title'][:60]}...")
                print(f"  progress: {task['completed']}/{task['total']} (剩余 {task['remaining']})")
                print(f"  pdf_url: https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={task['arnumber']}&ref=")
            else:
                print("NO_MORE_TASKS: 所有论文已下载完成")

        elif sys.argv[1] == 'status':
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
            print(f"下载进度: {tasks['completed']}/{tasks['total']}")
            print(f"失败: {tasks['failed']}")
            print(f"剩余: {tasks['total'] - tasks['completed'] - tasks['failed']}")

        elif sys.argv[1] == 'mark-done':
            if len(sys.argv) > 2:
                index = int(sys.argv[2])
                tasks = mark_completed(index, success=True)
                print(f"已标记第 {index} 篇为完成")
                print(f"进度: {tasks['completed']}/{tasks['total']}")

        elif sys.argv[1] == 'mark-fail':
            if len(sys.argv) > 2:
                index = int(sys.argv[2])
                error = sys.argv[3] if len(sys.argv) > 3 else 'Unknown error'
                tasks = mark_completed(index, success=False, error_msg=error)
                print(f"已标记第 {index} 篇为失败: {error}")
    else:
        # 默认输出下一篇
        task = get_next_task()
        if task:
            # 输出 JSON 格式供外部调用
            output = {
                'has_task': True,
                'index': task['index'],
                'arnumber': task['arnumber'],
                'title': task['title'],
                'pdf_url': f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={task['arnumber']}&ref=",
                'progress': f"{task['completed']}/{task['total']}",
                'remaining': task['remaining']
            }
            print(json.dumps(output, ensure_ascii=False))
        else:
            print(json.dumps({'has_task': False, 'message': '所有论文已下载完成'}))

if __name__ == '__main__':
    main()
