# CLAUDE.md — Danmo Scholar 项目指引

> 给 Claude Code 的上下文文件，帮助理解项目结构和约定。

## 项目简介

Danmo Scholar — AI 驱动的文献综述生成平台，支持中英文双语。

**技术栈**: FastAPI (Python) + React (TypeScript/Vite) + PostgreSQL + i18n (react-i18next)

**核心流程**: 文献检索 (OpenAlex + Semantic Scholar) → 综述生成 (8步) → 引用校验

> 详细流程: [docs/review_generation_flow.md](docs/review_generation_flow.md)

## 关键文件

### 后端
- `backend/main.py` — 所有 API 路由、中间件、额度检查
- `backend/services/smart_review_generator_final.py` — 综述生成核心
- `backend/services/review_task_executor.py` — 异步任务执行
- `backend/authkit/` — 独立可复用的认证 & 支付模块

### 前端
- `SimpleApp.tsx` — 主页 | `GenerateReviewPage.tsx` — 生成页 | `ReviewPage.tsx` — 综述页
- `ComparisonMatrixViewer.tsx` — 对比矩阵 | `SearchPapersPage.tsx` — 文献搜索
- `DavidPage.tsx` — 数据统计 (`/david`) | `DavidApprovePage.tsx` — 截图审核 (`/david/approve`)
- 认证: 验证码登录（无密码） | 支付: 支付宝(中文) / Paddle(英文)
- 导出: 前端生成，不检查付费（Markdown/Word/PDF/BibTeX/RIS）
- 国际化: `react-i18next` | 路由: hash 路由

## 关键约定

- **JWT**: 用户 ID 在 `sub` 字段
- **额度**: 注册送 2 积分，综述=2积分，对比矩阵=1积分
- **每日搜索**: `DAILY_SEARCH_LIMIT`（.env），User meta_data 跟踪
- **API**: 前端 `localhost:3006 → 8006`，前缀 `/api/...`，认证 `Bearer <token>`
- **定价**: 中文 CNY（¥9.9/¥19.8/¥49.8）| 英文 USD（$9.99/$24.99/$49.99）
- **白名单**: `DAVID_WHITELIST`、`JADE_WHITELIST`、`DEMO_TASK_IDS`（.env 配置）
- **数据库迁移**: `cd backend && python3 -m base migrate --dir migrations`（非 Alembic，自建框架）
- **OAuth**: `backend/authkit/oauth/`（Alipay + Google），Site 判断: Host 含 `en-` → 英文

## 子系统详细文档

| 模块 | 文档 |
|------|------|
| 额度体系 | [docs/CREDIT_SYSTEM.md](docs/CREDIT_SYSTEM.md) |
| 推广邮件 & 分享审核 | [docs/EMAIL_AND_REWARD.md](docs/EMAIL_AND_REWARD.md) |
| 统计功能 | [docs/STATS.md](docs/STATS.md) |
| 部署配置 | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| 综述生成流程 | [docs/review_generation_flow.md](docs/review_generation_flow.md) |
| 辅助脚本 | [docs/SCRIPTS.md](docs/SCRIPTS.md) |

## 文档索引

- [docs/INDEX.md](docs/INDEX.md) — 文档首页
- [docs/MAP.md](docs/MAP.md) — 完整文档目录
- [docs/PRE_COMMIT_CHECKLIST.md](docs/PRE_COMMIT_CHECKLIST.md) — 提交前检查清单
