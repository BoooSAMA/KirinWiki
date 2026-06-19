---
title: "Day 24 — 文章排版优化 + 左侧目录导航栏"
date: 2026-06-19
tags: ["typography", "TOC", "UX", "CSS", "JavaScript", "refactoring"]
summary: "移除无效的 prose 类，自定义文章排版样式（行距2.0、标题间距、代码块/引用/表格样式）；客户端动态生成左侧 fixed 目录栏，支持毛玻璃背景、层级缩进、滚动高亮"
description: "修复了两个问题：1) 项目使用 Tailwind 的 prose 类但未安装 @tailwindcss/typography 插件，导致文章排版完全依赖浏览器默认样式，阅读体验差；2) 为长文章添加可跳转的左侧目录栏。方案上用自定义 .article-content 替换 prose，避免引入外部依赖；TOC 用客户端 JS 动态扫描 heading 生成，fixed 定位不占文档流，配合毛玻璃背景和滚动高亮。"
---

# Day 24 — 文章排版优化 + 左侧目录导航栏

## 背景

用户反馈两个问题：

1. **文章排版难受**：正文行距太紧，阅读体验差
2. **长文章缺少目录导航**：如《人类历史的见证集》有多级标题（h2/h3/h4）但没有跳转目录，想快速定位章节需要手动滚动

---

## 问题 1：文章排版优化

### 诊断

项目使用 `<div class="prose max-w-none">` 包裹文章内容，但 Tailwind 的 `prose` 类由 `@tailwindcss/typography` 插件提供，**该项目从未安装该插件**。

| 项目状态 | 是否有 prose 样式 |
|---------|-----------------|
| `package.json` | ❌ 无 `@tailwindcss/typography` 依赖 |
| `astro.config.mjs` | ❌ 无 typography 插件配置 |
| `global.css` | ❌ `@import "tailwindcss"` 后无 `@plugin` 声明 |

结果：`prose` 类不产生任何样式，文章排版完全依赖浏览器默认样式——正文 `line-height` 约 1.2，标题与段落间距不足，代码块、引用、表格等均无合适样式。

### 修复

移除无效的 `prose` 类，用自定义 `.article-content` 替代，在 `global.css` 中定义完整的文章排版体系：

| 要素 | 值 | 说明 |
|------|-----|------|
| 正文字距 | `line-height: 2` | 中文阅读舒适行距 |
| 段落间距 | `margin-bottom: 1.2em` | 段落间呼吸感 |
| h2 间距 | `margin-top: 2em; margin-bottom: 0.6em` | 大标题上下分明 |
| h3 间距 | `margin-top: 1.8em; margin-bottom: 0.5em` | 子标题适当收紧 |
| h4 间距 | `margin-top: 1.5em; margin-bottom: 0.4em` | 最小标题不拥挤 |
| 代码块 | `border + border-radius + 背景` | 与玻璃态风格统一 |
| 引用（blockquote） | `左边框 + 斜体 + 次级文字色` | 标准引用样式 |
| 表格 | `完整边框 + 表头背景` | 数据可读性 |
| 图片 | `max-width: 100% + border-radius` | 自适应 + 圆角 |

所有颜色引用 CSS 变量（`var(--glass-text)`、`var(--glass-border)` 等），跟随时间主题自动切换。

顺便为所有标题添加 `scroll-margin-top: 5rem`，防止锚点跳转时被固定导航栏遮挡。

### 修改文件

| 文件 | 改动 |
|------|------|
| `src/styles/global.css` | 新增完整的 `.article-content` 排版样式（约 110 行） |
| `src/pages/blog/[category]/[slug].astro` | `prose max-w-none` → `article-content` |

---

## 问题 2：左侧目录导航栏

### 需求

在文章页面左侧添加一个 sticky 目录栏，列出文章的所有标题（h2/h3/h4），点击可跳转到对应章节，当前阅读位置高亮。

### 方案选型

#### 方案 A：Astro 服务端渲染（❌ 不可行）

Astro 的 `Content.getHeadings()` 是 **Content Collections API** 的一部分，而本项目使用 `import.meta.glob` 加载 Markdown（Content Collections Collections API 的前身/平替），`getHeadings()` 始终返回空数组。

```javascript
// 在 glob 导入的 Markdown 模块上调用 — 永远为空
ContentComp.getHeadings()  // → []
```

#### 方案 B：客户端动态扫描（✅ 采用）

