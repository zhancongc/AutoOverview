# 英文版前端构建部署指南

## 📋 概述

本指南说明如何构建和部署两个版本的前端：
- **中文版** (dist-zh)：部署到 https://autooverview.snappicker.com
- **英文版** (dist-en)：部署到 https://autooverview.plainkit.top

两个版本共用同一个后端服务（上海服务器）。

## 🎯 英文版特点

### 1. 去中国化内容
- ✅ 删除所有考研、985、课题组师兄、博导群等应试化内容
- ✅ 替换为海外学术场景

### 2. 聚焦核心卖点
- ✅ 100% 真实引用，DOI 可验证
- ✅ 无 AI 幻觉，无虚假论文
- ✅ 学术合规，可直接提交
- ✅ 5 分钟生成终稿

### 3. 简化竞品对比
- ✅ 只保留 Free AI (ChatGPT/DeepSeek) vs AutoOverview
- ✅ 删除国内竞品对比

### 4. 视觉风格
- ✅ 极简蓝白配色
- ✅ 大留白设计
- ✅ 海外学术工具标准风格

### 5. 定价策略
- ✅ 按次定价：$9.99/1篇、$19.99/3篇、$29.99/6篇
- ✅ 无订阅，额度永久有效

## 🚀 构建步骤

### 构建中文版

```bash
cd frontend
npm run build
```

构建产物：`dist-zh/`

### 构建英文版

```bash
cd frontend
npm run build:en
```

构建产物：`dist-en/`

### 同时构建两个版本

```bash
cd frontend
npm run build:both
```

这将同时构建 `dist-zh/` 和 `dist-en/` 两个目录。

## 📦 部署配置

### 中文版部署到上海服务器

```bash
# 部署中文版到上海服务器
rsync -avz dist-zh/ user@autooverview.snappicker.com:/var/www/html/
```

### 英文版部署到纽约服务器

```bash
# 部署英文版到纽约服务器
rsync -avz dist-en/ user@autooverview.plainkit.top:/var/www/html/
```

### 使用部署脚本

```bash
# 部署中文版
./deploy.sh zh

# 部署英文版
./deploy.sh en
```

## 🔧 配置说明

### API 地址自动路由

两个版本都会自动连接到上海服务器的后端 API：

| 版本 | 域名 | API 地址 |
|------|------|----------|
| 中文版 | autooverview.snappicker.com | /api (相对路径) |
| 英文版 | autooverview.plainkit.top | https://autooverview.snappicker.com/api |

### 支付集成

- **中文版**：使用支付宝支付
- **英文版**：使用 Paddle 支付

### 语言默认值

- **中文版**：默认语言为中文
- **英文版**：默认语言为英文

## 📁 文件结构

```
frontend/
├── dist-zh/              # 中文版构建产物
│   ├── index.html
│   └── assets/
├── dist-en/              # 英文版构建产物
│   ├── index.html
│   └── assets/
├── src/
│   ├── components/
│   │   ├── SimpleApp.tsx                 # 中文版组件
│   │   ├── SimpleAppInternational.tsx   # 英文版组件
│   │   └── SimpleAppInternational.css   # 英文版样式
│   └── locales/
│       ├── zh/translation.json           # 中文翻译
│       └── en/translation.json           # 英文翻译
├── index.html            # 中文版入口
├── index.en.html         # 英文版入口
├── vite.config.ts        # Vite 配置（支持双版本构建）
└── package.json          # 包含中英文构建脚本
```

## 🎨 样式差异

### 中文版（SimpleApp.css）
- 丰富的色彩和动效
- 中国化设计元素
- 更多的促销文案

### 英文版（SimpleAppInternational.css）
- 极简蓝白配色
- 大留白设计
- 专业学术风格
- 简洁的视觉层次

## 🔍 验证部署

### 验证中文版

```bash
# 1. 访问中文站
open https://autooverview.snappicker.com

# 2. 检查元素
# - 应该显示中文内容
# - 默认语言为中文
# - API 请求使用相对路径
```

### 验证英文版

