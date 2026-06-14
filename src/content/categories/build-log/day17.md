---
title: "Day 17 — 音乐播放器架构决策：为什么选 Astro + R2"
date: 2026-06-13
tags: ["Architecture", "Music", "Cloudflare", "R2", "D1", "View Transitions"]
description: "参考 Hugo + PJAX 博客的播放器方案，分析为什么对 Astro 技术栈来说 View Transitions + R2 + D1 是更好的选择"
---

# Day 17 — 音乐播放器架构决策：为什么选 Astro + R2

## 背景

给博客加音乐播放器，核心痛点不是"用什么播放器库"，而是**页面跳转时播放器不能断**。

参考了一篇 Hugo 博客的播放器实现文章，作者踩坑踩得很实在。但技术栈不同（Hugo vs Astro），直接照搬会走弯路。这篇文章梳理借鉴了什么、舍弃了什么、以及为什么。

---

## 参考方案回顾（Hugo + PJAX + Bilibili）

原文作者的实现链路：

```
Hugo 静态站点
  → APlayer 固定底部
  → Python 脚本从 Bilibili 收藏夹下载音频
  → 生成 JSON 歌单
  → PJAX 实现站内无刷新跳转
  → localStorage 持久化播放状态
  → KaTeX / Giscus / 搜索等组件 PJAX 后手动重初始化
```

### 值得借鉴的设计思路

| 思路 | 说明 |
|------|------|
| **歌单与代码解耦** | 脚本生成 JSON 数据文件，播放器只读数据，加歌不改代码 |
| **元数据覆盖层** | 自动抓取的歌名/歌手不准，保留手工修正层（`local.json`） |
| **localStorage 持久化** | 刷新后恢复播放进度、歌曲索引、暂停状态 |
| **分 P 视频拆分** | 一个 B 站视频含多首曲目时，拆成独立条目，播放器体验更像歌单 |

### 不适用于 Astro 的部分

#### 1. PJAX → View Transitions

原文作者用 PJAX 是被迫的——Hugo 是纯 SSG，没有内置页面切换 API。PJAX 引入后又带来一堆后遗症：

- body class 不同步 → 要覆写 `handleResponse`
- KaTeX 不自动渲染 → 要在 `pjax:complete` 手动调用
- Giscus 评论不加载 → 要动态创建 script 标签
- 搜索不重新绑定 → 要把初始化拆成可导出函数
- 代码复制按钮重复插入 → 要加 `data-init` 去重标记

**Astro 3+ 内置 View Transitions API**，一行 `<ViewTransitions />` 搞定所有页面切换。浏览器原生 API 负责 DOM 差异更新 + 平滑过渡，播放器实例自然存活。不需要额外库、不需要手动重初始化组件、不需要处理 body class 同步。

#### 2. 评论 / 公式 / 搜索重初始化

Astro 的 Island 架构（`client:load`、`client:only`）让组件在页面切换后自然重新挂载，不存在 PJAX 那种"DOM 换了但脚本没跑"的问题。这是架构层面的差异，不是补丁能拉平的。

#### 3. Bilibili 下载流

原文用 yt-dlp 本地下载 m4a，这部分的思路可以保留，但输出的目标变了：

```
原文：下载到 static/music/ → Hugo 直接读取
我们：下载后上传到 Cloudflare R2 → 通过 Worker API 提供
```

---

## 为什么选 Astro + R2 架构

### 技术选型全景

```
Bilibili 收藏夹
  ──→ Python 脚本（本地 / GitHub Actions）
        ├── Bilibili API 获取收藏夹列表
        ├── yt-dlp 下载音频（m4a）
        ├── 提取元数据（歌名、歌手、封面）
        ├── 上传音频到 Cloudflare R2
        └── 写入元数据到 Cloudflare D1
              │
              ▼
        Astro 博客
          ├── View Transitions（页面切换不断播）
          ├── APlayer / <audio> 组件（client:only）
          ├── D1 查询歌单（API Route / Server Function）
          └── R2 提供音频流（公开读 URL）
```

### 为什么是 Cloudflare R2 而不是本地存储

