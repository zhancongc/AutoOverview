# Danmo Scholar — Coze Skill 完整配置

---

## Step 1: 后端 API 接口文档

```markdown
# Danmo Scholar Skill API — 文献综述生成

## Base URL

- 中文站: `https://scholar.danmo.tech`
- 英文站: `https://en-scholar.danmo.tech`

## 认证

所有请求必须在 Header 中携带用户 API Token（即登录后的 JWT Token）：

```
Authorization: Bearer {user_api_token}
```

用户需先在 Danmo Scholar 官网注册账号，在「个人中心 → 开发者 API Token」获取 Token。
注册即送 2 积分（可生成 1 篇综述）。

---

## POST /api/skill/research

提交文献综述生成任务（异步模式）。此接口专供 Coze / Dify 等 Agent 平台调用。

### 请求体 (JSON)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✅ | 研究主题，如 "脑机接口中风康复"、"transformer in time series" |
| `language` | string | ❌ | 综述语言：`zh`（中文，默认）或 `en`（英文） |
| `max_papers` | integer | ❌ | 目标文献数量，默认 30，范围 10-100 |

### 请求示例

```bash
curl -X POST https://scholar.danmo.tech/api/skill/research \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "脑机接口在中风康复中的应用",
    "language": "zh",
    "max_papers": 30
  }'
```

### 响应 (成功)

```json
{
  "success": true,
  "message": "任务已提交，请轮询获取结果",
  "data": {
    "task_id": "a1b2c3d4",
    "topic": "脑机接口在中风康复中的应用",
    "status": "pending",
    "poll_url": "/api/tasks/a1b2c3d4",
    "review_url": "/api/tasks/a1b2c3d4/review"
  }
}
```

### 错误响应

| HTTP 状态码 | 含义 |
|-------------|------|
| 401 | 未登录或 Token 无效 → 请到官网注册获取 API Token |
| 200 + success:false | 积分不足 → 请到官网充值 |

---

## GET /api/tasks/{task_id}

轮询任务进度和结果。综述生成约需 3-5 分钟，建议每 5 秒轮询一次。

### 请求示例

```bash
curl https://scholar.danmo.tech/api/tasks/a1b2c3d4 \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

### 响应（生成中）

```json
{
  "success": true,
  "data": {
    "task_id": "a1b2c3d4",
    "topic": "脑机接口在中风康复中的应用",
    "status": "processing",
    "progress": {
      "step": "generating_review",
      "message": "正在生成综述..."
    }
  }
}
```

### 响应（已完成）

```json
{
  "success": true,
  "data": {
    "task_id": "a1b2c3d4",
    "topic": "脑机接口在中风康复中的应用",
    "status": "completed",
    "progress": {
      "step": "completed",
      "message": "综述生成完成"
    },
    "result": "..."
  }
}
```

`status` 可能值：`pending` → `searching` → `processing` → `completed` / `failed`

---

## GET /api/tasks/{task_id}/review

获取完整综述内容（含 Markdown 正文 + 参考文献列表）。

### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `format` | string | 引用格式：`ieee`（默认）、`apa`、`mla`、`gb_t_7714` |

### 请求示例

```bash
curl "https://scholar.danmo.tech/api/tasks/a1b2c3d4/review?format=ieee" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

### 响应

```json
{
  "success": true,
  "data": {
    "task_id": "a1b2c3d4",
    "topic": "脑机接口在中风康复中的应用",
    "review": "# 脑机接口在中风康复中的应用：文献综述\n\n## 1. 引言\n\n...(完整 Markdown 综述内容)...\n\n## References\n\n[1] Author et al., \"Paper Title\", Journal, 2024.\n...",
    "papers": [
      {
        "title": "Paper Title",
        "authors": ["Author A", "Author B"],
        "year": 2024,
        "doi": "10.xxxx/xxxxx",
        "abstract": "Abstract text..."
      }
    ],
    "cited_papers_count": 35,
    "created_at": "2026-04-25T10:30:00",
    "statistics": {
      "total_papers_searched": 150,
      "papers_cited": 35,
      "word_count": 5200,
      "duration_seconds": 240
    },
    "is_paid": true
  }
}
```

---

## 完整调用流程

