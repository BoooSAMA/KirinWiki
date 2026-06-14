---
title: "Day 20 — 3D 场景搭建：白色空间、蜂巢网格、末影水晶与纯脚本持久化"
date: 2026-06-16
tags: ["Three.js", "3D", "Astro", "View Transitions"]
description: "引入 Three.js 构建 3D 背景：球面曲率蜂巢网格、银色金属末影水晶、浮动阴影，以及解决 View Transitions 导致 3D 场景闪烁的纯脚本解耦方案"
---

# Day 20 — 3D 场景搭建：白色空间、蜂巢网格、末影水晶与纯脚本持久化

## 背景

博客已有玻璃态 UI 风格（径向渐变背景 + `backdrop-blur` 毛玻璃），但作为个人网站，想在视觉上增加独特的识别度。

目标是构建一个 3D 背景场景：
1. **纯白空间** + 有分割线的地面
2. **类似《小王子》的弯曲星球**——地面带弧度，地平线可见弯曲
3. **类 Minecraft 末影水晶**——银色金属光泽的菱形晶体，浮动自转
4. **作为背景层**——不干扰页面交互，不影响阅读

---

## 技术选型与架构

### 为什么选 Three.js

- 项目基于 Vite（Astro 底层构建工具），Three.js 对 Vite 有一等支持（ESM 导入、摇树优化）
- 部署在 Cloudflare Pages（纯静态），Three.js 客户端渲染，不受影响
- 包体积约 150KB gzip，通过 `import { Scene, ... } from 'three'` 按需导入可进一步控制

### 架构选型：B+ 混合方案

经过三种方案对比：

| 方案 | 做法 | 推荐度 |
|------|------|--------|
| A：内联 `<script>` | 在模板直接写 Three.js 代码 | ❌ 维护性差，View Transitions 难兼容 |
| B：Preact 组件 + `client:only` | 类似 `LikeButton`，组件生命周期管理 | ✅ 初期选用 |
| C：独立 JS 模块动态导入 | 完整模块化 | 稍重 |

初期选用 **B 方案**（Preact 组件薄壳 + 独立场景模块）：

```
src/
├── lib/crystalScene.js        ← 纯 Three.js 逻辑（可移植、可测试）
├── components/Background3D.jsx ← Preact 薄壳（仅挂载/卸载）
```

后来遇到 View Transitions 闪烁问题（见下文），改为 **纯 `<script>` 一次性注入**。

---

## 白色空间与星球曲率

### 第一版：纯白平面 + GridHelper

最简单的实现——白色 `PlaneGeometry(20, 20)` 地面 + `GridHelper(20, 20)` 黑格线。Camera 从斜上方 5° 俯视。

```
场景结构：
┌──────────────────────────────────────┐
│           纯白背景 (0xffffff)          │
│                                      │
│    ═══ ═══ ═══ ═══ ═══ ═══ ═══     │  ← GridHelper 细黑格线
│                                      │
│              💎 菱形晶体               │  ← 待添加
│                                      │
└──────────────────────────────────────┘
```

### 版次迭代细节

瓷砖和场景大小经历了多轮微调：

| 版本 | 动作 | 原因 |
|------|------|------|
| v1 | 瓷砖 1×1，场地 20×20 | 初始值 |
| v2 | 瓷砖 4×4，场地 40×40 | 用户觉得格子太小、延伸不够 |
| v3 | 场地从 44→80→200+ | 反复调大直到视线尽头全是格子 |
| v4 | 瓷砖调为 6×6 | 用户要求 1.5 倍大 |
| v5 | 格线偏移半格 | 让原点落在瓷砖中心，避免黑线穿过水晶 |

每次改动都需同步调整三个参数：

```javascript
const GRID_SIZE = 240  // 总尺寸
const CX = 3           // 中心偏移 X（保证 6%6===3 在格子中心）
const CZ = 3           // 中心偏移 Z
```

### 星球曲率

接受瓷砖大小后，用户提出想要《小王子》里小星球的弯曲感。于是从平地改为球面：

#### 曲率实现

