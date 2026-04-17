# CLAUDE.md — AutoOverview 项目指引

> 给 Claude Code 的上下文文件，帮助理解项目结构和约定。

## 项目简介

AutoOverview 是一个 AI 驱动的文献综述生成平台，支持中英文双语。用户输入研究主题，系统自动搜索文献并生成高质量的学术综述。

**产品定位**：
- **中文版**：面向中国高校和科研机构的学生、研究人员
- **英文版**：面向国际市场（美国、加拿大、英国、欧盟）的学术用户

**技术栈**: FastAPI (Python) + React (TypeScript/Vite) + PostgreSQL + i18n (react-i18next)

## 核心流程

1. **阶段1**: PaperSearchAgent - LLM + Function Calling 驱动的文献检索（Semantic Scholar）
2. **阶段2**: SmartReviewGeneratorFinal - 生成综述（预处理 → 初始生成 → 5条引用规范应用 → IEEE 格式）
3. **阶段3**: CitationValidatorV2 - 额外引用校验和修复

## 关键约定

### 后端
- **主入口**: `backend/main.py` — 所有 API 路由、中间件、额度检查
- **综述生成核心**: `backend/services/smart_review_generator_final.py`
- **异步任务**: `backend/services/review_task_executor.py`，通过 TaskManager 管理轮询
- **进度推送**: 文献搜索完成后通过 `progress.papers` 向前端推送文献列表预览
- **认证模块**: `backend/authkit/` — 独立可复用的认证 & 支付模块
- **统计模块**: `backend/authkit/services/stats_service.py` — 访问量、注册量统计
- **统计中间件**: `backend/authkit/middleware/stats_middleware.py` — 自动统计访问量（DDoS 防护）
- **JWT**: token 中用户 ID 存储在 `sub` 字段，不是 `user_id`
- **额度体系**: 注册送 2 积分，按次扣费（综述=2积分，对比矩阵=1积分），字段 `review_credits`
- **每日搜索限制**: `DAILY_SEARCH_LIMIT`（.env 配置，默认 5），通过 User meta_data 跟踪
- **环境变量**: `backend/.env` 配置 DeepSeek API Key、数据库等

### 前端
- **主页**: `SimpleApp.tsx`（输入框 + 定价卡片 + 功能介绍）
- **综述生成页**: `GenerateReviewPage.tsx`（输入 → 提交 → 进度条 + 文献预览 → 跳转结果）
- **文献搜索页**: `SearchPapersPage.tsx`（独立文献搜索，每日限制，导出 BibTeX/RIS/Word）
- **综述页**: `ReviewPage.tsx`（正文/参考文献分 Tab，URL: `/review?task_id=xxx`）
- **对比矩阵页**: `ComparisonMatrixPage.tsx` → `ComparisonMatrixViewer.tsx`
- **渲染器**: `ReviewViewer.tsx`（Markdown + TOC 侧边栏，标题级别会自动标准化）
- **数据统计**: `DavidPage.tsx`（访问量、注册量、付费数据统计，URL: `/david`）
- **认证**: 验证码登录（无密码），`LoginModal.tsx`（中文）/ `LoginModalInternational.tsx`（英文）
- **支付**:
  - 中文版：`PaymentModal.tsx`（支付宝扫码，CNY 定价）
  - 英文版：`PaddlePaymentModal.tsx`（Paddle 信用卡支付，USD 定价）
- **导出**:
  - PDF: `frontend/src/utils/pdfExport.ts`（html2canvas + jsPDF，纯前端）
  - Word: `backend/services/docx_generator.py`（服务端 python-docx）
  - 文献列表: `ExportFormatModal.tsx`（前端生成 BibTeX/RIS/Word 三种格式）
- **国际化**: `react-i18next` - 支持中英文动态切换
- **路由**: hash 路由（`/#/login`, `/#/pricing`, `/#/profile`）

### 额度与导出逻辑
- 免费额度：注册送 2 积分，可导出带水印 PDF
- 付费额度：可导出无水印 Word（服务端 python-docx）
- 生成时立即扣额度（`check_and_deduct_credit`），任务失败不退回
- 导出 Word 时检查 `has_purchased`，未购买弹支付弹窗

### 每日搜索限制
- 注册用户每日搜索文献次数限制，默认 5 次（`DAILY_SEARCH_LIMIT` 在 .env 配置）
- 通过 User 的 `meta_data` JSON 字段存储 `search_count_date` 和 `search_count`
- 未登录用户点搜索弹出登录弹窗，登录后自动继续搜索（`pendingSearchTopic` 机制）

### 定价策略
**中文版（CNY）**：
- 体验包（1篇）：¥29.8（原价 ¥39.8）
- 标准包（3篇）：¥69.8（原价 ¥89.4，约 ¥23.3/篇）
- 进阶包（6篇）：¥109.8（原价 ¥178.8，约 ¥18.3/篇）

**英文版（USD）**：
- Starter（6 credits）：$9.99
- Semester Pro（20 credits）：$24.99
- Annual Premium（50 credits）：$49.99

### API 路径
- 前端代理: `localhost:3000` → `localhost:8000`（vite.config.ts 配置）
- API 前缀: `/api/...`
- 认证头: `Authorization: Bearer <token>`

### 白名单配置
- **案例展示**: `DEMO_TASK_IDS`（.env 配置）
- **David 页面**: `DAVID_WHITELIST=zhancongc@icloud.com`（.env 配置）
- **Jade 页面**: `JADE_WHITELIST=`（.env 配置）

## 文档

- **[docs/INDEX.md](docs/INDEX.md)** — 文档首页，渐进式披露文档（推荐从这里开始）
- **[docs/MAP.md](docs/MAP.md)** — 完整文档目录，包含所有文档的列表
- **[docs/PRE_COMMIT_CHECKLIST.md](docs/PRE_COMMIT_CHECKLIST.md)** — 提交前检查清单
- **[docs/STATS.md](docs/STATS.md)** — 统计功能文档
- **[docs/CREDIT_SYSTEM.md](docs/CREDIT_SYSTEM.md)** — 额度体系设计
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** — 服务器部署配置
