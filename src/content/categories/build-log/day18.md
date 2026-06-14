---
title: "Day 18 — 首次部署：从 Pages 到 Workers 的认知修正"
date: 2026-06-13
tags: ["Deployment", "Cloudflare", "Workers", "Wrangler", "R2", "Domain"]
description: "实际部署时发现项目已经配置了 Workers 模式而非 Pages，全程踩坑记录：构建、部署、R2 自定义域名绑定、音频上线"
---

# Day 18 — 首次部署：从 Pages 到 Workers 的认知修正

## 背景

Day 17 的部署章节是在**假设 Pages 自动部署**的前提下写的。实际操作时发现：项目当前的 `wrangler.jsonc` 配置的是 **Workers 模式**，部署路径完全不同。

这篇日志记录从"准备部署"到"网站上线"的完整过程，以及其中发现的认知偏差。

---

## 认知冲击：项目已经配置了 Workers

### 以为是 Pages

翻看项目根目录，`wrangler.jsonc` 中的关键配置：

```jsonc
{
  "name": "my-blog",
  "main": "@astrojs/cloudflare/entrypoints/server",
  "assets": {
    "directory": "./dist",
    "binding": "ASSETS"
  }
}
```

`"main"` 指向适配器的服务器入口，再加上 `"assets"` 绑定静态资源目录——这是 **Workers + Static Assets** 模式，不是 Pages 模式。

### Pages vs Workers：有什么区别

| 维度 | Cloudflare Pages | Cloudflare Workers + Assets |
|------|-----------------|---------------------------|
| 配置入口 | `wrangler.toml` 无 `main` | `wrangler.jsonc` 有 `"main"` |
| 构建产物 | Pages 自动识别 `dist/` | Workers 需要手动 `wrangler deploy` |
| 部署命令 | `git push` 自动部署 | `npx wrangler deploy` |
| 自动部署 | GitHub 集成开箱即用 | 需额外配置 CI |
| Server Functions | 有限支持 | 原生 Workers 运行时 |

### 为什么会变成 Workers

回头看，是当初 `npx astro add cloudflare` 安装适配器时，Astro 自动生成的配置。适配器默认输出 Workers 模式（如果项目没有显式指定 Pages output）。之后又手动配了 D1 数据库绑定，一直没意识到项目已经在 Workers 轨道上。

Day 17 的部署章节写的是 Pages 流程：

```bash
# ❌ day17 写的（Pages 自动部署）
git add . && git commit && git push
```

实际需要的是：

```bash
# ✅ 实际要用的（Workers 手动部署）
npm run build && npx wrangler deploy
```

---

## 部署过程

### 第一步：构建

```bash
npm run build
```

成功输出到 `dist/` 目录。因为是 Hybrid 模式（`output: 'static'` 但适配器注入 Workers 入口），构建产物包含：

- `dist/` → 静态资源（HTML/CSS/JS/图片）
- Workers entrypoint → `@astrojs/cloudflare/entrypoints/server`

### 第二步：部署

```bash
npx wrangler deploy
```

第一次部署成功，终端返回：

```
Your worker has been deployed. 🎉
🚀 https://my-blog.booosama0113.workers.dev
```

### 第三步：验证

打开浏览器访问 `https://my-blog.booosama0113.workers.dev`：

- 首页正常显示 ✅
- 页面路由正常 ✅
- View Transitions 页面切换正常 ✅
- 播放器组件加载 ✅
- APlayer 歌单加载 ✅
- 音频来自 R2 直链 ✅

### 部署结果

| 资源 | 状态 |
|------|------|
| 首页 | ✅ `my-blog.booosama0113.workers.dev` |
| R2 歌单 | ✅ `playlist.r2.json` 正常加载 |
| R2 音频 | ✅ 可直接播放 |
| D1 数据库 | ✅ 绑定正常 |

---

## R2 音频上线

部署前需要确保音频已经在 R2 上，且播放器指向正确的 URL。

### 上传音频到 R2

之前 `upload_to_r2.py` 已经把本地 92 首音频上传到 `music-store` bucket。还需要做一步：**打开 R2 桶的公共访问**。