```
1. POST /api/skill/research  →  获取 task_id
2. GET  /api/tasks/{task_id}  →  轮询，直到 status == "completed"
3. GET  /api/tasks/{task_id}/review  →  获取完整综述 Markdown
```
```

---

## Step 2: Coze Skill 完整描述 + 提示词

```markdown
# Skill Name: Danmo Scholar - AI文献综述专家

# Skill Description
专业AI文献检索、对比矩阵分析、自动生成完整文献综述。支持中英文，引用真实论文，杜绝幻觉引用。

# Trigger Words
文献综述、科研助手、论文工具、文献矩阵、literature review、generate review、research assistant、paper review

# API Configuration

## Endpoint
```
URL: https://scholar.danmo.tech/api/skill/research
Method: POST
Headers:
  Content-Type: application/json
  Authorization: Bearer {{DANMO_API_TOKEN}}
```

## Request Body Template
```json
{
  "query": "{{用户输入的研究主题}}",
  "language": "{{用户语言：中文主题用zh，英文主题用en}}",
  "max_papers": 30
}
```

## Poll Endpoint
```
URL: https://scholar.danmo.tech/api/tasks/{{task_id}}
Method: GET
Headers:
  Authorization: Bearer {{DANMO_API_TOKEN}}
```

## Review Content Endpoint
```
URL: https://scholar.danmo.tech/api/tasks/{{task_id}}/review
Method: GET
Headers:
  Authorization: Bearer {{DANMO_API_TOKEN}}
```

# System Prompt (给 Coze Bot 的指令)

你是一个专业的学术文献综述助手，集成了 Danmo Scholar 的文献检索和综述生成能力。

## 你的工作流程

1. **接收用户的研究主题**（中文或英文均可）
2. **调用 Danmo Scholar API** 提交综述生成任务
3. **轮询任务状态**（约 3-5 分钟完成），期间告知用户正在处理
4. **获取完整综述内容**并格式化输出

## 输出格式

每次生成综述后，你必须按以下格式输出：

### 格式模板

```
📚 **文献综述：{研究主题}**

---

{完整 Markdown 格式的综述内容，包含：}
- 摘要/引言
- 研究背景
- 主题分类章节（2-4个）
- 文献对比分析
- 研究趋势与展望
- 参考文献（IEEE格式）

---

📊 **统计信息**
- 引用文献数：{N} 篇
- 综述字数：约 {N} 字

---

🔗 **获取更多功能**
> 📖 完整版综述、高清海报下载、Word/PDF导出、对比矩阵、多语言支持
> 👉 访问 [Danmo Scholar 官网](https://scholar.danmo.tech/dashboard?ref=coze_skill) 注册并升级付费
> 🇺🇸 International: [Danmo Scholar](https://en-scholar.danmo.tech/?ref=coze_skill)
> 🎁 新用户注册即送 2 积分（可免费生成 1 篇综述）

---
*Powered by [Danmo Scholar](https://scholar.danmo.tech) — 专业AI文献综述平台*
```

## 重要规则

1. **必须使用消费者变量 `DANMO_API_TOKEN`** 进行认证，不要硬编码任何 Token
2. 如果 API 返回 401 错误，告诉用户：**"请先到 [Danmo Scholar 官网](https://scholar.danmo.tech) 注册账号，在个人中心获取 API Token，然后填入消费者变量 DANMO_API_TOKEN"**
3. 如果 API 返回积分不足，告诉用户：**"您的积分不足，请访问 [Danmo Scholar 官网](https://scholar.danmo.tech/dashboard?ref=coze_skill) 充值，最低 ¥9.9 起"**
4. 每次输出的末尾**必须包含引流文案**
5. 不要编造任何论文信息，所有内容必须来自 API 返回
6. 综述内容使用 Markdown 格式输出

## 错误处理

- **Token 无效 (401)**: "请检查您的 API Token 是否正确。如未注册，请访问 [Danmo Scholar 官网](https://scholar.danmo.tech) 免费注册。"
- **积分不足 (success:false)**: "您的积分不足。请访问 [Danmo Scholar 官网](https://scholar.danmo.tech/dashboard?ref=coze_skill) 充值，支持支付宝和信用卡。"
- **任务失败**: "综述生成失败，请稍后重试或访问 [Danmo Scholar 官网](https://scholar.danmo.tech) 直接生成。"
- **超时**: "综述生成需要 3-5 分钟，请耐心等待。如长时间无响应，请访问 [Danmo Scholar 官网](https://scholar.danmo.tech) 直接生成。"
```

---

## Step 3: 消费者变量配置说明

```markdown
# 消费者变量配置指南

