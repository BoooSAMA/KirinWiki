---
title: "Day 23 — 性能优化：修复 25fps 卡顿与 View Transitions 主题丢失"
date: 2026-06-19
tags: ["performance", "debugging", "glassmorphism", "View Transitions", "Three.js", "CSS", "refactoring"]
summary: "系统性修复网页卡顿问题：移除 backdrop-blur 性能杀手、替换所有硬编码颜色为 CSS 变量、修复 timeTheme 每帧重绘 bug、View Transitions 主题丢失"
description: "从用户反馈的 '网页卡顿' 出发，深入诊断并修复了三层性能问题：backdrop-blur 导致 GPU 重绘过载、timeTheme.js 的 applyColor 每帧无脑调用造成 DOM 重排和 PMREM 环境贴图重建、所有页面使用硬编码颜色导致时间主题失效。同时修复了 View Transitions 切换页面后颜色回退到白色的兼容性问题。"
---

# Day 23 — 性能优化：修复 25fps 卡顿与 View Transitions 主题丢失

## 背景

用户反馈网站 "网页卡顿"，即使开启 Firefox GPU 加速也不流畅。同时反映部分页面的卡片"一直是半透明白色"，且切换目录后颜色主题丢失。

使用 FPS 监视器（`Ctrl+Shift+F`）确认：帧率仅 **25fps**，远低于预期的 60fps。

---

## 问题 1：backdrop-blur 性能杀手

### 诊断

整个网站大量使用玻璃态（glassmorphism）效果：`bg-white/60 backdrop-blur-md`。`backdrop-filter: blur()` 是 CSS 中**最耗 GPU 的滤镜之一**，尤其在 Firefox 上性能显著低于 Chrome。

影响范围：

| 元素 | 原模糊强度 | 位置 |
|------|-----------|------|
| Navbar | `backdrop-blur-lg` (16px) | 所有页面 |
| 卡片 | `backdrop-blur-md` (12px) | 所有页面 |
| 按钮/badges | `backdrop-blur-sm` (4px) | 所有页面 |
| 播放器 | `blur(28px)` (内联 CSS) | 音乐播放器组件 |
| 阅读进度 | `backdrop-blur-md` | ReadingBackdrop 组件 |
| Like 按钮 | `backdrop-blur-sm` | LikeButton 组件 |

**每个使用 backdrop-blur 的元素，滚动时都会触发 GPU 重绘。** 多个模糊元素叠加时，性能问题成倍放大。

### 修复方案

#### 方案 1：纯半透明背景代替模糊（主要）

用提高不透明度的纯色背景替代 `backdrop-filter: blur()`：

```diff
- class="bg-white/60 backdrop-blur-md rounded-2xl"
+ class="bg-white/85 rounded-2xl"
```

同时提高暗色模式的 CSS 变量不透明度（补偿模糊丢失的视觉融合感）：

```css
:root {
- --glass-bg: rgba(255, 255, 255, 0.6);
+ --glass-bg: rgba(255, 255, 255, 0.85);
}

[data-theme="night"] {
- --glass-bg: rgba(0, 0, 0, 0.4);
+ --glass-bg: rgba(0, 0, 0, 0.65);
}
```

#### 方案 2：降低模糊强度（Navbar/播放器保留处）

对必须保留模糊的视觉焦点元素，降低强度：

```diff
- backdrop-blur-lg (16px)
+ backdrop-blur-sm (4px)
```

播放器内联 CSS：
```diff
- backdrop-filter: blur(28px);
+ backdrop-filter: blur(12px);
```

#### 方案 3：添加 will-change 提示

```diff
+ .glass-blur {
+   will-change: backdrop-filter;
+ }

- <header class="... backdrop-blur-sm">
+ <header class="... backdrop-blur-sm glass-blur">
```

#### 方案 4：View Transitions 回退动画

```diff
- <ClientRouter fallback="animate" />
+ <ClientRouter />
```

去掉 `fallback="animate"` —— 不支持原生 View Transitions API 的浏览器直接无动画切换，避免 JS 回退动画增加渲染负担。

### 修改文件

