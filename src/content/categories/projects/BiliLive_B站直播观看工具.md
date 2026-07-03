# BiliLive — B 站直播观看工具项目深度解析

> **项目**: 基于 Flutter 的哔哩哔哩直播观看 Android 客户端
> **GitHub**: [BoooSAMA/dart_simple_live_bilibili](https://github.com/BoooSAMA/dart_simple_live_bilibili)
> **框架**: Flutter 3.38 + Dart
> **原项目**: [xiaoyaocz/dart_simple_live](https://github.com/xiaoyaocz/dart_simple_live) (GPL-3.0)
> **许可证**: GPL-3.0

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [项目架构](#3-项目架构)
4. [功能详解](#4-功能详解)
5. [核心 API 与数据流](#5-核心-api-与数据流)
6. [v2.0 重构亮点](#6-v20-重构亮点)
7. [v2.1 新增功能](#7-v21-新增功能)
8. [本地开发与构建](#8-本地开发与构建)
9. [与原项目的对比](#9-与原项目的对比)

---

## 1. 项目概述

### 一句话概括

> BiliLive 是基于 Simple Live 精简优化而来的 Android 端哔哩哔哩直播观看工具，专注于提供纯净、高效的 B 站直播浏览体验。

### 项目背景

原项目 [Simple Live](https://github.com/xiaoyaocz/dart_simple_live) 是一个支持多平台（Bilibili、虎牙、斗鱼、抖音等）的直播聚合客户端。本项目从原项目 fork 后进行了大幅精简和定制：

- **移除**了虎牙、斗鱼、抖音等多平台支持
- **移除**了账号登录、关注同步等需要服务端的非核心功能
- **保留并优化**了 B 站直播的核心观看体验
- **新增**了直播间录音、首页分区固定、本地关注等差异化功能

### 核心目标

- 提供纯净的 B 站直播浏览体验
- 零账号依赖——所有收藏、关注功能纯本地化存储
- 直播间音频录制——将直播音频实时保存为 M4A 文件
- 优化的分区浏览体系——支持子分区浏览与收藏
- 海外用户友好——绕过对海外 IP 屏蔽的 API 接口

---

## 2. 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| **框架** | Flutter 3.38 | 跨平台 UI 框架（当前仅 Android） |
| **语言** | Dart | 应用逻辑与 UI |
| **直播接口** | Bilibili Live API | 房间信息、弹幕、播放流 |
| **本地存储** | Hive | 轻量级 NoSQL 本地数据库 |
| **FFmpeg** | ffmpeg_kit_flutter | 直播音频录制引擎 |
| **状态管理** | GetX | 响应式状态管理 |
| **平台通道** | MethodChannel | Flutter ↔ 原生层通信 |

### 主要依赖

| 包名 | 用途 |
|------|------|
| `ffmpeg_kit_flutter_new_https_gpl` | FFmpeg 音频录制引擎 |
| `file_picker` | 文件选择器（录音存储路径） |
| `open_filex` | 打开文件 |
| `share_plus` | 文件分享 |
| `hive` / `hive_flutter` | 本地数据持久化 |
| `get` (GetX) | 状态管理与路由 |
| `wakelock_plus` | 防止设备休眠 |

---

## 3. 项目架构

### 整体结构

```
dart_simple_live_bilibili/
├── simple_live_core/                # 核心库（仅保留B站相关 API）
│   ├── lib/src/
│   │   ├── bilibili/
│   │   │   ├── bilibili_site.dart         # 站点注册
│   │   │   ├── bilibili_live_api.dart     # B站直播 API 封装
│   │   │   ├── bilibili_message.dart      # 弹幕/消息协议
│   │   │   └── models/                    # 数据模型
│   │   └── base/                          # 抽象基类
│   └── pubspec.yaml
│
└── simple_live_app/                  # Flutter APP 客户端
    ├── lib/
    │   ├── main.dart                        # 应用入口
    │   ├── app.dart                         # App 组件
    │   ├── store/                           # GetX 状态管理
    │   ├── pages/
    │   │   ├── home/                        # 首页（推荐+固定分区 Tab）
    │   │   ├── live_room/                   # 直播间详情页
    │   │   ├── search/                      # 搜索页
    │   │   ├── follow/                      # 本地关注列表
    │   │   ├── history/                     # 观看历史
    │   │   └── settings/                    # 设置页（含音频设置）
    │   ├── widgets/                         # 可复用组件
    │   └── utils/                           # 工具函数
    ├── android/
    └── pubspec.yaml
```

### 架构分层

```
┌─────────────────────────────────────────────┐
│              UI 层（Flutter Widgets）         │
│   Pages / Widgets / GetX Controllers          │
│   • 首页推荐流 + 固定分区 Tab                │
│   • 直播间详情（播放器 + 弹幕 + 录音）        │
│   • 搜索 / 关注 / 历史 / 设置                │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│            业务逻辑层（Store / Service）       │
│  • LiveRoomStore — 直播间状态管理              │
│  • FollowStore — 本地关注存储                  │
│  • HistoryStore — 观看历史                     │
│  • RecordingService — FFmpeg 录音管理          │
│  • SettingsStore — 外观/音频配置               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  simple_live_core（B站 API 封装层）            │
│  • 房间信息 API（base info / stream URL）     │
│  • 推荐流 API（recommend / area rooms）        │
│  • 弹幕 WebSocket 协议                        │
│  • 搜索 API                                   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           原生层 / 外部服务                    │
│  • FFmpeg（音频录制引擎）                     │
│  • Bilibili Live API（HTTP + WebSocket）      │
│  • Hive（本地持久化）                         │
│  • Platform Channel 通信                      │
└──────────────────────────────────────────────┘
```

---

## 4. 功能详解

### 4.1 直播间浏览

| 功能 | 说明 |
|------|------|
| **推荐流** | 首页推荐 Tab，启动时立即加载首屏数据 |
| **分区浏览** | 顶部分区下拉菜单，展开查看所有父分区下的子分区 |
| **子分区详情** | 点击子分区进入独立详情页，按 area_id 拉取房间列表 |
| **分区收藏** | 星标收藏常用子分区，显示在分区选择器底部"我的收藏" |
| **固定分区到首页** | 将常用子分区固定为首页独立 Tab，启动即加载 |
| **搜索** | 搜索直播间和主播 |
| **个人主页** | 查看主播信息和直播间列表 |

### 4.2 直播播放

- **多清晰度**：支持 B 站提供的各清晰度选项
- **弹幕显示**：WebSocket 实时弹幕，支持关键词屏蔽
- **播放控制**：播放/暂停、全屏切换

### 4.3 本地化功能（无账号）

所有个性化数据存储在本地，无需 B 站账号：

| 功能 | 存储方式 |
|------|---------|
| **关注/收藏直播间** | Hive 本地数据库 |
| **观看历史** | Hive 本地数据库 |
| **分区收藏** | Hive JSON 序列化 |
| **固定分区配置** | Hive 持久化 |
| **外观设置** | Hive / SharedPreferences |
| **音频设置** | Hive / 文件系统 |

### 4.4 直播间录音

详见 [v2.1 新增功能](#72-直播间录音功能)。

### 4.5 定时关闭

- 支持设置定时关闭计时器
- 到达设定时间后自动退出应用或停止播放

---

## 5. 核心 API 与数据流

### 5.1 API 接口

| API | 端点 | 用途 |
|-----|------|------|
| 推荐流 | `webMain/getMoreRecList` | 首页推荐直播间列表 |
| 分区房间列表 | `room/v1/area/getRoomList` | 按 area_id 获取子分区房间 |
| 房间信息 | `room/v1/Room/get_info` | 获取直播间基本信息 |
| 播放流地址 | `room/v1/Room/playUrl` | 获取直播流播放地址 |
| 搜索 | `live/v1/room/search` | 搜索直播间 |
| 弹幕 WebSocket | `broadcastlv.chat.bilibili.com` | 弹幕实时推送 |

### 5.2 API 升级（v2.0）

v2.0 中进行了重要的 API 迁移：

- **推荐流**：从 `second/getList` 和 `second/getListByArea` 迁移至 `webMain/getMoreRecList`（对海外 IP 屏蔽更少）
- **分区房间**：新增 `getAreaRooms`（`room/v1/area/getRoomList`），无需 WBI 签名，全球可用，每页 30 间
- **分区匹配**：三级匹配策略（精确父分区名 → 模糊父分区名 → 模糊子分区名），提高首页分区过滤准确率

### 5.3 图片加载优化

- 封面图片解码分辨率限制（`cacheWidth: 400px`）
- 大幅减少内存占用，修复列表滚动卡顿

---

## 6. v2.0 重构亮点

### 6.1 分区浏览体系

**旧版问题**：分区分类不够细，无法直接浏览子分区内容。

**新版方案**：
1. 顶部显示当前分区名称，点击弹出**分区选择器**
2. 分区选择器支持展开/收起父分区，查看所有子分区
3. 点击子分区进入独立详情页，使用 `getAreaRooms` API 拉取房间列表
4. 子分区支持星标收藏，收藏后出现在"我的收藏"区域

### 6.2 本地关注功能

**旧版问题**：原项目移除了关注功能，需要登录账号才能使用。

**新版方案**：
1. 纯本地关注/收藏，使用 Hive 持久化
2. 底部导航栏恢复"关注"标签页
3. 直播间详情页恢复"关注/取消关注"按钮
4. 关注列表支持筛选（全部 / 直播中 / 未开播）
5. 优化封面图片加载，减少内存占用

### 6.3 性能优化

- **并发控制**：修复 `loadData` 并发调用导致的 `ConcurrentModificationError`
- **异步安全**：使用代次计数器（generation）防止异步竞态导致数据错乱
- **图片解码**：封面图 cacheWidth 限制为 400px，大幅减少内存
- **Kotlin 升级**：升级至 2.3.21 以兼容 `screen_brightness_android` 插件

---

## 7. v2.1 新增功能

### 7.1 首页默认分区固定（Pin）

- **固定子分区到首页**：在分区选择菜单中为任意子分区添加图钉标记，将其固定为首页独立 Tab
- **独立加载**：固定的子分区自动加载内容，底部菜单显示图钉图标
- **持久化**：固定信息通过 JSON 序列化保存至 Hive，重启自动恢复
- **取消固定**：通过底部菜单或设置页清除

### 7.2 直播间录音功能

直播音频实时录制为 M4A 文件：

| 特性 | 说明 |
|------|------|
| **音频格式** | M4A（AAC 编码） |
| **录制引擎** | FFmpeg `-c:a copy` 流拷贝，零编码损耗 |
| **录制控制** | 开始/停止，状态栏显示录制时长 |
| **防误触** | 首次录音弹出确认对话框，支持"不再显示" |
| **断线重连** | FFmpeg `-reconnect` 参数自动重连 |
| **保存路径** | 文件选择器自定义目录，支持目录可写性验证 |
| **文件管理** | 查看已录制文件列表、分享、打开文件夹 |
| **生命周期** | 切换直播间或退出时自动停止录制 |
| **防止休眠** | 录制期间 Wakelock 保持设备唤醒 |

### 7.3 首页加载优化

- **启动立即加载**：`_initDefaultController` 在 `onInit` 中立即触发首屏数据请求
- **加载进度百分比**：刷新按钮显示当前加载进度百分比（如 `42%`）
- **自定义 Tab 预加载**：固定子分区参与启动预加载，错开 500ms 避免高并发

---

## 8. 本地开发与构建

### 8.1 环境要求

- **Flutter SDK**: 3.38
- **Dart SDK**: 随 Flutter 安装

### 8.2 构建运行

```bash
# 克隆仓库
git clone https://github.com/BoooSAMA/dart_simple_live_bilibili.git
cd dart_simple_live_bilibili

# 获取依赖
flutter pub get

# 运行（需连接 Android 设备或启动模拟器）
flutter run

# 构建 APK
flutter build apk --release
```

> **注意**：本项目不提供 Release 安装包，需自行编译后运行。

### 8.3 项目结构说明

```
simple_live_core/          # 核心库
  lib/src/bilibili/
    bilibili_site.dart         # 站点注册与配置
    bilibili_live_api.dart     # B站直播 API 封装
    bilibili_message.dart      # 弹幕 WebSocket 协议

simple_live_app/           # Flutter APP
  lib/
    store/                     # GetX 状态管理
    pages/                     # 页面
    widgets/                   # 组件
    utils/                     # 工具
```

---

## 9. 与原项目的对比

| 维度 | 原项目 (xiaoyaocz/dart_simple_live) | 本项目 (BoooSAMA/dart_simple_live_bilibili) |
|------|-----------------------------------|-------------------------------------------|
| **平台支持** | B站 + 虎牙 + 斗鱼 + 抖音等 | 仅 B 站 |
| **账号系统** | 需要登录 | 纯本地，无需登录 |
| **关注/收藏** | 服务端同步 | Hive 本地存储 |
| **分区浏览** | 基础分区 | 子分区详情 + 分区收藏 + 首页固定 |
| **录音功能** | 无 | v2.1 新增 FFmpeg 录音 |
| **代码复杂度** | 高（多平台适配） | 精简（仅 B 站） |
| **海外兼容** | 部分 API 被屏蔽 | 使用替代 API，全球可用 |
| **性能优化** | 基础 | v2.0 大幅优化图片加载与并发 |

### Fork 后的主要修改

1. **删除多平台代码**：仅保留 B 站相关代码
2. **删除账号相关功能**：移除登录、关注同步等
3. **新增本地关注**：Hive 存储的纯本地关注功能
4. **分区体系重构**：子分区浏览 + 收藏 + 首页固定
5. **API 迁移**：使用对海外友好的新 API 接口
6. **录音功能**：FFmpeg 音频录制

---

## 附录：关键文件索引

| 文件 | 用途 |
|------|------|
| `simple_live_core/lib/src/bilibili/bilibili_live_api.dart` | B 站直播 API 封装 |
| `simple_live_core/lib/src/bilibili/bilibili_message.dart` | 弹幕 WebSocket 协议 |
| `simple_live_app/lib/pages/live_room/` | 直播间详情页（播放器 + 弹幕 + 录音） |
| `simple_live_app/lib/pages/home/` | 首页（推荐流 + 固定分区 Tab） |
| `simple_live_app/lib/pages/follow/` | 本地关注列表 |
| `simple_live_app/lib/store/` | GetX 状态管理 |
