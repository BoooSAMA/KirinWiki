---
title: "Day 1 — 搭建个人网站的地基"
date: 2026-05-28
tags: ["Astro", "Cloudflare", "Tailwind", "Deployment", "DNS"]
description: "注册 Cloudflare / GitHub，买域名，部署 Astro 博客，搭建页面骨架，Tailwind CSS 初装修"
---

# Day 1 — 搭建个人网站的地基

## 今日完成

### 🧱 基础设施搭建

- [x] 注册 **Cloudflare** 账号
- [x] 注册 **GitHub** 账号
- [x] 购买域名（Cloudflare Registrar，.com $10/年）
- [x] 安装 **Node.js**（LTS 版本）
- [x] 安装 **VS Code** + Astro / Tailwind IntelliSense 扩展
- [x] 安装 **Git**

### 🚀 部署上线

- [x] 用 `npm create astro@latest` 创建项目（选 minimal template + TypeScript）
- [x] 安装 Tailwind CSS：`npx astro add tailwind`
- [x] 推送到 GitHub 仓库
- [x] Cloudflare Pages 连接 GitHub 自动部署
- [x] 绑定子域名 `blog.我的域名.com`
- [x] SSL 证书自动签发
- [x] 开启 Bot Fight Mode（Cloudflare → Security → Bots）

### 🏗️ 页面骨架

按「个人主页 + 博客 + 作品集 + 图片 + 推荐 + 关于」的结构搭建了完整路由：

```
/
├── /          首页
├── /blog      博客列表
├── /projects  作品集
├── /pictures  图片墙
├── /shares    推荐分享
└── /about     关于我
```

新建的文件：

- `src/layouts/BaseLayout.astro` — 全局页面外壳
- `src/components/Navbar.astro` — 顶部导航
- `src/pages/index.astro` — 首页
- `src/pages/blog/index.astro` — 博客列表
- `src/pages/projects/index.astro` — 作品集列表
- `src/pages/pictures.astro` — 图片墙
- `src/pages/shares.astro` — 推荐分享
- `src/pages/about.astro` — 关于我

### 🎨 Tailwind CSS 初装修

#### BaseLayout.astro

- 全局背景改为 `bg-gray-50`（浅灰色，不再是惨白）
- 内容区域 `max-w-3xl mx-auto`（居中，最宽 768px，阅读舒适）
- `px-6 py-12`（内容区有呼吸空间）

#### Navbar.astro

- 横排导航条，左侧网站名，右侧链接列表
- `sticky top-0` + `backdrop-blur`（滚动时导航始终粘在顶部，毛玻璃效果）
- 当前页面高亮：用 `Astro.url.pathname` 判断，当前页 `font-medium text-gray-900`，其余 `text-gray-500`
- 悬停时颜色过渡 `hover:text-gray-900 transition-colors`

#### index.astro（首页）

- 顶部大标题 `text-4xl font-bold` + 一句话介绍
- 板块入口改为 5 张卡片（2×2/3 网格 `grid grid-cols-2 sm:grid-cols-3`）
- 卡片样式：`bg-white rounded-2xl shadow-sm border`，hover 时 `shadow-md -translate-y-1`（阴影加深 + 上浮 1px）
- 底部社交链接：GitHub / Bilibili / Email

#### blog/index.astro（博客列表）

- 文章卡片：`bg-white rounded-xl shadow-sm border`，带日期、标题、摘要
- 日期灰色小字 `text-sm text-gray-400`

---

## 学到的概念

| 概念 | 理解 |
|------|------|
| Cloudflare Pages vs Workers | Pages 管静态网站托管，Workers 管边缘函数（动态 API） |
| Astro Island 架构 | 默认零 JS，交互组件按需加载 |
| 边缘 CDN | 网站文件分布在全球 330+ 节点，用户访问就近加载 |
| 代码与媒体分离 | 图片存 R2，视频存 YouTube/Bilibili，不进 Git 仓库 |
| ISR vs SSG vs SSR | 纯静态（预生成）、增量静态（缓存定时刷新）、服务端动态（每次渲染） |
| Serverless | 不用管服务器，平台自动处理扩容/缩容 |
| 公开仓库安全 | Astro 项目无敏感信息，公开是对的；以后有 API 密钥用 `.env` + 环境变量 |

---

## 技术栈总览

```
学习阶段 1（今天）：
  Astro + Tailwind CSS → Cloudflare Pages → Cloudflare DNS → GitHub
```

---

## 下一步

填首页自我介绍 → 写第一篇博客文章 → 搭作品集页面 → 加图片墙