```javascript
const R = 500  // 曲率半径

function surfaceY(wx, wz) {
  const d2 = wx * wx + wz * wz
  return d2 >= R * R ? -R : Math.sqrt(R * R - d2) - R
}
```

把平面改为 `R=500` 的球面。站在 5 单位高处，水平线在约 70 单位远处，具可见弧度。

#### 网格适配

不能再用 Three.js 内置 `GridHelper`（它只支持平面），改成自定义 `BufferGeometry`：

1. 用 `PlaneGeometry` 分段生成曲面地板（`SEG=120`，240 单位分 120 段）
2. 每 6×6 一个格线的交叉点，用 `surfaceY` 计算真实高度
3. 把两点之间的线段合并到单个 `LineSegments` 几何体

### 蜂巢六边形网格

方格改蜂巢—更大的视觉冲击力：

**六边形参数**：

```
hexSize = 4           ← 边长
colSpacing = 6         ← 列间距（flat-top 水平间距）
rowSpacing = 6.928     ← 行间距（√3 × hexSize）
rowOffset = 3.464      ← 奇数列偏移（rowSpacing / 2）
```

**Flat-top 六边形顶点**（从右顺时针）：

```
  ╱╲
 ╲__╱

顶点索引：右→右下→左下→左→左上→右上
```

**边去重**：用 `edgeKey(ax,az,bx,bz)` 为每条无向边生成唯一 key，共享边只画一次，避免重叠变粗。

**曲率适配**：每个顶点都用 `surfaceY(vx[n], vz[n])` 计算 Y 值。

---

## 末影水晶

### 实现

用两个 `OctahedronGeometry`（八面体）嵌套：

```javascript
const outerMat = new THREE.MeshStandardMaterial({
  color: 0xd0d0d0,      // 银灰
  metalness: 0.85,
  roughness: 0.1,
})
const outer = new THREE.Mesh(new THREE.OctahedronGeometry(1.6, 0), outerMat)
outer.scale.y = 2          // 拉高 2× → 钻石形
outer.position.set(-1, 4.5, 5.872)

const innerMat = new THREE.MeshStandardMaterial({
  color: 0xf0f0f0,
  metalness: 0.95,
  roughness: 0.0,
})
const inner = new THREE.Mesh(new THREE.OctahedronGeometry(0.85, 0), innerMat)
inner.rotation.y = Math.PI / 4
outer.add(inner)           // 作为子物体，继承 scale 和旋转
```

### 环境贴图

纯金属材质在无反射物时显示为纯黑。需要环境贴图提供漫反射：

```javascript
const pmrem = new THREE.PMREMGenerator(renderer)
const envScene = new THREE.Scene()
envScene.background = new THREE.Color(0xf5f5f5)
scene.environment = pmrem.fromScene(envScene).texture
pmrem.dispose()
```

`PMREMGenerator` 把白色场景渲染成 `Cubemap`，作为 `scene.environment` 供所有 PBR 材质使用。

### 浮动动画

```javascript
crystal.position.y = 4.5 + Math.sin(t * 0.7) * 0.25
crystal.rotation.y += 0.008
```

- Y 轴以 4.5 为基准，振幅 0.25，频率 0.7
- 自转速率 0.008 rad/frame（约 13 秒一圈）

### 浮动阴影

水晶正下方加一个半透明圆形阴影，随浮动缩放：

```
水晶最高 (Y=4.75)         水晶最低 (Y=4.25)
     💎                       💎
      ↑                        ↓
  ╭──────╯                 ╭──────────╯
  │ shadow │  scale 0.8    │  shadow   │  scale 1.2
  │ opacity │  0.45        │  opacity  │  0.85
  ╰──────╯                 ╰──────────╯
    更小更淡                  更大更深
  (远离地面)                (靠近地面)
```

用 Canvas 生成径向渐变纹理：

```javascript
const canvas = document.createElement('canvas')
const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64)
grad.addColorStop(0, 'rgba(0,0,0,0.7)')
grad.addColorStop(0.5, 'rgba(0,0,0,0.25)')
grad.addColorStop(1, 'rgba(0,0,0,0)')
```

