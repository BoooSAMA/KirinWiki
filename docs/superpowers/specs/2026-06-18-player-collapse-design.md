# 播放器收起/展开功能设计

## 概述

给博客底部 APlayer 播放器添加收起/展开功能。收起时显示迷你播放器（播放键 + 展开键），展开时恢复完整播放器。中间带缩放动画过渡，收起后释放渲染资源（`backdrop-filter` 不再计算）。

## 交互行为

| 状态 | 显示内容 | 位置 |
|------|---------|------|
| **展开（默认）** | 完整 APlayer（歌名、进度条、控制按钮、播放列表等） | 底部居中，左右下各 16px（当前设计） |
| **收起** | 迷你播放器：播放/暂停按钮 + 展开按钮 | 左下角浮动，离左/下边距 16px |
| **动画** | 缩放 + 淡出过渡 | `transform-origin: bottom left` |

### 展开 → 收起

1. 用户点击 APlayer 控制器上的收起按钮（▼）
2. APlayer 以左下角为基点做 `scale(0.15)` + `opacity: 0.6` 动画（0.35s ease）
3. 动画完成后，APlayer 切 `display: none`
4. 迷你播放器显示（`display: flex`）
5. 状态保存到 `localStorage`

### 收起 → 展开

1. 用户点击迷你播放器的展开按钮
2. 迷你播放器隐藏
3. APlayer 恢复显示
4. 如果 APlayer 之前是播放状态，自动继续播放
5. 状态保存到 `localStorage`

## 视觉设计

### 迷你播放器（收起状态）

```
           ← 左下角 16px ─┐
                          │
┌──────────────────────────┐
│ (▶/⏸)              (↗) │  ← 玻璃拟态 pill
└──────────────────────────┘
   · 播放/暂停按钮          · 展开按钮
   · 与 APlayer 播放状态同步  · 点击恢复完整播放器
```

- 形状：水平胶囊状，圆角 24px
- 背景：`rgba(255, 255, 255, 0.85)` + `backdrop-filter: blur(20px)`（与完整播放器一致的玻璃风格）
- 尺寸：约 72px × 40px，内部按钮 32px × 32px
- 暗色模式：深色背景（与完整播放器同步）

### 收起按钮（在完整播放器内）

在 APlayer 控制栏最右侧（播放列表切换按钮后面）加一个 chevron-down（▼）图标按钮，样式与 APlayer 其他图标按钮一致。

## 动画实现

```css
#aplayer.collapsing {
  transition: transform 0.35s ease, opacity 0.35s ease;
  transform-origin: bottom left;
  transform: scale(0.15);
  opacity: 0.6;
}
```

GPU 加速属性（transform/opacity），不影响性能。

## 状态持久化

- Key: `aplayer-collapsed`（`'true'` / `'false'`）
- 每次收起/展开时写入 localStorage
- 页面加载时读取，恢复上一次的状态
- View Transitions 页面切换时保持当前状态不变

## 流畅度优化原理

展开状态下，页面滚动时 `backdrop-filter: blur(24px)` 需要实时计算背景内容，这是主要的性能开销。收起后 APlayer 被 `display: none`，浏览器不再对其做任何渲染计算。迷你播放器面积小（~72px × 40px），`blur(20px)` 的计算量可忽略不计。

## 不涉及改动

- 不修改 APlayer 的初始化逻辑
- 不修改 localStorage 播放状态持久化（已有）
- 不修改歌单加载逻辑
- 不影响 View Transitions 页面切换

## 实现范围

仅修改一个文件：`src/components/MusicPlayer.astro`

- 新增 ~10 行 HTML（迷你播放器）
- 新增 ~40 行 CSS（迷你播放器样式 + 动画）
- 新增 ~40 行 JS（收起/展开逻辑）
