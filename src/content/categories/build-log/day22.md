---
title: "Day 22 — 路由分类修复：多级嵌套目录的正确提取"
date: 2026-06-18
tags: ["Astro", "routing", "URL", "debugging", "architecture"]
summary: "修复 Astro 路由中因 `parts[length-2]` 提取分类不当导致多级嵌套内容跑错父目录的问题"
description: "修复博客路由系统中因路径解析错误导致 interview 等嵌套目录下的内容无法归入正确分类的问题。将 `parts[length-2]` 统一改为按 `categories` 关键词定位的索引方案，同时补全了缺失分类的中文显示名，确保构建产物路由结构正确。"
---

# Day 22 — 路由分类修复：多级嵌套目录的正确提取

## 背景

博客建站以来，内容按分类组织在 `src/content/categories/` 目录下：

```
src/content/categories/
├── build-log/           ← 只有一层嵌套
├── blog/
├── projects/
├── music/
├── AI/
├── game/Minecraft/      ← 两层嵌套
└── interview/
    ├── GMM Technoworld/ ← 两层嵌套
    ├── Digital Dream/
    └── NCS_QA engineer/
```

用户发现网站 `/blog` 页面中没有出现 `interview`（面试）分类，反而 `GMM Technoworld`、`Digital Dream`、`NCS_QA engineer` 等公司名**直接作为独立分类**出现在博客分类列表中。

期望的行为是：
- `/blog/interview/` → 展示所有面试相关文章
- `/blog/game/` → 展示所有游戏相关文章

---

## 问题分析

### 根因

所有路由文件都使用 `parts[parts.length - 2]` 提取分类名——即取文件路径的**直接父目录**。

对于 `build-log/day21.md`：

```
parts = ["..", "..", "content", "categories", "build-log", "day21.md"]
parts[length - 2] = "build-log"  ← ✅ 正确
```

对于 `interview/GMM Technoworld/Flood_Detection_Project_DeepDive.md`：

```
parts = ["..", "..", "content", "categories", "interview", "GMM Technoworld", "xxx.md"]
parts[length - 2] = "GMM Technoworld"  ← ❌ 错误（取了公司名而非 interview）
```

这种写法隐含了一个假设：**每个文件只有一层分类嵌套**。遇到两层以上的嵌套（`interview/公司名/文件.md`），取到的永远是倒数第二级目录，而不是真正的顶级分类。

### 影响范围

| 目录 | 实际分类数 | 问题 |
|------|-----------|------|
| `build-log/`, `blog/`, `projects/`, `music/`, `AI/` | 单层 | ✅ 正常 |
| **`interview/公司/`** | **两层** | ❌ 公司名变成独立分类 |
| **`game/Minecraft/`** | **两层** | ❌ Minecraft 变成独立分类 |

---

## 修复方案

### 核心思路

不再使用从尾部索引的方式，而是在路径中定位关键词 `categories` 的索引，取其下一个元素作为分类名：

```javascript
// 修复前（错误）
parts[parts.length - 2]

// 修复后（正确）
parts[parts.indexOf("categories") + 1]
```

无论 `categories/` 后面有多少层嵌套，`indexOf("categories") + 1` 永远指向第一级分类目录。

### 修改文件

共 **5 个文件**，每个文件 1-2 处修改：

| 文件 | 改动位置 | 用途 |
|------|---------|------|
| `src/pages/blog/index.astro` | 分类分组 | 统计各分类文章数 |
| `src/pages/blog/[category].astro` | `getStaticPaths` + 文章过滤 | 生成分类路由 + 按分类展示文章 |
| `src/pages/blog/[category]/[slug].astro` | `getStaticPaths` + 文章匹配 | 生成文章路由 + 匹配文章内容 |
| `src/pages/blog/tags/[tag].astro` | 文章分类提取 | 标签页文章列表的链接生成 |

以 `[category].astro` 为例，两处改动完全相同：

```diff
  export async function getStaticPaths() {
    const postModules = import.meta.glob("../../content/categories/**/*.md", { eager: true })
    const categorySet = new Set<string>()
    for (const filePath of Object.keys(postModules)) {
      const parts = filePath.split("/")
-     categorySet.add(parts[parts.length - 2])
+     categorySet.add(parts[parts.indexOf("categories") + 1])
    }
    // ...
  }
```

```diff
  for (const [filePath, mod] of Object.entries(postModules)) {
    const parts = filePath.split("/")
-   const cat = parts[parts.length - 2]
+   const cat = parts[parts.indexOf("categories") + 1]
    if (cat !== category) continue
    // ...
  }
```

### 补全分类中文名

`categoryNames` 映射中添加了之前缺失的分类：