| 维度 | 本地 `static/` | Cloudflare R2 |
|------|---------------|---------------|
| Git 仓库 | 膨胀，clone/pull 慢 | 不进 Git |
| 存储上限 | 取决于仓库大小（~1GB 就痛苦了） | 免费 10GB，够存上千首歌 |
| 带宽 | 全靠 Pages 源站 | R2 本身是 CDN，全球边缘分发 |
| 扩容 | 换更大的 Git LFS / 外部服务 | 无上限，按量付费 |
| 音频处理 | 本地 | 未来可叠 Workers' 转码/封面裁剪 |

### 为什么是 D1 而不是 JSON 文件

| 维度 | JSON 本地文件 | D1 数据库 |
|------|-------------|-----------|
| 查询 | 全量加载后 JS 侧 filter | SQL 查询，按需返回 |
| 搜索 | 前端遍历大数组 | `WHERE name LIKE ?` 索引查询 |
| 排序 | 手动 sort | `ORDER BY` 原生支持 |
| 更新 | 重新构建 | API 写入即时生效 |
| 部署 | 每次构建打包 | Workers 查询实时 |

### Bilibili vs Telegram 数据源对比

| | Telegram Bot | Bilibili 收藏夹 |
|---|---|---|
| 配置复杂度 | 注册 Bot、关 Privacy Mode、设 Webhook | **只需要收藏夹 ID**（`fid`） |
| 运行位置 | Cloudflare Worker（全在线） | 本地跑 Python 脚本 / GitHub Actions |
| 音频来源 | 手动上传的音频文件 | Bilibili 视频提取（m4a） |
| 音频质量 | 取决于上传的文件 | Bilibili 压缩约 128kbps |
| 同步方式 | Worker 实时监听 TG 消息 | 脚本手动跑 / 定时任务 |
| 额外依赖 | grammY / Hono | **yt-dlp**（无需 ffmpeg） |

**决策：先用 Bilibili 方案搭起来**，一个收藏夹 ID + 一个 Python 脚本就能跑通全链路。Telegram Bot 作为后续补充源，两套数据都往同一个 R2 + D1 写。

---

## 实操：适配器安装与 Hybrid 模式配置

为了让博客同时支持静态页面和 API 端点，需要做两步基础设施搭建。

### 安装 @astrojs/cloudflare 适配器

```bash
npx astro add cloudflare
```

这个命令会自动：
- 安装 `@astrojs/cloudflare` 依赖
- 在 `astro.config.mjs` 中添加适配器配置
- 更新 `package.json`

装完后，构建时会自动适配 Cloudflare Pages 的运行环境，包括正确的模块格式、静态资源路径等。

### 设置 Hybrid 渲染模式

`astro.config.mjs` 中的关键配置：

```js
// astro.config.mjs
import { defineConfig } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  output: 'static',  // 默认静态模式
  adapter: cloudflare(),
  // ...
});
```

`output: 'static'` 是 Astro 的默认模式，所有页面在构建时预渲染为静态 HTML。但如果某个页面或 API 路由需要动态能力（比如查询 D1 数据库），只需要在该文件顶部加一行：

```astro
---
export const prerender = false;
---
```

这个页面就会在请求时由 Cloudflare Worker 动态渲染，而不是构建时生成。这就是 **Hybrid 模式**——大部分页面静态，个别路由动态。

### D1 数据库绑定

因为项目之前已经创建过 D1 数据库（`blog-db`），`wrangler.jsonc` 中已有绑定配置：

```jsonc
{
  "d1_databases": [
    {
      "binding": "DB",
      "database_name": "blog-db",
      "database_id": "<已有的 database_id>"
    }
  ]
}
```

这样 API 路由中就可以通过 `context.locals.DB` 或 `Platform.env.DB` 访问 D1 数据库。

### 验证

```bash
npm run build
```

构建成功，47 个页面全部通过，证明适配器配置正确、所有静态路由正常输出，且已有的 D1 绑定兼容。

### 为什么 Hybrid 模式适合这套架构

