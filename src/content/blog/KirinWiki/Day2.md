---
title: "Day 2 — 修复 CSS 骨架问题"
date: 2026-05-29
description: "诊断修复页面 CSS 失效问题：5 个 bug 导致 Tailwind 样式全部未应用"
---

# Day 2 — 修复 CSS 骨架问题

## 问题现象

网站页面呈现「骷髅骨架」状态——文字堆在左上角，没有卡片布局、没有背景色、没有阴影、没有网格。所有 Tailwind CSS 样式完全未应用。

## 根本原因

**`src/layouts/BaseLayout.astro` 没有 import `global.css`**。

虽然 `@tailwindcss/vite` 插件能自动扫描 Astro 组件中的 class，但 Astro 需要组件显式引用 CSS 文件才会将生成的样式注入页面 `<head>`。缺少这行 `import`，所有 `bg-*`、`rounded-*`、`shadow-*`、`grid` 等 Tailwind class 都不会生成对应的 CSS，浏览器只能看到裸 HTML。

## 修复清单

| # | 文件 | 问题 | 修复 |
|---|---|---|---|
| 1 | `src/layouts/BaseLayout.astro` | 缺少 CSS import | 在 frontmatter 中添加 `import "../styles/global.css"` |
| 2 | `src/layouts/BaseLayout.astro` | 文件末尾多余 `---` | 删除末尾多余的 `---` |
| 3 | `src/pages/index.astro` L9 | class 语法错误 | `<p class="text-lg text-gray-500" max-w-lg mx-auto>` → `class="text-lg text-gray-500 max-w-lg mx-auto"` |
| 4 | `src/pages/index.astro` L42 | 多余 `</div>` | 删除没有对应 `<div>` 的 `</div>` |
| 5 | `src/pages/pictures.astro` L4 | title 错误 | `title="Shares"` → `title="Pictures"` |

## 修复内容

### BaseLayout.astro
```diff
---
+ import "../styles/global.css"
  import Navbar from "../components/Navbar.astro"
  const { title } = Astro.props
---
```

末尾删除多余 `---`。

### index.astro
```diff
- <p class="text-lg text-gray-500" max-w-lg mx-auto>
+ <p class="text-lg text-gray-500 max-w-lg mx-auto">
```
删除多余 `</div>`。

### pictures.astro
```diff
- <BaseLayout title="Shares">
+ <BaseLayout title="Pictures">
```

## 学到的教训

1. **Astro 中 CSS 必须被组件引用**——即使使用 `@tailwindcss/vite` 插件，也需要在组件 frontmatter 中 `import` CSS 文件，否则样式不会注入到 HTML。
2. **语法错误会静默降级**——`max-w-lg mx-auto` 被放在 class 引号外时 Astro 不会报错，只是生成无效 HTML，样式不生效。
3. **多余标签破坏结构**——`</div>` 没有对应开标签会导致嵌套错误，但不一定在控制台触发可见错误。
4. **复制粘贴注意细节**——`pictures.astro` 的内容是从 `shares.astro` 复制来的，标题和内容都需要同步修改。

## 验证方式

```bash
npm run dev
```

打开 `http://localhost:4321`，首页应显示：
- 浅灰背景（不再惨白）
- 5 张卡片 2×3 网格布局
- 卡片有白色背景、圆角、阴影、hover 上浮效果
- 顶部导航毛玻璃 sticky
- 所有页面标题正确
