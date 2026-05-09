---
name: review
description: 回顾当天工作，更新 raw/notes/daily/YYYY-MM-DD.md 中的 done 和 review；项目知识入库单独走 wiki-ingest。
---

# Daily Review

## 前置约束

写入任何 raw/wiki 文件前，**必须先读取** `/mnt/c/obsidian_wiki/CLAUDE.md` 获取契约和入库规范。

Vault 根路径：`/mnt/c/obsidian_wiki/`

## 触发
用户输入 `/review`

## 执行流程

### 第一阶段：准备

1. **确定日期**：`date_str = YYYY-MM-DD`（当前日期）

2. **读取 daily 文件**：
   - 路径：`/mnt/c/obsidian_wiki/raw/notes/daily/{date_str}.md`
   - **不存在** → 创建包含 `Todo / Done / Review` 的基础文件
   - **存在** → 读取现有 `## Todo`、`## Done`、`## Review`

3. **提取当天计划与完成情况**：
   - 读取 `## Todo` 列表
   - 收集用户提供的今日完成项、偏差、阻碍和简短反思

4. **可选参考项目 session**：
   - 可读取：`/mnt/c/obsidian_wiki/raw/notes/projects/*/logs/{date_str}-*-session.md`
   - 用于辅助回忆今天做了什么
   - 不自动触发完整 ingest

### 第二阶段：整理 review 内容

5. **生成每日工作回顾**：
   - 更新 `## Done`
   - 更新 `## Review`
   - 在 `## Review` 中记录：
     - 完成了什么
     - 哪些 TODO 未完成
     - 主要阻碍
     - 明日优先事项

### 第三阶段：提示后续入库动作

6. **识别值得后续入库的项目日志**：
   - 提示用户哪些 project logs 值得跑 `wiki-ingest`
   - 不从 `raw/notes/daily/YYYY-MM-DD.md` 直接升格知识节点

## 回顾正文模板

```markdown
## Done

- ...

## Review

- 今日完成：
- 未完成 TODO：
- 主要阻碍：
- 明日优先事项：
```

7. **呈现 review**：
   - 在对话中展示更新后的 `Done / Review`
   - 高亮未完成项和明日重点

## 规则

- `/review` 更新的是 `raw/notes/daily/YYYY-MM-DD.md`
- `/review` 不直接执行完整 ingest
- 知识入库从项目日志触发，不从 daily 页面触发
- 所有文件操作使用 Read + Write/Edit 工具，不执行脚本修改 registry