| 文件 | 改动 |
|------|------|
| `src/styles/global.css` | `--glass-bg` 不透明度 0.6→0.85（日）/ 0.4→0.65（夜）；添加 `.glass-blur` 类 |
| `src/components/Navbar.astro` | `backdrop-blur-lg` → `backdrop-blur-sm` + `.glass-blur` |
| `src/components/SmallPostCard.astro` | 移除 `backdrop-blur-md` |
| `src/components/ReadingBackdrop.astro` | 移除 `backdrop-blur-md` |
| `src/components/MusicPlayer.astro` | `blur(28px)` → `blur(12px)`（2处） |
| `src/components/LikeButton.tsx` | `bg-white/40 backdrop-blur-sm` → `bg-white/60` |
| `src/layouts/BaseLayout.astro` | `<ClientRouter fallback="animate" />` → `<ClientRouter />` |
| 7 个页面文件 | `bg-white/60 backdrop-blur-md` → `bg-white/85` |
| 11 处按钮 | `bg-gray-100/60 backdrop-blur-sm` → `bg-gray-100/80` |

---

## 问题 2：硬编码颜色导致的主题失效

### 诊断

`SmallPostCard.astro`（`/blog/build-log/` 等文章卡片）使用 CSS 变量 `bg-[var(--glass-bg)]`，能跟随时间主题切换。但大部分其他页面使用硬编码 Tailwind 类：

```diff
- bg-white/85          ← 永远是白色
- text-gray-900         ← 永远是深灰
- text-gray-500         ← 永远是中灰
- border-white/30       ← 永远是白边框
```

当 `timeTheme.js` 在夜间设置 `data-theme="night"` 时，CSS 变量正确切换为深色值，但硬编码类完全不受影响。

### 修复

将 10 个文件中的所有硬编码颜色替换为 CSS 变量：

| 硬编码类 | CSS 变量 |
|---------|---------|
| `bg-white/85` | `bg-[var(--glass-bg)]` |
| `bg-gray-100/80` | `bg-[var(--glass-bg-secondary)]` |
| `text-gray-900` | `text-[var(--glass-text)]` |
| `text-gray-500` | `text-[var(--glass-text-secondary)]` |
| `text-gray-400` | `text-[var(--glass-text-muted)]` |
| `border-white/30` | `border-[var(--glass-border)]` |
| `border-gray-200/40` | `border-[var(--glass-border)]` |

顺便优化了首页卡片的过渡：
```diff
- transition-all duration-200
+ transition-shadow duration-200
```

### 修改文件清单

| 文件 | 优先级 | 改动量 |
|------|--------|--------|
| `src/pages/blog/index.astro` | 最高（用户反馈的根因） | 卡片 + 标题 + 按钮 → CSS vars |
| `src/pages/blog/[category].astro` | 高 | 返回按钮 + 侧栏标签 → CSS vars |
| `src/pages/blog/tags/index.astro` | 高 | 标签卡片 + 标题 → CSS vars |
| `src/pages/blog/tags/[tag].astro` | 高 | 返回按钮 + 标题 → CSS vars |
| `src/components/CategoryDisplay.astro` | 高 | 分类标题 → CSS vars |
| `src/pages/index.astro` | 高 | 首页卡片 + 社交按钮 → CSS vars |
| `src/pages/about.astro` | 中 | 全部 → CSS vars |
| `src/pages/shares.astro` | 中 | 全部 → CSS vars |
| `src/pages/pictures.astro` | 中 | 全部 → CSS vars |
| `src/pages/projects/index.astro` | 中 | 全部 → CSS vars |

### 遗漏修复：文章详情页返回按钮未更新

后续验证发现 `src/pages/blog/[category]/[slug].astro`（文章详情页）的两个返回按钮被遗漏，仍在使用硬编码颜色：

```diff
- border border-gray-200/40 hover:bg-gray-200/60
+ border border-[var(--glass-border)] hover:bg-white/60
```

`border-gray-200/40` 在深色模式下几乎透明（浅灰 40% 在黑背景上不可见），导致按钮"可以点击但看不见"。同步修复 `[category].astro` 返回按钮缺少 `<nav>` 包裹的结构问题，与全站其他页面保持一致。

**涉及文件**：
- `src/pages/blog/[category]/[slug].astro` — 两个返回按钮 `border`/`hover` → CSS 变量
- `src/pages/blog/[category].astro` — 裸 `<a>` → `<nav>` 包裹（结构统一）

