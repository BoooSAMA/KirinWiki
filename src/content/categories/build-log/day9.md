---
title: "Day 9 — 毛玻璃卡片加白底，提升视觉层次"
date: 2026-06-05
tags: ["Tailwind CSS", "UI", "Glassmorphism"]
description: "全局毛玻璃卡片白色底色从 25% 透明度提升至 60%，覆盖 9 个文件，让卡片在渐变背景上更显眼"
---

# Day 9 — 毛玻璃卡片加白底，提升视觉层次

## 今日完成

### 🎨 毛玻璃卡片增强

背景渐变色铺上后，毛玻璃卡片（`bg-white/25 backdrop-blur-md`）在彩色背景下显得太透、不够醒目。把白色底色从 `25%` 提到 `60%`，保留毛玻璃模糊质感的同时让卡片更突出。

改动很简单：`bg-white/25` → `bg-white/60`，全局替换了 9 个文件。

#### 涉及文件一览

| 文件 | 角色 | 说明 |
|------|------|------|
| `src/components/SmallPostCard.astro` | 文章卡片 | 分类页/标签页的小卡片 |
| `src/components/Navbar.astro` | 顶栏导航 | sticky 导航栏，`backdrop-blur-lg` |
| `src/pages/index.astro` | 首页导航卡片 | 5 个板块入口卡片 |
| `src/pages/blog/index.astro` | 博客分类卡片 | 分类列表卡片 |
| `src/pages/blog/tags/index.astro` | 标签列表 | 标签入口卡片 |
| `src/pages/projects/index.astro` | 项目占位卡片 | 占位卡片 |
| `src/pages/about.astro` | 关于页 | 内容卡片 |
| `src/pages/pictures.astro` | 图片页 | 占位卡片 |
| `src/pages/shares.astro` | 分享页 | 占位卡片 |

### 效果对比

```
改前: bg-white/25 backdrop-blur-md   →   改后: bg-white/60 backdrop-blur-md

  25% 透明度                         60% 透明度
  背景色透得很明显                     卡片更实、文字更清晰
  在渐变背景上有点飘                   视觉上更稳、层次更分明
```

---

## 学到的概念

| 概念 | 理解 |
|------|------|
| Tailwind 透明度简写 | `bg-white/25` = `background-color: rgba(255, 255, 255, 0.25)`，`/` 后面的数字是百分比透明度 |
| Glassmorphism 三要素 | 半透明底 + `backdrop-blur` 模糊 + `border border-white/30` 浅白边框，共同营造磨砂玻璃质感 |
| 背景透明度与可读性平衡 | 透明度太低卡片飘、文字辨识度差；透明度太高失去玻璃质感。`60%` 是本项目当前较好的平衡点 |

---

## 下一步

考虑额外加固卡片质感的小优化方向：
- 卡片 hover 时 `backdrop-blur` 增强（`md` → `lg`）增加深度反馈
- 或者用 `@theme` 在 `global.css` 里抽出卡片样式变量，方便统一维护