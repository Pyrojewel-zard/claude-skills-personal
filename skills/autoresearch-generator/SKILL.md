---
name: autoresearch-generator
description: 增强版ML实验生成器 - 分析项目结构，集成Codex审核，生成项目特定autoresearch skill
---

# Autoresearch Generator (Enhanced)

增强版元skill：分析ML训练项目，集成Codex MCP审核关键决策，生成项目特定autoresearch skill。

## 核心增强

| 维度 | 原版 | 增强版 |
|------|------|--------|
| 决策验证 | 单模型判断 | Claude + Codex 双重审核 |
| SSH执行 | 可能相对路径 | 强制绝对路径，禁止scp |
| 阶段顺序 | 随机 | 固定顺序 0→1→3→2→4 |
| 统计显著性 | 单run比较 | 多seed + 0.3%阈值 |

---

## Codex集成规则

### MUST: 模型参数
```json
{
  "model": "gpt-5.4",
  "prompt": "..."
}
```

### 触发时机

| 阶段 | 触发点 | Codex任务 |
|------|--------|-----------|
| Stage 1 结束 | 诊断报告完成后 | 审核诊断结论合理性 |
| Stage 2 结束 | 架构选择决策 | 验证架构候选覆盖度 |
| Stage 4 开始 | 最终配置确认 | 检查搜索空间完整性 |

### Codex Prompt模板

**诊断审核**:
```
审核以下autoresearch诊断结论：

## 诊断数据
- baseline val_rel_l2: {value}
- train/val gap: {gap}
- per-frequency MAE分布: {freq_mae_summary}
- 物理约束违反: {physics_summary}

## Claude结论
{claude_conclusion}

请判断：
1. 诊断结论是否合理？
2. 推荐方向是否遗漏关键可能性？
3. 是否有额外建议？
```

**架构审核**:
```
审核以下架构搜索计划：

## 诊断结论
{diagnosis_summary}

## Claude架构候选
{architecture_candidates}

请判断：
1. 候选是否覆盖关键架构类型？
2. 实现难度评估是否准确？
3. 实验顺序是否合理？
```

---

## SSH执行规则

### MUST: 绝对路径 + 先cd

```bash
# ✅ 正确格式
ssh user@remote-host 'bash -lc "cd /path/to/project && source ~/miniconda3/etc/profile.d/conda.sh && conda activate your-env && python /path/to/project/scripts/train_local.py --scheme {scheme} > logs/run_{tag}.log 2>&1"'
```

### 禁止

| 操作 | 原因 |
|------|------|
| scp/rsync | NAS自动同步 |
| 相对路径python | 远程执行会失败 |
| 无cd直接python | 工作目录错误 |

---

## 分析流程

### Step 1: 项目结构扫描

| 文件类型 | 搜索模式 |
|----------|---------|
| 入口脚本 | `train*.py`, `cli*.py`, `main.py` |
| 配置文件 | `*.yaml`, `configs/` |
| 模型定义 | `models/`, `model*.py` |
| 数据处理 | `data/`, `dataset*.py` |

### Step 2: 识别关键参数

**超参数** (config):
- `learning_rate`, `batch_size`, `epochs`
- `dropout`, `weight_decay`

**架构参数** (models):
- `hidden_dims`, `latent_dim`, `num_heads`
- `activation`, `use_batchnorm`

**Loss参数**:
- `loss_type`, `delta`, `weighting`

### Step 3: 提取主指标

扫描trainer代码：
```python
# 常见输出模式
print(f"val_rel_l2_base: {metric}")
logging.info("Best val_rel_l2: %.6f", best)
```

记录：指标名、方向(minimize)、解析命令。

### Step 4: 确认执行环境

| 类型 | 检测标志 |
|------|---------|
| SSH远程 | `RFRLSERVER5`, `RFRL26` |
| Conda环境 | `pacosyt`, `miniconda3` |
| GPU选择 | `device.mode: auto` |

---

## 生成Skill模板

生成的skill必须包含：