| 页面类型 | 渲染模式 | 说明 |
|---------|---------|------|
| 首页、博客、关于等 | 静态（SSG） | 构建时生成 HTML，CDN 直接响应 |
| 歌单 API `/api/music/songs` | 动态（SSR） | 请求时查询 D1，返回最新数据 |
| 音频文件 | 静态（R2 直链） | R2 公开读 URL，不经过博客服务器 |

静态页面享受 CDN 缓存和边缘分发，API 路由保持实时查询能力，音频由 R2 直接提供——各层各司其职。

---

## 实操：APlayer 集成

### 播放器组件

在 `src/components/` 下创建播放器组件，使用 APlayer 库，固定在页面底部：

```astro
---
// MusicPlayer.astro
---
<link
  rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/aplayer/dist/APlayer.min.css"
/>
<script src="https://cdn.jsdelivr.net/npm/aplayer/dist/APlayer.min.js"></script>

<div id="aplayer" data-astro-transition-persist></div>

<script>
  const ap = new APlayer({
    container: document.getElementById('aplayer'),
    fixed: true,
    order: 'random',
    audio: [
      {
        name: '测试歌曲 1',
        artist: 'SoundHelix',
        url: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
        cover: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.jpg',
      },
      {
        name: '测试歌曲 2',
        artist: 'SoundHelix',
        url: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
        cover: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.jpg',
      },
      {
        name: '测试歌曲 3',
        artist: 'SoundHelix',
        url: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3',
        cover: 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.jpg',
      },
    ],
  });
</script>
```

### 关键：`data-astro-transition-persist`

播放器容器上加了 `data-astro-transition-persist` 属性：

```html
<div id="aplayer" data-astro-transition-persist></div>
```

这是 Astro View Transitions 提供的原生保活机制。页面切换时，带有此属性的 DOM 节点**不会被销毁重建**，而是直接保留在页面中。播放器实例（APlayer 内部创建的各种 DOM 和音频上下文）自然存活，音乐持续播放。

对比一下：

| 方案 | 播放器保活方式 | 额外成本 |
|------|--------------|---------|
| 原文 PJAX | 播放器放在 footer 外层，不随 `.main-container` 替换 | 要配 PJAX selectors、处理 body class 同步 |
| 我们 View Transitions | 一行 `data-astro-transition-persist` | 浏览器原生支持，零额外代码 |

### 播放状态持久化

页面切换虽不销毁播放器，但**浏览器刷新**仍会重建。为此加 localStorage 持久化：

```js
// 页面卸载前保存状态
window.addEventListener('beforeunload', () => {
  const playInfo = {
    index: ap.list.index,
    currentTime: ap.audio.currentTime,
    paused: ap.paused,
  };
  localStorage.setItem('aplayer_playInfo', JSON.stringify(playInfo));
});

// 页面加载后恢复状态
window.addEventListener('load', () => {
  const saved = localStorage.getItem('aplayer_playInfo');
  if (!saved) return;

  const playInfo = JSON.parse(saved);
  ap.list.switch(playInfo.index);

  setTimeout(() => {
    ap.seek(playInfo.currentTime);
    if (!playInfo.paused) ap.play();
  }, 500);
});
```

`setTimeout(500)` 是因为 `ap.list.switch()` 不是同步的——播放器需要时间加载新歌曲的元数据，过早 `ap.seek()` 会失效。

### 验证

在 `BaseLayout.astro` 中引入组件：

```astro
---
import MusicPlayer from '../components/MusicPlayer.astro';
---
<html>
  <body>
    <slot />
    <MusicPlayer />
  </body>
</html>
```

然后 `npm run dev` 本地启动，底部出现 APlayer 横条，点击站内链接时音乐持续播放不中断。

---

## 踩坑：静态资源大小限制

### 问题

播放器 UI 搭好了，开始加真实歌单。运行 `scripts/sync_music.py` 扫描本地音乐库（`/home/cat/Music/`），92 首歌的歌单 JSON（`public/music/playlist.json`）顺利生成。但构建时发现了问题：

**Cloudflare Pages 对 `public/` 下的静态资源有 25MB 上限。** FLAC 格式的音频文件一首就可能 30-50MB，92 首歌全部放进 `public/` 显然不可能。