```
Cloudflare Dashboard → R2 → music-store → 设置
  → 往下翻到 "Public Access"
  → 打开开关
  → 复制 Public URL（类似 https://pub-xxx.r2.dev）
```

### 生成 R2 歌单

```bash
export R2_PUBLIC_URL="https://pub-xxx.r2.dev"
python3 scripts/upload_to_r2.py
```

脚本重新生成 `public/music/playlist.r2.json`，所有 `url` 字段替换为 R2 直链：

```json
{
  "name": "杀死那个石家庄人",
  "artist": "万能青年旅店",
  "url": "https://pub-xxx.r2.dev/万青/杀死那个石家庄人.flac",
  "cover": "https://pub-xxx.r2.dev/cover/default.jpg"
}
```

### R2 的 Development URL 警告

R2 桶刚打开公共访问时，Public URL 会显示一个黄色警告：

> "You are using the r2.dev Development URL. This URL should only be used for testing."

这不是错误——r2.dev 域名本身就不适合做生产 URL（不能套 WAF、不能绑自定义规则）。对于个人博客项目，先这样用着，后续可以绑自定义域名消除警告。

---

## 部署命令确认

部署成功后，确认项目的部署工作流：

```bash
# 构建 + 部署（两步）
npm run build          # 构建静态站点 + Workers entry
npx wrangler deploy    # 部署到 Cloudflare Workers
```

这是当前唯一的部署方式。GitHub 推送不会触发自动部署，因为：

- 项目是 Workers 模式，不是 Pages 模式
- Workers 没有内置的 Git 集成自动部署
- 后续可以配置 GitHub Actions 实现 CI/CD

---

## 部署后的架构验证

### 实际生产架构

```
用户浏览器
  ↓ 请求 my-blog.booosama0113.workers.dev
Cloudflare Workers（运行 Astro SSR entry）
  ├── 静态页面 → 从 ASSETS KV 读取 (dist/)
  ├── API 路由 → Workers 运行时动态响应
  │     └── D1 数据库绑定 (blog-db)
  └── 音频文件 → Cloudflare R2 直链 (music-store)
        └── 播放器从 playlist.r2.json 读取 R2 URL
```

### 和 Day 17 规划的对比

| 项目 | Day 17 计划 | 实际 |
|------|-------------|------|
| 部署方式 | Pages 自动部署（git push） | Workers 手动部署（wrangler deploy） |
| 静态资源 | Pages 托管 | Workers Assets (KV) |
| API 路由 | Pages Functions | Workers 运行时 |
| 音频 | R2 直链（不变） | R2 直链（一致） |
| D1 绑定 | 通过 Pages Functions | 通过 Workers 绑定 |

大部分架构设计是对的——音频走 R2、D1 存元数据、播放器 View Transitions 保活——只是底层运行时从 Pages 变成了 Workers。这两者对博客来说差别不大，静态页面生成 + 个别动态路由的 Hybrid 模式在 Workers 上完全跑得通。

---

## R2 绑定自定义域名

### 为什么绑

之前 R2 的公开访问域名是 `https://pub-xxx.r2.dev`，控制台一直挂着黄色警告：

> "You are using the r2.dev Development URL. This URL should only be used for testing."

这个警告无害，但不美观。绑一个自己的域名上去，警告消失，URL 也更正式。

### 操作步骤

Cloudflare 里已经有一个域名 `myproxy2.cc.cd`（之前 Pages 项目就在用），直接给它加个子域名给 R2。

```
1. 打开 https://dash.cloudflare.com/
2. 左侧 → R2 → music-store → 设置
3. 往下翻到 "Custom Domains"
4. 点 "Add Domain"
5. 输入：music.myproxy2.cc.cd
6. 点 "Continue"
```

Cloudflare 会自动添加 DNS 记录（CNAME 指向 R2 端点），不需要手动配。等几分钟生效后，R2 的音频 URL 就从：

```
https://pub-xxx.r2.dev/万青/杀死那个石家庄人.flac
↓
https://music.myproxy2.cc.cd/万青/杀死那个石家庄人.flac
```

### 重新上传歌单

域名变了，歌单里的 URL 需要更新：

```bash
export R2_PUBLIC_URL="https://music.myproxy2.cc.cd"
python3 scripts/upload_to_r2.py
```