```bash
# 1. 访问英文站
open https://autooverview.plainkit.top

# 2. 检查元素
# - 应该显示英文内容
# - 默认语言为英文
# - API 请求指向 snappicker.com
```

### 浏览器控制台验证

```javascript
// 检查构建版本
console.log('Build Version:', __BUILD_VERSION__)

// 检查 API 地址
console.log('API Base:', window.location.hostname.includes('plainkit.top')
  ? 'https://autooverview.snappicker.com/api'
  : '/api')
```

## 📊 关键差异对比

| 特性 | 中文版 | 英文版 |
|------|--------|--------|
| 默认语言 | 中文 | 英文 |
| Hero 标题 | "5分钟，生成一份高水平文献综述" | "100% Real Citations, No Hallucinations" |
| 竞品对比 | 多个国内竞品 | 仅 Free AI vs AutoOverview |
| 定价 | ¥39.8/¥119.4/¥238.8 | $9.99/$19.99/$29.99 |
| 支付方式 | 支付宝 | Paddle |
| 视觉风格 | 丰富色彩 | 极简蓝白 |
| 案例展示 | 中文案例 | 英文案例 |
| 用户评价 | 国内学生 | 海外研究者 |

## 🎯 内容本地化

### 案例展示

**中文版**：
- 深度学习在图像识别中的应用
- 自然语言处理最新进展
- 区块链技术综述

**英文版**：
- Deep Learning in Image Recognition
- Recent Advances in NLP
- Blockchain Technology Survey

### 用户评价

**中文版**：
- "课题组师兄推荐来的..."
- "考研前夜救命神器..."
- "博导群里都在传这个工具..."

**英文版**：
- "Trusted by researchers worldwide..."
- "Saved me weeks of literature searching..."
- "Finally an AI tool that generates real citations..."

## 🔒 安全和合规

### 学术诚信声明

英文版包含学术诚信声明模块，强调：
- 所有引用都是真实可验证的
- 支持 DOI 验证
- 符合学术诚信标准

### 数据隐私

英文版强调：
- GDPR 合规
- 隐私政策
- 服务条款

## 📈 性能优化

### 构建优化

- 代码分割
- 懒加载
- Tree shaking

### 资源优化

- 图片压缩
- CSS 压缩
- JS 压缩

### CDN 加速

建议为静态资源配置 CDN：
- 中文版：国内 CDN
- 英文版：国际 CDN

## 🛠️ 开发模式

### 启动中文版开发服务器

```bash
npm run dev
```

访问：http://localhost:3006

### 启动英文版开发服务器

```bash
npm run dev:en
```

访问：http://localhost:3006（显示英文版）

## 📝 注意事项

1. **环境变量**：英文版无需特殊环境变量配置
2. **构建检测**：使用 `__BUILD_VERSION__` 检测构建版本
3. **API 配置**：根据 hostname 自动选择 API 地址
4. **支付集成**：根据语言自动选择支付方式
5. **SEO 优化**：两个版本有独立的 meta 标签

## 🎉 完成检查清单

部署完成后，使用以下清单验证：

- [ ] 中文站可以正常访问
- [ ] 英文站可以正常访问
- [ ] 中文站默认显示中文
- [ ] 英文站默认显示英文
- [ ] 两个站的 API 请求都正常
- [ ] 登录/注册功能正常（两个站）
- [ ] 支付功能正常（中文站支付宝，英文站 Paddle）
- [ ] 案例展示正常（对应语言的案例）
- [ ] 用户评价正常（对应语言的评价）
- [ ] 定价显示正确（中文版 CNY，英文版 USD）
- [ ] 学术诚信声明显示（英文版）
- [ ] 数据源 logo 显示（英文版）

## 📞 支持

如遇到问题：
1. 检查构建日志
2. 验证环境配置
3. 检查浏览器控制台错误
4. 查看后端日志

## 🚀 部署后下一步

1. 监控两个版本的访问数据
2. 收集用户反馈
3. A/B 测试关键功能
4. 根据数据优化转化率
5. 持续改进用户体验