而且即使 size 够用，把音频放 `public/` 也不对：
- 构建时间暴增（要复制几百 MB 文件）
- Git 仓库爆炸（代码 + 音频混在一起）
- 开发和生产环境路径不一致

### 解决方案：开发 / 生产双轨架构

不能让 Astro 直接托管音频文件。重新设计：

```
开发环境（localhost）:
  浏览器 → Astro dev server (:4321)
         → Vite proxy 转发 /music/audio/*
         → Python HTTP server (:8765) ← 本地读取硬盘文件

生产环境（Cloudflare）:
  浏览器 → Cloudflare Pages
         → 音频走 Cloudflare R2 直链 URL
```

### Vite Proxy 配置

在 `astro.config.mjs` 中为开发服务器添加代理规则：

```js
export default defineConfig({
  // ...
  vite: {
    server: {
      proxy: {
        '/music/audio/': {
          target: 'http://localhost:8765',
          changeOrigin: true,
        },
      },
    },
  },
});
```

这样 Astro dev server 收到 `/music/audio/xxx.flac` 的请求时，会自动转发到 `localhost:8765` 上的 Python 服务器，不经过 Vite 的静态资源处理管道。

### Python 脚本体系

写了两个 Python 脚本，职责清晰分离：

#### scripts/sync_music.py — 歌单扫描器

扫描本地音乐目录结构，生成 `public/music/playlist.json`。

```
输入：/home/cat/Music/
        ├── 万能青年旅店/
        │     ├── 01 杀死那个石家庄人.flac
        │     └── ...
        ├── 東京事変/
        └── ...

输出：public/music/playlist.json
       [
         {
           "name": "杀死那个石家庄人",
           "artist": "万能青年旅店",
           "url": "/music/audio/万能青年旅店/01 杀死那个石家庄人.flac",
           "cover": "/music/cover/default.jpg"
         },
         ...
       ]
```

路径映射逻辑：
- **歌单 JSON** 路径：`/music/playlist.json` → Astro 构建时复制到 `dist/`，走 CDN
- **音频文件 URL**：`/music/audio/{artist}/{filename}` → 开发时由 Vite proxy 转发到 `:8765`，生产时替换为 R2 URL
- **封面图片 URL**：同理，走 proxy 或 R2

这样歌单 JSON 是静态文件（很小，只有几 KB），音频文件走代理通道，两者不冲突。

#### scripts/serve_music.py — 音频开发服务器

一个简单的 HTTP 服务器，监听 8765 端口，只做一件事：

```python
# 核心逻辑
request_path → 映射到本地 /home/cat/Music/ 下的文件
            → 读取文件返回（支持 Range 请求，允许音频拖动进度）
            → 不存在的文件返回 404
```

支持 `Range` 请求头是因为浏览器播放音频时需要分段读取，不支持 Range 的话拖动进度条会失败。

### 音乐扫描成果

扫描 `/home/cat/Music/`，共识别 **4 位艺术家、92 首歌曲**：

| 艺术家 | 歌曲数 | 说明 |
|--------|--------|------|
| 万能青年旅店 | 9 首 | 完整 |
| 東京事変 | 30 首 | 完整 |
| 林忆莲 | 31 首 | 完整 |
| 陈绮贞 | 21 首 | 完整 |
| 张雨生 | 空文件夹 | 没有音频文件 |
| 椎名林檎 | 空文件夹 | 没有音频文件 |

### 开发时使用流程

开两个终端：

```bash
# 终端 1：音乐服务器
python3 scripts/serve_music.py        # 启动 :8765

# 终端 2：Astro
npm run dev                            # 启动 :4321，自动 proxy 音频请求
```

打开 `http://localhost:4321` → 底部 APlayer 展示 92 首歌的歌单 → 点击任意站内链接 → 播放器继续播不间断 → 刷新页面 → 恢复播放进度。

### 生产环境待办

目前生产环境（Cloudflare Pages）音频还不能播，因为 proxy 只在 `vite.server` 中生效。生产环境需要：

1. 把音频文件上传到 Cloudflare R2
2. 播放器组件根据环境切换 URL 前缀：
   - 开发：`/music/audio/...`（走 proxy）
   - 生产：`https://r2.example.com/audio/...`（走 R2 直链）
