---
title: "Day 19 — 自制播放器：从 APlayer 到自建，UI 反复迭代的全记录"
date: 2026-06-14
tags: ["UI", "Music", "APlayer", "SVG", "CSS Animations"]
description: "彻底替换 APlayer，用 Preact + HTML5 Audio API 自建音乐播放器。深色毛玻璃、彩灯边框、阶梯面板、SVG 图标、竖排音量……两天内迭代了十几个版本"
---

# Day 19 — 自制播放器：从 APlayer 到自建，UI 反复迭代的全记录

## 背景

Day 18 把博客部署上线后，底部音乐播放器用的是 **APlayer**（一个开源 HTML5 播放器库），嵌在 Astro 组件里搭配 `data-astro-transition-persist` 实现页面切换不断播。

APlayer 本身功能没问题，但和定制化需求打架了：

1. **定位压不住**：APlayer `fixed: true` 模式用 JS `element.style.cssText` 锁定元素位置，CSS `!important` 都覆盖不了
2. **UI 改不动**：想加圆角、毛玻璃、间距——APlayer 的 JS 在初始化后不断重置样式，改了一会被还原
3. **代码不透明**：出问题不知道是库的 bug 还是自己的用法问题

最终决定：**弃用 APlayer，自己写一个。**

---

## 重构过程

### 第一阶段：与 APlayer 内联样式的死磕（已废弃）

第一轮尝试用 CSS 全覆盖 APlayer 样式，花了大量时间写毛玻璃、圆角、渐变进度条、暗色模式适配。效果看着不错——直到发现 DevTools 里 APlayer JS 设的内联样式把所有定位覆盖都划掉了。

用 `element.style.setProperty('left', '16px', 'important')` 勉强压住，但 APlayer 在特定交互（点击歌单、切换歌曲、调整音量）后会重新写入 `style.cssText`，把我们的覆盖冲掉。

试了 `MutationObserver` 监听 style 变化——但 `cssText` 赋值是原子操作，Observer 拿到回调时已经覆盖完了，改回来会有肉眼可见的闪烁。

**结论：APlayer 的架构设计不开放给深度定制。要么接受它的样式，要么不用它。**

### 第二阶段：从零自建播放器

#### 技术选型

一开始写了 Preact 组件（`MusicPlayer.jsx`，用 `client:only="preact"` 挂载），因为项目已经有 `@astrojs/preact`。但遇到 View Transitions 兼容问题——Preact 组件在页面切换时会重新挂载，导致 `<audio>` 实例中断、状态丢失。

**最终方案**：Astro 组件 + 内置 `<script>` + 全局 `window.__player` 对象

```astro
<audio id="player-audio" preload="none" style="display:none"></audio>
<div id="player-floating" data-astro-transition-persist>
  <!-- 面板 + 播放栏的 HTML -->
</div>
<script>
(function() {
  // 所有函数定义在 IIFE 顶层，页面切换也能访问
  function renderTree() { ... }
  function updateBarDisplay() { ... }
  function updateProgressBar() { ... }

  // 页面切换时直接恢复，不重新初始化
  if (window.__playerReady) {
    if (window.__player && window.__player.songs) {
      renderTree(); updateBarDisplay();
    }
    return;
  }
  window.__playerReady = true;
  // ... 首次初始化
})();
</script>
```

核心设计：

| 机制 | 作用 |
|------|------|
| `window.__player` 全局对象 | 持有所有状态（歌曲列表、播放队列、展开路径、面板开关） |
| `data-astro-transition-persist` | 关键 DOM 元素跨页存活 |
| IIFE 顶层函数 | 页面切换重新执行脚本时函数已在作用域内，不会 `ReferenceError` |
| `window.__playerReady` 标志 | 防止重复初始化 |

#### 踩坑：作用域 bug

第一次重构时 `renderTree` 定义在 `loadPlaylist().then()` 回调内部，页面切换时重新执行脚本，检测到 `window.__playerReady` 为 `true`，直接调用 `renderTree()`——但此时函数还没定义，`ReferenceError`。

**修复**：把 `renderTree`、`updateBarDisplay`、`updateProgressBar` 全部提升到 IIFE 顶层，和 `if (window.__playerReady)` 检查在同一作用域层级。