### 1. Frontmatter
```markdown
---
name: autoresearch-{scheme}
description: {scheme_desc}自动超参数调优 - 两阶段架构探索流程
---
```

### 2. 固定阶段顺序
```
Stage 0: 流程校准 → Stage 1: 诊断 → Stage 3: Loss → Stage 2: 架构 → Stage 4: 验证
```

### 3. 主指标定义
| 阶段 | 主指标 | 方向 |
|------|--------|------|
| Base | `val_rel_l2_base` | minimize |
| Final | `val_rel_l2_final` | minimize |

### 4. KEEP/DISCARD标准
```python
# 绝对提升阈值
if abs_improvement < 0.001:
    return DISCARD

# 相对提升阈值
if rel_improvement < 0.003:  # 0.3%
    return DISCARD

# 多seed方差阈值
if variance_std > 0.01:
    return DISCARD
```

### 5. SSH执行模板
```bash
ssh user@remote-host 'bash -lc "cd {PROJECT_PATH} && source ~/miniconda3/etc/profile.d/conda.sh && conda activate your-env && python {ABSOLUTE_SCRIPT_PATH} --scheme {scheme} --config {ABSOLUTE_CONFIG_PATH} --stage {stage} > {ABSOLUTE_LOG_PATH} 2>&1"'
```

### 6. Codex审核节点

在生成skill中标记：
```markdown
## Stage 1 结束 → Codex审核
调用 mcp__codex__codex(model="gpt-5.4", prompt=诊断审核模板)
```

---

## 目录结构

生成的skill位置：
```
{PROJECT}/.claude/skills/autoresearch-{scheme}/
└── SKILL.md
```

创建目录：
```bash
mkdir -p {PROJECT}/.claude/skills/autoresearch-{scheme}
```

---

## 用户确认流程

分析完成后输出：

```
=== 项目分析摘要 ===

入口脚本: {entry_point}
配置文件: {config_files}
可调参数: {tunable_params}
主指标: {primary_metric}

=== Codex审核节点 ===
- Stage 1 结束: 诊断审核
- Stage 2 结束: 架构审核
- Stage 4 开始: 配置审核

=== 执行环境 ===
SSH: user@remote-host
Conda: pacosyt
绝对路径: {project_path}

=== 配置确认 ===
1. 实验epochs: {default_epochs}
2. 目标阈值: {target_threshold}
3. 最大trials: {max_trials}

确认生成skill? [Y/n]
```

---

## 输出文件

生成后创建：

1. **SKILL.md** - 项目特定autoresearch skill
2. **results.tsv模板** - 结果记录格式

### results.tsv格式
```
stage	experiment	commit	val_rel_l2_base	val_rel_l2_final	arch_type	hidden_dims	lr	variance_std	status	description
```

---

## 关键设计约束

### MUST

| 规则 | 说明 |
|------|------|
| Codex模型 | 必须用 `gpt-5.4` |
| SSH格式 | `cd` + 绝对路径 |
| 禁止scp | NAS同步，无需传输 |
| 阶段顺序 | 0→1→3→2→4 固定 |
| 多seed | 至少3个seed验证 |

### 禁止

| 操作 | 原因 |
|------|------|
| git add . | 只stage修改文件 |
| scp/rsync | NAS已同步 |
| 相对路径 | 远程执行失败 |
| 单run判断 | 统计不显著 |

---

## 快速参考

| 命令 | 说明 |
|------|------|
| `mkdir -p .claude/skills/autoresearch-{scheme}` | 创建skill目录 |
| `ssh user@remote-host 'cd ... && python /abs/path'` | 远程执行 |
| `mcp__codex__codex(model="gpt-5.4", prompt=...)` | Codex审核 |
| `grep "val_rel_l2" logs/run.log | tail -1` | 解析指标 |

---

## 资源预算

| 参数 | 默认值 |
|------|--------|
| max_trials | 20 |
| timeout/trial | 2 hours |
| no_improve_threshold | 5 consecutive discards |
| seed_count | 3 |