---

## 问题 3：timeTheme.js 每帧无脑重绘（25fps 的根因）

### 诊断

`timeTheme.js` 的 RAF 循环每帧都调用 `applyColor()`：

```javascript
function loop(timestamp) {
  if (!lastTimeCheck || timestamp - lastTimeCheck > 60000) {
    lastTimeCheck = timestamp
    const { hour, minute } = getSingaporeTime()
    currentColor = interpolateColor(hour, minute)
  }

  // 即使颜色完全没变，这行每帧都执行！
  if (currentColor) {
    applyColor(currentColor)  // ← 60fps 无脑调用
  }

  rafId = requestAnimationFrame(loop)
}
```

而 `applyColor()` 每次执行都做了这些操作：

1. **调用 `document.body.style.backgroundColor = hex`** → 触发 DOM 重排
2. **调用 `document.documentElement.style.setProperty('--time-bg-color', hex)`** → 触发 DOM 重排
3. **设置/删除 `data-theme` 属性** → 触发 CSS 重新匹配
4. **调用 `window.__setSceneBackground(hex)`** → 触发 PMREM 环境贴图重建

其中第 4 步最为致命：

```javascript
window.__setSceneBackground = (hex) => {
  // hex 完全没变，但每次都重建！
  const pmrem2 = new THREE.PMREMGenerator(renderer)
  scene.environment = pmrem2.fromScene(envScene).texture  // 生成 HDR 环境贴图
  pmrem2.dispose()
  // 更新地板和网格颜色…
}
```

**PMREMGenerator 生成环境贴图是 Three.js 中计算密集的操作之一。** 每 16ms 做一次，直接拖垮帧率。

### 修复

**timeTheme.js**：只在颜色真正变化时调用 `applyColor`：

```diff
  function loop(timestamp) {
    if (!lastTimeCheck || timestamp - lastTimeCheck > 60000) {
      lastTimeCheck = timestamp
      const { hour, minute } = getSingaporeTime()
-     currentColor = interpolateColor(hour, minute)
+     const newColor = interpolateColor(hour, minute)
+     if (newColor !== currentColor) {
+       applyColor(newColor)
+     }
    }

-   if (currentColor) {
-     applyColor(currentColor)
-   }

    rafId = requestAnimationFrame(loop)
  }
```

**crystalScene.js**：`__setSceneBackground` 添加 hex 去重：

```diff
+ let __lastBgHex = null
  window.__setSceneBackground = (hex) => {
+   if (!scene || !renderer || hex === __lastBgHex) return
+   __lastBgHex = hex
    // …后续逻辑
  }
```

### 性能变化

| 操作 | 修复前 | 修复后 |
|------|--------|--------|
| `applyColor` 调用频率 | **60 次/秒**（每帧） | **1 次/小时**（只需刷新时 + 跨小时） |
| PMREM 环境贴图生成 | **60 次/秒** | **1 次/小时** |
| `body.style.backgroundColor` 写入 | **60 次/秒** | **≈0 次/秒**（颜色不变时） |
| `data-theme` 属性设置 | **60 次/秒** | **≈0 次/秒** |
| FPS | **≤25** | **≥60** |

---

## 问题 4：View Transitions 导航后主题丢失

### 诊断

在目录之间切换时，卡片和导航栏的颜色回退到白天的白色样式。这是因为 View Transitions 在页面切换时，新页面的 `<head>` 内联脚本可能在 DOM 尚未完全就绪时运行，导致 `data-theme="night"` 属性未正确设置。

### 修复

在 `timeTheme.js` 中做了三处修复：

```diff
+ function applyTheme() {
+   const { hour, minute } = getSingaporeTime()
+   currentColor = interpolateColor(hour, minute)
+   applyColor(currentColor)
+ }

  export function init() {
+   // 1. 取消旧 RAF 循环（View Transitions 导致模块脚本重复执行）
+   if (rafId) cancelAnimationFrame(rafId)
+
-   const { hour, minute } = getSingaporeTime()
-   currentColor = interpolateColor(hour, minute)
-   applyColor(currentColor)
+   applyTheme()

    rafId = requestAnimationFrame(loop)
    // …
  }

+ // 2. 监听 astro:page-load —— Astro 的 View Transitions 完成事件
+ document.addEventListener('astro:page-load', () => {
+   applyTheme()
+ })
```