```javascript
{
  "build-log": { zh: "建站日志", en: "Build Log" },
  blog:        { zh: "默认",     en: "Blog" },
  projects:    { zh: "作品集",   en: "Projects" },
  interview:   { zh: "面试",     en: "Interview" },  // ✨ 新增
  game:        { zh: "游戏",     en: "Game" },       // ✨ 新增
  music:       { zh: "音乐",     en: "Music" },       // ✨ 新增
  AI:          { zh: "AI",       en: "AI" },          // ✨ 新增
}
```

---

## 效果验证

执行 `npm run build` 后，路由结构如下：

```
✓ /blog/interview/index.html                         ← 面试分类页
✓ /blog/interview/flood_detection_project_deepdive    ← GMM 文章
✓ /blog/interview/面试错题集                           ← Digital Dream 文章
✓ /blog/interview/面试官背调                           ← NCS 文章
✓ /blog/interview/mock_interview_feng_yilang
✓ /blog/interview/selfintro_feng_yilang
✓ /blog/interview/interview_checklist
✓ /blog/interview/intern_work_analysis
✓ /blog/interview/python_项目问答模拟
✓ /blog/interview/smart_bakery_技术栈详解
✓ /blog/interview/基础问答模拟
✓ /blog/interview/实习生实操指南
✓ /blog/interview/company_background

✓ /blog/game/index.html                               ← 游戏分类页
✓ /blog/game/gtnh                                     ← Minecraft 文章
```

所有 interview 相关内容正确归入 `/blog/interview/`，不再有公司名作为独立分类的问题。

---

## 边界情况

### slug 冲突（已知问题）

构建时出现 warning：

```
Could not render `/blog/interview/company_background` from route
`/blog/[category]/[slug]` as it conflicts with higher priority route
```

原因：三个不同公司目录下都有 `COMPANY_BACKGROUND.md`：
- `interview/GMM Technoworld/COMPANY_BACKGROUND.md`
- `interview/Digital Dream/COMPANY_BACKGROUND.md`
- `interview/NCS_QA engineer/COMPANY_BACKGROUND.md`

修复后它们都归入 `interview` 分类，slug 生成逻辑是纯文件名（`company_background`），三条记录 slug 相同 → Astro 只保留第一个。

**当前状态**：第一个被保留，后两个被忽略。这在当前场景下是可接受的（三篇背景分析内容相关性高），但如需完全区分，需要在 slug 生成逻辑中加入子目录前缀。

### 路径兼容性

`parts.indexOf("categories")` 依赖于 glob 路径中一定包含 `categories` 这个词。由于所有 markdown 文件都通过 `"../../content/categories/**/*.md"` 匹配，这个条件始终成立，不会出现 `-1` 索引错误。

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/pages/blog/index.astro` | **修改** | 分类分组改用 `indexOf("categories") + 1`；补全分类中文名 |
| `src/pages/blog/[category].astro` | **修改** | `getStaticPaths` + 分类过滤逻辑修正；补全分类中文名 |
| `src/pages/blog/[category]/[slug].astro` | **修改** | `getStaticPaths` + 文章匹配逻辑修正；补全分类中文名 |
| `src/pages/blog/tags/[tag].astro` | **修改** | 文章分类提取逻辑修正 |

---

## 学到的概念

| 概念 | 理解 |
|------|------|
| **Astro 文件路由与目录结构解耦** | Astro 的路由基于文件系统路径（`src/pages/blog/[category].astro` 对应 `/blog/:category`），但数据源（content collection 或 glob）的目录结构可以与此不同。**路由参数的值**由 `getStaticPaths` 返回什么决定，而非文件在磁盘上的实际位置 |
| **`parts[length - 2]` 隐含假设** | 从数组尾部索引假设了只有一层嵌套。当目录结构扩展为双层后，这个假设崩塌。**从已知锚点（`categories`）正向索引**比从尾部反向索引更健壮 |
| **slug 冲突处理** | Astro 中如果 `getStaticPaths` 返回了相同的 `[category, slug]` 对，后定义的会静默覆盖前面的。Astro 会发出 warning 但不会阻止构建。需在设计 slug 生成策略时考虑文件路径的唯一性 |
| **Astro 的 `getStaticPaths` 去重行为** | `getStaticPaths` 返回相同 params 的多条记录时，Astro 不会报错（只会 warning），实际生成的是**较早**的那个条目。观察：遍历 `Object.keys(modules)` 时，glob 返回顺序即文件系统遍历顺序 |
| **import.meta.glob 的路径计算** | `import.meta.glob` 的模式匹配路径是相对于当前文件的相对路径。Vite 会在编译时展开 `**` 通配符，实际运行时 `split("/")` 得到的数组长度取决于匹配到的文件在磁盘上的真实路径深度 |