脚本重新生成 `public/music/playlist.r2.json`，所有 `url` 替换为新域名。

### 重新部署

```bash
npm run build && npx wrangler deploy
```

构建成功（47 pages），资产上传正常（1 个新文件 `playlist.r2.json`）。但部署遇到问题——详见下一节。

### 最终架构

```
用户浏览器
  ├── 博客 → my-blog.booosama0113.workers.dev
  │     ├── 静态页面（Workers Assets）
  │     └── API 路由（Workers 运行时 + D1）
  └── 音频 → music.myproxy2.cc.cd（R2 自定义域名）
        └── 播放器读取 playlist.r2.json 中的 R2 直链
```

两个域名各司其职，播放器从架构上完全解耦了博客服务的压力。

---

## KV 命名空间冲突：自动 Provision 的坑

### 现象

第二次部署（绑定 R2 自定义域名后重跑 `npm run build && npx wrangler deploy`）时，构建和资产上传都成功了，但最后一步部署出错：

```
🌀 Building list of assets...
✨ Read 109 files from the assets directory dist/client
🌀 Starting asset upload...
+ /music/playlist.r2.json
Uploaded 1 of 1 asset
✨ Success! Uploaded 1 file (57 already uploaded)

Experimental: The following bindings need to be provisioned:
Binding             Resource          
env.SESSION         KV Namespace      

Provisioning SESSION (KV Namespace)...
🌀 Creating new KV Namespace "my-blog-session"...

✘ [ERROR] A request to the Cloudflare API failed.
  a namespace with this account ID and title already exists [code: 10014]
```

构建 ✅ → 资产上传 ✅ → Provision KV ❌ → 部署中断

### 根因

`wrangler.jsonc` 中的 SESSION KV binding 没有指定 `id`，只指定了 `binding` 名称：

```jsonc
{
  "kv_namespaces": [
    {
      "binding": "SESSION"
      // 没有 "id" 字段
    }
  ]
}
```

Wrangler 4 的 `deploy` 遇到没有 `id` 的 binding 时，会尝试**自动创建**（Auto-Provision）对应的资源。第一次部署时 `wrangler.jsonc` 里的 `kv_namespaces` 没有 `id` 字段，Wrangler 自动创建了 `my-blog-session`，部署成功。但第二次部署时 Wrangler 再次尝试创建同名 KV——已存在 → 冲突报错 → deploy 中断。

### 修复

两种修复思路：

#### 方案 A：指定已有的 KV namespace ID（推荐）

先查一下已有的 KV namespace ID：

```bash
npx wrangler kv namespace list
```

输出中找到 `my-blog-session` 对应的 `id`，然后写进 `wrangler.jsonc`：

```jsonc
{
  "kv_namespaces": [
    {
      "binding": "SESSION",
      "id": "62f6d1941d934bc3af6d7466975db850"
    }
  ]
}
```

加上 `id` 后，Wrangler 知道这个资源已存在，不再尝试自动创建，deploy 跳过 provision 步骤直接部署。

#### 方案 B：删除旧的 KV 命名空间

如果不想查 ID，也可以先删掉旧的，让 Wrangler 重新创建：

```bash
# 查 ID
npx wrangler kv namespace list

# 删掉旧的
npx wrangler kv namespace delete --namespace-id <id>
```

然后重新 deploy，Wrangler 会重新创建。**注意这会导致已存储的 session 数据丢失**，不过项目目前还没用 session 存东西，所以无所谓。

### 验证

加上 `id` 后重新部署：

```bash
npm run build && npx wrangler deploy
```

这次不再有 provision 步骤，直接部署成功：

```
✅ Deployed!
🚀 https://my-blog.booosama0113.workers.dev
```

播放器正常播放，音频请求走 `music.myproxy2.cc.cd`，R2 控制台的 Development URL 警告消失。

---

## 全部完成：系统上线状态确认

Dashboard 确认自定义域名状态：

| Domain | Minimum TLS | Status | Access |
|--------|-------------|--------|--------|
| `music.myproxy2.cc.cd` | 1.0 | **Active** | Enabled |

验证最终系统中所有组件：

