---
title: "Day 5 — 社交链接优化：Email 复制 + GitHub Octocat 图标"
date: 2026-06-01
description: "将首页 Email 链接改为点击复制到剪贴板，GitHub 链接替换为 Octocat SVG 图标。"
---

## 改动

- **Email 链接 → 点击复制到剪贴板**：点击邮件图标将 `booosama0113@gmail.com` 复制到剪贴板，成功时弹出 "已复制！" 气泡提示，1.5 秒后消失；不支持 Clipboard API 时降级为 `mailto:` 打开邮件客户端
- **GitHub 文字 → Octocat SVG 图标**：文字 "GitHub" 替换为 GitHub 官方的 Octocat（黑色猫猫）SVG 图标，添加 `target="_blank"` 在新标签页打开
- 两个链接用 `flex` + `gap-5` 排列，视觉更统一

## 修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/pages/index.astro` | 修改 L38-42 | 社交链接区段重写 |

## 技术细节

### 剪贴板 API

```js
navigator.clipboard.writeText('booosama0113@gmail.com')
```

使用 Astro 内联 `<script>` 标签，在客户端运行。Toast 提示用 CSS `opacity` 过渡实现淡入淡出，纯 Tailwind 无额外依赖。

### Octocat 图标

内联 SVG，`fill="currentColor"` 使图标颜色继承文字颜色，支持 hover 变色。

### 降级策略

`try/catch` 包裹 Clipboard API，失败时 `window.location.href = 'mailto:...'` 回退到传统邮件客户端。