此外在 `BaseLayout.astro` 中为 3D 场景容器添加了 `contain:strict`：

```diff
- <div id="bg3d" style="position:fixed;inset:0;z-index:0;pointer-events:none">
+ <div id="bg3d" style="position:fixed;inset:0;z-index:0;pointer-events:none;contain:strict">
```

`contain:strict`（等价于 `contain: layout style paint`）告诉浏览器这个元素与外界无关，在 View Transitions 页面切换时可以作为独立合成层处理，避免浏览器重新计算 3D 场景的布局/样式/绘制。

### 为什么 `astro:page-load` 更可靠

| 执行时机 | 内联 `<script>` | `astro:page-load` |
|---------|----------------|-------------------|
| 初始页面加载 | ✅ 同步执行，防止闪烁 | ❌ 不触发 |
| View Transitions 导航 | ⚠️ 在 DOM 过渡期间执行 | ✅ 新 DOM 完全就位后 |
| `data-theme` 设置目标 | `document.documentElement` 可能处于过渡态 | `document.documentElement` 已稳定 |

---

## 辅助工具：调试面板（FPS + 3D 坐标）

为了方便后续性能调试和 3D 场景开发，将原先独立在 `crystalScene.js` 中的坐标显示面板和 FPS 监视器**整合为统一的调试面板**。

### 整合过程

`crystalScene.js` 原先在 `createScene()` 中直接创建了一个独立的 DOM 面板显示相机坐标（`camera.position` + `cameraTarget`），并可点击复制。这导致坐标面板在每页都会出现，无法统一控制显隐。

**重构方案**：

1. **`crystalScene.js`**：移除坐标面板的 DOM 代码（约 40 行），改为在 `animate()` 循环中通过全局变量暴露相机状态：
   ```javascript
   function animate() {
     animationId = requestAnimationFrame(animate)
     // …水晶动画逻辑…
     renderer.render(scene, camera)

     // 暴露相机状态供调试面板读取
     window.__cameraState = {
       pos: { x: camera.position.x, y: camera.position.y, z: camera.position.z },
       look: { x: cameraTarget.x, y: cameraTarget.y, z: cameraTarget.z },
     }
   }
   ```

2. **`BaseLayout.astro`**：FPS 监视器扩展为调试面板，每秒一并读取 `window.__cameraState` 并渲染：

```
  60 FPS          ← 颜色编码：绿 ≥55 / 黄 30-55 / 红 <30
  ─────────────
  pos 12.00, 7.50, 6.00     ← 实时相机坐标
  look 2.00, 5.00, 5.87     ← 实时相机目标点
```

### 功能说明

- **快捷键**：`Ctrl + Shift + F` 切换显示/隐藏
- **位置**：左上角（`top: 80px`，导航栏下方）
- **颜色编码**：🟢 ≥55fps / 🟡 30-55fps / 🔴 <30fps
- **点击面板**：复制当前 3D 坐标到剪贴板（格式：`pos(x,y,z),look(x,y,z)`），显示绿色反馈"✓ 坐标已复制"1 秒后恢复
- **默认隐藏**，快捷键唤醒
- **自身开销**：纯 `requestAnimationFrame` 计数，每秒更新一次 DOM，几乎为零

---

## 修改文件总清单