### 第三阶段：数据准备——album 字段

原来 `playlist.json` 只有 `name`、`artist`、`url` 三个字段。做歌手→专辑→歌曲阶梯树需要 `album`。

**修改 `sync_music.py`**：扫描 ID3 元数据时把 album 字段输出到 JSON。

**修改 `upload_to_r2.py`**：用 boto3 S3 API 列出 R2 已有对象，不重复上传也能正确生成带 album 的新歌单。

### 第四阶段：彩灯边框（迭代 3 版）

第一版用 `conic-gradient` + `transform: rotate(360deg)`，大面积渐变旋转频繁触发 repaint，肉眼可见掉帧。

| 版本 | 方案 | 问题 |
|------|------|------|
| v1 | `conic-gradient` + `rotate(360deg)` | 大面积旋转频繁 repaint，掉帧 |
| v2 | `linear-gradient` + `background-position` 滑动 + `will-change` | GPU 合成层，流畅了 |
| v3 | 默认 `animation-play-state: paused`，音乐播放时 JS 设为 `running` | 播放才亮灯，停时熄灭 |

最终方案：

```css
.bar-border {
  background: linear-gradient(90deg, #ff0080, #ffcc00, #00d4aa, #0066ff, #7c3aed, #ff0080);
  background-size: 300% 100%;
  animation: border-slide 12s linear infinite;
  animation-play-state: paused;
  will-change: background-position;
}
.bar-border.active {
  animation-play-state: running;
}

@keyframes border-slide {
  0% { background-position: 0% 50%; }
  100% { background-position: 300% 50%; }
}
```

光条和播放器主体的 2px 间隙通过 `box-shadow: 0 0 0 2px rgba(10,10,24,0.92)` 实现，实际上是一个内阴影边框的效果——而不是真的 `border` 或 `outline`。

### 第五阶段：SVG 图标替换

用户反馈：icon 能不能不用 emoji，播放键（`▶`，U+25B6 几何符号）看着挺高端，其他按钮（🔊↔↔）风格不统一。

全部替换为内联 SVG：

```javascript
const I = {
  play: '<svg viewBox="0 0 20 20" width="1em" height="1em"><path d="M5 3l12 7-12 7V3z" fill="currentColor"/></svg>',
  pause: '<svg viewBox="0 0 20 20" width="1em" height="1em"><rect x="5" y="3" width="3" height="14" rx="1" fill="currentColor"/><rect x="12" y="3" width="3" height="14" rx="1" fill="currentColor"/></svg>',
  prev: '<svg viewBox="0 0 20 20" width="1em" height="1em"><path d="M4 3h2v14H4zm12 0l-2 .95L6 10l8 6.05V3z" fill="currentColor"/></svg>',
  next: '<svg viewBox="0 0 20 20" width="1em" height="1em"><path d="M14 3h-2v14h2zm0 7l-2 .95L4 17V3z" fill="currentColor"/></svg>',
  vol: '<svg viewBox="0 0 20 20" width="1em" height="1em"><path d="M3 7v6h4l5 5V2L7 7H3zm11 0v1.5c0 ..."/></svg>',
  list: '<svg viewBox="0 0 20 20" width="1em" height="1em"><rect x="3" y="4" width="14" height="2" rx="1" .../></svg>',
};
```

关键设计：

- `viewBox="0 0 20 20"` + `width="1em" height="1em"` → SVG 自动缩放匹配按钮的 `font-size`
- `fill="currentColor"` → 颜色跟随 CSS `color`，hover 变色自动生效
- 所有路径纯几何图形，和播放键 `▶` 一致的视觉风格

### 第六阶段：布局大改（约 8 次迭代）

播放器的布局是改动最频繁的部分：

