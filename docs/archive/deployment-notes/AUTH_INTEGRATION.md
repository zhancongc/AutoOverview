# 认证系统使用说明

## 后端配置

### 1. 安装依赖

```bash
cd backend
source .venv/bin/activate
pip install 'passlib[bcrypt]' pydantic-settings jinja2 redis pyjwt
```

### 2. 配置环境变量

复制 `.env.auth.example` 为 `.env.auth` 并填写配置：

```bash
cp .env.auth.example .env.auth
```

编辑 `.env.auth`：

```env
# JWT 配置
AUTH_JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars

# 邮件配置（Gmail 示例）
AUTH_SMTP_HOST=smtp.gmail.com
AUTH_SMTP_PORT=587
AUTH_SMTP_USER=your-email@gmail.com
AUTH_SMTP_PASSWORD=your-app-password
AUTH_SMTP_FROM_EMAIL=your-email@gmail.com
AUTH_SMTP_FROM_NAME=论文综述生成器

# Redis 配置
AUTH_REDIS_HOST=localhost
AUTH_REDIS_PORT=6379
```

### 3. 启动 Redis

```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis
```

### 4. 启动后端服务

```bash
cd backend
source .venv/bin/activate
python main.py
```

## 前端使用

### 登录状态检查

```typescript
import { isLoggedIn, getLocalUserInfo } from './authApi'

// 检查是否已登录
if (isLoggedIn()) {
  const user = getLocalUserInfo()
  console.log('当前用户:', user)
}
```

### API 调用示例

```typescript
import { authApi } from './authApi'

// 密码登录
const data = await authApi.login('user@example.com', 'password')
localStorage.setItem('auth_token', data.access_token)

// 验证码登录
await authApi.sendCode('user@example.com', 'login')
const data = await authApi.loginWithCode('user@example.com', '123456')

// 获取当前用户
const user = await authApi.getCurrentUser()

// 登出
authApi.logout()
```

## 路由说明

- `/login` - 登录页面
- `/` - 首页（需要登录）
- `/review` - 综述展示页面（需要登录）
- `/jade` - 测试界面（无需登录）

## Auth Kit 模块结构

```
backend/auth-kit/
├── core/
│   ├── config.py          # 配置管理
│   ├── security.py        # JWT、密码加密
│   └── validator.py       # 输入验证
├── models/
│   ├── __init__.py        # SQLAlchemy 模型
│   └── schemas.py         # Pydantic 模型
├── services/
│   ├── auth_service.py    # 认证业务逻辑
│   ├── email_service.py   # 邮件服务
│   └── cache_service.py   # Redis 缓存服务
├── routers/
│   └── auth.py            # FastAPI 路由
└── database.py            # 数据库初始化
```

## API 接口

### 认证相关

- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 密码登录
- `POST /api/auth/send-code` - 发送验证码
- `POST /api/auth/login-with-code` - 验证码登录
- `GET /api/auth/me` - 获取当前用户
- `PUT /api/auth/me` - 更新用户信息
- `POST /api/auth/reset-password` - 重置密码

## 复用 Auth Kit 到其他项目

1. 复制 `auth-kit` 目录到新项目
2. 安装依赖
3. 配置环境变量
4. 在 main.py 中集成：

```python
from authkit.database import init_database, get_db as auth_get_db
from authkit.routers import router as auth_router

# 初始化数据库
init_database("sqlite:///./auth.db")

# 注入依赖
import authkit.routers.auth as auth_module
auth_module.get_db = auth_get_db

# 添加路由
app.include_router(auth_router)
```