页面加载后，通过 DOM API 扫描 `.article-content` 下的 `h2/h3/h4` 元素，提取 `id`（Astro 自动为 heading 生成 id）和 `textContent`，动态拼接成 `<a>` 列表插入左侧栏。

**实现细节：**

1. **骨架静态渲染**：TOC 容器用 `fixed` 定位（不占文档流），`display:none` 初始隐藏，内联 `style` 中的 `left` 通过 CSS calc 精确对准主内容左侧位置：

```css
left: max(0.5rem, calc(50% - 28rem - 12rem - 0.75rem));
/* 50% - 28rem = max-w-4xl 左边缘
   -12rem = TOC 宽度 192px
   -0.75rem = 间距 */
```

2. **JS 动态填充**：在 `astro:page-load` 事件中执行：

```javascript
const headings = document.querySelectorAll('.article-content h2, .article-content h3, .article-content h4')
// 遍历 headings，生成对应缩进的 <a> 标签
// h2 → 不缩进，h3 → pl-4，h4 → pl-8 text-xs
nav.innerHTML = html
sidebar.style.display = ''  // 显示侧栏
```

3. **滚动高亮**：监听 `scroll` 事件，遍历 headings 检查其 `getBoundingClientRect().top`，找到第一个在视口顶部的 heading（阈值 120px），对应 TOC 链接加粗变亮：

```javascript
function updateActive() {
  let currentId = ''
  for (const h of headings) {
    if (h.getBoundingClientRect().top <= 120) currentId = h.id
  }
  links.forEach(link => {
    if (link.getAttribute('href') === `#${currentId}`) {
      link.style.color = 'var(--glass-text)'
      link.style.fontWeight = '600'
    }
  })
}
```

### 布局方案

目录栏和标签栏采用 `fixed` 定位（参见 day25）：

| 元素 | 定位 | 显示条件 | 背景 |
|------|------|---------|------|
| TOC 目录 | `fixed top-24`，左贴主内容 | `lg:block`（≥1024px） | 毛玻璃 `bg-[var(--glass-bg)] backdrop-blur-md` |
| 标签栏 | `fixed top-24`，右贴主内容 | `xl:block`（≥1280px） | 毛玻璃 | 
| 标签栏（移动端） | 文章底部 | `xl:hidden` | 跟随卡片背景 |

主内容保持 `max-w-4xl mx-auto` 完全居中，不受两侧元素影响。

### 修改文件

| 文件 | 改动 |
|------|------|
| `src/pages/blog/[category]/[slug].astro` | 新增 TOC 侧栏骨架 + 标签栏 fixed 版 + 客户端 JS（buildTOC 函数 + 滚动高亮 + astro:page-load 触发） |

---

## 学到的概念

| 概念 | 理解 |
|------|------|
| **`getHeadings()` 的局限性** | 是 Astro Content Collections 的 API，对 `import.meta.glob` 方式加载的 Markdown 无效。在非 Content Collections 项目中需要用客户端 DOM 方案替代 |
| **`astro:page-load` 事件的用途** | View Transitions 场景下，`astro:page-load` 在每次导航完成后触发。适用于需要在 SPA 导航后重新初始化的客户端逻辑（TOC 生成、滚动监听等） |
| **CSS `calc()` 与 `max()` 配合 fixed 定位** | 不使用 sticky（依赖文档流）时，`left: max(x, calc(...))` 语法可以同时满足"基于主内容定位"和"不超过视口边界"两个约束 |
| **`getBoundingClientRect()` 做 scroll spy** | 比 Intersection Observer 更轻量（无额外回调队列），在 scroll 事件中直接读取元素相对于视口的位置，触发实时性更好。注意 `{ passive: true }` 不会阻塞滚动 |
| **Tailwind v4 没有 `@tailwindcss/typography`** | v4 的 prose 类需要单独安装该插件，否则 `prose` 类是空类。可考虑完全自定义排版（本项目方案）或安装插件 |

---

## 后续可能的优化

- **TOC 展开/折叠**：长文章的 TOC 默认只显示 h2，点击展开 h3/h4
- **阅读进度指示**：在 TOC 顶部添加当前阅读百分比进度条
- **代码块高亮**：考虑集成 Shiki 或 Prism 实现代码语法高亮
- **`@tailwindcss/typography` 升级评估**：如果 Tailwind v4 的 typography 插件稳定，可以重新评估使用 prose 类