```
v1 — 底部横条（APlayer fixed: true）
     满宽横条，黏在底部，没有间距

v2 — CSS 覆盖 APlayer 内联样式（setProperty）
     能控制了，但 APlayer 交互后会重置

v3 — 彻底自建（弃 APlayer）
     浮窗底部，圆角毛玻璃，自由控制

v4 — 宽度 280px 方形卡片
     不再是横条，更像一个独立组件

v5 — 音量竖排（writing-mode: vertical-lr）
     竖排在左侧，占空间不好用

v6 — 音量横排 + 顶行布局（最终版）
     ┌──────────────────────────────────────┐
     │ 🔊 ██████░    │   ⏮ ⏭ ☰           │  ← 顶行
     │ ─────────────────────────────────── │
     │ ▶ 歌名 — 歌手                       │  ← 中行
     │ ██████████████████░░░░░░            │  ← 进度条
     │          0:00                       │  ← 时间居中在下
     └──────────────────────────────────────┘
```

v4→v6 之间的微调：

| 调整 | 方向 |
|------|------|
| 音量横排→竖排→横排 | 竖排占用高度太多，最终横排在顶行左侧 |
| 切歌键下移→上移 | 从进度条左右移到顶行右侧，和歌单按钮并排 |
| 时间右置→居中→下移 | 最终放在进度条下方居中显示 |
| 按钮尺寸反复调 | 播放 20px、切歌 22px、歌单 26px、音量 17px |
| 整体缩放 | `transform: scale(1.2)`，`transform-origin: bottom left` |
| 播放卡宽高比 | 最终 280px 宽，~200px 高，接近正方形 |

### 交互细节

| 交互 | 实现 |
|------|------|
| 点击歌单 ☰ | `panelOpen = !panelOpen` → `overflow: hidden/auto` 配合 `max-height` 过渡 |
| 点击歌手 | 切换 `expanded` 中该歌手的展开状态 → 重新 `renderTree()` |
| 点击专辑 ▶ | 设置 `queue` 为该专辑所有歌曲，`queueIndex = 0`，立即播放 |
| 空格键 | `document.addEventListener('keydown', e => if(e.key===' ' && e.target===document.body) play/pause)` |
| 折行歌名 | 太长用 `text-overflow: ellipsis` 截断 |

### 持久化策略

| 存储 | 时机 |
|------|------|
| `localStorage.setItem('player-state', JSON.stringify(...))` | `astro:before-swap`（View Transitions 切换前）+ `beforeunload`（刷新前） |
| 恢复 | 脚本初始化时 `JSON.parse(localStorage.getItem('player-state'))` |
| 保存内容 | 当前 URL、播放进度、暂停状态、音量、队列及索引、面板展开路径 |

页面切换流程：

```
保存状态 → astro:before-swap 触发 → View Transitions 交换内容
  → data-astro-transition-persist 元素保留 → 新页脚本执行
  → 读取 localStorage → 恢复渲染 → audio 继续播放
```

---

## 全部修改的文件

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `src/components/MusicPlayer.astro` | **重写** | 从 APlayer wrapper → 完整自建播放器（~650 行） |
| `scripts/sync_music.py` | **修改** | 加入 `album` 字段输出，URL 改用实际文件系统路径 |
| `scripts/upload_to_r2.py` | **重写** | 用 boto3 S3 API 列出已有对象，增量上传 + 带 album 生成 |
| `scripts/serve_music.py` | **修改** | 加入 URL 解码、CORS 头、MIME 类型 |
| `.gitignore` | **修改** | `public/music/` → `public/music/playlist.json` |
| `astro.config.mjs` | **修改** | 加入 Vite proxy + `is:inline` 保留 CDN 脚本 |

---

## 学到的概念

| 概念 | 理解 |
|------|------|
| **CSS 优先级回溯** | APlayer `fixed: true` 用 JS 写入 `element.style.cssText`，CSS `!important` 压不住。需要 `setProperty(key, val, 'important')` 生成内联+important 的最高优先级组合 |
| **第三方库样式覆盖策略** | 三级递进：CSS 选择器 → CSS `!important` → JS 运行时覆盖。每级尝试后验证，够用就行 |
| **SVG `currentColor`** | SVG 的 `fill="currentColor"` 让图标颜色继承父元素 `color`，hover/active 变色自动生效 |
| **SVG `1em` 缩放** | `width="1em" height="1em"` 让 SVG 跟随按钮 font-size，一套图标适配不同尺寸 |
| **View Transitions 脚本执行** | 每次页面导航脚本都会重新执行。利用 `window.__playerReady` 做守卫，首次初始化、后续直接恢复 |
| **`will-change` 性能** | `will-change: background-position` 触发 GPU 合成层，`linear-gradient` 背景滑动不触发 repaint |
| **`transform-origin`** | `scale(1.2)` + `transform-origin: bottom left` 从左下角缩放，不改变 `bottom/left` 定位 |
| **`astro:before-swap`** | View Transitions 在交换页面内容前触发，适合保存播放器状态到 localStorage |
| **阶梯树事件委托** | 面板整体 `innerHTML` 渲染 + `treeEl.addEventListener('click', handler)` 委托事件，避免重新渲染后监听丢失 |
| **彩灯边框性能对比** | `conic-gradient` + `rotate` → CPU repaint。`linear-gradient` + `background-position` → GPU 合成层，前者掉帧 |
| **`animation-play-state`** | CSS 属性，`running/paused` 控制动画启停，JS 只需切换类名 |

