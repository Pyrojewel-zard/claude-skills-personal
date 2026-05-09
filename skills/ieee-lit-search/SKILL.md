---
name: ieee-lit-search
description: IEEE 优先的多轮文献检索编排。自动生成多组关键词，调用 ieee-advanced-search 执行检索，去重合并返回论文列表。
argument-hint: "[研究方向描述] --venues: [期刊列表] --year-range: [年份范围] --max-results: [数量]"
allowed-tools: Agent, mcp__chrome-devtools__*
---

# IEEE Literature Search

多轮检索编排，返回 IEEE 论文列表。

## Constants

- **DEFAULT_VENUES** — 核心期刊白名单（完整标题）：
  - TMTT: `IEEE Transactions on Microwave Theory and Techniques`
  - MWCL: `IEEE Microwave and Wireless Components Letters`
  - IMS: `IEEE MTT-S International Microwave Symposium`
  - RFIC: `IEEE Radio Frequency Integrated Circuits Symposium`
  - JSSC: `IEEE Journal of Solid-State Circuits`
  - TCAS: `IEEE Transactions on Circuits and Systems I: Regular Papers`
  - TCAS-II: `IEEE Transactions on Circuits and Systems II: Express Briefs`
  - ISSCC: `IEEE International Solid-State Circuits Conference`
  - TAP: `IEEE Transactions on Antennas and Propagation`
  - AWPL: `IEEE Antennas and Wireless Propagation Letters`
  - TCOM: `IEEE Transactions on Communications`
  - TWC: `IEEE Transactions on Wireless Communications`
  - JSAC: `IEEE Journal on Selected Areas in Communications`

- **DEFAULT_YEAR_RANGE = `2021-2026`** — 近 5 年
- **DEFAULT_MAX_RESULTS = 50** — 每轮最大结果数
- **SEARCH_DELAY = 2s** — 多轮检索间隔（避免限流）
- **MAX_RETRIES = 3** — 429 响应最大重试次数

## Workflow

### Step 1: 解析参数

从 `$ARGUMENTS` 提取：
- `query`: 研究方向描述（必填）
- `venues`: 期刊列表（可选，默认核心期刊白名单）
- `year_range`: 年份范围（可选，默认近 5 年）
- `max_results`: 最大结果数（可选，默认 50）

参数解析规则：
- `--venues:` 后跟逗号分隔的期刊缩写或完整标题
- `--year-range:` 后跟 `YYYY-YYYY` 格式
- `--max-results:` 后跟整数
- 其余内容作为 query

### Step 2: 关键词生成

使用 LLM 将 query 分解为多组搜索关键词：

1. **结构化分解**：将 query 分解为 [方法] × [对象] × [应用] 维度
2. **同义词扩展**：每个维度生成同义词/相关术语/上下位词
3. **组合生成**：生成 3-5 组搜索关键词

示例：
```
Query: "AI 辅助 LNA 设计"

分解：
- 方法: AI, machine learning, neural network, deep learning
- 对象: LNA, low noise amplifier, receiver frontend
- 应用: RF, microwave, wireless communication

关键词组：
1. "machine learning" AND "low noise amplifier" AND "RF"
2. "neural network" AND "LNA" AND "microwave"
3. "deep learning" AND "receiver frontend" AND "wireless"
```

**关键词生成要求**：
- 每组关键词使用 AND 连接不同概念
- 同一概念的同义词使用 OR
- 多词短语必须用双引号包裹
- 添加领域锚点词防止跨域噪声

### Step 3: 构造期刊过滤

将 venues 列表转换为 IEEE Xplore 布尔查询：

```
publication_title:("IEEE Transactions on Microwave Theory and Techniques" OR "IEEE Microwave and Wireless Components Letters" OR ...)
```

### Step 4: 多轮检索

对每组关键词调用 `ieee-advanced-search`：

```
for i, keyword_set in enumerate(keyword_list):
    # 检索间隔（避免限流）
    if i > 0:
        sleep(SEARCH_DELAY)  # 2s 延迟

    # 构造布尔查询：关键词 + 期刊过滤
    boolean_query = keyword_set AND publication_title filter

    result = /ieee-advanced-search {boolean_query} from {year_range}

    # 429 限流处理
    if result.status == 429:
        for retry in range(MAX_RETRIES):
            sleep(2 ** retry * SEARCH_DELAY)  # 指数退避
            result = /ieee-advanced-search {boolean_query} from {year_range}
            if result.status != 429:
                break

    results += result
```

**注意**：串行执行，避免浏览器冲突。每轮检索间隔 2 秒，429 响应时指数退避重试。

### Step 5: 去重合并

- 按 `arnumber` 去重
- 按引用数（citedBy）降序排序
- 返回 top-N（max_results）

### Step 6: 输出

返回 IEEE 论文元数据列表（**仅 IEEE 来源，不含 arXiv**）：

```json
[
  {
    "title": "论文标题",
    "authors": ["作者1", "作者2"],
    "venue": "IEEE TMTT",
    "year": 2023,
    "doi": "10.1109/...",
    "arnumber": "12345678",
    "abstract": "摘要文本",
    "citations": 42,
    "source": "ieee"
  }
]
```

**重要**：`source` 字段必须始终为 `"ieee"`，以便 `lit-reading` 正确路由全文获取。arXiv 补充由 `research-lit` 在后续步骤处理。

## 失败处理

| 条件 | 处理 |
|------|------|
| 无访问权限 | 停止并询问用户：配置 VPN？跳过 IEEE？ |
| 零结果 | 返回空列表，继续其他来源 |
| 部分失败 | 返回成功的结果，标记失败的关键词 |
| 429 限流 | 指数退避重试，最多 3 次 |
| 浏览器冲突 | 串行执行，不并行 |
