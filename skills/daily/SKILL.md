---
name: daily
description: 创建或维护当天的工作记录，写入 raw/notes/daily/YYYY-MM-DD.md。仅保留 todo、done 和 review。
---

# Daily

## 前置约束

写入任何 raw/wiki 文件前，**必须先读取** `/mnt/c/obsidian_wiki/CLAUDE.md` 获取契约和路径规范。

## 触发
用户输入 `/daily`

## 执行流程

1. **确定日期**：`date_str = YYYY-MM-DD`（当前日期）

2. **读取昨日 daily 记录**（如果存在）：
   - 路径：`/mnt/c/obsidian_wiki/raw/notes/daily/{yesterday}.md`
   - 优先读取 `## Todo`、`## Done`、`## Review`
   - 提取未完成 TODO 作为"继承建议"列表

3. **检查今日文件状态**：
   - 路径：`/mnt/c/obsidian_wiki/raw/notes/daily/{date_str}.md`
   - **不存在** → 新建文件（跳到步骤 5）
   - **存在** → 读取现有 `Todo / Done / Review`，询问是否修改

4. **若修改现有计划**：
   - 展示现有内容
   - 询问要修改/添加/删除哪些项
   - 更新文件

5. **若新建文件**：
   - 询问"今天的 TODO 是什么？"
   - 展示昨日继承建议（如果有）："昨日未完成的 TODO：..."
   - 收集当天 TODO
   - 写入文件

## 文件模板

```markdown
# {date_str}

## Todo
- [ ] {TODO 1}
- [ ] {TODO 2}

## Done
- {完成项}

## Review
- {简短回顾}
```

## 边界

- `daily` 只保留当天 `todo / done / review`
- 不写入 `wiki/synthesis/daily/`
- 不承载项目碎片、截图、参数变化、调试细节
- 这些内容改走 `project-daily-capture`，写入 `raw/notes/projects/{project}/logs/YYYY-MM-DD-{project}-log.md`

## 规则
- 所有写入使用 Read + Write/Edit 工具，不执行脚本
- 写入前必须读取 CLAUDE.md 确认规范
- 不要把 `daily` 当作直接入库源
