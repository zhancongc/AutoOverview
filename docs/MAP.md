# 项目文件目录

> 最后更新: 2026-04-20
>
> 本文档展示项目整体结构和文档目录。
> 如需文档导航，请查看 [INDEX.md](INDEX.md)。

---

## 项目结构

```
AutoOverview/
├── 📄 CLAUDE.md                    # Claude Code 项目指引
├── 📄 README.md                    # 项目说明与快速开始
├── 📄 docker-compose.yml           # PostgreSQL 容器配置
├── 📄 server-install.sh            # 服务器初始化安装脚本
├── 📄 server-update.sh             # 服务器自动更新脚本
├── 📄 setup-ssl.sh                 # SSL 证书配置脚本
├── 📁 docs/                        # 项目文档目录
├── 📁 backend/                     # FastAPI 后端
└── 📁 frontend/                    # React 前端
```

---

## 📁 docs/ — 项目文档

```
docs/
├── 📄 INDEX.md                      # 文档首页（渐进式导航）
├── 📄 MAP.md                        # 本文档（项目文件目录）
├── 📄 PRE_COMMIT_CHECKLIST.md       # 提交前检查清单
├── 📄 SCRIPTS.md                    # 辅助脚本使用说明
├── 📄 DEPLOYMENT.md                 # 服务器部署配置
├── 📄 CREDIT_SYSTEM.md              # 额度体系设计
├── 📄 STATS.md                      # 统计功能文档
├── 📄 async_api.md                  # 异步 API 设计
├── 📄 review_generation_flow.md     # 综述生成流程
├── 📄 slides_generation.md          # 幻灯片生成（3种框架）
├── 📄 smart_review_generator.md     # 综述生成器文档
├── 📄 function_calling_unified.md   # Function Calling 实现
├── 📄 advanced_features.md          # 高级功能说明
├── 📁 archive/                      # 归档文档（历史参考）
└── 📁 samples/                      # 生成样本（测试用）
```

### 归档文档 (archive/)

| 文档 | 说明 |
|------|------|
| `changes2english.md` | 英文版首页改造计划（已完成） |
| `mvp_product.md` | MVP 技术方案（已实施） |
| `relevance_scoring_plan.md` | 相关性评分方案（待实施） |
| `function_calling_integration.md` | Function Calling 集成（已被 unified 版本取代） |

---

## 📁 backend/ — 后端服务

```
backend/
├── 📄 main.py                  # FastAPI 主入口（路由 + 中间件）
├── 📄 database.py              # 数据库初始化
├── 📄 requirements.txt         # Python 依赖
├── 📄 .env                     # 环境变量（不提交）
├── 📁 authkit/                 # 认证 & 支付模块
│   ├── 📄 README.md            # AuthKit 文档
│   ├── 📁 models/              # 数据模型（User, Subscription, PaymentLog）
│   ├── 📁 routers/             # API 路由（auth, stats, subscription, webhook）
│   ├── 📁 services/            # 业务逻辑（auth, stats, email, cache）
│   ├── 📁 middleware/          # 中间件（stats_middleware）
│   ├── 📁 core/                # 核心功能（security, config）
│   └── 📁 templates/           # 邮件模板
├── 📁 services/                # 核心业务服务
│   ├── 📄 smart_review_generator_final.py  # 综述生成核心
│   ├── 📄 review_task_executor.py          # 异步任务执行
│   ├── 📄 task_manager.py                  # 任务管理
│   ├── 📄 progress_messages.py             # 进度消息国际化
│   ├── 📄 paper_filter.py                  # 论文过滤
│   └── 📄 *_search.py                      # 多源文献搜索
├── 📁 models/                  # SQLAlchemy 数据模型
├── 📁 config/                  # 配置文件
└── 📁 tests/                   # 测试用例
```

### 关键文件说明

| 文件 | 说明 |
|------|------|
| `main.py` | FastAPI 应用入口，所有 API 路由、额度检查、每日搜索限制 |
| `services/review_task_executor.py` | 异步任务执行器，含文献搜索进度推送 |
| `services/smart_review_generator_final.py` | 综述生成核心逻辑 |
| `config/__init__.py` | 服务端配置（DAILY_SEARCH_LIMIT 等） |

---

## 📁 frontend/ — 前端应用

```
frontend/
├── 📄 package.json           # Node 依赖
├── 📄 vite.config.ts         # Vite 配置
├── 📁 src/
    ├── 📄 api.ts             # 后端 API 客户端
    ├── 📄 authApi.ts         # 认证 API 客户端
    ├── 📄 main.tsx           # 应用入口（路由配置）
    └── 📁 components/        # React 组件
        ├── 📄 SimpleApp.tsx           # 主页（输入 + 定价）
        ├── 📄 GenerateReviewPage.tsx  # 综述生成页（含文献预览）
        ├── 📄 SearchPapersPage.tsx    # 文献搜索页（每日限制 + 多格式导出）
        ├── 📄 ReviewPage.tsx          # 综述展示页
        ├── 📄 ComparisonMatrixPage.tsx # 对比矩阵页
        ├── 📄 ExportFormatModal.tsx   # 导出格式选择（BibTeX/RIS/Word）
        ├── 📄 LoginModal.tsx          # 登录弹窗（中文）
        ├── 📄 PaymentModal.tsx        # 支付弹窗（支付宝）
        ├── 📄 ProfilePage.tsx         # 个人中心
        └── 📄 DavidPage.tsx           # 数据统计页
```

---

## 技术栈速览

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI + Python |
| 前端框架 | React + TypeScript + Vite |
| 数据库 | PostgreSQL |
| 缓存 | Redis（统计缓存、验证码存储） |
| LLM | DeepSeek API |
| 数据源 | Semantic Scholar, Crossref, DataCite, AMiner |

---

## 环境变量配置（.env）

```bash
# 数据库
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432

# LLM
DEEPSEEK_API_KEY=your_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 每日搜索限制
DAILY_SEARCH_LIMIT=5

# 白名单
DEMO_TASK_IDS=xxx,yyy
DAVID_WHITELIST=email@example.com
JADE_WHITELIST=
```
