---
title: "Day 25 — 播放器持久化与 View Transitions 的兼容之战"
date: 2026-06-22
tags: ["Debug", "View Transitions", "DOM", "R2", "Music Library"]
description: "修复播放器三连 bug（浏览器后退失效、页面切换累积 UI、URL不更新），根因直指一个空字符串的 persist-id。R2 重传 189 首。音乐库大整理：東京事変独立、专辑排序、元数据修复。"
---

# Day 25 — 播放器持久化与 View Transitions 的兼容之战

## 今天踩的三个大坑

### Bug 1：后退键 404，URL 跳转到 `/%EF%BC%8C`

这是全角逗号 `，` 被塞进 URL 了。本地开发环境一直显示 `http://localhost:4321/%EF%BC%8C`。

**排查过程：**
- 以为是中文标点被误用，搜遍代码没找到
- 清缓存、重启 dev server、换无痕窗口……折腾了半天
- 最后发现生产环境根本没这个问题

**根因：** 是本地 Vite 缓存导致 View Transitions 历史状态错乱。清掉 `.vite` 缓存后恢复正常。但在排查过程中发现了更严重的 Bug 2。

### Bug 2：切换页面播放器越积越多

每次导航就多一个播放器叠加在左下角，页面越来越卡。

**排查过程：**
- 加了 `dedupePersist()` 清理重复 DOM
- 改成每次导航前 `cleanupPlayerDOM()` 全部删除再重建
- 切换到彻底分离架构：`<audio>` 只创建一次，UI 由脚本动态管理

**都没用。** 元素累积是因为 View Transitions 根本没正确保留旧元素。

### Bug 3：浏览器后退键点不了

部署的网站上，进入子页面后后退键始终跳到根路径。

## 根因：一个空字符串的 `persist-id`

把 View Transitions 的文档翻出来一行行读，发现了一个关键约束：

```
data-astro-transition-persist — 可选值，用作元素的持久化标识
```

回头看我们的代码：

```html
<audio data-astro-transition-persist ...></audio>
<div id="player-floating" data-astro-transition-persist>
```

**两个元素的 `persist-id` 都是空字符串 `""`！**

View Transitions 用 `persist-id` 来决定新页面的哪个元素替换旧页面的哪个元素。当两个元素的 persist-id 相同时：

1. 旧页面的 `<audio>` 匹配到第一个需要保留的元素 → 保留
2. 旧页面的 `#player-floating` 想匹配新的 `#player-floating`
3. 但 `querySelector` 只找到第一个匹配（`<audio>`），把它移到了新位置
4. 然后尝试删除剩余的持久元素 → `parentNode is null` → `moveBefore` 崩溃
5. **`history.pushState` 没执行** → URL 不更新 → 后退键失效

**修复：**

```html
<audio data-astro-transition-persist="audio" ...></audio>
<div id="player-floating" data-astro-transition-persist="floating">
```

两个 `persist-id` 不同，View Transitions 才知道它们是对应不同的持久元素。

## View Transitions 导入修复

Astro 6 的 `ClientRouter` 导入路径也出了问题：

```astro
<!-- ❌ 错误：这个路径在 Astro 6 里被弃用了 -->
import { ClientRouter } from "astro:transitions"

<!-- ✅ 正确：直接引用组件文件 -->
import ClientRouter from "astro/components/ClientRouter.astro"
```

## Audio/UI 解耦架构

Bug 2（播放器累积）的根本原因是：旧元素没被保留，新元素又不断创建。彻底解决方法：

```
旧架构（问题所在）：
┌───────────────────────────┐
│ HTML: 组件输出播放器 DOM   │  ← View Transitions 处理 persist
│ JS:  状态挂到 window      │  ← 页面切换时脚本重跑
│                          │
│ 页面切换: persist 没处理好 → 旧没删、新又加 → 累积
└───────────────────────────┘

新架构（修复后）：
┌───────────────────────────┐
│ HTML: <audio persist>     │  ← 唯一持久元素
│       <div persist>       │  ← UI 占位容器
│ JS: 动态创建/销毁 UI      │  ← 每次导航重建，用完即焚
│     状态挂到 window       │  ← 跨页不丢失
│                          │
│ 页面切换:                 │
│ ① JS 执行 → 销毁旧 UI     │
│ ② 保留 <audio> 继续播     │
│ ③ 创建新 UI ← 当前状态    │
└───────────────────────────┘
```

## R2 上传 + 播放修复

重排后的歌曲文件在本地有正确的路径，但 R2 上还是旧文件名的 92 首。需要重新上传。

```bash
# 先拿到 R2 Access Key
export R2_ACCESS_KEY_ID=c920ed1c712e98889eacda3e49212af0
export R2_ACCESS_KEY_SECRET=d47f0479...
export R2_ACCOUNT_ID=1b39eea1974aebea3efad1049edeffec

# 上传全部 189 首到 R2
python3 scripts/upload_to_r2.py
# ✅ 189/189 上传成功，3507.8MB
```