| 项目 | 状态 | 说明 |
|------|------|------|
| 博客上线 | ✅ | `my-blog.booosama0113.workers.dev` |
| R2 绑定 | ✅ | `music.myproxy2.cc.cd`，Active，Development URL 警告消失 |
| 歌单 | ✅ | 92 首歌，URL 指向 `music.myproxy2.cc.cd`（非 dev URL） |
| 播放器 | ✅ | 底部 APlayer，页面切换不断播，刷新恢复进度 |
| 部署命令 | ✅ | `npm run build && npx wrangler deploy` |
| 部署配置 | ✅ | KV binding 已写死 `id`，不会再触发自动 Provision 报错 |

### 完整数据流（最终版）

```
/home/cat/Music/（92 首）
       │
       ▼
scripts/sync_music.py → 扫描目录 → public/music/playlist.json
       │
       ▼
scripts/upload_to_r2.py → 上传到 R2 music-store 桶
       │                     └── 生成 playlist.r2.json（URL → music.myproxy2.cc.cd）
       ▼
npm run build && npx wrangler deploy → Cloudflare Workers + Assets
       │
       ▼
用户浏览器 → 博客页面 → 播放器读取 playlist.r2.json
                       → 音频请求 music.myproxy2.cc.cd → R2 边缘节点
```

### 以后加新歌三步

```bash
python3 scripts/sync_music.py          # 刷新歌单
python3 scripts/upload_to_r2.py        # 上传到 R2
npm run build && npx wrangler deploy   # 部署
```

### 还没搞的（不急）

- **Bilibili 同步** — `sync_bilibili.py` 已写好，收藏夹里那首 Beyond 可以下
- **Telegram Bot** — 后续补充歌源

---

## 部署自动化：告别 4 步手动流程

### 痛点

现在加一首新歌到博客要手动跑 4 步：

```bash
python3 scripts/sync_music.py          # ① 刷新歌单
python3 scripts/upload_to_r2.py        # ② 上传 R2（要先 export 一堆环境变量）
npm run build                          # ③ 构建
npx wrangler deploy                    # ④ 部署
```

每次都要敲一遍，而且 `upload_to_r2.py` 还要先 `export R2_ACCOUNT_ID=xxx R2_ACCESS_KEY_ID=xxx ...`，环境变量一多就容易漏。

### 一键脚本 deploy.py（已实现）

写了一个 `scripts/deploy.py`，把 4 步串成一行：

```python
#!/usr/bin/env python3
"""一键部署：扫描音乐 → 上传 R2 → 构建 → 部署"""

import subprocess
import os
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent

def step(msg, cmd, cwd=None):
    print(f"\n{'='*50}")
    print(f"▶ {msg}")
    print(f"{'='*50}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or ROOT)
    if result.returncode != 0:
        print(f"✘ 失败: {msg}")
        exit(result.returncode)
    print(f"✓ 完成: {msg}")

if __name__ == "__main__":
    step("① 扫描本地音乐 → 生成歌单", "python3 scripts/sync_music.py")
    step("② 上传音频到 R2",           "python3 scripts/upload_to_r2.py")
    step("③ 构建 Astro 站点",         "npm run build")
    step("④ 部署到 Cloudflare Workers", "npx wrangler deploy")
    print("\n🎉 全部完成！")
```

### 环境变量持久化

`.env` 文件在项目根目录，存储 R2 凭证，由 `gitignore` 排除不进 Git：

```bash
cat > .env << 'EOF'
R2_ACCOUNT_ID=1b39eea1974aebea3efad1049edeffec
R2_ACCESS_KEY_ID=你在 Dashboard 创建的那个
R2_ACCESS_KEY_SECRET=那个密钥
R2_PUBLIC_URL=https://music.myproxy2.cc.cd
EOF
```

`upload_to_r2.py` 会自动从 `.env` 读取（而不是每次手动 export），脚本逻辑：

```python
from dotenv import load_dotenv
load_dotenv()  # 从 .env 加载环境变量

R2_ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
R2_ACCESS_KEY_ID = os.environ["R2_ACCESS_KEY_ID"]
# ...
```

### 使用效果

```bash
# 放好新歌后，一行搞定
python3 scripts/deploy.py
```

输出：

