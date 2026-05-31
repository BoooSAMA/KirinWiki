---
title: "Day 2 — CSS 骨架修复 + 灯条动画 + 博客分类系统"
date: 2026-05-29
tags: ["CSS", "Tailwind", "Animation", "Debugging", "Architecture"]
description: "修复 Tailwind 不生效、实现卡片 LED 灯条动画、搭建博客分类路由、连接建站日志文档"
---

# Day 2 — CSS 骨架修复 + 灯条动画 + 博客分类系统

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

---

## Part 2 — 卡片边缘灯条动画

### 效果

首页、博客列表、作品集等所有卡片 hover 时，卡片边缘出现一圈多色「LED 灯条」追逐动画——蓝色 → 紫色 → 粉色 → 黄色 → 绿色 → 靛蓝 → 蓝色，光线从顶部小点开始、展开到完整一圈。

### 实现原理

使用 **CSS `@property` 注册的自定义属性** 驱动动画，无需 JavaScript：

```css
@property --p {
  syntax: '<percentage>';
  initial-value: 0%;
  inherits: false;
}
```

核心思路：

1. 给卡片加 `::before` 伪元素，定位在卡片外侧（`inset: -3px`），作为发光边框
2. 用 `conic-gradient`（锥形渐变）画出多色光环，中间用 `transparent` 区域做缺口
3. 用 `mask-composite: exclude` 把中间掏空，只留边框
4. 自定义属性 `--p` 控制发光区域占比：0%（hover 前 = 一小段）→ 100%（hover 时 = 整圈），通过 `transition: --p 0.6s` 平滑过渡

```css
.ring-glow::before {
  --p: 0%;
  background: conic-gradient(
    #60a5fa 0%, #a78bfa ..., transparent ...,
    #60a5fa 100%
  );
  mask-composite: exclude;
  transition: --p 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.ring-glow:hover::before {
  --p: 100%;
}
```

### 关键技术点

| 技术 | 说明 |
|------|------|
| `@property` | CSS Houdini API，将自定义属性注册为 `<percentage>` 类型，浏览器才能对它做插值动画 |
| `conic-gradient` | 锥形渐变，围绕中心点旋转着色，天然适合做环形灯带效果 |
| `mask-composite` | CSS Mask 裁剪，把 `::before` 的中间区域抠掉，只保留边框环 |
| `cubic-bezier` 缓动 | 灯条展开有加速→减速的节奏感，比线性 `ease` 更生动 |
| GPU 加速 | `--p` 的动画由浏览器 Compositor 线程处理，不触发重排 |

### 应用范围

所有使用 `class="ring-glow"` 的卡片：首页 5 张导航卡片、博客分类卡片、文章小卡片、作品集/图片/推荐/关于卡片 —— 共 7 种场景统一使用同一套灯条效果。

### 背景渐变

同时将 `body` 背景从单调的 `bg-gray-50` 改为 **8 层叠加的 `radial-gradient`**：

- 左上：水蓝色（aqua）
- 右上：玫瑰金色（rose-gold）
- 左下：玫瑰金色
- 中下方：水银色（silver）
- …共 8 层，`background-attachment: fixed`

产生的效果：页面背景不再是平的灰色，而是有柔和的水彩光斑，和毛玻璃卡片搭配更协调。

---

## Part 3 — 博客分类系统

### 架构

采用 **文件系统即分类** 的设计，不使用 Astro 内置的 Content Collections，而是用 `import.meta.glob` 动态发现所有 `.md` 文件，按父目录名自动归类：

```
src/content/categories/
├── build-log/          → 分类: build-log → 显示名: "建站日志" / "Build Log"
│   ├── day1.md
│   └── day2.md
├── blog/               → 分类: blog → 显示名: "默认" / "Blog"
│   └── first-post.md
├── projects/           → 分类: projects → "作品集" / "Projects"
└── AI/                 → 分类: AI（待补充显示名）
```

### 三级路由结构

```
/blog                            →  分类列表页面
/blog/build-log                  →  该分类下的文章列表
/blog/build-log/day2             →  单篇文章页面
```

对应 3 个路由文件：

| 文件 | 路由 | 功能 |
|------|------|------|
| `src/pages/blog/index.astro` | `/blog` | 扫描所有 `.md`，按目录分组，显示每个分类的卡片 + 文章数量 |
| `src/pages/blog/[category].astro` | `/blog/:category` | `getStaticPaths` 动态生成所有分类页，列出该分类的所有文章 |
| `src/pages/blog/[category]/[slug].astro` | `/blog/:category/:slug` | `getStaticPaths` 生成所有文章页，渲染 Markdown 内容 |

每层都有「返回上级」的面包屑导航：文章页 → 分类页 → 分类列表。

### 统计生成

所有 3 个路由文件都用 `getStaticPaths()` + `import.meta.glob("../../content/categories/**/*.md", { eager: true })` 扫描内容，因此：
- **添加新文章**：只需在对应分类目录下新建 `.md`，下次部署时自动生成页面
- **添加新分类**：新建子目录 + 在 3 个路由文件的 `categoryNames` 对象中加一行显示名映射

### 文章 Frontmatter

```yaml
---
title: "Day 2 — 修复 CSS 骨架问题"
date: 2026-05-29
description: "诊断修复页面 CSS 失效问题"
---
```

字段均为可选，无 Schema 校验——学习阶段暂时不引入 Zod。

---

## Part 4 — 连接建站日志文档

### 改造前

建站日志的 `.md` 文件存在 `src/content/categories/build-log/` 目录下，但没有被任何页面引用，访问不到。

### 改造后

通过上面的三级路由系统，建站日志自动接入博客框架：

- 访问 `/blog` → 看到「建站日志」分类卡片，显示文章数量
- 点击进入 `/blog/build-log` → 看到 day1、day2……按日期倒序排列
- 点击任一文章 → 进入 `/blog/build-log/day2` 等详情页，渲染 Markdown
- 文章页有面包屑：`← 分类 ← 建站日志`，可快速返回

### 工作流

从现在开始，每天写建站日志只需在 `build-log/` 目录下新建 `dayN.md`，填写 frontmatter 和内容，部署后自动上线 ——**不需要修改任何路由或组件代码**。

---

## 今日代码量

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/styles/global.css` | 重写 | `@property --p` + `conic-gradient` 灯条动画 + 8 层背景渐变 |
| `src/pages/blog/index.astro` | 新建 | 分类列表页面（`import.meta.glob` 扫描 + 分组计数） |
| `src/pages/blog/[category].astro` | 新建 | 动态分类路由（`getStaticPaths` + 文章列表） |
| `src/pages/blog/[category]/[slug].astro` | 新建 | 动态文章路由（`getStaticPaths` + Markdown 渲染） |
| `src/components/CategoryDisplay.astro` | 新建 | 分类文章网格组件 |
| `src/components/SmallPostCard.astro` | 新建 | 紧凑文章卡片组件 |
| `src/components/PostCard.astro` | 新建 | 占位符（待实现） |
| `src/content/categories/build-log/day1.md` | 新建 | Day 1 建站日志 |
| `src/content/categories/build-log/day2.md` | 新建 → 续写 | Day 2（本文档） |
| `src/content/categories/blog/first-post.md` | 新建 | 第一篇博客占位 |
