# 基于新加坡时区的 3D 场景动态时间背景

## 概述

为博客的 Three.js 水晶 3D 场景添加基于新加坡时间（UTC+8）的 24 小时动态背景系统。场景背景色根据小时平滑过渡，UI 卡片和文字同步调整明暗，营造从白昼到夜晚的自然沉浸体验。

## 核心机制

### 时间检测

- 使用 `Intl.DateTimeFormat` 结合 `timeZone: 'Asia/Singapore'` 获取新加坡当前小时和分钟
- 无需额外依赖，浏览器原生支持
- 每 60 秒重新检测一次，配合 `requestAnimationFrame` 实现帧级插值平滑

### 颜色插值引擎

- 24 个关键帧（每小时一个）存储在 `colorPalette.js` 中
- 客户端运行时根据当前时间找到相邻两个关键帧，按分钟比例线性插值
- 插值结果同步应用到三个层面：3D 场景背景、全局 CSS 变量、UI 卡片主题

### 更新策略

- `requestAnimationFrame` 驱动渲染循环，颜色变化平滑连续
- 页面 `visibilitychange` 事件恢复时强制同步时间
- 无后端依赖，纯客户端运行

## 24 色调色板

| 时间 | 色值 | 时段 |
|------|------|------|
| 00:00 | `#0a0a1a` | 深夜墨蓝 |
| 01:00 | `#0d0d20` | 深夜 |
| 02:00 | `#0f0f25` | 深夜 |
| 03:00 | `#12122a` | 深夜 |
| 04:00 | `#1a1a3e` | 黎明前 |
| 05:00 | `#2a1a3e` | 紫粉晨曦 |
| 06:00 | `#6a3050` | 日出紫 |
| 07:00 | `#d4a060` | 晨光暖金 |
| 08:00 | `#e8d8b0` | 清晨暖白 |
| 09:00 | `#f0e8d0` | 上午 |
| 10:00 | `#f8f4e8` | 近午 |
| 11:00 | `#ffffff` | 纯白 |
| 12:00 | `#ffffff` | 正午纯白 |
| 13:00 | `#faf8f0` | 午后 |
| 14:00 | `#f0ece0` | 午后 |
| 15:00 | `#e8dcc8` | 午後暖白 |
| 16:00 | `#d4c098` | 午后暖黄 |
| 17:00 | `#c89060` | 黄昏暖橙 |
| 18:00 | `#b06040` | 日落橙红 |
| 19:00 | `#6a3050` | 暮色紫 |
| 20:00 | `#1a1a3e` | 入夜深蓝 |
| 21:00 | `#0d0d2b` | 深夜 |
| 22:00 | `#0a0a1a` | 深夜墨蓝 |
| 23:00 | `#0a0a1a` | 深夜墨蓝 |

## 受影响组件

### 1. Three.js 3D 场景 (`src/lib/crystalScene.js`)

- **`scene.background`** — 主场景背景色，跟随当前插值颜色变化
- **`envScene.background`** — 环境贴图背景色，同步跟随
- 通过暴露 `setSceneBackground(colorHex)` 方法供外部调用
- 颜色变化通过 Three.js `Color.set()` 实现，无场景重建

### 2. 全局 CSS 变量 (`src/styles/global.css`)

新增 CSS 自定义属性用于卡片和文字主题：

```css
@theme {
  --color-glass-bg: rgba(255, 255, 255, 0.6);
  --color-glass-border: rgba(255, 255, 255, 0.3);
  --color-glass-text: #374151;       /* gray-800 */
  --color-glass-text-secondary: #6b7280; /* gray-500 */
}
```

Tailwind v4 的 `--color-*` 变量会自动生成 `bg-glass-bg`、`border-glass-border`、`text-glass-text` 等工具类，直接用在模板中。

夜间通过 `[data-theme="night"]` 属性覆写 `@theme` 变量（优先级高于 `:root` 中的定义）：

```css
[data-theme="night"] {
  --color-glass-bg: rgba(0, 0, 0, 0.4);
  --color-glass-border: rgba(255, 255, 255, 0.1);
  --color-glass-text: #e5e7eb;       /* gray-200 */
  --color-glass-text-secondary: #9ca3af; /* gray-400 */
}
```

### 3. UI 卡片

- 将硬编码的 Tailwind 类 `bg-white/60 text-gray-800` 替换为 `bg-glass-bg text-glass-text`
- 所有磨砂玻璃卡片（导航栏、首页卡片、小卡片）统一响应主题变化
- 白天：白色磨砂玻璃 (`rgba(255 255 255 / 0.6)`) + 深色文字
- 夜晚：黑色磨砂玻璃 (`rgba(0 0 0 / 0.4)`) + 浅色文字

### 4. 阅读背景 (`src/components/ReadingBackdrop.astro`)

- 现有的 `--reading-bg-opacity` 系统保留
- 夜间模式下，基础背景色从白色切换为黑色，`--reading-bg-opacity` 依然可调
- 用户调节的透明度设置通过 localStorage 持久化，独立于时间主题

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/lib/timeTheme.js` | **新增** | 时间检测 + 颜色插值引擎 |
| `src/lib/colorPalette.js` | **新增** | 24 色调色板数据 |
| `src/lib/crystalScene.js` | **修改** | 添加 `setSceneBackground()` 方法 |
| `src/layouts/BaseLayout.astro` | **修改** | 引入 timeTheme 脚本，初始化主题循环 |
| `src/styles/global.css` | **修改** | 新增 `@theme` CSS 变量 + `[data-theme]` 规则 |
| `src/components/Navbar.astro` | **修改** | 磨砂玻璃类替换为 CSS 变量 |
| `src/components/SmallPostCard.astro` | **修改** | 同上 |
| `src/components/ReadingBackdrop.astro` | **修改** | 支持夜间深色背景 |
| `src/pages/blog/[category]/[slug].astro` | **修改** | 适配新的 CSS 变量 |

## 架构数据流

```
[新加坡时间] → timeTheme.js → 插值颜色
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
          crystalScene.js     CSS 变量       [data-theme] 属性
          (场景背景变色)     (body/卡片)    (文字颜色切换)
```

## 边界情况

1. **时区偏移**：使用 `Intl.DateTimeFormat` 而非系统时区，确保所有访客看到的都是新加坡时间背景
2. **页面休眠恢复**：监听 `visibilitychange`，页面恢复可见时重新同步时间
3. **浏览器不支持 Intl**：罕见情况，降级使用 UTC+8 手动偏移计算
4. **初始加载闪烁**：在 `<head>` 内联一段阻塞脚本，在首次渲染前设置好初始主题，避免白屏后跳变
5. **localStorage 优先级**：用户手动调节的阅读不透明度独立于时间主题，两者互不覆盖

## 不做（YAGNI）

- 不做手动切换白天/夜晚的开关（用户未要求，后续可按需添加）
- 不做服务器端时间检测（纯客户端实现，SSR 无时间相关渲染）
- 不做复杂的日出日落天文计算（新加坡近赤道，固定时间表足够准确）
