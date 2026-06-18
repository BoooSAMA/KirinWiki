---
title: "Day 21 — 让 3D 场景拥有时间灵魂：24 小时昼夜系统"
date: 2026-06-17
tags: ["Three.js", "3D", "CSS", "UX", "time"]
summary: "为 3D 场景注入 24 小时昼夜循环，三层同步驱动背景、卡片和文字的自动明暗切换"
description: "为博客引入基于新加坡时区的 24 小时动态背景系统：Three.js 3D 场景根据时间自动变色，UI 卡片和文字同步切换明暗模式"
---

## 背景

博客的 3D 场景（白色背景 + 银色水晶 + 蜂巢网格）在 Day 20 搭建完成，但仅限固定亮色模式。作为个人网站，想在视觉上增加时间维度的沉浸感——让背景跟随真实时间流动，白天明亮、黄昏暖橙、夜晚沉蓝。

目标是：
1. **根据新加坡时间（UTC+8）**自动调整背景色 —— 不依赖用户系统时区
2. **24 小时平滑过渡** —— 每小时一个关键帧，线性插值，无跳变
3. **场景、UI 卡片、文字颜色同步切换** —— 三个层面统一响应

---

## 技术选型

### 时间检测方案对比

| 方案                                     | 做法                                             | 选型 |
|------------------------------------------|--------------------------------------------------|:----:|
| 服务器端渲染                             | 在 Astro SSR 中检测时间，渲染不同 CSS             |  ❌  |
| 客户端 `Intl.DateTimeFormat`             | 浏览器内置 API，指定 `timeZone: 'Asia/Singapore'` |  ✅  |
| 第三方库 (dayjs / luxon)                 | 安装时区库处理                                   |  ❌  |

### 颜色更新方案对比

| 方案                                     | 做法                                             | 推荐度 |
|------------------------------------------|--------------------------------------------------|:------:|
| CSS 变量 + `data-theme` 属性             | 在 `:root` 定义白天变量，`[data-theme="night"]` 覆写 | ⭐ 最轻量 |
| 直接操作 DOM 类名                        | JS 为每个元素切换类                               | ❌ 侵入性强 |
| Three.js 颜色 API 直接调用               | 3D 场景通过 `Color.set()` 动态更新                | ✅ 场景必备 |

---

## 架构设计

```text
[新加坡时间] → timeTheme.js → 插值颜色
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
          crystalScene.js     CSS 变量       [data-theme] 属性
          (场景背景变色+      (body/卡片/    (文字颜色切换)
           地板/网格同步)      导航栏背景)
```

### 三层同步策略

**第 1 层：Three.js 3D 场景**
- `scene.background` — 主场景背景色，跟随时间变化
- `envScene.background` — 环境贴图颜色，同步更新（确保水晶材质正确反射环境色）
- 地板网格和六边形线条颜色同步缩放——白天保持浅灰，夜晚自然变暗

**第 2 层：CSS 自定义属性**
- 6 个 `--glass-*` 变量控制所有 UI 组件的背景色、边框色、文字色
- 白天：白色磨砂玻璃 (`rgba(255 255 255 / 0.6)`) + 深灰文字
- 夜晚：黑色磨砂玻璃 (`rgba(0 0 0 / 0.4)`) + 浅灰文字
- 通过 `[data-theme="night"]` 属性选择器统一覆盖

**第 3 层：HTML `data-theme` 属性**
- `timeTheme.js` 计算当前颜色的亮度值
- 亮度 < 0.5 → `document.documentElement.dataset.theme = 'night'`
- 亮度 ≥ 0.5 → 移除 `data-theme` 属性（恢复白天模式）
- CSS 选择器 `[data-theme="night"] { --glass-bg: ... }` 自动生效

---

## 24 色调色板

基于新加坡近赤道的自然光规律（日出约 06:00，日落约 19:00，全年稳定）：

