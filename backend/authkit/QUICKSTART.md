# Auth Kit 快速集成指南

将 auth-kit 复制到你的项目后，按以下步骤集成：

## 1. 复制模块

```bash
# 复制整个 auth-kit 目录到你的项目
cp -r auth-kit /path/to/your-project/backend/
```

## 2. 安装依赖

```bash
pip install passlib[bcrypt] pydantic-settings jinja2 redis pyjwt sqlalchemy
```

## 3. 配置环境变量

```bash
# 复制配置模板
cp auth-kit/.env.example .env.auth

# 编辑配置文件，填写必需的配置项
nano .env.auth
```

**必须配置的项：**
- `AUTH_JWT_SECRET_KEY` - JWT 密钥
- `AUTH_SMTP_*` - 邮件服务配置

## 4. 集成到 FastAPI

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

## 5. 前端调用示例

```typescript
// 登录
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
})
const data = await response.json()

// 保存 token
localStorage.setItem('auth_token', data.access_token)

// 后续请求携带 token
const userResponse = await fetch('/api/auth/me', {
  headers: { 'Authorization': `Bearer ${data.access_token}` }
})
```

## 6. 目录结构

```
your-project/
├── auth-kit/           # 认证模块
│   ├── .env.example    # 配置模板
│   ├── README.md       # 详细文档
│   ├── core/           # 核心功能
│   ├── models/         # 数据模型
│   ├── services/       # 业务服务
│   └── routers/        # API 路由
├── main.py             # 你的应用入口
└── .env.auth           # 认证配置（从 .env.example 复制）
```

## 7. 常见问题

**Q: 邮件发送失败？**
A: 检查 SMTP 配置，Gmail 需要使用"应用专用密码"

**Q: Redis 连接失败？**
A: 确保 Redis 服务已启动：`brew services start redis` (macOS)

**Q: Token 无效？**
A: 检查 `AUTH_JWT_SECRET_KEY` 是否设置且保持一致

## 8. 下一步

- 阅读 [README.md](./README.md) 了解完整 API 文档
- 查看示例项目获取完整集成代码
