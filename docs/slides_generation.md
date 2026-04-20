# 幻灯片生成文档

> 最后更新: 2026-04-20

## 概述

项目提供 3 个脚本，将 Markdown 综述转换为 HTML 幻灯片，均位于 `backend/scripts/`。

| 脚本 | 框架 | 输出 | 适用场景 |
|------|------|------|----------|
| `md2slides.py` | reveal.js | 单文件 HTML | 轻量、零依赖、短视频展示 |
| `md2slides_slidev.py` | Slidev (Vue) | HTML SPA | 交互丰富、需要 Vue 组件 |
| `md2slides_swd.py` | senangwebs-deck | 单文件 HTML | 简洁、双击即开、密集中文内容 |

## 通用设计原则

所有脚本遵循相同的内容处理策略：

- **段落** → 提取核心观点，一句话概括
- **列表** → 每项截断到关键词
- **大段内容** → 强制拆分到多个 slide
- **参考文献** → 极小字体密集排列
- **布局自适应** → 自动检测表格、两列、三列布局

## 1. md2slides.py — reveal.js 版

### 用法

```bash
python backend/scripts/md2slides.py input.md [-o output.html] [--title "标题"] [--lang zh|en]
```

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `input.md` | 必填 | 输入 Markdown 文件 |
| `-o` | 同名 `.html` | 输出文件路径 |
| `--title` | 从 Markdown 提取 | 幻灯片标题 |
| `--lang` | `zh` | 语言（`zh`/`en`） |

### 技术栈

- reveal.js 5.1.0（CDN 加载）
- Google Fonts：Crimson Pro、Source Sans 3、Noto Sans SC
- 自定义 CSS 紧凑样式，专为短视频展示优化

### 幻灯片结构

1. **标题页** — 标题 + 副标题
2. **大纲页** — 自动从章节标题生成
3. **内容页** — 每个章节拆分为多页，自动布局
4. **参考文献页** — 密集排列
5. **致谢页**

### 特点

- 单文件输出，无外部依赖
- CSS 变量控制主题色（`--accent: #c0392b`）
- 支持两列（`.two-col`）、三列（`.three-col`）布局
- 卡片组件（`.card`）用于对比展示

## 2. md2slides_slidev.py — Slidev 版

### 用法

```bash
python backend/scripts/md2slides_slidev.py input.md [-o output_dir] [--title "标题"] [--no-build]
```

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `input.md` | 必填 | 输入 Markdown 文件 |
| `-o` | 同名目录 | 输出目录 |
| `--title` | 从 Markdown 提取 | 幻灯片标题 |
| `--no-build` | false | 只生成 Slidev Markdown，不构建 HTML |

### 技术栈

- Slidev CLI（`@slidev/cli`）
- Vue.js 组件系统
- Tailwind CSS
- 主题：seriph（学术风格）

### 前置要求

需要 Node.js 环境：

```bash
npm install -g @slidev/cli
```

### 流程

```
input.md → 解析 → 生成 Slidev Markdown → npx slidev build → 输出 HTML SPA
```

### 特点

- 支持 Vue 组件和交互功能
- 输出为完整的 HTML SPA
- 可使用 `--no-build` 只生成中间 Markdown 文件

## 3. md2slides_swd.py — senangwebs-deck 版

### 用法

```bash
python backend/scripts/md2slides_swd.py input.md [-o output.html] [--title "标题"]
```

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `input.md` | 必填 | 输入 Markdown 文件 |
| `-o` | 同名 `.html` | 输出文件路径 |
| `--title` | 从 Markdown 提取 | 幻灯片标题 |

### 技术栈

- senangwebs-deck（SWD，CDN 加载）
- Tailwind CSS（CDN 加载）
- 单文件 HTML 结构

### 特点

- 单文件输出，双击即可打开
- 优化密集中文学术内容
- CSS 覆盖针对学术排版（表格、引用、多列布局）
- 封面页和章节页有居中布局样式

## 文件位置

```
backend/scripts/
├── md2slides.py            # reveal.js 版
├── md2slides_slidev.py     # Slidev 版
└── md2slides_swd.py        # SWD 版
```

## 样式参考

`frontend/.claude-design/slide-previews/` 目录下有设计预览：

| 文件 | 风格 |
|------|------|
| `style-a-swiss.html` | 瑞士风格 |
| `style-b-paper.html` | 纸张风格 |
| `style-c-bold.html` | 粗体信号风格 |
