---
name: wiki-capture
description: Use when the material is still low-density or provisional and should first be appended into raw notes before any compile or typed knowledge promotion.
user_invocable: true
---

# wiki-capture

运行 `/wiki-capture <material-or-text> --intent "<一句话意图>"`。

## 目标

把低密度输入先落到正确的 `raw/` 入口，不直接写 accepted wiki。

这是三入口 flow 的第一步：

`wiki-capture -> wiki-compile -> wiki-refine`

## 默认适用

- Claude Code / Codex 对话洞见
- 项目推进碎片
- Virtuoso 仿真截图与单次观察
- 课程片段
- 论文相关性提醒

## 路由规则

- 项目 / session / 仿真 -> `raw/notes/projects/{project}/logs/YYYY-MM-DD-{project}-log.md`
- 独立课程 / 讲演录片段 -> `raw/notes/courses/`
- 若材料已经足够稳定，不继续 capture，改走 `/wiki-compile`

## 规则

- append-only
- 只写 `raw/`
- 不默认创建 `claim / procedure / entity`
- 不直接写 accepted edges
- 保留原始上下文，不在 capture 阶段过度总结

## 后续

- 当同一主题已经形成阶段性总结、完整记录、或足够稳定的材料时，转到 `/wiki-compile`
- 只有在确有明确知识提炼价值时，才进一步使用 `/wiki-refine`
