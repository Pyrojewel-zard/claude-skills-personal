---
name: academic-writing-improver
description: Use when improving, polishing, or correcting academic text (papers, thesis, technical reports). Triggers on "改进", "润色", "improve", "polish" for academic content. NOT for emails, chat messages, or casual writing.
---

# Academic Writing Improver

## Overview

改进学术文本的拼写、语法、清晰度、简洁性和可读性，支持任意语言。

**核心原则：润色文字，不改变内容。**

## When to Use

```
用户请求"改进/润色/修改" + 学术文本
              ↓
    是学术论文/技术报告？
         ↓是              ↓否
    使用此skill      提醒用户这是非学术文本
```

**触发场景：**
- "改进这段论文段落"
- "润色这段文字" + 学术内容
- "帮我修改这段话" + 技术文档

**不适用场景：**
- 邮件、聊天消息
- 非技术性日常文本
- 用户明确要求内容纠错而非润色

## Core Rules

### Rule 0: 文本类型检测（第一步，必须执行）

**收到请求后，首先判断文本类型。这是强制步骤，不可跳过。**

**判断标准：**

| 特征 | 学术/技术文本 | 非学术文本 |
|------|--------------|------------|
| 内容 | 方法、实验、分析、结论 | 日常沟通、邀约、闲聊 |
| 语气 | 客观、正式 | 主观、口语化 |
| 标志词 | 提出、实验、结果表明 | 嗨、吗、一下、大概 |

**非学术文本特征识别：**
- 口语问候："嗨"、"你好"、"在吗"
- 疑问邀约："开会吗"、"有空吗"、"方便吗"
- 口语填充："一下"、"大概"、"左右"
- 日常场景：会议、聚餐、讨论方案

**处理流程：**

```
收到改进请求
    │
    ├── 包含非学术特征？
    │       │
    │       ├── 是 → 停止润色，询问用户：
    │       │       "这段文字看起来是日常沟通内容，是否需要：
    │       │        1. 学术化改写（用于论文）
    │       │        2. 商务正式化（用于邮件）
    │       │        3. 仅修正语病"
    │       │
    │       └── 否 → 继续润色
    │
    └── 学术/技术文本 → 继续润色
```

**示例：**

❌ **错误行为：** 直接润色 "嗨，明天开会吗？"
✅ **正确行为：** 识别为非学术文本，询问用户意图

### Rule 1: 语言检测
- 检测原文主要语言
- **输出语言与原文一致**
- 修改说明使用原文语言

### Rule 2: 技术术语处理（禁止翻译）

**铁律：技术术语保留英文原文，不得翻译。**

**禁止翻译的术语类型：**
- 行业通用缩写：RF, LNA, PDN, PCB, CAD, EDA, MOSFET
- 工程流程术语：design iteration, tape-out, sign-off, PDK
- 性能指标术语：bottleneck, trade-off, overhead, yield
- 技术概念术语：corner case, edge case, workaround

**正确处理方式：**
```
原文: design iteration
✅ 保留: design iteration
✅ 加注释: 设计迭代（design iteration）
❌ 翻译: 设计迭代  # 禁止！
```

| 情况 | 处理方式 | 示例 |
|------|----------|------|
| 行业通用缩写 | **必须保留** | RF, LNA, PDN, PCB, CAD |
| 技术流程术语 | **必须保留** | design iteration, tape-out |
| 性能指标术语 | **必须保留** | bottleneck, trade-off |
| 首次出现的缩写 | 展开全称 + 保留缩写 | PCB电源分配网络（PDN） |
| 非技术性英文短语 | 可翻译 | "on the other hand" → "另一方面" |

### Rule 3: 润色边界（严格执行）

**两步流程，不可合并：**

```
Step 1: 文字润色
    │   - 修正语法、拼写
    │   - 优化句式、删除冗余
    │   - 不改变原文的任何论点或结论
    │
    ↓
Step 2: 内容问题提示（可选）
    │   - 仅当发现事实错误时
    │   - 在文末独立区块提示
    │   - 不在润色版本中修改内容
```

```
润色 ✅（Step 1）     内容纠错 ❌（不属于润色）
─────────────────────────────────────────────
语法错误修正         物理原理纠正
句式优化             实验数据质疑
冗余删除             论证逻辑重构
术语规范化           结论修改/推翻
拼写纠正             添加新内容
```

**如果发现内容错误：**
1. **先完成文字润色**（不修改错误内容）
2. 在文末添加独立区块：

```markdown
---

## ⚠️ 内容提示

原文可能存在以下问题，建议核实：
- [描述问题，如：Q与频率的关系描述不完整，未考虑Rs的频率依赖性]
```

### Rule 4: 公式与符号
- 保留所有数学公式不变
- 保留希腊字母（ω, θ, λ）
- 保留变量名（L, Q, Rs）
- 不修改方程结构

## Output Format

```markdown
## 改进版本

> [更正后的文本]

---

## 修改说明

| 原文 | 修改 | 理由 |
|------|------|------|
| ... | ... | ... |

---

## 注意事项（可选）

[内容问题提示，如有]
```

## Quick Reference

| 改进维度 | 操作 |
|----------|------|
| 拼写/语法 | 直接修正 |
| 长句 | 拆分为2-3句 |
| 冗余 | 删除重复表达 |
| 术语 | 保留技术术语 |
| 公式 | 完全保留 |

## Red Flags

当用户请求模糊时，询问：

| 输入 | 响应 |
|------|------|
| "改一下这段话" + 内容过短 | "这是学术论文的一部分吗？需要什么方向的改进？" |
| 非学术文本 | "这段文字看起来像日常沟通，是否需要学术化改写？" |
| 发现内容错误 | 润色完成后提示："注意：原文可能存在XX问题" |

## Examples

### English Academic Text

**Input:**
> The proposed method make use of multi-task learning framework for the purpose of simultaneously predicting both inductance L and quality factor Q.

**Output:**
> The proposed method employs a multi-task learning framework to simultaneously predict both inductance L and quality factor Q.

| Original | Corrected | Reason |
|----------|-----------|--------|
| "make use of" | "employs" | Subject-verb agreement + conciseness |
| "for the purpose of" | "to" | Remove wordiness |

### Chinese Academic Text

**Input:**
> 本文提出了一种基于深度学习的方法来对RF电感的Q值进行预测。

**Output:**
> 本文提出了一种基于深度学习的RF电感品质因数预测方法。

| 原文 | 修改 | 理由 |
|------|------|------|
| "来对...进行预测" | "...预测方法" | 去除冗余动词 |

### Technical Term Preservation（新规则示例）

**Input:**
> PCB的PDN分析对于design iteration是一个bottleneck。

**Output:**
> PCB电源分配网络（PDN）分析对于设计迭代（design iteration）是一个主要瓶颈（bottleneck）。

| 处理 | 说明 |
|------|------|
| PDN | 首次出现，展开缩写 |
| design iteration | **技术术语，保留英文**，添加中文注释 |
| bottleneck | **技术语境，保留英文**，添加中文注释 |

**对比：如果按旧规则翻译**
> ❌ PCB电源分配网络（PDN）分析已成为设计迭代的主要瓶颈。
> （问题：丢失了技术术语的英文原文，不符合行业写作习惯）