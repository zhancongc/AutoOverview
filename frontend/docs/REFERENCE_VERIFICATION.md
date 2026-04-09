# 参考文献验证功能

## 功能说明

每篇参考文献现在都支持在多个第三方平台验证真实性：
- 🔬 **Google Scholar** - 全球最大的学术搜索引擎
- 🎓 **百度学术** - 中文学术资源
- 📚 **Semantic Scholar** - AI驱动的学术搜索
- 🔗 **DOI** - 数字对象标识符

## 使用方式

### 点击标题验证
点击文献标题，会自动在 Semantic Scholar 中搜索该文献

### 点击平台图标
点击右侧的平台图标，直接跳转到对应平台搜索结果

## 视觉效果

```
┌─────────────────────────────────────────────────┐
│ 1. [🔬] [🎓] [📚] [🔗]                          │
│ ────────────────────────────────────────────── │
│ Deep Learning for Image Recognition              │
│ Zhang, Wei, et al. (2023)                       │
└─────────────────────────────────────────────────┘
```

## 链接生成规则

### Google Scholar
```
https://scholar.google.com/scholar?q={encoded_title}
```

### 百度学术
```
https://xueshu.baidu.com/s?wd={encoded_title}
```

### Semantic Scholar
- 优先使用论文的原始 `url` 字段
- 如果没有，使用搜索：`https://www.semanticscholar.org/search?q={encoded_title}`

### DOI
```
https://doi.org/{doi}
```

## 数据要求

后端返回的论文数据应包含以下字段：
```typescript
{
  id: string
  title: string
  authors: string[]
  year: number
  doi?: string
  url?: string  // Semantic Scholar 直接链接
}
```

## 响应式设计

- **桌面端**：显示完整平台名称和图标
- **移动端**：只显示图标，节省空间
- **悬停效果**：平台卡片高亮，提升交互体验

## SEO 优化

- `rel="noopener noreferrer"` - 安全性
- `target="_blank"` - 新标签页打开
- `title` 属性 - 提示用户功能