| 时间   | 色值        | 时段     |    | 时间   | 色值        | 时段     |
|:-------|:------------|:---------|:---|:-------|:------------|:---------|
| 00:00  | `#0a0a1a`   | 深夜墨蓝  |    | 12:00  | `#ffffff`   | 正午纯白 |
| 01:00  | `#0d0d20`   |          |    | 13:00  | `#faf8f0`   |          |
| 02:00  | `#0f0f25`   |          |    | 14:00  | `#f0ece0`   |          |
| 03:00  | `#12122a`   |          |    | 15:00  | `#e8dcc8`   |          |
| 04:00  | `#1a1a3e`   | 黎明前   |    | 16:00  | `#d4c098`   | 午后暖黄 |
| 05:00  | `#2a1a3e`   | 紫粉晨曦 |    | 17:00  | `#c89060`   | 黄昏暖橙 |
| 06:00  | `#6a3050`   | 日出紫   |    | 18:00  | `#b06040`   | 日落橙红 |
| 07:00  | `#d4a060`   | 晨光暖金 |    | 19:00  | `#6a3050`   | 暮色紫   |
| 08:00  | `#e8d8b0`   | 清晨暖白 |    | 20:00  | `#1a1a3e`   | 入夜深蓝 |
| 09:00  | `#f0e8d0`   |          |    | 21:00  | `#0d0d2b`   |          |
| 10:00  | `#f8f4e8`   |          |    | 22:00  | `#0a0a1a`   | 深夜墨蓝 |
| 11:00  | `#ffffff`   | 正午纯白 |    | 23:00  | `#0a0a1a`   | 深夜墨蓝 |

每小时一个关键帧，相邻帧之间按分钟比例 RGB 通道线性插值。

---

## 实现细节

### 颜色插值引擎 (`src/lib/timeTheme.js`)

核心算法：给定当前小时和分钟，找到两个相邻关键帧，**LERP** 每个通道：

```javascript
function interpolateColor(hour, minute) {
  const current = hexToRgb(COLOR_PALETTE[hour])
  const next = hexToRgb(COLOR_PALETTE[(hour + 1) % 24])
  const fraction = minute / 60

  const r = Math.round(current.r + (next.r - current.r) * fraction)
  const g = Math.round(current.g + (next.g - current.g) * fraction)
  const b = Math.round(current.b + (next.b - current.b) * fraction)

  return '#' + [r, g, b].map(c => c.toString(16).padStart(2, '0')).join('')
}
```

### 更新策略

```text
RAF 循环:
  ├── 每 60 秒重新获取新加坡时间
  ├── 每帧：应用当前插值颜色到三层
  └── visibilitychange 事件：页面恢复可见时立即重新同步
```

使用 `requestAnimationFrame` 而不是 `setInterval`——RAF 在标签页不可见时会自动暂停，节省性能。

### 防闪烁初始化

内联阻塞脚本放在 `<head>` 中，在首次渲染前执行：

```html
<script is:inline>
// 在浏览器画出第一帧之前设置好初始主题
const parts = new Intl.DateTimeFormat('en-SG', { timeZone: 'Asia/Singapore', ... })
  .format(new Date()).split(':')
const hour = parseInt(parts[0])
const c = palette[hour % 24]
document.documentElement.style.setProperty('--time-bg-color', c)
document.body.style.backgroundColor = c
if (brightness < 128) document.documentElement.dataset.theme = 'night'
</script>
```

这样用户永远看不到"白屏然后突然变暗"的跳变。

### 3D 场景动态更新 (`src/lib/crystalScene.js`)

`window.__setSceneBackground(hex)` 同步更新三个 3D 元素：

```javascript
// 1. 主场景背景
scene.background = new THREE.Color(hex)

// 2. 环境贴图（重建 PMREMGenerator 让水晶正确反射新颜色）
envScene.background = color
const pmrem2 = new THREE.PMREMGenerator(renderer)
scene.environment = pmrem2.fromScene(envScene).texture

// 3. 地板 + 网格线颜色（按背景亮度线性映射）
const bgBrightness = 0.299*r + 0.587*g + 0.114*b
// 地板范围: 0x1a1a1a ~ 0xf8f8f8
// 网格范围: 0x404040 ~ 0xaaaaaa
```

> **为什么重建环境贴图？** 水晶的 `metalness: 0.95` 意味着它几乎完全反射环境。如果不更新 `scene.environment`，水晶会保持反射旧颜色，和背景脱节。

### CSS 变量体系 (`src/styles/global.css`)

```css
:root {
  --glass-bg: rgba(255, 255, 255, 0.6);
  --glass-border: rgba(255, 255, 255, 0.3);
  --glass-text: #374151;
  --glass-text-secondary: #6b7280;
  --glass-text-muted: #9ca3af;
  --glass-bg-secondary: rgba(243, 244, 246, 0.6);
}

[data-theme="night"] {
  --glass-bg: rgba(0, 0, 0, 0.4);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-text: #e5e7eb;
  --glass-text-secondary: #9ca3af;
  --glass-text-muted: #6b7280;
  --glass-bg-secondary: rgba(0, 0, 0, 0.3);
}
```

