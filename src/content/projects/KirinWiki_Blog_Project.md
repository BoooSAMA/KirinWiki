---
title: "KirinWiki 博客项目 — 架构与技术实现详解"
date: "2026-07-03"
description: "基于 Astro 6 + Tailwind CSS v4 + Three.js 的个人博客站点的完整技术实现与架构解析。覆盖时基主题、3D 场景、自建音乐播放器等核心功能。"
tags: ["Astro", "Tailwind CSS", "Three.js", "Cloudflare", "博客"]
---

# KirinWiki 博客项目 — 架构与技术实现详解

> **项目**: 个人博客与知识维基站点
> **网址**: `kirinwiki.tech`
> **框架**: Astro 6
> **部署**: Cloudflare Pages
> **GitHub**: [BoooSAMA/my-blog](https://github.com/BoooSAMA/my-blog)

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [项目架构](#3-项目架构)
4. [页面路由](#4-页面路由)
5. [核心功能](#5-核心功能)
6. [数据管理](#6-数据管理)
7. [UI/UX 设计](#7-uiux-设计)
8. [本地开发与部署](#8-本地开发与部署)
9. [开发路线图](#9-开发路线图)
10. [经验与踩坑](#10-经验与踩坑)

---

## 1. 项目概述

### 一句话概括

> 基于 Astro 6 的静态博客站点，结合 Tailwind CSS v4、Preact 交互组件、Cloudflare 边缘基础设施，是一个为学习 Web 开发全过程而搭建的个人知识维基。

### 项目背景

这是一个**从零开始学习 Web 开发**的项目。技术选型遵循「先理解原理，再上复杂框架」的思路：

1. **第一阶段**：用 Astro 做纯静态博客，理解 SSG、Markdown 驱动内容、样式系统
2. **第二阶段**：加动态功能（点赞、搜索），理解前后端通信、数据库
3. **第三阶段**：横向拓展到 React/Next.js，建立框架对比认知

### 核心目标

- 拥有一个完全可控的个人网站
- 理解 Web 全链路（DNS → CDN → 静态生成 → 部署）
- 为学习更复杂的前端框架（React/Next.js）打好基础
- 记录技术探索与学习笔记

---

## 2. 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| **框架** | [Astro 6](https://astro.build) | 静态站点生成器，Islands 架构 |
| **样式** | [Tailwind CSS v4](https://tailwindcss.com) | Utility-First CSS，通过 `@tailwindcss/vite` 集成 |
| **交互** | [Preact](https://preactjs.com) | 轻量级 React 替代（3KB），用于点赞等交互组件 |
| **3D 图形** | [Three.js](https://threejs.org) | 首页水晶场景动画（`r184`） |
| **语言** | TypeScript (strict) | 全站 TypeScript |
| **包管理** | npm | Node >= 22.12 |
| **数据库** | Cloudflare D1 | SQLite 兼容的边缘数据库 |
| **存储** | Cloudflare R2 | 图片等媒体文件存储 |
| **部署** | Cloudflare Pages | 全球边缘网络静态托管 |
| **域名** | Cloudflare DNS | DNS 管理与 HTTPS |

### 依赖概览

```json
{
  "dependencies": {
    "@astrojs/cloudflare": "^13.7.0",
    "@astrojs/preact": "^5.1.4",
    "@tailwindcss/vite": "^4.3.0",
    "astro": "^6.3.8",
    "preact": "^10.29.2",
    "tailwindcss": "^4.3.0",
    "three": "^0.184.0"
  },
  "devDependencies": {
    "wrangler": "^4.100.0"
  }
}
```

### Tailwind CSS v4 注意事项

本项目使用 **Tailwind v4**，与 v3 的关键区别：

- **无 `tailwind.config.js`** — 配置通过 CSS 中的 `@theme { ... }` 指令完成
- CSS 入口文件 `src/styles/global.css` 以 `@import "tailwindcss"` 引入
- 基础类名（`flex`、`p-4`、`text-lg` 等）与 v3 兼容
- 在 `.astro` 组件中通过 `import '../styles/global.css'` 导入

---

## 3. 项目架构

### 目录结构

```
my-blog/
├── public/                    # 静态资源（直接复制到 dist）
│   ├── favicon.ico
│   ├── favicon.svg
│   └── music/                 # 音乐播放器歌单文件
├── src/
│   ├── pages/                 # 文件路由（每个文件 = 一个 URL）
│   │   ├── index.astro        # 首页
│   │   ├── about.astro        # 关于
│   │   ├── pictures.astro     # 图片
│   │   ├── shares.astro       # 分享/推荐
│   │   ├── blog/              # 博客分区
│   │   │   ├── index.astro    # 博客分类总览
│   │   │   ├── [category].astro     # 分类页
│   │   │   ├── [category]/          # 分类下文章详情
│   │   │   └── tags/          # 标签页
│   │   └── projects/          # 项目页
│   │       └── index.astro
│   ├── layouts/
│   │   └── BaseLayout.astro   # 全局布局（导航、页脚、播放器、3D背景）
│   ├── components/            # 可复用组件
│   │   ├── Navbar.astro
│   │   ├── Footer.astro
│   │   ├── MusicPlayer.astro
│   │   ├── LikeButton.tsx     # Preact 交互组件
│   │   ├── PostCard.astro
│   │   ├── SmallPostCard.astro
│   │   ├── CategoryDisplay.astro
│   │   └── ReadingBackdrop.astro
│   ├── content/               # 内容集合（Markdown 驱动）
│   │   └── categories/        # 按分类组织的文章
│   │       ├── blog/
│   │       ├── projects/
│   │       ├── interview/
│   │       ├── build-log/
│   │       └── bible/
│   ├── lib/                   # 客户端 JavaScript
│   │   ├── crystalScene.js    # Three.js 3D 场景
│   │   ├── timeTheme.js       # 时基主题切换
│   │   └── colorPalette.js    # 24 色调色板
│   └── styles/
│       └── global.css         # 全局样式 + Tailwind 入口
├── db/                        # 数据库相关
├── functions/                 # Cloudflare Functions
├── astro.config.mjs           # Astro 配置
├── wrangler.jsonc             # Cloudflare Workers 配置
├── AGENTS.md                  # AI 开发助手项目上下文
├── 阶段学习搭建计划.md         # 多阶段学习路线图
└── package.json
```

### 架构特点

```
[用户请求] → [Cloudflare CDN] → [Cloudflare Pages] → [静态 HTML]
                                    │
                            [Astro 构建时]
                            ├── Markdown → HTML 页面
                            ├── Tailwind → 编译后的 CSS
                            └── Preact/JS → 水合交互组件
```

- **静态优先**：构建时生成完整 HTML，无需服务端运行时
- **Islands 架构**：仅在需要交互的地方加载 JavaScript（如点赞按钮）
- **View Transitions**：使用 Astro 的 `<ClientRouter />` 实现 SPA 风格页面切换
- **持久化状态**：音乐播放器状态通过 `data-astro-transition-persist` 在导航间保持

---

## 4. 页面路由

| 路由 | 文件 | 说明 |
|------|------|------|
| `/` | `src/pages/index.astro` | 首页：欢迎语 + 导航卡片 + 点赞 + 社交链接 |
| `/about` | `src/pages/about.astro` | 个人介绍页 |
| `/blog` | `src/pages/blog/index.astro` | 博客分类总览，按分类聚合文章 |
| `/blog/[category]` | `src/pages/blog/[category].astro` | 某分类下的文章列表 |
| `/blog/[category]/[slug]` | 动态路由 | 具体文章页（Markdown 渲染） |
| `/blog/tags` | `src/pages/blog/tags/` | 标签页 |
| `/projects` | `src/pages/projects/index.astro` | 项目作品集 |
| `/pictures` | `src/pages/pictures.astro` | 图片墙 |
| `/shares` | `src/pages/shares.astro` | 推荐分享/资源链接 |

### 内容分类体系

博客内容通过 `src/content/categories/` 下的子目录组织，目前有 5 个分类：

| 分类 | 标识 | 文章数量 |
|------|------|---------|
| 建站日志 | `build-log` | 记录站点搭建过程 |
| 默认 | `blog` | 日常随笔 |
| 作品集 | `projects` | 项目深度解析 |
| 面试 | `interview` | 面试经验 |
| 圣经 | `bible` | 圣经研读笔记 |

---

## 5. 核心功能

### 5.1 时基主题系统（Time-Based Theme）

根据新加坡时间（`Asia/Singapore`）自动切换页面背景色和主题模式：

- 24 色调色板模拟从深夜到日出的自然色彩变化
- 亮度低于阈值时自动切换到夜间主题（`data-theme="night"`）
- 通过 CSS 自定义属性 `--time-bg-color` 控制背景
- 每分钟检查一次时间，整点之间颜色渐变过渡
- 使用 `requestAnimationFrame` 循环驱动，页面不可见时暂停

**关键文件**：
- `src/lib/timeTheme.js` — 时间计算与颜色插值
- `src/lib/colorPalette.js` — 24 色调色板
- `src/styles/global.css` — CSS 变量定义（`:root` / `[data-theme="night"]`）

### 5.2 3D 水晶场景

使用 Three.js 构建的全屏 3D 背景场景：

- 弯曲面地板（基于球体曲率计算）
- 水晶状几何体作为视觉焦点
- 相机缓慢环绕动画
- 场景背景色与时基主题同步
- 通过 `window.__setSceneBackground()` 接口响应主题变化

**关键文件**：
- `src/lib/crystalScene.js`（303 行，Three.js 场景构建）
- 在 `BaseLayout.astro` 中初始化，通过 `data-astro-transition-persist="bg3d"` 保持跨页持久化

### 5.3 音乐播放器

自建的全局音乐播放器，使用 `<audio>` API + 自定义 UI：

- **持久化**：通过 `data-astro-transition-persist` 在 View Transitions 间保持播放状态
- **歌单加载**：支持 `playlist.json`（本地开发）和 `playlist.r2.json`（生产 R2 URL）
- **播放模式**：支持单曲播放、专辑播放、上下曲切换
- **UI 层次**：艺术家 → 专辑 → 歌曲 三级树形结构
- **状态恢复**：通过 `localStorage` 保存播放状态、音量、收起/展开状态
- **彩灯边框**：播放时底部播放栏有渐变色流动动画
- **收起/展开**：可收起为迷你播放器模式
- **键盘快捷键**：空格键切换播放/暂停

**关键文件**：
- `src/components/MusicPlayer.astro`（682 行，完整播放器实现）
- `public/music/playlist.json` / `playlist.r2.json` — 歌单数据

### 5.4 点赞功能

首页的点赞功能使用 Preact 交互组件：

- **组件**：`src/components/LikeButton.tsx`（Preact，`client:load` 水合）
- **后端**：Cloudflare D1 数据库存储点赞数
- **持久化**：使用 `localStorage` 记录用户是否已点赞

### 5.5 毛玻璃 UI（Glassmorphism）

全站采用毛玻璃设计风格：

- 卡片使用 `backdrop-blur-md` + 半透明背景
- CSS 变量体系统一管理颜色主题
- 悬停时边框光晕动画（`ring-glow` 类，`conic-gradient` + CSS `@property`）
- 深色/浅色模式通过 CSS 变量自动适配

### 5.6 调试面板

隐藏的开发者工具（Ctrl+Shift+F 切换）：

- 实时 FPS 显示（绿色 ≥55、黄色 ≥30、红色 <30）
- Three.js 相机坐标（pos + lookAt）
- 点击复制坐标到剪贴板

---

## 6. 数据管理

### 6.1 内容集合（Content Collections）

当前使用 Astro 的 `import.meta.glob` 模式读取 Markdown 文件：

```typescript
const postModules = import.meta.glob("../../content/categories/**/*.md", {
  eager: true,
}) as Record<string, { frontmatter: Record<string, any>; file: string }>
```

文章按分类放在 `src/content/categories/{category}/` 目录下，每个 `.md` 文件自动映射为一个页面。

### 6.2 Cloudflare D1 数据库

用于存储动态数据（点赞数）：

```sql
CREATE TABLE likes (
  slug TEXT PRIMARY KEY,
  count INTEGER DEFAULT 0
);
```

通过 Cloudflare Functions 提供 API 接口，Astro 构建时/运行时调用。

### 6.3 Cloudflare R2 对象存储

- 图片等媒体文件存储在 R2 bucket 中
- 生产环境下的音乐文件 URL 指向 R2
- Markdown 文章通过完整 URL 引用图片

### 6.4 媒体分离策略

**Git 中不存储任何媒体文件**：
- 图片 → Cloudflare R2
- 视频 → YouTube / Bilibili（通过 iframe 嵌入）
- 音乐 → 歌单 JSON + R2 音频文件

---

## 7. UI/UX 设计

### 7.1 设计语言

| 维度 | 风格 |
|------|------|
| **整体风格** | 毛玻璃（Glassmorphism） |
| **配色** | 时基动态背景 + CSS 变量主题 |
| **字体** | 系统字体栈（`font-sans`） |
| **交互反馈** | 悬停光晕、微动效、平滑过渡 |
| **响应式** | Tailwind 断点（`max-sm:` 等） |

### 7.2 CSS 变量体系

```css
:root {
  --glass-bg: rgba(255, 255, 255, 0.85);
  --glass-border: rgba(255, 255, 255, 0.3);
  --glass-text: #374151;
  --glass-text-secondary: #6b7280;
  --glass-text-muted: #9ca3af;
  --glass-bg-secondary: rgba(243, 244, 246, 0.85);
}

[data-theme="night"] {
  --glass-bg: rgba(0, 0, 0, 0.65);
  --glass-text: #e5e7eb;
  /* …暗色变体 */
}
```

### 7.3 文章排版

在 `.article-content` 类中定义了完整的文章排版系统：

- 行高 2.0 的舒适阅读间距
- 多级标题（h2/h3/h4）的层级间距
- 引用块、代码块、表格、图片的统一样式
- 列表缩进与间距

### 7.4 光晕悬停效果

使用 CSS `@property` + `conic-gradient` 实现卡片悬停时的渐变色边框动画：

```css
@property --p {
  syntax: '<percentage>';
  initial-value: 0%;
  inherits: false;
}

.ring-glow:hover::before {
  --p: 100%;  /* 触发 0.6s 过渡动画 */
}
```

---

## 8. 本地开发与部署

### 8.1 环境要求

- **Node.js** >= 22.12
- **npm**（随 Node 安装）

### 8.2 常用命令

```bash
# 启动开发服务器
npm run dev          # http://localhost:4321

# 构建生产版本
npm run build        # 输出到 dist/

# 本地预览构建结果
npm run preview

# 生成 Wrangler 类型
npm run generate-types
```

### 8.3 开发代理配置

开发服务器配置了音乐文件的反向代理：

```js
// astro.config.mjs
server: {
  proxy: {
    '/music/audio': {
      target: 'http://127.0.0.1:8765',
      changeOrigin: true,
    }
  }
}
```

### 8.4 构建与部署

**构建命令**：`npm run build`
**输出目录**：`dist/`

**部署流程**（Cloudflare Pages）：
1. 推送代码到 GitHub
2. Cloudflare Pages 自动检测仓库
3. 执行 `npm run build`，输出 `dist/`
4. 自动部署到全球边缘网络
5. 绑定自定义域名（通过 Cloudflare DNS）

### 8.5 配置文件

| 文件 | 用途 |
|------|------|
| `astro.config.mjs` | Astro 框架配置（集成、Vite、适配器、代理） |
| `wrangler.jsonc` | Cloudflare Workers 配置（D1/R2 绑定） |
| `.env` / `.env.production` | 环境变量（已 gitignore） |
| `tsconfig.json` | TypeScript 严格模式配置 |

---

## 9. 开发路线图

### 当前状态：第一阶段（静态博客脚手架）

已完成的里程碑：
- [x] Astro 6 项目初始化
- [x] Tailwind CSS v4 集成
- [x] 页面路由搭建（首页、博客、项目、关于等）
- [x] Markdown 内容集合
- [x] 全局导航与布局
- [x] 音乐播放器（自建）
- [x] Three.js 3D 背景
- [x] 时基主题系统
- [x] 毛玻璃 UI 主题
- [x] Cloudflare Pages 部署
- [x] 自定义域名绑定

### 第二阶段规划：动态功能

- [ ] 点赞功能（D1 数据库）
- [ ] 搜索功能（Pagefind 或 D1 + Worker）
- [ ] 联系表单
- [ ] 标签系统完善

### 第三阶段规划：横向拓展

- [ ] 尝试用 Next.js 重写或另建项目
- [ ] 深入 React 学习
- [ ] 更多 Cloudflare Workers 实践

---

## 10. 经验与踩坑

### 10.1 Astro + Tailwind v4 集成

**问题**：`npx astro add tailwind` 在 Astro 6 中使用的是 Tailwind v3，但项目要用 v4。

**解决**：手动通过 `@tailwindcss/vite` Vite 插件集成，在 `astro.config.mjs` 的 `vite.plugins` 中添加。CSS 入口文件通过 `@import "tailwindcss"` 引入。

### 10.2 View Transitions 与组件持久化

**问题**：音乐播放器在页面切换时需要保持播放状态不中断。

**解决**：使用 Astro 的 `data-astro-transition-persist` 属性标记持久化元素（`<audio>` 和浮动容器），配合 `localStorage` 保存和恢复播放状态。每次页面切换时，JS 检测 `window.__playerReady` 避免重复初始化。

### 10.3 首屏闪烁（Flash of Unstyled Content）

**问题**：时基背景色在页面加载时会有短暂的白屏闪烁。

**解决**：在 `<head>` 中使用内联阻塞脚本（`is:inline`），在首屏渲染前计算当前时间的背景色并设置到 `document.documentElement`，避免 FOUC。

### 10.4 Tailwind v4 夜间模式

**问题**：Tailwind v4 移除了 `darkMode: 'class'` 配置方式。

**解决**：使用 CSS 变量 + `data-theme` 属性手动控制主题，而非依赖 Tailwind 的 `dark:` 变体。所有颜色通过 `var(--glass-text)` 等自定义属性引用。

### 10.5 Three.js 场景跨页复用

**问题**：每次页面切换都重新创建 Three.js 场景会导致性能问题和闪烁。

**解决**：通过 `data-astro-transition-persist="bg3d"` 保持 Canvas 元素，`window.__bg3dInitialized` 标记防止重复初始化，场景背景色通过 `window.__setSceneBackground` 函数接口响应主题变化。

### 10.6 Astro 6 + Cloudflare Adapter

**问题**：`@astrojs/cloudflare` 适配器在 Astro 6 中有特定版本要求。

**解决**：锁定 `@astrojs/cloudflare@^13.7.0` 与 `astro@^6.3.8` 版本配对，使用 `wrangler@^4.100.0` 管理 Cloudflare 资源。

---

## 附录：关键文件索引

| 文件 | 行数 | 功能 |
|------|------|------|
| `src/layouts/BaseLayout.astro` | 154 | 全局布局（导航、3D 场景、播放器、FOUC 防护、调试面板） |
| `src/components/MusicPlayer.astro` | 682 | 自建音乐播放器完整实现 |
| `src/components/LikeButton.tsx` | - | Preact 点赞组件 |
| `src/lib/crystalScene.js` | 303 | Three.js 3D 水晶场景 |
| `src/lib/timeTheme.js` | 118 | 时基主题切换 |
| `src/styles/global.css` | 207 | 全局样式 + Tailwind v4 入口 |
| `src/pages/blog/index.astro` | 119 | 博客分类总览页 |
| `src/pages/index.astro` | 89 | 首页 |
| `astro.config.mjs` | 27 | Astro + Vite + Preact + Cloudflare 配置 |