3. playlist.json 中的 URL 构建时注入环境变量前缀

这留到后续 R2 部署阶段处理。

---

## 实操：Bilibili 同步脚本

### sync_bilibili.py

写完了 `scripts/sync_bilibili.py`，核心流程：

```
Bilibili API 读取收藏夹（fid / media_id）
  → 遍历视频列表
  → 检查每个视频是否分 P
  → 调用 yt-dlp 下载音频（m4a，无需 ffmpeg）
  → 提取元数据写入 info.json
  → 跳过本地已有的音频（--skip-existing）
```

### 收藏夹实际分析

收藏夹 ID `4057903921`，实际包含 4 个视频：

| 视频 | 本地状态 | 操作 |
|------|---------|------|
| 林忆莲《Sandy'94》 | ✅ 已有 10 首 FLAC | 跳过 |
| 林忆莲《野花》 | ✅ 已有 10 首 FLAC | 跳过 |
| 万青《万能青年旅店》 | ✅ 已有 9 首 MP3 | 跳过 |
| Beyond《乐与怒》 | ❌ 没有 | 可下载 |

3 个本地已有，1 个新的。这说明收藏夹里存的主要是自己熟悉的专辑，B 站同步的增量价值主要在"发现新东西"。

### data/music/local.json 元数据覆盖

B 站视频标题不适合直接当歌名——标题通常带"顶级音质""中日字幕完整版"等前缀，UP 主也不是歌手。

在 `data/music/local.json` 中手动修正：

```json
{
  "bilibili": {
    "BV1sK411t7PN": {
      "p1": {
        "name": "乐与怒",
        "artist": "Beyond"
      }
    }
  }
}
```

`sync_bilibili.py` 下载时优先读取 `local.json` 中的 `name` 和 `artist`，没有覆盖项才 fallback 到 B 站标题。这样即使以后重新同步，已经整理过的元数据不会被覆盖。

### 系统三组件总览

整个播放器后端由三个 Python 脚本组成：

```
music_player/
├── sync_music.py        # 扫描本地 /home/cat/Music/ → playlist.json（92 首已有）
├── sync_bilibili.py     # 从 B 站收藏夹下载 → 补充到本地音乐库
└── serve_music.py       # 开发时提供音频流（支持 Range 请求）
```

| 脚本 | 职责 | 运行时机 |
|------|------|---------|
| `sync_music.py` | 扫描本地目录 → 生成歌单 JSON | 本地音乐有变动时 |
| `sync_bilibili.py` | B 站 API + yt-dlp 下载 → 补充本地 | 收藏夹有更新时 |
| `serve_music.py` | 开发环境 HTTP 音频服务器 | 每次 `npm run dev` 时 |

`sync_bilibili.py` 下载的音频也放在 `/home/cat/Music/` 下，按 `{artist}/{filename}` 组织。`sync_music.py` 再扫描时自动收录新歌，两个数据源共享同一套本地目录结构。

### B 站收藏夹 ID 查看

```
https://space.bilibili.com/<UID>/favlist?fid=4057903921&ftype=create
                                             ↑^^^^^^^^
                                             这就是 fid
```

也可用 `media_id=4057903921` 格式，脚本同时支持两种参数。

### 开发 vs 生产对比现状

| | 开发（localhost） | 生产（Cloudflare Pages） |
|---|---|---|
| 音频来源 | `serve_music.py` 本地 HTTP 服务 (:8765) | R2 直链（TODO） |
| 歌单 JSON | `public/music/playlist.json`（静态文件） | 同左（已构建入 dist） |
| 播放器 | 显示全部 92 首 + B 站新增 | 待 R2 接入后一致 |

---

## 问题排查：本地音频播不了

### 现象

`npm run dev` 启动后，播放器显示歌单正常，但点击播放时没有声音。浏览器控制台报 404。

### 根因 1：URL 路径用 ID3 元数据，不是实际文件路径

`sync_music.py` 最初用音频文件的 ID3 元数据（歌名、歌手）来构建播放器 URL：

```
ID3 歌手 = "万能青年旅店"  →  URL = /music/audio/万能青年旅店/...
```