---

## 最终架构

```
/home/cat/Music/（92 首）
       │
       ▼
scripts/sync_music.py → playlist.json（含 album 字段）
       │
       ▼
upload_to_r2.py → R2 music-store 桶 → playlist.r2.json（R2 URL）
       │
       ▼
MusicPlayer.astro（自建播放器 → HTML5 <audio> + localStorage 持久化）
       │
       ▼
浏览器播放（跨页不断播）
```

### 生产数据流

```
localStorage player-state
  ├── url: 当前播放的 R2 直链
  ├── currentTime: 播放进度
  ├── paused: 暂停状态
  ├── volume: 音量
  ├── queue: 当前队列（歌曲 URL 列表）
  ├── queueIndex: 当前索引
  └── expanded: 面板展开路径
```

### 最终播放卡效果

```
  ┌──────── 16px ────────┐
  │ 🔊 ██████░ │ ⏮ ⏭ ☰  │  ← 彩灯亮时边框渐变动画
  │ ───────────────────── │
  │ ▶ 杀死那个石家庄人     │
  │ ██████████████░░░     │  ← 点击进度条跳转
  │      03:42           │
  └───────────────────────┘
     左下角浮窗，深色毛玻璃
     面板展开：歌手 > 专辑 > 歌曲
     transform: scale(1.2)
```

| 交互 | 效果 |
|------|------|
| 点击 ☰ | 歌手列表从上方展开（max-height 过渡动画） |
| 点击歌手 | 展开/收起该歌手的所有专辑 |
| 点击专辑旁的 ▶ | 整张专辑顺序入队并播放 |
| 点击歌曲 | 立即播放 |
| 空格键 | 播放/暂停 |
| 页面切换 | 播放不中断 |
| 刷新 | 恢复进度、音量、面板 |

### 后续待办

- [ ] 给博客绑个自定义域名
- [ ] Bilibili 同步脚本完整流程
- [ ] Telegram Bot 补充歌源

---

## 后期修复：页面切换累积播放器 + URL 不更新

上线后发现两个严重 bug：切页面时播放器越攒越多导致卡顿，以及浏览器后退键无效（部署版正常但开发版 URL 不更新）。

### 播放器累积的根因

播放器组件同时输出带 `data-astro-transition-persist` 的 HTML 容器 + JS 初始化脚本。View Transitions 切换页面时，旧的持久容器应被保留、新的丢弃。但旧版脚本没有「清理已有 UI」的逻辑，每次导航重新执行脚本时又创建一份播放器 HTML，旧那份也没被正确移除。

**修复**：音频与 UI 解耦。

```
旧方案：                             新方案：
┌─────────────────────────┐          ┌──────────────────────────┐
│ <audio persist>          │          │ <audio persist>           │
│ <div persist> 内含播放器  │          │ <div persist></div>       │
│  JS 只初始化一次          │          │ JS: cleanupPlayerDOM()    │
└─────────────────────────┘          │     → 清理 #player-floating│
                                      │      内部的所有子元素     │
                                      │     → 重新创建 UI         │
                                      └──────────────────────────┘
```

关键函数：

```javascript
function cleanupPlayerDOM() {
  const root = document.getElementById('player-floating');
  if (root) root.innerHTML = '';  // 清除所有旧 UI
  // 移除旧的 <audio>（如果有重复）
  const audios = document.querySelectorAll('#player-audio');
  for (let i = 1; i < audios.length; i++) audios[i].remove();
}
```