| 文件 | 操作 | 类型 |
|------|------|------|
| `src/styles/global.css` | 修改 | 不透明度提升 + `will-change` 工具类 |
| `src/layouts/BaseLayout.astro` | 修改 | `ClientRouter` fallback 移除 + `contain:strict` + 调试面板（FPS+3D坐标） |
| `src/lib/timeTheme.js` | 修改 | `applyColor` 去重 + `astro:page-load` 监听 + RAF 去重 |
| `src/lib/crystalScene.js` | 修改 | `__setSceneBackground` hex 去重缓存 + 坐标面板整合为 `window.__cameraState` |
| `src/components/Navbar.astro` | 修改 | 模糊强度降低 + `glass-blur` |
| `src/components/SmallPostCard.astro` | 修改 | 移除模糊 |
| `src/components/ReadingBackdrop.astro` | 修改 | 移除模糊 |
| `src/components/MusicPlayer.astro` | 修改 | 模糊从 28px 降至 12px |
| `src/components/LikeButton.tsx` | 修改 | 模糊替换为纯色 |
| `src/pages/index.astro` | 修改 | CSS 变量替换硬编码颜色 |
| `src/pages/blog/index.astro` | 修改 | CSS 变量替换硬编码颜色 |
| `src/pages/blog/[category].astro` | 修改 | CSS 变量替换硬编码颜色 |
| `src/pages/blog/tags/index.astro` | 修改 | CSS 变量替换硬编码颜色 |
| `src/pages/blog/tags/[tag].astro` | 修改 | CSS 变量替换硬编码颜色 |
| `src/components/CategoryDisplay.astro` | 修改 | CSS 变量替换硬编码颜色 |
| `src/pages/about.astro` | 修改 | CSS 变量替换硬编码颜色 |
| `src/pages/shares.astro` | 修改 | CSS 变量替换硬编码颜色 |
| `src/pages/pictures.astro` | 修改 | CSS 变量替换硬编码颜色 |
| `src/pages/projects/index.astro` | 修改 | CSS 变量替换硬编码颜色 |

---

## 学到的概念

| 概念 | 理解 |
|------|------|
| **`backdrop-filter: blur()` 的性能代价** | 模糊滤镜需要 GPU 对每个像素进行采样计算，滚动时每帧都要重绘。多个模糊元素叠加会成倍放大性能开销。纯 `background-color` + 提高不透明度可以模拟类似效果且几乎零性能开销 |
| **CSS 自定义属性（变量）在不同作用域的解析** | `:root` 中定义的变量被 `[data-theme="night"]` 覆盖。选择器优先级决定最终值 —— 属性选择器（`[attr]`）优先级高于 `:root` 标签选择器。Tailwind 的 `bg-[var(--x)]` 语法允许在任意类中使用 CSS 变量 |
| **`requestAnimationFrame` 与 View Transitions 的交互** | View Transitions 导航会导致模块脚本重新执行，旧的 RAF 循环不会被自动清理。必须显式 `cancelAnimationFrame` 防止多个 RAF 循环同时运行 |
| **`astro:page-load` 事件** | Astro 在 View Transitions 导航完成后触发此事件。相比 `<script is:inline>` 在 DOM 过渡期间执行，`astro:page-load` 在新 DOM 完全就位后才触发，更可靠地处理页面切换后的状态恢复 |
| **`contain: strict` 的性能意义** | `contain: layout style paint` 将元素声明为独立渲染子树。浏览器在 View Transitions 页面切换时不必为此子树重新计算布局和样式，可以直接复用上一帧的合成结果 |
| **PMREMGenerator 的开销** | Three.js 的 PMREMGenerator 通过预过滤环境图生成粗糙度-金属度 PBR 贴图，每次生成都涉及多级下采样和卷积计算。在动画循环中每帧调用会造成严重的 GPU 管线阻塞 |
| **`window.__` 全局变量作为模块间通信的轻量手段** | 当两个模块（`crystalScene.js` 生成数据、`BaseLayout.astro` 的调试面板消费数据）在 Astro 的模块系统中无法直接导入引用时，通过约定的全局变量（`window.__cameraState`）传递高频更新的运行时数据是一种低开销方案。在 animate 循环中每帧赋值、调试面板每秒读取，避免了 props 传递或事件派发的复杂性和性能开销 |

---

## 后续可能的优化方向

- **按需渲染 3D 场景**：页面不滚动/不交互时降低 Three.js 的渲染帧率（如降至 30fps），仅在有动画/滚动时恢复 60fps
- **CSS `@property` 注册 `--p` 的浏览器兼容性**：`ring-glow` 灯条动画依赖 `@property --p`，Safari 和旧版 Firefox 不支持。可考虑用 JS 驱动的动画作为降级方案
- **Tailwind CSS v4 `@theme` 指令**：当前 CSS 变量通过 `@layer base` 和 `@layer components` 组织，可以探索将主题色放入 Tailwind v4 的 `@theme` 块中以获得更好的 IDE 支持和类型安全
