# Auth Kit 复用性指南

Auth Kit 设计为完全独立、可复用的认证模块，可以轻松集成到任何 FastAPI 项目。

## 设计原则

### 1. 零耦合
- ❌ 不依赖任何业务特定代码
- ✅ 只使用标准库和通用依赖
- ✅ 通过环境变量配置所有选项

### 2. 可扩展
- ✅ 使用 `metadata` 字段存储业务数据
- ✅ 支持自定义邮件模板
- ✅ 支持多种数据库

### 3. 易集成
- ✅ 复制即用
- ✅ 配置简单
- ✅ 文档完善

## 快速集成到新项目

### 步骤 1: 复制模块

```bash
# 复制 auth-kit 到你的项目
cp -r auth-kit /path/to/your-project/backend/
```

### 步骤 2: 安装依赖

```bash
pip install fastapi sqlalchemy passlib[bcrypt] pydantic-settings jinja2 redis pyjwt
```

### 步骤 3: 配置环境变量

```bash
cp auth-kit/.env.example .env.auth
# 编辑 .env.auth 填写配置
```

**最小配置：**
```env
AUTH_JWT_SECRET_KEY=your-secret-key-min-32-chars
AUTH_DATABASE_URL=sqlite:///./auth.db
```

**完整配置：**
```env
# JWT
AUTH_JWT_SECRET_KEY=your-secret-key-min-32-chars

# 数据库
AUTH_DATABASE_URL=postgresql://user:pass@localhost/db

# 邮件（可选）
AUTH_SMTP_HOST=smtp.gmail.com
AUTH_SMTP_PORT=587
AUTH_SMTP_USER=your-email@gmail.com
AUTH_SMTP_PASSWORD=your-password
AUTH_SMTP_FROM_EMAIL=your-email@gmail.com

# 邮件模板（可选）
AUTH_EMAIL_APP_NAME=Your App
AUTH_EMAIL_APP_URL=https://yourapp.com
AUTH_EMAIL_LOGO_EMOJI=🔐
AUTH_EMAIL_CONTACT_EMAIL=support@yourapp.com
AUTH_EMAIL_PRIMARY_COLOR=#667eea
AUTH_EMAIL_SECONDARY_COLOR=#764ba2

# Redis（用于验证码，可选）
AUTH_REDIS_HOST=localhost
AUTH_REDIS_PORT=6379
```

### 步骤 4: 集成到 FastAPI

```python
# main.py
from fastapi import FastAPI
from authkit.database import init_database, get_db as auth_get_db
from authkit.routers import router as auth_router

app = FastAPI()

# 初始化认证数据库
init_database("sqlite:///./auth.db")

# 注入数据库依赖
import authkit.routers.auth as auth_module
auth_module.get_db = auth_get_db

# 添加认证路由
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "API is running"}
```

### 步骤 5: 启动服务

```bash
python main.py
```

用户表会自动创建！

## 扩展业务功能

### 方式 1: 使用 metadata 字段

```python
from authkit.models import User

# 创建用户时设置业务数据
user = User(email="user@example.com")
user.set_meta("plan", "premium")
user.set_meta("quota", 100)
user.set_meta("company", "Acme Inc")

# 读取业务数据
plan = user.get_meta("plan", "free")
quota = user.get_meta("quota", 10)
```

### 方式 2: 创建扩展模型

```python
# models/business.py
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from authkit.models import Base, User

class UserProfile(Base):
    """用户档案（业务特定）"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company = Column(String(100))
    title = Column(String(100))

    user = relationship("User", backref="profile")
```

### 方式 3: 扩展用户类

```python
# models/extended.py
from authkit.models import User

class ExtendedUser(User):
    """扩展用户模型"""

    @property
    def quota(self):
        return self.get_meta("quota", 10)

    @property
    def is_premium(self):
        return self.get_meta("plan") == "premium"
```

## 自定义邮件模板

### 方式 1: 环境变量配置

```env
AUTH_EMAIL_APP_NAME=My App
AUTH_EMAIL_LOGO_EMOJI=🚀
AUTH_EMAIL_PRIMARY_COLOR=#ff6b6b
```

### 方式 2: 自定义模板

```python
# templates/my_emails.py
from authkit.templates.base_emails import EmailTemplateConfig

class MyEmailConfig(EmailTemplateConfig):
    def __init__(self):
        super().__init__()
        self.app_name = "My App"
        self.logo_emoji = "🚀"
        self.primary_color = "#ff6b6b"

# 使用自定义配置
my_config = MyEmailConfig()
html_content = my_config.render_verification_code(code="123456")
```

## API 接口

所有接口都挂载在 `/api/auth` 前缀下：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 密码注册 |
| POST | `/api/auth/login` | 密码登录 |
| POST | `/api/auth/send-code` | 发送验证码 |
| POST | `/api/auth/login-with-code` | 验证码登录 |
| GET | `/api/auth/me` | 获取当前用户 |
| PUT | `/api/auth/me` | 更新用户信息 |
| GET | `/api/auth/me/stats` | 获取用户统计 |
| POST | `/api/auth/reset-password` | 重置密码 |

## 数据库支持

支持以下数据库：

```python
# SQLite（默认）
init_database("sqlite:///./auth.db")

# PostgreSQL
init_database("postgresql://user:pass@localhost/db")

# MySQL
init_database("mysql://user:pass@localhost/db")

# SQL Server
init_database("mssql+pyodbc://user:pass@dsn")
```

## 目录结构

```
auth-kit/
├── __init__.py
├── database.py           # 数据库初始化
├── .env.example          # 配置模板
├── README.md             # 使用文档
├── QUICKSTART.md         # 快速开始
├── REUSABILITY.md        # 本文档
├── core/
│   ├── __init__.py
│   ├── config.py         # 配置管理
│   ├── security.py       # JWT/密码加密
│   └── validator.py      # 输入验证
├── models/
│   ├── __init__.py       # SQLAlchemy 模型
│   └── schemas.py        # Pydantic 模型
├── services/
│   ├── __init__.py
│   ├── auth_service.py   # 认证业务逻辑
│   ├── email_service.py  # 邮件服务
│   └── cache_service.py  # Redis 缓存
├── routers/
│   ├── __init__.py
│   └── auth.py           # FastAPI 路由
└── templates/
    ├── __init__.py
    └── base_emails.py    # 通用邮件模板
```

## 最佳实践

### 1. 使用环境变量

所有配置都通过环境变量设置，不要硬编码。

### 2. 保持 User 模型纯净

业务特定数据使用 `metadata` 字段或创建关联表。

### 3. 自定义邮件模板

通过环境变量配置品牌信息，而不是修改模板代码。

### 4. 使用独立的数据库

建议使用独立的数据库或 schema，避免与业务表混淆。

### 5. 定期备份

用户数据很重要，定期备份数据库。

## 故障排除

### 问题 1: 表已存在

```python
# 删除旧表重新创建
from authkit.models import Base
from authkit.database import engine
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
```

### 问题 2: 邮件发送失败

检查 SMTP 配置：
- 端口是否正确（通常是 587 或 465）
- 用户名/密码是否正确
- 是否开启了"应用专用密码"

### 问题 3: Redis 连接失败

确保 Redis 正在运行：
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis
```

## 从 AutoOverview 迁移

AutoOverview 项目展示了如何使用和扩展 auth-kit：

1. **基础集成**：见 `main.py`
2. **业务扩展**：见 `models/extended.py`
3. **自定义配置**：见 `.env.auth.example`

参考这些文件了解完整的集成示例。