每次 IIFE 执行时先清理，再重建 UI。保证页面上永远只有一份播放器。

### persist 重复导致 View Transitions 崩溃

调试开发版后退键问题时，在控制台发现关键错误：

```
TypeError: can't access property "moveBefore", parent is null
    moveBefore swap-functions.js:55
    swapBodyElement swap-functions.js:70
```

追踪到 Astro 的 `swap-functions.js` 源码：

```javascript
function swapBodyElement(newElement, oldElement) {
  // 第一步：找出旧页面中所有带 data-astro-transition-persist 的元素
  for (const el of oldElement.querySelectorAll(`[${PERSIST_ATTR}]`)) {
    const id = el.getAttribute(PERSIST_ATTR);
    // 第二步：在新页面 HTML 中找到具有相同 persist-id 的元素
    const newEl = newElement.querySelector(`[${PERSIST_ATTR}="${id}"]`);
    if (!newEl) continue;
    persistPairs.push({ old: el, newTarget: newEl });
  }
  // 第三步：替换 body
  oldElement.replaceWith(newElement);
  // 第四步：把旧 persist 元素插回新 DOM 中对应位置
  for (const { old: el, newTarget } of persistPairs) {
    moveBefore(newTarget.parentNode, el, newTarget);  // ← 崩溃在这里
    newTarget.remove();
  }
}
```

**问题**：`<audio>` 和 `<div id="player-floating">` 都有 `data-astro-transition-persist`，但**都没有值**。`el.getAttribute(PERSIST_ATTR)` 对两者都返回 `""`（空字符串）。于是 `querySelector` 只找到**第一个匹配的元素**（`<audio>`），两个 persist 对指向同一个 `newTarget`。

执行过程：

```
persistPairs = [
  { old: <audio旧>, newTarget: <audio新> },    ← 两个对的 newTarget
  { old: <div旧>,   newTarget: <audio新> }     ← 指向同一个元素
]

第 1 次迭代: moveBefore(audio新.parentNode, 旧audio, 音频新)
             → 旧 audio 插到新 audio 前面
             → newTarget.remove() 删掉音频新       ✅ 成功

第 2 次迭代: moveBefore(audio新.parentNode, 旧div, 音频新)
             → 但音频新已经被删了！parentNode 是 null！
             → TypeError: can't access property "moveBefore", parent is null
             ❌ 崩溃
```

崩溃后 `history.pushState` 没被执行 → URL 不更新 → 后退键无处可退。

**修复**：给每个 persist 元素不同的值。

```html
<!-- 修复前 -->
<audio data-astro-transition-persist></audio>
<div data-astro-transition-persist></div>

<!-- 修复后 -->
<audio data-astro-transition-persist="audio"></audio>
<div data-astro-transition-persist="floating"></div>
```

这样 `getAttribute` 返回 `"audio"` 和 `"floating"`，`querySelector` 能正确找到各自对应的元素，不会相互覆盖。

---

## 反思

### APlayer 的教训

花了大量时间尝试 CSS 覆盖 APlayer。如果提前检查 APlayer 的样式注入方式（JS 内联 vs CSS），会更快判断出这条路走不通。

第三方库的选择标准应该加一条：**样式系统的开放性**。如果库用 JS 频繁重写内联样式，定制化成本很高。

### 自建 vs 用库的成本判断

回头看，如果一开始就自建，可能比和 APlayer 死磕半天再推倒重来更快——自建加所有功能花了大概 2 小时，和 APlayer CSS 战斗花了 1 天。

但这是**事后诸葛亮**。APlayer 提供了开箱即用的渐进式、歌单、歌词、随机播放……这些如果从头实现也会花时间。合理判断是：**先用库快速跑通功能，如果定制需求明确且库不支持，果断换自建。**

### 布局迭代太快了

播放器的 UI 在一天内迭代了大约 8 个版本，每次改动 -> 编译 -> 部署 -> 查看 -> 再改。很多时间花在细调上（按钮大 2px 还是小 2px）。

以后可以：先画个简单的布局草图，确定大框架（横条/卡片、音量位置、按钮分组），再进入像素级微调。大框架稳定了细调才有意义。
