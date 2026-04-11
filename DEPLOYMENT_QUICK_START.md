# 快速部署指南 - 多前端单后端架构

## 📋 部署前准备

### 1. 确认服务器信息
- **上海服务器**（主服务器）:
  - 域名: `autooverview.snappicker.com`
  - 用途: 前端 + 后端 + 数据库
  
- **纽约服务器**（前端服务器）:
  - 域名: `autooverview.plainkit.top`
  - 用途: 仅前端（静态文件）

### 2. 确认后端已在上海服务器运行
```bash
# 测试后端 API
curl https://autooverview.snappicker.com/api/health
```

## 🚀 快速部署步骤

### 第一步：构建前端

```bash
cd frontend
npm install
npm run build
```

### 第二步：部署到上海服务器（中文站）

```bash
# 方法 1: 使用部署脚本
./deploy.sh shanghai

# 方法 2: 手动部署
rsync -avz dist/ user@autooverview.snappicker.com:/var/www/html/

# 方法 3: 如果有 SSH 访问权限
scp -r dist/* user@autooverview.snappicker.com:/var/www/html/
```

### 第三步：部署到纽约服务器（英文站）

```bash
# 方法 1: 使用部署脚本
./deploy.sh newyork

# 方法 2: 手动部署
rsync -avz dist/ user@autooverview.plainkit.top:/var/www/html/

# 方法 3: 如果有 SSH 访问权限
scp -r dist/* user@autooverview.plainkit.top:/var/www/html/
```

### 第四步：验证部署

#### 验证中文站
```bash
# 1. 访问网站
open https://autooverview.snappicker.com

# 2. 测试 API
curl https://autooverview.snappicker.com/api/health
```

#### 验证英文站
```bash
# 1. 访问网站
open https://autooverview.plainkit.top

# 2. 浏览器中测试 API
# 打开控制台 (F12) -> Network -> 发起请求 -> 检查 URL
# 应该看到请求指向: https://autooverview.snappicker.com/api
```

## 🔧 配置说明

### API 地址自动选择

前端代码会根据域名自动选择 API 地址：

| 部署位置 | 域名 | API 地址 |
|---------|------|----------|
| 上海服务器 | autooverview.snappicker.com | /api (相对路径) |
| 纽约服务器 | autooverview.plainkit.top | https://autooverview.snappicker.com/api |

### 无需额外配置

- ✅ 不需要配置环境变量
- ✅ 不需要修改构建产物
- ✅ 同一套代码适用于两个服务器

## ⚠️ 常见问题

### 问题 1: CORS 错误

**症状**: 纽约前端访问上海后端时出现 CORS 错误

**解决方案**: 
确认上海服务器后端已配置 CORS：
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 已配置
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 问题 2: 支付回调错误

**症状**: 支付成功后没有正确返回

**解决方案**:
1. 检查上海服务器的 FRONTEND_URL 配置
2. 确认支付平台的回调地址指向上海服务器
3. 查看上海服务器的后端日志

### 问题 3: 性能问题

**症状**: 纽约前端访问速度慢

**解决方案**:
1. 启用 CDN 加速静态资源
2. 使用 gzip/brotli 压缩
3. 优化图片和代码分割

## 📊 监控建议

### 后端监控

在上海服务器添加请求来源监控：

```python
# 记录来自不同域名的请求
logger.info(f"Request from: {request.headers.get('origin', 'unknown')}")
```

### 前端监控

在浏览器控制台检查：
```javascript
// 检查 API 基础地址
console.log('API Base:', window.location.hostname.includes('plainkit.top') 
  ? 'https://autooverview.snappicker.com/api' 
  : '/api')
```

## 🎯 验证清单

部署完成后，使用以下清单验证：

- [ ] 中文站可以访问
- [ ] 英文站可以访问
- [ ] 中文站 API 请求正常
- [ ] 英文站 API 请求指向上海服务器
- [ ] 登录功能正常（两个站）
- [ ] 注册功能正常（两个站）
- [ ] 支付功能正常（中文站）
- [ ] 支付功能正常（英文站）
- [ ] 语言切换正常
- [ ] 日期格式显示正确

## 📞 支持

如果遇到问题：
1. 查看完整的架构文档: `MULTI_FRONTEND_ARCHITECTURE.md`
2. 检查后端日志
3. 使用浏览器开发者工具调试
4. 运行验证脚本: `./verify-api.sh`

## 🎉 完成

部署完成后，你将拥有：
- ✅ 统一的后端服务（上海）
- ✅ 两个前端站点（中文 + 英文）
- ✅ 简化的部署流程
- ✅ 集中的数据管理