但实际文件目录名是"万青"：

```
文件系统 = /home/cat/Music/万青/...
```

两者不一致，Python 服务器自然找不到文件。而且 ID3 元数据本身也乱：

| 文件夹名 | ID3 歌手/专辑 | 问题 |
|---------|-------------|------|
| 万青 | 万能青年旅店 | 路径和元数据歌手不同 |
| 总结 | 総合 | 日文 vs 中文文件夹名 |

**修复**：URL 路径从**实际文件系统路径**构建，而不是从 ID3 元数据提取。文件夹名是什么，URL 就用什么。ID3 元数据只用于展示（歌名、歌手显示在播放器 UI 上），不参与路径生成。

### 根因 2：curl 测试中文 URL 编码问题

用 `curl` 命令行测试 `/music/audio/万能青年旅店/...` 返回 404，一度怀疑是服务器不支持中文路径。

实际上 curl 不会自动编码中文——浏览器会。用 Python 验证服务器正常工作：

```python
import urllib.request
# 浏览器行为：自动 URL 编码中文
url = "http://localhost:8765/music/audio/%E4%B8%87%E8%83%BD%E9%9D%92%E5%B9%B4%E6%97%85%E5%BA%97/..."
resp = urllib.request.urlopen(url)
print(resp.status)  # → 200 ✅
```

**还原论**：服务器没问题，问题出在 `sync_music.py` 生成的 URL 路径与实际文件路径不匹配。修复根因 1 后，两个问题一起解决。

### 修复效果

修复后本地播放正常，92 首歌全部可播。这也验证了 Vite proxy + Python 音频服务器的双轨架构设计本身是正确、可工作的——问题只出在数据生成层的路径映射逻辑上。

---

## 准备 R2 云存储

本地播放打通后，下一步是让**生产环境也能播**。生产环境没有 `serve_music.py`，音频必须走 Cloudflare R2。

### R2 开通

```
1. 打开 https://dash.cloudflare.com/
2. 左侧菜单 → R2
3. 点击 Activate R2（免费 10GB，无需绑卡）
4. 终端创建 bucket：
   npx wrangler r2 bucket create music-store
```

### upload_to_r2.py 完成

`scripts/upload_to_r2.py` 编写完成，核心逻辑：

```
读取 public/music/playlist.json 歌单列表
  → 遍历每首歌的本地文件路径
  → 检查 R2 bucket 中是否已存在（跳过已上传的）
  → 上传缺失文件到 music-store bucket
  → 生成 playlist.r2.json（URL 替换为 R2 直链）
```

### R2 API 凭证配置

上传脚本需要 S3 兼容的 API 凭证。注意入口**不是** Dashboard 左侧的"API 令牌"（那个是 Cloudflare 通用 API），R2 有自己的专属入口：

```
Dashboard → R2（左侧菜单）→ 管理 API 令牌 → 创建 API 令牌
```

#### 为什么不用另外两种 Token？

Cloudflare Dashboard 里有三种不同的令牌，别走错：

| 入口 | 用途 | 是否适用 |
|------|------|---------|
| **R2 → 管理 API 令牌** | 生成 S3 兼容凭证（Account ID + Key ID + Secret） | ✅ 正确入口 |
| 左侧"API 令牌" → User API Tokens | 调 Cloudflare 通用 JSON API | ❌ 接口不同 |
| 左侧"API 令牌" → Account API Tokens | 也是 Cloudflare 通用 API | ❌ 接口不同 |

R2 的 S3 兼容 API 需要**专门的三组凭证**（Account ID + Access Key ID + Secret Key），只能从 R2 管理页面生成。

#### 创建令牌三步填

**第一栏：权限** → 选 **Object Read & Write**

- Write：上传音乐到 R2
- Read：读文件（播放器回源）
- Object 级别就够了，不需要 Admin（Admin 能删桶、改配置，没必要露更多权限）
- 最后下拉选应用到 `music-store` 桶

**第二栏：有效期** → 选 **Never expire**

这是给脚本用的 Token，不是给外人用的。选了永不过期就不用隔段时间重新创建。

**第三栏：IP 过滤** → **全部留空**

