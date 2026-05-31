---
title: "Day 4 — Added white background for reading"
date: 2026-05-31
description: "Added white reading backdrop with adjustable opacity slider for blog post pages."
---

## 改动

- 新增 `src/components/ReadingBackdrop.astro` — 白色文章阅读背景 + 可调节透明度滑块
- 修改 `src/pages/blog/[category]/[slug].astro` — 将 `<article>` 包裹在 `<ReadingBackdrop>` 中
- 滑块位于右下角，透明度自动保存到 localStorage，范围 0~100%，默认 92%