同时修复了播放器的 URL 加载逻辑：

```javascript
// 修复前：先试 playlist.json（新路径），回退到 r2.json（旧路径）
//          → 新路径在 R2 上不存在 → 404
let res = await fetch('/music/playlist.json?' + ts);
if (!res.ok) res = await fetch('/music/playlist.r2.json?' + ts);

// 修复后：先试 r2.json（已有正确 R2 URL）
//         → 全部 189 首可直接从 R2 播放 ✅
let res = await fetch('/music/playlist.r2.json?' + ts);
if (!res.ok) res = await fetch('/music/playlist.json?' + ts);
```

## 音乐库大整理

### 东京事变独立为单独歌手

```
之前：椎名林檎 → 总结/ → 東京事変 × 30 首（混在一起）
现在：東京事変 → 総合/ → 東京事変 30 首（独立艺人）
```

### 专辑排序修复

| 专辑 | 修复 | 曲数 |
|------|------|------|
| 椎名林檎/三文ゴシップ | 空 metadata → 人工补全英日文曲名 | 14 |
| 椎名林檎/日出処 | 空 metadata → 补全 | 13 |
| 林忆莲/野花 | 字母排序 → 原版曲序 | 11 |
| 林忆莲/94 Sandy | `10.` 排在 `2.` 前 → 零填充 | 10 |
| 万青/万能青年旅店 | 字母排序 → 原版曲序 | 9 |
| 万青/冀西南林路行 | 新增专辑 | 8 |
| 宇多田光/First Love | 字母排序 → 原版曲序 | 12 |
| 東京事変/総合 | 按专辑发行时间排序 | 30 |

### 元数据修复

```bash
# 对不起了爱（林忆莲 vs 林忆莲 伦永亮同名）
mutagen 元数据 artist = "林忆莲 伦永亮"
→ 手动修正为 "林忆莲"

# 椎名林檎 / 東京事変 MP3（空 ID3 标签）
→ 批量补全 TIT2/TPE1/TALB/TRCK

# 大额 flac 跳过 ID3 直接修改 Vorbis Comments
→ file.tags['artist'] = '林忆莲'
```

## 最终架构

```
┌──────────────┐    ┌───────────────────┐    ┌──────────────────────┐
│ 本地音乐      │───▶│ sync_music.py      │───▶│ playlist.json         │
│ /home/cat/   │    │ (mutagen 扫描)      │    │ (本地 URL 格式)       │
│ Music/       │    └───────────────────┘    └──────────────────────┘
│              │                             ┌──────────────────────┐
│ 189 首       │───▶│ upload_to_r2.py      │───▶│ playlist.r2.json      │
│ 8 个艺人      │    │ (boto3 S3 API)       │    │ (R2 全量 URL)         │
│ 16 张专辑    │    └───────────────────┘    └──────────────────────┘
└──────────────┘                                    │
                                                    ▼
┌────────────────────────────────────────────────────────┐
│ MusicPlayer.astro                                      │
│                                                        │
│ ① 加载 playlist.r2.json（优先） → 直接 R2 URL ✅       │
│ ② 回退 playlist.json + URL 重写（本地开发）✅            │
│ ③ <audio> persist="audio"                              │
│    <div> persist="floating"              ← 不同 persist-id！│
│ ④ JS 每次导航销毁重建 UI，<audio> 保持播放              │
│ ⑤ View Transitions <ClientRouter> 管理导航历史           │
└────────────────────────────────────────────────────────┘
```

### 学到的概念

| 概念 | 关键 |
|------|------|
| `data-astro-transition-persist` 的 persist-id | 两个持久元素的 id 不能重复（即使是空字符串），否则 View Transitions 的 `querySelector` 会找错元素，导致 `moveBefore` 崩溃 |
| `history.pushState` 与 View Transitions | View Transitions 的导航历史管理依赖 DOM 操作的成功。如果 DOM 操作失败（`parentNode is null`），`pushState` 不会执行，URL 不更新，后退键失效 |
| `import.meta.env.PROD` | Astro 提供的内置变量，在构建产物中为 `true`，开发环境为 `false`。用于区分本地 URL 和 R2 URL 的加载策略 |
| R2 S3 API 认证 | 需要三样东西：Account ID、Access Key ID、Secret Access Key。三者缺一不可。失密后在 Dashboard 重新创建 API Token 可以找回 Access Key，但 Secret 只能重新生成 |
| 文件系统 URL 排序 | 字母排序 `10.file` 出现在 `2.file` 之前。用零填充 `01`-`10` 解决 |
| ID3 vs Vorbis Comments | MP3 用 `mutagen.id3.ID3` 操作，FLAC 用 `mutagen.File` 的 `tags` 属性。写入方式完全不同 |