纹理贴到 `PlaneGeometry(2.5, 2.5)` 上，`rotation.x = -π/2` 平贴地面。

---

## 摄像头调试

### 设计思路

用户需要微调相机到"最佳视角"，但双方无法直观沟通坐标值。设计一个键盘操作的实时调试面板：

```javascript
面板显示：
  pos  (12.00, 7.50, 6.00)   ← 相机位置
  look (2.00, 5.00, 5.87)    ← 注视点

按键控制：
  W/A/S/D  → 前后左右移动相机
  R/F      → 上下移动相机
  ↑↓←→    → 移动注视点
  Shift + 键 → 细调 (×0.1)
```

调试完成后，用户把满意的坐标告诉我，我写死到代码里，移除调试面板。

### 复制坐标功能

保留一个精简的左上角面板，显示当前相机坐标，点击一键复制。

```
┌──────────────────────────┐
│ 🗐 复制坐标               │
│ ──────────────────────── │
│ pos (12.00, 7.50, 6.00)  │
│ look (2.00, 5.00, 5.87)  │
└──────────────────────────┘
```

复制按钮使用内联 SVG 图标（不用 emoji），点击显示 `✓ 已复制` 反馈。

---

## View Transitions 持久化

### 问题

页面切换时 3D 背景闪烁——黑屏/白屏一闪，然后重新渲染。

**根因**：Three.js 场景通过 Preact 组件 `Background3D.jsx` + `client:only="preact"` 挂载。Astro 的 View Transitions 在页面切换时会重新执行布局中的脚本，Preact 组件重新挂载 → `useEffect` 重新运行 → canvas 销毁重建 → 闪。

### 第一次尝试：动态创建

```javascript
// ❌ 失败：View Transitions 不认识动态创建的元素
const div = document.createElement('div')
div.setAttribute('data-astro-transition-persist', 'bg3d')
document.body.prepend(div)
createScene(div)
```

**为什么失败**：`data-astro-transition-persist` 需要元素**同时存在于旧页面和新页面的静态 HTML 中**。JS 动态创建的只在一侧有，切换时 Astro 找不到匹配元素 → 丢弃 → 背景消失。

### 最终方案：静态占位 + 脚本守卫

```astro
<body>
  <div id="bg3d" data-astro-transition-persist="bg3d"
       style="position:fixed;inset:0;z-index:0;pointer-events:none"></div>
  <!-- 其他内容 -->
</body>

<script>
import { createScene } from '../lib/crystalScene'

if (!window.__bg3dInitialized) {
  window.__bg3dInitialized = true
  createScene(document.getElementById('bg3d'))
}
</script>
```

**关键点**：

1. **静态 div** 在 BaseLayout 模板中——所有使用该布局的页面都输出相同的 `<div id="bg3d" data-astro-transition-persist="bg3d">`
2. **View Transitions 逻辑**：旧页面和新页面都有 `[data-astro-transition-persist="bg3d"]` → Astro 保留旧的 DOM 子树 → canvas 不被移除 → 不闪烁
3. **`window.__bg3dInitialized` 标志**：脚本在页面切换时会重新执行，标志阻止 `createScene` 被重复调用
4. 移除了 Preact 组件（删除 `Background3D.jsx`），彻底放弃框架生命周期

**流程图**：

```
首次访问 → script 执行 → __bg3dInitialized = false
         → createScene(div) → canvas 插入 div
         → __bg3dInitialized = true

切换页面 → script 再次执行
         → __bg3dInitialized = true → 跳过初始化
         → div#bg3d 被新页面 HTML 中的 div#bg3d 匹配
         → Astro 保留旧 div（含 canvas）→ 3D 场景持续渲染
```

---

## 全部修改的文件

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `src/lib/crystalScene.js` | **新增** | 纯 Three.js 场景模块（~250 行） |
| `src/components/Background3D.jsx` | **新增→删除** | Preact 薄壳（后因 View Transitions 问题移除） |
| `src/layouts/BaseLayout.astro` | **修改** | 移除 Preact 组件导入，增加静态 div + 初始化脚本 |
| `src/styles/global.css` | **修改** | 移除径向渐变背景，改为纯白 fallback |
| `package.json` | **新增依赖** | `three` |

