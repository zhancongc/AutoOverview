# AutoOverview 邮件模板

## 邮件类型

### 1. 验证码邮件

用于登录、注册、重置密码等场景。

**特点：**
- 渐变色头部设计（紫色主题）
- 大字号验证码显示
- 有效期提示
- 安全警告

**预览效果：**
```
┌─────────────────────────────────────┐
│      📚 论文综述生成器               │
├─────────────────────────────────────┤
│                                     │
│ 您好！                             │
│ 您正在进行 登录 操作，验证码如下：  │
│                                     │
│     ┌─────────────────────────┐    │
│     │      1 2 3 4 5 6        │    │
│     └─────────────────────────┘    │
│                                     │
│ 验证码有效期为 10 分钟             │
│                                     │
│ ⚠️ 如果这不是您的操作...          │
│                                     │
│ 联系我们：service@snappicker.com   │
└─────────────────────────────────────┘
```

### 2. 欢迎邮件

用户注册成功后自动发送。

**特点：**
- 热情的欢迎语
- 三大核心功能展示
- CTA 按钮（开始使用）

**预览效果：**
```
┌─────────────────────────────────────┐
│   🎉 欢迎加入 AutoOverview！       │
├─────────────────────────────────────┤
│                                     │
│ 感谢您注册论文综述生成器！          │
│                                     │
│ 🔍 智能检索 - 自动检索相关文献      │
│ 📊 智能分析 - AI 分析文献内容       │
│ ✨ 自动生成 - 一键生成专业综述      │
│                                     │
│      [  开始使用  ]                 │
│                                     │
│ 联系我们：service@snappicker.com   │
└─────────────────────────────────────┘
```

### 3. 密码重置邮件

用户请求重置密码时发送。

**特点：**
- 清晰的重置步骤
- 验证码展示
- 安全提示

## 使用方式

### 在代码中调用

```python
from authkit.services import email_service

# 发送验证码
email_service.send_verification_code(
    to_email="user@example.com",
    code="123456",
    purpose="login"  # login/register/reset_password
)

# 发送欢迎邮件
email_service.send_welcome_email(
    to_email="user@example.com",
    nickname="张三"  # 可选
)

# 发送密码重置邮件
email_service.send_password_reset_email(
    to_email="user@example.com",
    code="654321"
)
```

### 自定义模板

如需修改邮件样式，编辑 `autooverview_emails.py` 文件：

```python
# 修改主题色
将 `#667eea` 改为你的品牌色

# 修改 Logo
将 `📚` 改为你的图标

# 修改功能介绍
修改 feature-list 部分
```

## 配置发件人

在 `.env.auth` 中配置：

```env
AUTH_SMTP_HOST=your-smtp-host.com
AUTH_SMTP_PORT=587
AUTH_SMTP_USER=service@snappicker.com
AUTH_SMTP_PASSWORD=your-password
AUTH_SMTP_FROM_EMAIL=service@snappicker.com
AUTH_SMTP_FROM_NAME=AutoOverview
```

## 邮件发送流程

1. 用户触发操作（登录/注册/重置密码）
2. 系统生成 6 位随机验证码
3. 验证码存入 Redis（10 分钟有效）
4. 调用邮件服务发送 HTML 邮件
5. 用户输入验证码完成验证

## 技术栈

- **模板引擎**: Jinja2
- **邮件协议**: SMTP
- **样式**: 内联 CSS（兼容各大邮箱）

## 兼容性

已测试兼容以下邮箱：
- ✅ Gmail
- ✅ QQ 邮箱
- ✅ 163 邮箱
- ✅ Outlook
- ✅ 企业微信邮箱