```
==================================================
▶ ① 扫描本地音乐 → 生成歌单
==================================================
✓ 扫描完成: 92 首歌 → public/music/playlist.json
✓ 完成: ① 扫描本地音乐 → 生成歌单

==================================================
▶ ② 上传音频到 R2
==================================================
✓ 已是最新，无新文件上传
✓ 完成: ② 上传音频到 R2

==================================================
▶ ③ 构建 Astro 站点
==================================================
✓ 47 page(s) built in 2.03s
✓ 完成: ③ 构建 Astro 站点

==================================================
▶ ④ 部署到 Cloudflare Workers
==================================================
✅ Deployed!
✓ 完成: ④ 部署到 Cloudflare Workers

🎉 全部完成！
```

### Git 自动部署怎么办

有个关键认知：**音乐在本机，不在 Git 仓库里**。所以 Git 自动构建（Pages / GitHub Actions）扫描不到 `/home/cat/Music/` 里的新歌。

`deploy.py` 解决的是「加新歌要部署」的问题。Git 自动部署解决的是「改代码要部署」的问题——两者场景不同：

| 场景 | 方式 | 原因 |
|------|------|------|
| 加新歌 | `python3 scripts/deploy.py` | 音乐在本机，必须本地扫描上传 |
| 改代码（CSS/组件/配置） | 可配 Git 自动部署 | 代码在 Git 里，CI 能读到 |
| 两者同时 | 先本地 deploy.py，再推代码 | deploy.py 会上传新歌并部署，push 触发二次部署（无新文件就很快） |

Git 自动部署可以搞，但不是现在急需——`deploy.py` 已经覆盖了最常用的场景。

### 学到的：音乐 ≠ 代码

| 以前的想法 | 实际 |
|-----------|------|
| "Git 自动部署就能一劳永逸" | CI 扫不到本地 `/home/cat/Music/`，自动构建对加新歌没用 |
| "手动部署太麻烦" | 一个 `deploy.py` 脚本就解决，4 步串成一行 |
| "环境变量好烦" | `.env` 文件自动加载，设一次永不用再管 |

---

## Git 自动部署：从 Pages 死胡同到 GitHub Actions

上节说"后续再考虑 CI 自动部署"。结果还是直接开干了——推代码还要手动 `wrangler deploy` 实在太反人性。

### 第一次尝试：Cloudflare Pages 自动构建

项目本来就和 GitHub 关联了一个 Pages 项目（`kirinwiki`），理论上推代码就能自动部署。但试了几次全失败。

### 踩坑 1：playlist.r2.json 没进 Git

Pages 构建时找不到歌单，构建失败。

**根因**：`.gitignore` 里有一行 `public/music/`——之前为了不让本地 `playlist.json`（dev URL 版本）进仓库而设的。但 `public/music/` 这个规则也把 `playlist.r2.json`（生产版本）挡在外面了。

**修复**：把 `.gitignore` 里的 `public/music/` 改为只忽略本地开发用的 `playlist.json`：

```
# 原来：public/music/       ← 全目录忽略
# 改成：
public/music/playlist.json  ← 只忽略 dev 版本
```

`playlist.r2.json` 正常被 Git 追踪。

### 踩坑 2：.wrangler/ 目录污染了 Git

Pages 构建时又报错，查看日志发现 `.wrangler/deploy/config.json` 引用了构建产物路径，但这个文件在 Git 里。

**根因**：之前 `wrangler deploy` 时 Wrangler 生成了 `.wrangler/` 目录，里面记录了构建路径（`/home/cat/Documents/...`）。提交 Git 后，Pages 的 CI 服务器上显然没有这个本地路径，报错。

**修复**：删掉 Git 里的 `.wrangler/`，加到 `.gitignore`：

```bash
git rm -r --cached .wrangler/
echo ".wrangler/" >> .gitignore
git add .gitignore
git commit -m "fix: remove .wrangler from git (breaks Pages build)"
```

### 踩坑 3：Pages 输出目录

构建终于通过了，但网站 404。问题出在 Astro Cloudflare 适配器把构建产物放到了 `dist/client/`，但 Pages 默认从 `dist/` 读取。

**修复**：在 Pages Dashboard 把输出目录从 `dist/` 改为 `dist/client`。