本机 IP 可能变（家里、出门、换网络），留空最省事。

#### 创建后

点 **Create** 后页面会显示一次 `Access Key ID` 和 `Secret Access Key`。**把 Secret Key 复制下来**（页面关了再也看不到）。

使用方式（环境变量注入，不写进代码）：

```bash
export R2_ACCOUNT_ID="1b39eea1974aebea3efad1049edeffec"
export R2_ACCESS_KEY_ID="<刚创建的 Access Key ID>"
export R2_ACCESS_KEY_SECRET="<刚创建的 Secret Key>"
python3 scripts/upload_to_r2.py
```

脚本运行完后生成 `public/music/playlist.r2.json`——与 `playlist.json` 结构相同，但所有 `url` 字段替换为 R2 公开直链。

### R2 防刷与安全性

R2 默认行为：

| 机制 | 说明 |
|------|------|
| **公开读** | 通过 `r2.dev` 域名可直接访问，无需认证（适合博客音频场景） |
| **无内置鉴权** | 知道 URL 就能访问，不限制 Referer/IP |
| **无速率限制** | Cloudflare 不提供 R2 请求级别的速率限制 |
| **无 WAF 支持** | `r2.dev` 域名不能套 Cloudflare WAF |

针对博客场景的安全策略：

```
轻度防护（推荐）：
  只上传音频文件到 R2，不存敏感数据
  URL 用随机前缀或 hash 命名，不易被扫
  免费额度内的异常流量 Cloudflare 会告警

中度防护（可选）：
  用 Cloudflare Workers 代理 R2，加上 Referer 检查
  在 Worker 中实现速率限制
  套上自定义域名（可以开 WAF + 速率限制）

注意：r2.dev 域名不能配置防盗链或 IP 白名单。
如果用自定义域名接入，可以通过 Cloudflare WAF 规则做更多限制。
```

对个人博客来说，R2 默认的公开读模式足够安全——音频文件本身没有敏感信息，免费额度内被刷的可能性低。如果后续流量大了，再加 Worker 代理层。

### R2 URL 格式

```
R2 公开直链：https://pub-<哈希>.r2.dev/music/audio/万青/01 杀死那个石家庄人.flac
自定义域名：https://music.你的域名.com/万青/01 杀死那个石家庄人.flac（需绑域名）
```

后续需要在播放器组件中根据环境切换 URL 前缀（见生产环境待办）。

### R2 容量评估

| 项目 | 数值 |
|------|------|
| R2 免费额度 | 10GB |
| 本地 92 首总大小 | ~2.1GB |
| B 站 M4A（~8MB/首） | 可存 1200+ 首 |
| 结论 | 个人音乐库绰绰有余 |

### 全部问题修复总结

从本地播放不响到最终打通，修复链路：

| # | 问题 | 根因 | 修复 |
|---|------|------|------|
| 1 | URL 路径找不到文件 | URL 用 ID3 元数据路径，不是实际文件路径（万青≠万能青年旅店） | URL 从实际文件路径构建 |
| 2 | 中文 URL 请求失败 | 中文和空格没做 URL 编码 | `urllib.parse.quote` 编码路径 |
| 3 | 服务器找不到解码后的路径 | `serve_music.py` 没对请求路径做 URL 解码 | `unquote` 解码后再映射文件 |
| 4 | 浏览器跨域报错 | 音频服务器没返回 CORS 头 | 加上 `Access-Control-Allow-Origin: *` |
| 5 | 浏览器无法解码音频 | 响应的 Content-Type 不对 | 根据文件扩展名设置正确 MIME type |
| 6 | APlayer 不读取 playlist.json | 播放器只认 `.r2.json` 后缀，没有回退 | 加回退逻辑：先找 `.r2.json`，没有再找 `.json` |

最终验证：92 首歌全部可播，页面跳转不断播，刷新恢复进度。

---

## 部署到 Cloudflare Pages

生产环境要让音频走 R2，需要在部署前做三件事。

### 第一步：R2 桶开公共访问

R2 桶默认是私有的，需要打开公开访问：

```
Dashboard → R2 → music-store → 设置
  → 向下翻到 "Public Access"（公开访问）
  → 打开开关
  → 复制 Public URL
```

