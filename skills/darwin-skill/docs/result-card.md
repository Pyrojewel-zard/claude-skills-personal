# 成果卡片生成（Result Card）

每个 skill 优化完成后（或全量汇总后），自动生成视觉成果卡片，截图保存为 PNG。

## 卡片模板

模板位置：`templates/result-card.html`

3 种风格，每次随机选择一种：

| 风格 | CSS类 | URL hash | 视觉特点 |
|------|--------|----------|---------|
| Warm Swiss | `.theme-swiss` | `#swiss` | 暖白底+赤陶橙，Inter字体，干净网格 |
| Dark Terminal | `.theme-terminal` | `#terminal` | 近黑底+荧光绿，等宽字体，扫描线 |
| Newspaper | `.theme-newspaper` | `#newspaper` | 暖白纸+深红，衬线字体，双栏编辑风 |

## 生成流程

```
1. 复制 templates/result-card.html 到临时工作文件
2. 用 sed/编辑工具 替换占位数据：
   - data-field="skill-name" → 实际skill名
   - data-field="score-before/after/delta" → 实际分数
   - 8个维度的 dim-bar-before/after width → 实际百分比
   - data-field="improvement-1/2/3" → 实际改进摘要
   - data-field="date" → 当前日期
3. 随机选择风格：hash 设为 swiss/terminal/newspaper 之一
4. 用 scripts/screenshot.mjs 截图：
   node scripts/screenshot.mjs /abs/path/to/card.html /abs/path/to/output.png
5. 提示用户查看成果卡片 PNG
```

## 截图脚本使用

```bash
# 主方案
node scripts/screenshot.mjs /abs/path/to/card.html /abs/path/to/output.png

# 回退方案（脚本失败时）
npx playwright screenshot "file:///path/to/card.html#[theme]" \
  output.png --viewport-size=960,1280 --wait-for-timeout=2000
```

## 资源文件速查

| 路径 | 用途 |
|---|---|
| `templates/result-card.html` | 3风格主模板（swiss/terminal/newspaper，hash切换） |
| `templates/result-card-dark.html` | 单一暗色风格模板 |
| `templates/result-card-white.html` | 单一亮色风格模板 |
| `scripts/screenshot.mjs` | 2x 高清截图，只截 .card 元素，自动 open |
| `results.tsv` | 历次优化日志（9列含 eval_mode） |
| `{skill目录}/test-prompts.json` | 每个 skill 的测试 prompt 集 |

## 何时生成

| 场景 | 生成内容 |
|------|----------|
| 单 skill 优化完成 | 该 skill 的分数变化卡片 |
| 全量优化完成（Phase 3） | 全局战绩总览卡片 |

## 品牌元素

- **顶部**：Darwin.skill 品牌标识 + 日期
- **底部**：「Train your Skills like you train your models」+ github.com/alchaincyf/darwin-skill