### 踩坑 4：Pages 和 Workers 模式冲突 —— 死胡同

上面三个坑都填了，但根本问题没解决：`wrangler.jsonc` 配的是 **Workers 模式**（有 `"main"` 字段），Pages 想把它当 Functions 项目处理。

项目实际已经在 Workers 上正常跑了，强行用 Pages 自动构建会导致：
- 构建产物格式不兼容
- Workers binding 无法正确绑定
- 维护两套部署配置

### 最终方案：GitHub Actions + Wrangler

既然 Workers 模式是既成事实，就别硬套 Pages。换 GitHub Actions，在 CI 里直接跑 `wrangler deploy`。

创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    name: Build & Deploy to Cloudflare Workers

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npm run build
      - name: Deploy to Workers
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
```

流程：`checkout` → `npm ci` → `npm run build` → `wrangler deploy`。

### 最后一步：GitHub Secrets

在 GitHub 仓库设置中添加 Cloudflare API Token，让 GitHub Actions 有权限部署到 Cloudflare。

#### Token 创建（Cloudflare 侧）

试了两种方式，记录一下。

**第一次：用 "Edit Cloudflare Workers" 模板**

模板自带 Workers Scripts + Workers Routes + Workers KV Storage，还需要手动加 D1。而且模板里写的是 "Edit"，但新版 API 里叫 **"Write"**——Write = 创建+修改+删除，没有单独的 Edit。

**最终方案：用 Custom 模板，只要 3 个权限**

```
Dashboard → API 令牌 → 创建令牌
→ 选择 "Custom"（自定义）
```

只加三条权限，不多不少：

| 权限 | 资源范围 | 级别 | 用途 |
|------|---------|------|------|
| Workers Scripts → **Edit** | Entire Account | 必选 | 部署 Worker |
| Workers KV Storage → **Edit** | Entire Account | 必选 | SESSION KV 绑定 |
| D1 → **Edit** | Entire Account | 必选 | 数据库绑定 |

> **不需要** Workers Routes、Account Settings Read——部署用不到。

资源范围全部选 **Entire Account**（整个账户），不用限制到具体资源。

创建后复制 Token（只显示一次，页面关了再也看不到）。

#### Secret 配置（GitHub 侧）

```
GitHub → KirinWiki 仓库 → Settings → Secrets and variables → Actions
→ New repository secret
  Name: CF_API_TOKEN
  Secret: 粘贴刚复制的 Token
```

配置完后，以后每次推 `main` 分支代码到 GitHub，Actions 会自动执行：
`npm ci` → `npm run build` → `wrangler deploy`

### CI 里 KV 问题又出现了

第一次在 GitHub Actions 里跑部署时，又报了一样的错：

```
✘ [ERROR] a namespace with this account ID and title already exists [code: 10014]
```

和之前一模一样——Wrangler 在 CI 环境也尝试自动创建 `my-blog-session`，但已存在。

**根因**：这次问题出在**构建产物**上。Astro 的 `@astrojs/cloudflare` 适配器在构建时会重新生成 `dist/client/wrangler.json`，这是 `wrangler deploy` 实际读取的配置文件。生成过程中 KV 的 `id` 字段可能被丢掉或者格式变了。

**修复**：检查 `wranger.jsonc` 确认已有 `id`，然后重新构建部署，确保生成的 `dist/client/wrangler.json` 也包含 `id`：

```bash
# 确认 wrangler.jsonc 已有 id
cat wrangler.jsonc
# → "id": "62f6d1941d934bc3af6d7466975db850"

# 重新构建
npm run build

