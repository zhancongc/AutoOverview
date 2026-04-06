# Auth Kit 复用性改进总结

## 改进内容

### 1. 移除业务耦合
- ❌ 删除 `ReviewRecord` 模型（移到项目扩展）
- ❌ 删除 `review_records` 关联关系
- ❌ 删除业务特定字段（`review_count`, `review_quota`, `total_papers_used`）
- ✅ 添加通用 `metadata` 字段（JSON 格式）

### 2. 通用邮件模板系统
- ✅ 创建可配置的邮件模板
- ✅ 支持通过环境变量自定义品牌信息
- ✅ 保留 AutoOverview 专属模板作为参考

### 3. 简化的用户模型

```python
# 通用字段（所有项目通用）
- id, email, hashed_password
- nickname, avatar_url
- gender, country, province, city, language
- is_active, is_verified, is_superuser, is_staff

# 扩展字段（用于存储业务数据）
- metadata (JSON)
```

### 4. 扩展方式

#### 方式 1: 使用 metadata
```python
user.set_meta("quota", 100)
user.set_meta("plan", "premium")
```

#### 方式 2: 创建扩展模型
```python
# models/extended.py
from authkit.models import User, Base

class ReviewRecord(Base):
    user_id = Column(Integer, ForeignKey("users.id"))
    topic = Column(String(500))
```

#### 方式 3: 扩展用户类
```python
class ExtendedUser(User):
    @property
    def quota(self):
        return self.get_meta("quota", 10)
```

## 目录结构

```
auth-kit/                      # 通用认证模块（可复用）
├── core/                      # 核心功能
├── models/                    # 通用数据模型
│   ├── __init__.py           # User 模型（简化版）
│   └── schemas.py            # Pydantic 模型
├── services/                  # 业务服务
├── routers/                   # API 路由
└── templates/                 # 通用邮件模板
    └── base_emails.py        # 可配置模板

models/                        # AutoOverview 特有
└── extended.py                # ReviewRecord 等业务模型

backend/
└── .env.auth.example          # AutoOverview 配置
```

## 配置系统

### 通用配置（auth-kit/.env.example）
```env
AUTH_JWT_SECRET_KEY=...
AUTH_DATABASE_URL=...
AUTH_SMTP_HOST=...
AUTH_SMTP_USER=...
```

### 品牌配置（可选）
```env
AUTH_EMAIL_APP_NAME=Your App
AUTH_EMAIL_APP_URL=https://yourapp.com
AUTH_EMAIL_LOGO_EMOJI=🔐
AUTH_EMAIL_PRIMARY_COLOR=#667eea
```

## 使用示例

### 新项目集成
```bash
# 1. 复制 auth-kit
cp -r auth-kit /path/to/new-project/

# 2. 配置环境变量
cp auth-kit/.env.example .env.auth

# 3. 集成到 FastAPI
from authkit.database import init_database
from authkit.routers import router as auth_router

init_database("sqlite:///./auth.db")
app.include_router(auth_router)
```

### 扩展业务功能
```python
from authkit.models import User

# 创建用户
user = User(email="user@example.com")

# 设置业务数据
user.set_meta("company", "Acme Inc")
user.set_meta("role", "admin")

# 读取业务数据
company = user.get_meta("company")
```

## 文档

| 文档 | 说明 |
|------|------|
| README.md | 项目介绍和快速开始 |
| QUICKSTART.md | 5 分钟集成指南 |
| REUSABILITY.md | 复用性详细文档 |
| .env.example | 配置模板 |

## 兼容性

- ✅ Python 3.8+
- ✅ FastAPI 0.100+
- ✅ SQLAlchemy 1.4/2.0
- ✅ SQLite/PostgreSQL/MySQL

## 零耦合验证

可以通过以下方式验证 auth-kit 的独立性：

```bash
# 检查是否有业务依赖
grep -r "autooverview\|snappicker" auth-kit/
# 应该只在文档/注释中出现

# 检查是否有业务模型引用
grep -r "ReviewRecord" auth-kit/
# 应该没有结果
```

## 复用清单

将 auth-kit 复制到新项目时，只需要：

- [ ] 复制 `auth-kit` 目录
- [ ] 安装依赖
- [ ] 配置环境变量（至少 `AUTH_JWT_SECRET_KEY`）
- [ ] 在 FastAPI 中集成（3 行代码）

即可获得完整的用户认证功能！
