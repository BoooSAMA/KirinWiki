---
title: "Day 5 — 社交链接优化 + 点赞功能 + Tag 分类系统"
date: 2026-06-01
tags: ["Feature", "Architecture", "Cloudflare", "D1", "Preact", "Tag"]
description: "Email 复制到剪贴板、GitHub Octocat 图标、Cloudflare Workers + D1 点赞 API、Tag 标签分类系统"
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

---

## 点赞功能（Phase 2 开篇）

在首页底部新增一个 ❤️ 点赞按钮，支持任何人点击、计数持久化、多次点击。

### 架构

```
用户点击 LikeButton (Preact Island)
  → POST /api/likes { slug: "homepage" }
    → Pages Function (functions/api/likes.ts)
      → D1 数据库 INSERT ... ON CONFLICT DO UPDATE
        → 返回 { slug, count }
          → LikeButton 更新显示
```

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Preact Island (`client:load`) | 交互组件，点击有缩放动画 |
| API | Cloudflare Pages Functions | `GET /api/likes?slug=` 查询、`POST /api/likes` 点赞 |
| 数据库 | Cloudflare D1 (SQLite) | `likes` 表，slug 为主键，`ON CONFLICT` 原子递增 |

### D1 数据库

```sql
CREATE TABLE IF NOT EXISTS likes (
  slug TEXT PRIMARY KEY,
  count INTEGER NOT NULL DEFAULT 0
);
```

```sql
-- 点赞核心：不存在则插入，存在则原子 +1
INSERT INTO likes (slug, count) VALUES (?, 1)
ON CONFLICT(slug) DO UPDATE SET count = count + 1
RETURNING slug, count;
```

`ON CONFLICT` + `RETURNING` 保证并发安全，一次查询完成读-改-写，无需事务。

### 修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `wrangler.toml` | 新增 | Cloudflare 配置，D1 绑定 `DB → blog-db` |
| `db/schema.sql` | 新增 | likes 建表语句 |
| `functions/api/likes.ts` | 新增 | Pages Function API 端点 |
| `src/components/LikeButton.tsx` | 新增 | Preact Island 组件 |
| `src/pages/index.astro` | 修改 L2-3, L71-74 | 导入并使用 LikeButton |
| `astro.config.mjs` | 修改 L6, L14 | 添加 `@astrojs/preact` 集成 |
| `tsconfig.json` | 修改 | JSX 配置指向 Preact |
| `package.json` | 修改 | 新增 `@astrojs/preact`、`preact`、`wrangler` |

### 技术细节

**LikeButton 组件**：Preact hooks（`useState`/`useEffect`/`useCallback`），页面加载时 `GET /api/likes` 获取初始计数，点击时 `POST /api/likes` 提交。错误时静默失败（空 catch），不影响页面其他功能。❤️ emoji 点击后触发 `scale-125` 缩放动画（400ms）。

**本地开发**：`wrangler d1 execute --local` 使用本地 SQLite（`.wrangler/state/`），无需 Cloudflare 认证即可测试 API。`wrangler pages dev ./dist` 同时跑前端 + Functions。

**部署配置**：Cloudflare Pages 控制台 → Settings → Functions → D1 bindings 绑定 `DB` 变量到 `blog-db`，否则线上 API 会报错。

---

## Tag 分类系统

给博客文章增加标签（tag）功能，支持按标签筛选文章，标签显示在右侧边栏集中管理。

### 功能

- **文章标签**：每篇 `.md` 文章的 frontmatter 可添加 `tags` 字段，支持多个标签
- **标签总览页**（`/blog/tags`）：标签云展示所有标签，按文章数量降序排列
- **标签筛选页**（`/blog/tags/[tag]`）：动态路由，列出所有包含该标签的文章
- **右侧边栏**：文章详情页和分类列表页均有右侧标签栏，sticky 跟随滚动
- **标签格式**：侧边栏标题统一用 `# 标签`，每个 tag 不加 `#` 前缀，带文章计数

### 架构

```
/blog                        → 分类列表（含"浏览标签"入口）
/blog/[category]              → 该分类文章 + 右侧全站 tags 侧边栏
/blog/[category]/[slug]       → 文章详情 + 右侧当前文章 tags 侧边栏
/blog/tags                    → 标签云（全部 tags + 计数）
/blog/tags/[tag]              → 该 tag 下的文章列表
```

侧边栏内容区分：
| 页面 | 侧边栏展示 |
|------|-----------|
| 分类列表页 | 全站所有 tags，按文章数量排序 + 计数 |
| 文章详情页 | 当前文章自己的 tags |

### Frontmatter 格式

```yaml
---
title: "Day 1 — 搭建个人网站的地基"
date: 2026-05-28
tags: ["Astro", "Cloudflare", "Tailwind", "Deployment", "DNS"]
description: "..."
---
```

`tags` 为可选的字符串数组，未设置时不显示标签侧边栏。

### 修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/content/categories/build-log/day1.md` | 修改 | 添加 `tags: ["Astro", "Cloudflare", "Tailwind", "Deployment", "DNS"]` |
| `src/content/categories/build-log/day2.md` | 修改 | 添加 `tags: ["CSS", "Tailwind", "Animation", "Debugging", "Architecture"]` |
| `src/pages/blog/[category].astro` | 修改 | 提取 frontmatter tags + 全站 tags 侧边栏 |
| `src/pages/blog/[category]/[slug].astro` | 修改 | header 去 tags，改两栏布局 + 文章 tags 侧边栏 |
| `src/pages/blog/index.astro` | 修改 | 加"浏览标签"入口链接 |
| `src/pages/blog/tags/index.astro` | 新建 | 标签云总览页 |
| `src/pages/blog/tags/[tag].astro` | 新建 | 按 tag 筛选文章页（`getStaticPaths` 动态路由） |
| `src/components/CategoryDisplay.astro` | 修改 | PostMeta 新增 `tags` 类型（后续清理） |
| `src/components/SmallPostCard.astro` | 修改 | Tags 从卡片内移除（集中到侧边栏） |

### 技术细节

**完全静态**：标签系统基于 `import.meta.glob` 在构建时扫描所有 `.md` 文件，提取 `tags` frontmatter 生成静态 HTML。无需后端、无需数据库，新增文章后下次构建自动生成标签路由。

**`getStaticPaths` 动态路由**：`[tag].astro` 扫描全部文章收集唯一标签名，为每个标签生成独立页面。部署后 Cloudflare Pages 自动 rebuild。

**侧边栏布局**：使用 `lg:flex lg:gap-8` 实现桌面端左右两栏，移动端自动垂直堆叠。侧边栏 `lg:sticky lg:top-24` 保持可见。

**Tag 计数与排序**：标签云按文章数量降序，同数量按字母排序，高频标签自动靠前。