---

## 学到的概念

| 概念 | 理解 |
|------|------|
| **PMREMGenerator** | `WebGLRenderer` 的环境贴图生成器。从纯色场景生成 `Cubemap`，让高 `metalness` 材质有东西可反射，避免金属材质显示为纯黑 |
| **`metalness` 与环境反射** | `metalness: 0.95` 意味着物体表面几乎完全反射环境。如果没有环境贴图 = 反射全黑 = 物体呈黑色 |
| **`scene.environment`** | Three.js r131+ 的功能，给场景设置默认环境贴图，所有 `MeshStandardMaterial` 自动使用，无需单独为每个材质设置 `envMap` |
| **Flat-top 六边形网格** | 顶边和底边水平的六边形。列间距 `1.5×hexSize`，行间距 `√3×hexSize`，奇数列偏移半行。用 `edgeKey` 去重共享边 |
| **BufferGeometry 构建** | 用 `new Float32BufferAttribute(positions, 3)` 构建自定义几何体。`positions` 是 `[x,y,z, x,y,z, ...]` 的平铺数组 |
| **球面曲率参数** | `R=500` 时，30 单位外的水平落差约 0.9 单位。公式 `surfaceY = √(R² - x² - z²) - R` |
| **`data-astro-transition-persist` 机制** | Astro View Transitions 在切换时比较新旧 HTML，找到相同 `persist` 值的元素对后，**保留旧 DOM 子树 + 丢弃新对应的元素**。所以静态 HTML 必须两端都有 |
| **`client:only` 与 View Transitions 的冲突** | `client:only` 组件在切换时会重新挂载，因为 Astro 对框架组件的处理方式不同于普通 DOM 元素。**纯 `<script>` + 静态占位**更可靠 |
| **WebGLRenderer `dispose()`** | 调用 `renderer.dispose()` 释放 GPU 资源，但不会自动清理场景中的几何体/材质。需要 `scene.traverse()` 手动 `dispose` |
| **Canvas 径向渐变纹理** | `createRadialGradient(cx, cy, r0, cx, cy, r1)` 创建放射渐变，绘制到 `<canvas>` 再用 `CanvasTexture` 导入 Three.js，实现软阴影边缘 |

---

## 最终架构

```
src/lib/crystalScene.js
  │
  ├── buildCurvedFloor()       ← 球面地板（PlaneGeometry 分段弯曲）
  ├── buildHexGrid()           ← 蜂巢六边形网格（LineSegments + 边去重）
  ├── createScene(container)   ← 完整场景初始化
  │     ├── Scene (白色背景)
  │     ├── Camera (PerspectiveCamera, 45° FOV)
  │     ├── Renderer (antialias, pixel ratio 上限 2)
  │     ├── PMREMGenerator (环境贴图)
  │     ├── Lighting (Ambient + 2× Directional)
  │     ├── Crystal (2× OctahedronGeometry, 银色金属)
  │     ├── Shadow (CanvasTexture + PlaneGeometry)
  │     └── animate() loop (自转 + 浮动 + 阴影缩放)
  └── destroyScene()           ← 遍历 dispose + renderer 清理
```

### 场景参数一览

```
星球曲率半径:    R=500
地板尺寸:        240×240（延伸到 far 面外）
六边形边长:      4 单位
列间距:          6 单位 / 行间距: 6.928 单位

水晶外层:        OctahedronGeometry(1.6, 0), scale.y=2
水晶内层:        OctahedronGeometry(0.85, 0), rot.y=45°
水晶位置:        (-1, 4.5, 5.872)
自转速度:        0.008 rad/frame
浮动幅度:        ±0.25, 频率 0.7

相机位置:        (12.00, 7.50, 6.00)
注视点:          (2.00, 5.00, 5.87)
Far 裁面:        200
FOV:             45°

阴影大小:        2.5×2.5 平面
阴影透明度:      0.45~0.85 (随浮动变化)
阴影缩放:        0.8~1.2× (随浮动变化)
```