你会得到一个类似这样的 URL：
```
https://pub-xxxxxxxxxxxxxxxxxxxxx.r2.dev
```

### 第二步：用 R2 公开 URL 更新歌单

之前 `upload_to_r2.py` 生成的 `playlist.r2.json` 中 URL 还是 `/music/audio/...` 格式。需要换成 R2 的公开地址：

```bash
export R2_PUBLIC_URL="https://pub-xxx.r2.dev"
python3 scripts/upload_to_r2.py
```

脚本会重新生成 `playlist.r2.json`，所有 URL 变成：
```
/path/万青/万能青年旅店/01 杀死那个石家庄人.flac
↓
https://pub-xxx.r2.dev/万青/万能青年旅店/01 杀死那个石家庄人.flac
```

### 第三步：部署

项目已关联 Git 仓库自动部署，只需要：

```bash
git add .
git commit -m "feat: 添加音乐播放器与 R2 云存储"
git push
```

Cloudflare Pages 自动检测推送 → 自动构建 → 自动部署。

构建时 `playlist.r2.json` 作为静态资源被打入 `dist/`，播放器在 Pages 运行时读取它，音频 URL 全部指向 R2。

### 部署后的播放器架构（生产环境）

```
用户浏览器
  ↓ 请求页面
Cloudflare Pages（Astro 静态站点）
  ↓ 加载 playlist.r2.json
  读取音频 URL → 请求 Cloudflare R2
  ↓
R2 边缘网络 → 返回音频流 → 用户听歌
```

页面跳转由 View Transitions 处理，播放器实例持续存活。音频不走 Pages 源站，不消耗 Workers 请求次数。

---

## 完整的播放器体验链路

```
1. 用户访问首页
2. APlayer 从 D1 API 加载歌单
3. 点击任意站内链接
4. View Transitions 拦截请求，平滑过渡
5. 底部播放器实例未销毁，音乐继续播放
6. 页面切换后，URL、标题、内容更新
7. 播放器保持当前进度，无缝衔接
```

对比原文的 PJAX 链路：

```
原文：点击链接 → PJAX 拦截 → Ajax 请求 → 替换 DOM → 手动重初始化 KaTeX/Giscus/搜索...
我们：点击链接 → View Transitions 拦截 → 浏览器原生 DOM 差异更新 → 完成
```

减少了至少 5 个手动维护点的代码量。

---

## 持久化策略

沿用原文的 localStorage 方案（具体代码见上一节），核心思路：

- **页面卸载前**：保存 `{ index, currentTime, paused }` 到 `localStorage`
- **页面加载后**：恢复歌曲索引 → `setTimeout(500ms)` → 恢复播放进度 → 恢复暂停状态
- `setTimeout(500)` 是因为 `ap.list.switch()` 不是同步的，播放器加载新歌元数据需要时间，过早 `ap.seek()` 会失效

---

## 学到的概念

| 概念 | 理解 |
|------|------|
| View Transitions vs PJAX | 前者是浏览器原生 API，后者是第三方 Hack。Astro 内置支持让 View Transitions 成为默认选择 |
| 播放器架构分层 | 数据源（Bilibili/TG）→ 存储层（R2 + D1）→ API 层（Workers）→ 展示层（APlayer）→ 持久化层（localStorage），各层独立可替换 |
| D1 适合元数据不适合音频 | 音频文件放 R2（对象存储），元数据放 D1（SQL 查询），各司其职 |
| 媒体不进 Git | 音频/图片存 R2，不进仓库。.gitignore 保障、CI 不下载额外资源 |
| 数据源可叠加 | Bilibili 和 Telegram 是两个独立采集器，都往同一个 R2 + D1 写，展示层无感知 |

---

## 后续可扩展

- **GitHub Actions 定时同步**：每周自动跑一次脚本，B 站收藏夹有新歌自动入库
- **Telegram Bot 补充源**：B 站找不到的歌通过 TG 手动上传
- **Workers 音频转码**：m4a → mp3 或动态码率适配
- **播放列表推荐**：基于 D1 标签/风格的简单推荐查询