# 确认生成的文件也有 id
cat dist/client/wrangler.json | grep -A2 kv_namespaces
# → "kv_namespaces":[{"binding":"SESSION","id":"62f6d1941d934bc3af6d7466975db850"}]
```

推上去后 Actions 跑通了——Wrangler 看到 `id` 已存在，跳过 provision，直接部署。

### 自动化体系完整版

经过一整天的折腾，最终部署体系成型：

| 场景 | 操作 | 自动触发 |
|------|------|---------|
| 🖥️ **改代码** | `git push` | GitHub Actions → 构建 → 部署 Workers |
| 🎵 **加新歌** | `python3 scripts/deploy.py` | 本地脚本 4 步合 1 步 |
| 🔄 **都改了** | 先本地 `deploy.py`，再 `git push` | 推送时 CI 自动再部署一次 |
| 🧪 **本地开发** | `npm run dev` + `serve_music.py` | 开发环境 Proxy 音频 |

### 关键认知

花了很长时间折腾 Pages 自动部署，最后发现**方向不对**——项目已经是 Workers 架构，Pages 是另一套产品线。不是"修修补补就能兼容"的。

正确路径：**用 GitHub Actions 跑 Wrangler**，和本地 `wrangler deploy` 做一样的事，只不过放 CI 里自动跑。

这也解释了为什么一开始部署成功（`wrangler deploy`），但 Pages 自动构建就是不行——走错门了。

---

## 后续待办

### 近期

- [x] ~~一键部署脚本~~ ✅ `deploy.py` + `.env` 已完成
- [x] ~~Git 自动部署（代码变更）~~ ✅ GitHub Actions + Wrangler
- [ ] 给博客也绑个自定义域名，让 `my-blog.booosama0113.workers.dev` 换成好记的地址

### 中期

- [ ] 实现 Bilibili 同步脚本完整流程（yt-dlp 下载 → 自动上传 R2）
- [ ] Telegram Bot 补充数据源
- [ ] 完善播放器 UI（音量控制、播放模式切换）

---

## 学到的概念

| 概念 | 理解 |
|------|------|
| Workers vs Pages | 两个产品线。Pages 偏向"托管静态站+Function"，Workers 是"边缘计算平台"。`@astrojs/cloudflare` 默认输出 Workers 模式 |
| `wrangler.jsonc` 的 `"main"` 字段 | 有 `"main"` 就是 Workers 模式，没有就是 Pages 模式。这是区分两者的最直观标志 |
| Workers Assets | 通过 KV 存储提供静态资源，等效于 Pages 的静态托管，但有 1GB 软限制 |
| R2 公开访问 | 需要手动开启 Public Access，r2.dev 域名有 Development URL 警告，生产应绑自定义域名 |
| Hybrid 部署 | `output: 'static'` + 适配器 Workers entry = 大部分静态页面 + 个别动态路由，Workers 上完全兼容 |
| Wrangler 自动 Provision | binding 没有指定 `id` 时，Wrangler 4 会在 deploy 时自动创建资源。但第二次 deploy 会尝试重新创建已存在的资源导致报错——所以 binding 要写死 `id` 避免自动 provision |
| Astro 构建生成 `dist/client/wrangler.json` | wrangler deploy 实际使用的是 Astro 构建后生成的配置，不是项目根目录的 `wrangler.jsonc`。两个文件不一致可能导致 deploy 行为不同 |
| 音乐 ≠ 代码 | 音频文件在本机不在 Git，CI 扫不到。Git 自动部署只对代码变更有效，加新歌需要本地脚本 |
| 一键脚本降本 | 4 步手动流程（含 export 环境变量）→ 1 行 `python3 scripts/deploy.py`。人容易忘步骤，脚本不会 |
| Pages 自动构建 ≠ Workers 自动部署 | 项目是 Workers 架构，Pages 的自动构建不兼容。正确的自动部署方式是用 GitHub Actions 跑 Wrangler |
| `.gitignore` 要精确 | `public/music/` 太宽泛，挡住了不该挡的 `playlist.r2.json`。精确到文件名比范围匹配更安全 |
| `.wrangler/` 不进 Git | Wrangler 生成的构建产物含有本地路径，提交后会污染 CI 构建环境，必须 `.gitignore` |
| GitHub Actions + Wrangler | `cloudflare/wrangler-action@v3` 可以直接在 CI 里调 `wrangler deploy`，和本地操作等效 |
| API Token 权限最小集 | Workers Scripts Edit + Workers KV Edit + D1 Edit，3 条就够了。模板自带的 Routes 等多余权限不加 |
| Cloudflare API："Write" = "Edit" | 新版 API 里没有 "Edit" 这一级，Write 就是修改权限。旧模板写的 "Edit" 到 Custom 里选 "Write" 即可 |
| CI 里 KV 问题复现 | 本地修好了 `wrangler.jsonc` 不代表 CI 修好了——Astro 构建会重新生成 `dist/client/wrangler.json`，要确认生成的文件也包含 `id` |

---

## 反思

Day 17 写部署章节时犯了一个错误：**默认了部署路径是 Pages**，没有先检查 `wrangler.jsonc` 的实际配置。

教训：
1. 写部署文档前先确认运行时环境（Pages vs Workers）
2. `wrangler.jsonc` 有 `"main"` 就是 Workers，没有就是 Pages——规则很简单，花 10 秒看一眼就能避免方向性错误
3. 项目脚手架生成的配置可能和自己想的不一样，不要假设

### KV Provisioning 的教训

Wrangler 的自动 provision 看似方便，但第二次部署就踩坑了——已存在的资源它不会跳过，而是报错退出。

两个教训：

1. **binding 配置写死 `id`**，不要让 Wrangler 自动创建。手动创建一次后把 `id` 写进 `wrangler.jsonc`，之后的 deploy 就不会再尝试 provision。
2. **注意 `dist/client/wrangler.json` 和 `wrangler.jsonc` 是两份配置**。Astro 构建会重新生成一份配置丢到 `dist/client/`，`wrangler deploy` 实际用的是那份。两者请保持同步。

### 自动化认知修正

一开始的想法是"配好 Git 自动部署就一劳永逸了"。

第一步发现：**音乐在本机，不在 Git 里。** CI 扫不到 `/home/cat/Music/`，自动构建对加新歌没用——所以先做了 `deploy.py`。

第二步试图搞 Pages 自动部署：方向错了，项目是 Workers 架构，Pages 不兼容。三个坑（`.gitignore`→`.wrangler/`→输出目录）填完后发现是死胡同。

第三步才找到正解：**GitHub Actions + Wrangler**。用 `cloudflare/wrangler-action@v3` 在 CI 里跑和本地一模一样的 `wrangler deploy` 命令。

最终部署体系：

| 场景 | 方案 |
|------|------|
| 加新歌 | `python3 scripts/deploy.py`（本地，必须的）|
| 改代码 | `git push` → GitHub Actions 自动部署 |

花了大量时间在 Pages 死胡同里，**如果一开始就意识到项目是 Workers 架构，会直接想到 GitHub Actions 而不是 Pages**。

教训：不要在错误的方向上努力修修补补，先搞清楚架构再选工具。

---

## 总结

Day 18 从一个简单的目标开始——把博客部署上线——最终走完了一整条链路：从认知修正（Workers 而非 Pages）到手动部署，再到 R2 绑定域名、一键脚本、GitHub Actions 自动部署。

一条路上踩了六个坑：

| # | 坑 | 修复 |
|---|-----|------|
| 1 | Pages 模式 vs Workers 模式 | 认清架构，切换部署命令 |
| 2 | KV 自动 Provision 冲突 | binding 写死 `id` |
| 3 | Pages 自动构建不兼容 | 放弃 Pages，改用 GitHub Actions |
| 4 | `.gitignore` 挡住歌单 | 精确到文件名而非目录 |
| 5 | `.wrangler/` 污染 Git | 删掉跟踪，加到 `.gitignore` |
| 6 | CI 里 KV 问题复现 | 确认生成配置也包含 `id` |

### 最终状态

```
                    ┌──────────────┐
  git push ────────▶│ GitHub Actions│────▶ npm run build
                    └──────────────┘            │
                                               ▼
                      ┌──────────────────────────────┐
                      │ npx wrangler deploy           │
                      │ → my-blog.workers.dev          │
                      │ → music.myproxy2.cc.cd (R2)    │
                      └──────────────────────────────┘
```

| 场景 | 操作 |
|------|------|
| 🖥️ **改代码** | `git push` → GitHub Actions 自动构建+部署 |
| 🎵 **加新歌** | `python3 scripts/deploy.py`（本地 4 步合 1） |
| 🔄 **都改了** | 先 `deploy.py` 传音乐，再 `git push` 推代码 |
| 🧪 **本地开发** | `npm run dev` + `python3 scripts/serve_music.py` |

所有环节全部到位，博客正式上线并可自动运维。
