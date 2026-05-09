---
name: ieee-download-one
description: 下载任务清单中的下一篇 IEEE PDF
disable-model-invocation: true
---

# IEEE 单篇下载

从 `download_tasks.json` 读取下一篇待下载的论文，执行下载并更新状态。

## 执行流程

1. 读取任务清单，获取下一篇 pending 的论文
2. 导航到 PDF URL
3. 触发下载
4. 更新任务状态

## 使用

```
/ieee-download-one
```

配合 loop 使用：
```
/loop 1m /ieee-download-one
```