## 什么是消费者变量？

消费者变量允许每个 Coze 用户填入自己的 API Token，而不是使用开发者统一的密钥。
这样每个用户用自己的 Danmo Scholar 账号和积分，实现真正的 SaaS 分发。

## 配置步骤

### 1. 在 Coze 中创建消费者变量

1. 进入 Coze 工作台 → 你的 Bot → **「变量」** 标签页
2. 点击 **「添加消费者变量」**
3. 配置如下：

| 配置项 | 值 |
|--------|-----|
| 变量名 | `DANMO_API_TOKEN` |
| 显示名称 | `Danmo Scholar API Token` |
| 描述 | `你的 Danmo Scholar API 密钥。注册即送 2 积分。获取地址：https://scholar.danmo.tech` |
| 类型 | `String` |
| 是否必填 | `是` |
| 默认值 | （留空） |

### 2. 在 Skill 中引用变量

在 API 请求的 Header 中使用双花括号语法：

```
Authorization: Bearer {{DANMO_API_TOKEN}}
```

### 3. 用户使用流程

1. 用户在 Coze 中使用你的 Bot
2. 首次使用时，Coze 提示用户填写 `DANMO_API_TOKEN`
3. 用户去 [Danmo Scholar 官网](https://scholar.danmo.tech) 注册 → 个人中心 → API Token 区域 → 复制 Token
4. 填入消费者变量 → 即可使用

### 4. 引流机制

- 用户必须先注册 Danmo Scholar 账号才能获得 API Token
- 注册即送 2 积分（可免费生成 1 篇综述）
- 积分用完后需到官网充值 → 自然转化为付费用户
- 每次综述输出都带引流文案 → 持续转化

## API Token 获取路径

```
官网首页 → 验证码登录 → 个人中心(/profile) → 🔑 开发者 API Token → 复制 Token
```

中文站：https://scholar.danmo.tech
英文站：https://en-scholar.danmo.tech
```

---

## Step 4: Skill 输出示例

### 示例 1：中文主题

```markdown
📚 **文献综述：大语言模型在金融风控中的应用**

---

## 1. 引言

近年来，以 GPT-4、DeepSeek 为代表的大语言模型（Large Language Model, LLM）在自然语言处理领域取得了突破性进展。金融风控作为高度依赖数据分析和文本理解的领域，正面临 LLM 技术带来的深刻变革。本文系统梳理了 2020-2026 年间相关文献，从欺诈检测、信用评估、市场风险预测三个维度，分析 LLM 在金融风控中的应用现状与研究趋势。

## 2. LLM 在欺诈检测中的应用

传统欺诈检测主要依赖规则引擎和机器学习模型（如 XGBoost、Random Forest），但面对日益复杂的欺诈手段，传统方法存在特征工程成本高、难以捕捉语义信息等局限。Wang et al. [1] 提出 FinGPT 框架，利用 LLM 的自然语言理解能力分析交易备注和行为文本，在信用卡欺诈检测中实现了 94.2% 的 AUC。Li et al. [3] 进一步结合知识图谱与 LLM，将实体关系建模与文本理解相融合...

## 3. 信用评估中的 LLM 方法

信用评估是金融风控的核心环节。传统评分卡模型依赖结构化数据，难以利用非结构化信息。Zhang et al. [5] 利用 LLM 对借款人的社交媒体文本、财报附注进行语义分析...

## 4. 市场风险预测

LLM 在市场风险预测中的应用主要体现在新闻情绪分析和宏观预测两个方向。Chen et al. [8] 构建了基于 FinBERT 的新闻情绪指标...

## 5. 研究趋势与展望

| 方向 | 代表文献 | 核心方法 | 主要发现 |
|------|----------|----------|----------|
| 欺诈检测 | [1][2][3] | LLM + 知识图谱 | AUC 提升 3-8% |
| 信用评估 | [5][6][7] | LLM + 多模态融合 | 覆盖提升 15% |
| 市场风险 | [8][9][10] | FinBERT + 时序模型 | 预测准确率 87% |

现有研究的主要局限：(1) LLM 的可解释性不足；(2) 实时推理成本高；(3) 金融领域的合规性要求与 LLM 的黑盒特性存在矛盾。未来研究应关注模型蒸馏、可解释 AI 和监管科技三个方向。

## References

[1] Wang, H., et al., "FinGPT: Open-source Financial Large Language Models", *Proceedings of IJCAI*, 2024.

[2] Liu, Y., et al., "Large Language Models for Financial Fraud Detection: A Multi-agent Approach", *ACL Workshop on NLP for Finance*, 2024.

[3] Li, Z., et al., "Knowledge Graph Enhanced LLM for Credit Risk Assessment", *AAAI*, 2025.

... (共 28 篇参考文献)

---

📊 **统计信息**
- 引用文献数：28 篇
- 综述字数：约 4,800 字
- 生成耗时：约 4 分钟

---

🔗 **获取更多功能**
> 📖 完整版综述、高清海报下载、Word/PDF导出、对比矩阵、多语言支持
> 👉 访问 [Danmo Scholar 官网](https://scholar.danmo.tech/dashboard?ref=coze_skill) 注册并升级付费
> 🎁 新用户注册即送 2 积分（可免费生成 1 篇综述）

---
*Powered by [Danmo Scholar](https://scholar.danmo.tech) — 专业AI文献综述平台*
```

### 示例 2：英文主题

```markdown
📚 **Literature Review: Transformer Models for Time Series Forecasting**

---

## 1. Introduction

Time series forecasting is a fundamental task in numerous domains, from financial markets to weather prediction and energy management. The advent of Transformer architecture, originally designed for natural language processing, has sparked significant interest in its adaptation for sequential time series data. This review surveys 32 papers published between 2021 and 2026, examining how Transformer variants have been modified to capture temporal dependencies, handle varying horizons, and address the computational challenges unique to time series data.

## 2. Pure Transformer Approaches

The direct application of self-attention to time series faces key challenges: quadratic complexity with sequence length and inability to capture local patterns effectively. Zhou et al. [1] proposed Informer, introducing a ProbSparse self-attention mechanism that reduces complexity from O(L²) to O(L log L) while maintaining forecasting accuracy on ETTh1 and Weather benchmarks...

## 3. Hybrid Architectures

Recognizing the limitations of pure attention mechanisms, several works combine Transformers with classical time series components. Wu et al. [5] proposed Autoformer, replacing standard attention with auto-correlation mechanism...

## 4. Multi-scale and Hierarchical Methods

Time series data often exhibits patterns at multiple temporal scales. Liu et al. [9] introduced PatchTST, which segments time series into patches...

## 5. Trends and Future Directions

| Direction | Key Papers | Innovation | Performance |
|-----------|-----------|-------------|-------------|
| Efficient Attention | [1][2][3] | Sparse/Linear attention | 3-5x speedup |
| Decomposition | [5][6][7] | Trend-seasonal split | MSE ↓ 15-25% |
| Patching | [9][10][11] | Local patch tokens | SOTA on 6 benchmarks |
| Foundation Models | [15][16] | Pre-trained TS models | Zero-shot capable |

Key challenges remain: (1) distribution shift in non-stationary series, (2) efficient long-horizon forecasting beyond 720 steps, (3) lack of unified benchmarks for fair comparison. The emergence of time series foundation models (e.g., TimesFM, Chronos) represents an exciting frontier.

## References

[1] Zhou, H., et al., "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting", *AAAI*, 2021.

[2] Kitaev, N., et al., "Reformer: The Efficient Transformer", *ICLR*, 2020.

[5] Wu, H., et al., "Autoformer: Decomposition Transformers with Auto-Correlation for Long-Term Series Forecasting", *NeurIPS*, 2021.

... (32 references total)

---

📊 **Statistics**
- Papers cited: 32
- Word count: ~3,200 words
- Generation time: ~4 minutes

---

🔗 **Get More Features**
> 📖 Full review, HD poster download, Word/PDF export, comparison matrix, multi-language support
> 👉 Visit [Danmo Scholar](https://en-scholar.danmo.tech/?ref=coze_skill) to sign up and upgrade
> 🎁 New users get 2 free credits (1 free review)

---
*Powered by [Danmo Scholar](https://en-scholar.danmo.tech) — Professional AI Literature Review Platform*
```
