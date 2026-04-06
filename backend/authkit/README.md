# Auth Kit - 可复用的用户认证模块

一个**完全独立、零耦合**的 FastAPI 认证模块，可轻松集成到任何项目。

## ✨ 特性

- 🔐 **多种登录方式**：密码登录、验证码登录
- 📧 **邮件系统**：可自定义品牌的邮件模板
- 🔑 **JWT 认证**：安全的 Token 机制
- 💾 **多数据库支持**：SQLite、PostgreSQL、MySQL
- 🎨 **可定制**：通过环境变量配置所有选项
- 🧩 **零耦合**：不依赖任何业务代码
- 📦 **开箱即用**：复制即可使用

## 🚀 5 分钟快速开始

```bash
# 1. 复制模块
cp -r auth-kit /path/to/your-project/backend/

# 2. 安装依赖
pip install fastapi sqlalchemy passlib[bcrypt] pydantic-settings jinja2 redis pyjwt

# 3. 配置环境变量
cp auth-kit/.env.example .env.auth
# 编辑 .env.auth 填写 AUTH_JWT_SECRET_KEY

# 4. 集成到 FastAPI
from authkit.database import init_database, get_db as auth_get_db
from authkit.routers import router as auth_router

init_database("sqlite:///./auth.db")
import authkit.routers.auth as auth_module
auth_module.get_db = auth_get_db
app.include_router(auth_router)

# 5. 启动服务
python main.py
```

## 📁 目录结构

```
auth-kit/
├── database.py           # 数据库初始化
├── .env.example          # 配置模板
├── README.md             # 本文档
├── QUICKSTART.md         # 快速开始指南
├── REUSABILITY.md        # 复用性详细文档
├── core/                 # 核心功能
│   ├── config.py         # 配置管理
│   ├── security.py       # JWT/密码加密
│   └── validator.py      # 输入验证
├── models/               # 数据模型
│   ├── __init__.py       # SQLAlchemy User 模型
│   └── schemas.py        # Pydantic 模型
├── services/             # 业务服务
│   ├── auth_service.py   # 认证逻辑
│   ├── email_service.py  # 邮件服务
│   └── cache_service.py  # Redis 缓存
├── routers/              # API 路由
│   └── auth.py           # /api/auth/* 接口
└── templates/            # 邮件模板
    └── base_emails.py    # 可配置的邮件模板
```

## 🔌 API 接口

所有接口挂载在 `/api/auth` 前缀下：

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

## 🎯 用户模型

```python
class User(Base):
    # 基础字段
    id: int
    email: str              # 邮箱（唯一）
    hashed_password: str    # 加密密码

    # 用户信息
    nickname: str           # 昵称
    avatar_url: str         # 头像
    gender: int             # 性别
    country: str            # 国家
    province: str           # 省份
    city: str               # 城市
    language: str           # 语言
    phone_number: str       # 手机号

    # 账号状态
    is_active: bool         # 是否活跃
    is_verified: bool       # 邮箱是否验证
    is_superuser: bool      # 是否超级管理员
    is_staff: bool          # 是否员工

    # 扩展字段（存储业务数据）
    metadata: str           # JSON 格式
```

## 🔧 扩展业务功能

### 使用 metadata 字段

```python
from authkit.models import User

# 设置业务数据
user.set_meta("plan", "premium")
user.set_meta("quota", 100)

# 读取业务数据
plan = user.get_meta("plan", "free")
quota = user.get_meta("quota", 10)
```

### 创建关联表

```python
from authkit.models import Base, User

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company = Column(String(100))

    user = relationship("User", backref="profile")
```

## 🎨 自定义邮件模板

通过环境变量配置品牌信息：

```env
AUTH_EMAIL_APP_NAME=Your App
AUTH_EMAIL_APP_URL=https://yourapp.com
AUTH_EMAIL_LOGO_EMOJI=🚀
AUTH_EMAIL_CONTACT_EMAIL=support@yourapp.com
AUTH_EMAIL_PRIMARY_COLOR=#667eea
AUTH_EMAIL_SECONDARY_COLOR=#764ba2
```

## 📋 配置项

所有配置通过环境变量设置（前缀 `AUTH_`）：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| JWT_SECRET_KEY | JWT 密钥 | **必须设置** |
| DATABASE_URL | 数据库连接 | sqlite:///./auth.db |
| SMTP_HOST | SMTP 服务器 | - |
| SMTP_USER | SMTP 用户名 | - |
| SMTP_PASSWORD | SMTP 密码 | - |
| EMAIL_APP_NAME | 应用名称 | 应用 |
| EMAIL_PRIMARY_COLOR | 主题色 | #667eea |
| REDIS_HOST | Redis 主机 | localhost |
| REDIS_PORT | Redis 端口 | 6379 |

## 📚 更多文档

- [快速开始](./QUICKSTART.md) - 5 分钟集成指南
- [复用性详解](./REUSABILITY.md) - 如何扩展和定制
- [配置模板](./.env.example) - 完整配置示例

## 🌟 使用示例

- **AutoOverview** - 论文综述生成器
- **Snappicker** - 商品推荐系统

## 📄 许可

MIT License