所有 UI 组件（导航栏、首页卡片、文章页面、标签）都从 `bg-white/60 text-gray-900` 改为 `bg-[var(--glass-bg)] text-[var(--glass-text)]`，通过 CSS 变量自动响应时间主题。

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/lib/colorPalette.js` | **新增** | 24 色调色板 + 亮度计算辅助函数 |
| `src/lib/timeTheme.js` | **新增** | 时间检测、颜色插值、三层同步更新引擎 |
| `src/lib/crystalScene.js` | **修改** | 添加 `window.__setSceneBackground()`；地板/网格颜色跟随背景同步 |
| `src/styles/global.css` | **修改** | 添加 `:root` CSS 变量 + `[data-theme="night"]` 暗色覆写 |
| `src/layouts/BaseLayout.astro` | **修改** | 内联阻塞脚本防闪烁 + timeTheme 初始化 |
| `src/components/Navbar.astro` | **修改** | 改用 CSS 变量驱动明暗 |
| `src/components/SmallPostCard.astro` | **修改** | 同上 |
| `src/components/ReadingBackdrop.astro` | **修改** | 阅读卡片背景跟随主题变化 |
| `src/pages/blog/[category]/[slug].astro` | **修改** | 适配新 CSS 变量 |

---

## 边界情况处理

| 场景 | 处理方式 |
|------|---------|
| **时区** | `Intl.DateTimeFormat('en-SG', { timeZone: 'Asia/Singapore' })` —— 所有访客看到同一"新加坡时间"背景 |
| **浏览器不支持 Intl** | 降级使用 UTC+8 手动偏移：`new Date().getUTCHours() + 8` |
| **页面休眠恢复** | `visibilitychange` 事件，页面恢复可见时强制重置 `lastTimeCheck = 0` |
| **初始加载闪烁** | `<head>` 内联阻塞脚本，在首次渲染前设置好颜色和 `data-theme` |
| **View Transitions 页面切换** | 内联脚本每个页面都会执行，但重复设置相同值不会产生闪烁；timeTheme 的 `__bg3dInitialized` + RAF 循环不受影响 |
| **正午纯白** | 11:00-12:00 连续两帧 `#ffffff`，插值结果为纯白，不触发夜间模式 |
| **深夜最暗** | 00:00 和 22:00-23:00 均为 `#0a0a1a`，亮度约 0.04，夜间模式稳定生效 |

---

## 调试技巧

浏览器 Console 中可以直接测试夜间效果：

```javascript
// 模拟深夜
window.__setSceneBackground('#0a0a1a')
document.documentElement.dataset.theme = 'night'

// 恢复白天
window.__setSceneBackground('#ffffff')
document.documentElement.dataset.theme = ''
```

---

## 效果预览

```text
白天 (11:00-12:00)              夜晚 (00:00-04:00)
┌──────────────────────────┐   ┌──────────────────────────┐
│  ☀️  #ffffff 纯白背景       │   │  🌙  #0a0a1a 深蓝背景       │
│  ┌─ white/60 磨砂玻璃 ─┐  │   │  ┌─ black/40 暗色玻璃 ─┐  │
│  │  gray-900 深色文字   │  │   │  │  gray-200 浅色文字   │  │
│  └──────────────────────┘  │   │  └──────────────────────┘  │
└──────────────────────────┘   └──────────────────────────┘
```

三层同步后，整体视觉感受从"白色空间"变为"沉浸式时间体验"，时间段感一目了然。

---

## 学到的概念

| 概念 | 理解 |
|------|------|
| **`Intl.DateTimeFormat` 时区指定** | 浏览器原生 API 支持 `timeZone: 'Asia/Singapore'`，无需第三方库。`hourCycle: 'h23'` 获取 0-23 时 |
| **RGB 线性插值 (LERP)** | `lerp(a, b, t) = a + (b - a) * t`，分别对 R/G/B 三个通道插值，再拼回 `#rrggbb` |
| **Rec.601 亮度公式** | `brightness = 0.299R + 0.587G + 0.114B`。人眼对绿色最敏感，加权和比简单平均更接近感知亮度 |
| **PMREMGenerator 运行时重建** | 新建 `PMREMGenerator` → `fromScene(envScene)` → 赋值给 `scene.environment` → 立即 `dispose()`。开销约 1-2ms |
| **CSS `[data-*]` 属性选择器** | `[data-theme="night"]` 优先级高于 `:root`，天然适合主题开关。无需 JS 操作类名 |
| **Tailwind 任意值语法** | `bg-[var(--glass-bg)]` 支持动态 CSS 变量，无需在配置文件中预设颜色 |
| **内联阻塞脚本防闪烁** | `<script is:inline>` 不被 Vite 打包，同步执行。放在 `<head>` 中确保首次渲染前主题已就位 |
| **`requestAnimationFrame` vs `setInterval`** | RAF 在标签页不可见时自动暂停。60 秒检查 + RAF 每帧渲染是最优组合 |
