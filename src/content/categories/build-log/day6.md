---
title: "Day 6 — 阅读面板加宽 + 透明度滑块修复 + 全站毛玻璃样式统一"
date: 2026-06-02
tags: ["UI", "CSS", "Tailwind", "View Transitions", "Glassmorphism", "Astro"]
description: "阅读面板加宽到 4xl、修复 View Transitions 下透明度滑块不工作、全站返回按钮和社交图标统一毛玻璃样式"
---

## 改动

- **阅读面板加宽**：`max-w-3xl` (768px) → `max-w-4xl` (896px)，文章正文区域宽了 128px
- **透明度滑块修复**：`ReadingBackdrop.astro` 的初始化逻辑移入 `astro:page-load` 事件，解决 View Transitions 客户端导航下组件内联 `<script>` 不重新执行的问题
- **全站返回按钮 + 毛玻璃底**：所有二级页面缺少返回按钮的统一补上，并给返回链接加上 `bg-gray-100/60 backdrop-blur-sm` 浅灰色毛玻璃底，白色背景下清晰可见
- **首页社交图标毛玻璃底**：GitHub Octocat 和 Email 复制按钮同样加上毛玻璃底，与全站风格统一

## 修改文件

### 阅读面板加宽

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/layouts/BaseLayout.astro` | 修改 L18 | `<main>` 的 `max-w-3xl` → `max-w-4xl` |
| `src/components/Navbar.astro` | 修改 L14 | 导航栏同步改为 `max-w-4xl` 保持对齐 |

### 透明度滑块修复

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/components/ReadingBackdrop.astro` | 修改 L57-106 | 脚本用 `document.addEventListener('astro:page-load', initSlider)` 包裹，移除 TypeScript 语法 |

### 返回按钮 + 毛玻璃样式

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/pages/blog/[category]/[slug].astro` | 修改 L69-79 | `← 分类`、`← {catName}` 加毛玻璃底 |
| `src/pages/blog/[category].astro` | 修改 L83-88 | `← 返回分类` 加毛玻璃底 |
| `src/pages/blog/index.astro` | 修改 | 新增 `← 返回首页` 按钮 |
| `src/pages/blog/tags/index.astro` | 修改 L31-35 | `← 分类` 改毛玻璃样式 |
| `src/pages/blog/tags/[tag].astro` | 修改 L78-85 | `← 分类`、`← 标签` 改毛玻璃样式 |
| `src/pages/projects/index.astro` | 修改 | 新增 `← 返回首页` 按钮 |
| `src/pages/pictures.astro` | 修改 | 新增 `← 返回首页` 按钮 |
| `src/pages/about.astro` | 修改 | 新增 `← 返回首页` 按钮 |
| `src/pages/shares.astro` | 修改 | 新增 `← 返回首页` 按钮 |

### 社交图标毛玻璃底

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/pages/index.astro` | 修改 | GitHub 和 Email 按钮加 `bg-gray-100/60 backdrop-blur-sm` 毛玻璃底 |

## 技术细节

### View Transitions 脚本生命周期

Astro 的 `<ClientRouter>` 启用 View Transitions 后，组件级内联 `<script>` 在客户端导航时 **不会重新执行**——只有页面级脚本才会。这导致 `ReadingBackdrop.astro` 中的透明度滑块在从其他页面导航到文章页时虽然 HTML 被加载到了 DOM 中，但事件监听器从未绑定，滑块完全无法操作。

修复方案：用 `astro:page-load` 事件包装初始化逻辑：

```js
document.addEventListener('astro:page-load', initSlider)
```

`astro:page-load` 在**初次加载**和**每次 View Transition 完成后**都会触发，且旧 DOM 被替换后旧监听器自动消失，不存在重复绑定的问题。

### Tailwind 毛玻璃按钮统一样式

全站返回按钮统一使用以下 Tailwind 类：

```css
inline-flex items-center gap-1.5 text-sm no-underline text-gray-500
bg-gray-100/60 backdrop-blur-sm rounded-lg px-3 py-1.5
border border-gray-200/40
hover:bg-gray-200/60 hover:text-gray-700 transition-colors
```

社交图标按钮改为 `p-2` 方形毛玻璃底，与返回按钮的 `px-3 py-1.5` 略有区别但保持同一视觉体系。

### `max-w-3xl` → `max-w-4xl`

Tailwind v4 默认断点值：
| Class | rem | px |
|-------|------|-----|
| `max-w-3xl` | 48rem | 768px |
| `max-w-4xl` | 56rem | 896px |

Navbar 和 `<main>` 必须同步修改，否则导航栏内容会与正文错位。
