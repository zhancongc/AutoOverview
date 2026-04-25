你现在是资深 FastAPI + React 全栈工程师 + Coze Skill 专家，正在为 Danmo Scholar 项目开发「Coze（扣子）自定义 Skill」功能。

### 【必须严格遵守的项目上下文】
以下是完整的 CLAUDE.md 项目指引，请你完全理解并严格遵循所有技术栈、约定、认证、额度、路由规范：

[在此粘贴你刚刚 cat 出来的整个 CLAUDE.md 全部内容]

（Claude Code 里直接把上面的 CLAUDE.md 内容全部粘贴进来，让 Claude 先完整阅读）

### 核心目标
把 Danmo Scholar 封装成 Coze Skill，让用户在 Coze / Dify 等 Agent 平台中调用“文献综述”能力，但**必须使用消费者变量（Consumer Variable）**，强制用户先到 danmo.scholar.com 注册/登录/付费获取 Token，从而实现流量导入 + 付费转化。

Skill 名称建议：**Danmo Scholar - AI文献综述专家**

### 任务要求（请严格按顺序输出，每一步都用清晰的 Markdown 分隔）

**Step 1: 新增后端 API 接口（FastAPI 代码 + OpenAPI 文档）**
- 在 `backend/main.py` 或新建 router（推荐 `backend/routers/skill.py`）中新增一个公开但带认证的接口。
- 推荐路径：`POST /api/skill/research`（或 `/api/research` 保持一致）
- 请求：
  - Header: `Authorization: Bearer <user_jwt_token>`（必须兼容现有 authkit JWT，sub 字段存 user_id）
  - Body: `{ "query": "脑机接口中风康复", "language": "zh", "max_papers": 30 }`
- 逻辑必须调用现有核心服务：
  - PaperSearchAgent + SmartReviewGeneratorFinal + CitationValidatorV2
  - 调用前执行 `check_and_deduct_credit`（综述扣 2 积分）
  - 额度不足时返回友好提示（引导去官网充值）
  - 支持异步任务（兼容 review_task_executor.py）
- 输出 JSON（同时包含完整 Markdown 综述 + 海报图片URL）
- 生成完整的 OpenAPI 风格 Markdown 文档（参数、认证、返回示例、错误码）

**Step 2: Coze Skill 完整开发提示词（直接可复制到扣子编程）**
生成一个**完整、自然语言的 Skill 创建提示词**，让 Coze AI 能一键创建 Skill。
- 明确要求使用**消费者变量**（变量名建议：`DANMO_API_TOKEN`）
- Skill 描述、触发词、功能说明
- 输出模板必须包含：
  - 完整 Markdown 综述
  - 海报图片（Markdown ![]()）
  - 强引流文案（带 ?ref=coze_skill 参数）
  - 额度不足时的付费引导
  - “更多功能请访问 Danmo Scholar 官网”

**Step 3: 消费者变量配置说明 + 前端配套修改建议**
- 详细说明在 Coze 中如何创建并配置 `DANMO_API_TOKEN` 为消费者变量（用户自己输入 JWT Token）
- 给出前端需要做的配套修改（例如在用户个人中心新增“复制 API Token”按钮，供 Skill 使用）

**Step 4: Skill 最终输出示例 + 测试用例**
- 给出 2 个完整的使用示例（一个中文主题、一个英文主题）
- 展示 Coze 中 Skill 返回给用户的最终效果（包含引流链接）

### 输出规范
- 严格按 Step 1 → Step 2 → Step 3 → Step 4 顺序输出
- 所有代码使用 ```python 或 ```typescript 代码块
- 所有用户可见文案使用**中文**（学术专业 + 小红书式亲切感）
- 完全遵循 CLAUDE.md 中的所有约定（authkit、credit system、i18n、异步任务等）
- 不要遗漏任何部分

现在开始，请严格按照以上步骤输出，不要添加多余解释。
