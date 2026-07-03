---
title: "Simple Recorder — 多平台直播音频录制工具项目深度解析"
date: "2026-07-03"
description: "基于 Flutter 的多平台直播音频录制工具，支持 Bilibili/抖音/斗鱼/虎牙/猫耳FM 五大平台直播间音频录制。基于 FFmpeg 实现纯音频流拷贝，支持并行录制、后台保活与文件管理。"
tags: ["Flutter", "Dart", "FFmpeg", "直播", "音频录制", "跨平台"]
---

# Simple Recorder — 多平台直播音频录制工具项目深度解析

> **项目**: 基于 Flutter 的多平台直播音频录制工具
> **GitHub**: [BoooSAMA/simple_recorder](https://github.com/BoooSAMA/simple_recorder)
> **框架**: Flutter + Dart
> **许可证**: GPL-3.0
> **支持平台**: Android / iOS / Linux / macOS / Windows

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [项目架构](#3-项目架构)
4. [功能详解](#4-功能详解)
5. [核心模块解析](#5-核心模块解析)
6. [录制引擎设计](#6-录制引擎设计)
7. [性能优化](#7-性能优化)
8. [本地开发与构建](#8-本地开发与构建)
9. [免责声明](#9-免责声明)

---

## 1. 项目概述

### 一句话概括

> Simple Recorder 是一款跨平台直播音频录制工具，支持 Bilibili、抖音、斗鱼、虎牙、猫耳FM 五大平台的直播间音频录制，基于 FFmpeg 实现纯音频流拷贝（不重编码），支持并行录制、后台保活与文件管理。

### 项目背景

本项目融合了两个开源项目的核心能力：

| 来源 | 贡献能力 |
|------|---------|
| **[Simple Live](https://github.com/xiaoyaocz/dart_simple_live)** | 多平台直播搜索与房间信息获取 |
| **[Bililive](https://github.com/BoooSAMA/bililive)** | 基于 FFmpeg 的直播间音频录制核心 |

项目定位是"纯粹的录音工具"——**不做直播观看、不做视频录制**，专注音频采集与文件管理。

### 核心设计理念

1. **录音优先** — 仅做音频录制，不做推流/播放
2. **零编码损耗** — FFmpeg `-c:a copy` 流拷贝，保留原始 AAC 音质
3. **并行录制** — 同时录制多个直播间，互不干扰
4. **后台保活** — Android 前台服务保障熄屏不中断
5. **纯本地** — 所有数据存储在本地，无需账号

---

## 2. 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| **框架** | Flutter | 跨平台 UI（6 平台支持） |
| **语言** | Dart | 应用逻辑与 UI |
| **录制引擎** | FFmpeg (ffmpeg_kit_flutter) | 音频流拷贝录制 |
| **直播接口** | simple_live_core | 多平台直播 API 封装 |
| **本地存储** | Hive | NoSQL 本地数据库 |
| **状态管理** | GetX | 响应式状态管理与路由 |
| **后台服务** | flutter_background_service | Android 前台服务保活 |
| **权限管理** | permission_handler | 运行时权限 |
| **屏幕常亮** | wakelock_plus | 防止设备休眠 |

### 主要依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `ffmpeg_kit_flutter_full_gpl` | - | FFmpeg 录制引擎（GPL 变体） |
| `simple_live_core` | - | 多平台直播 API |
| `flutter_background_service` | - | Android 前台服务保活 |
| `hive` / `hive_flutter` | - | 本地数据持久化 |
| `get` | - | 状态管理与路由 |
| `permission_handler` | - | 运行时权限 |
| `wakelock_plus` | - | 防止休眠 |

---

## 3. 项目架构

### 目录结构

```
simple_recorder/
├── lib/
│   ├── main.dart                           # 入口：Hive/GetX/Permissions/Service 初始化
│   │
│   ├── app/                                # 应用基础设施
│   │   ├── app_style.dart                  # Material3 light/dark 主题
│   │   ├── constant.dart                   # 全局常量
│   │   ├── log.dart                        # 日志工具
│   │   ├── sites.dart                      # 多平台站点注册表
│   │   ├── event_bus.dart                  # 跨模块事件总线
│   │   └── controller/
│   │       └── app_settings_controller.dart  # 全局设置（路径、主题、置顶）
│   │
│   ├── models/                             # 数据模型
│   │   └── db/
│   │       ├── follow_user.dart            # 收藏用户模型（Hive 适配器）
│   │       └── recording_task.dart         # 录制任务模型
│   │
│   ├── services/                           # 业务服务层
│   │   ├── db_service.dart                 # Hive CRUD 操作
│   │   ├── local_storage_service.dart      # Hive settings box
│   │   ├── recording_service.dart          # RecordingSession — FFmpeg 录制核心
│   │   ├── recording_manager.dart          # 并行录制管理器（RxList 响应式）
│   │   └── follow_export_service.dart      # 收藏数据导入/导出
│   │
│   ├── modules/                            # 功能模块（页面）
│   │   ├── home/                           # 首页：卡片列表 + 录制控制 + 筛选栏
│   │   ├── search/                         # 多平台搜索 + 心形收藏即时反馈
│   │   ├── settings/                       # 设置页：存储路径/外观/数据/日志
│   │   ├── recordings/                     # 录音文件浏览 + 内置音频播放器
│   │   ├── ts_unpack/                      # TS 解包工具（支持批量多选）
│   │   └── debug_log/                      # 调试日志页面
│   │
│   ├── routes/                             # 路由配置
│   │   ├── app_pages.dart                  # 页面路由表
│   │   └── route_path.dart                 # 路由路径常量
│   │
│   └── widgets/                            # 可复用组件
│       └── settings/                       # 设置页组件（card, switch, action）
│
├── android/app/src/main/.../
│   └── MainActivity.kt                     # Android MethodChannel（openFolder + BackgroundService）
│
├── docs/superpowers/                       # 设计文档
├── test/                                   # 测试文件
├── pubspec.yaml                            # 项目配置
└── README.md
```

### 架构分层

```
┌─────────────────────────────────────────────┐
│              UI 层（Flutter Widgets）         │
│  • 首页卡片列表（直播间状态 + 录制控制）      │
│  • 搜索页（多平台搜索 + 即时收藏）            │
│  • 录音文件浏览器 + 音频播放器               │
│  • 设置页（主题、路径、日志）                │
│  • TS 解包工具页                             │
└──────────────────┬──────────────────────────┘
                   │  GetX 响应式绑定
┌──────────────────▼──────────────────────────┐
│         服务层（Services / GetX Controllers） │
│  • RecordingManager — 并行录制调度            │
│  • RecordingSession — 单直播间录制会话        │
│  • DbService — Hive 增删改查                  │
│  • AppSettingsController — 全局设置          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│            核心引擎 / 外部依赖                │
│  • FFmpeg（ffmpeg_kit） — 音频录制           │
│  • simple_live_core — 直播 API              │
│  • Hive — 本地持久化                         │
│  • flutter_background_service — 保活         │
└──────────────────────────────────────────────┘
```

---

## 4. 功能详解

### 4.1 首页卡片布局

| 元素 | 说明 |
|------|------|
| **主播信息** | 头像 + 用户名 + 直播状态指示灯 |
| **直播状态** | 直播中 / 未开播 |
| **录制控制** | 录制中显示"停止"+"取消"双按钮（红底），支持确认取消 |
| **置顶功能** | 📌 图标置顶，绿色边框高亮 |
| **录制状态** | 实时录制时长（时:分:秒）+ 文件大小 |
| **错误日志** | 录制出错时显示红色日志区域，可点击查看详情 |
| **重连状态** | 断线重连时显示"重连中(N/3)" |
| **循环布局** | 非 Grid，单个卡片垂直排列，每行一个 |

### 4.2 录制核心

参见 [第 6 章 录制引擎设计](#6-录制引擎设计)。

### 4.3 搜索与收藏

- **多平台搜索**：支持 Bilibili/抖音/斗鱼/虎牙/猫耳FM 直播间搜索
- **猫耳FM 房间号**：支持直接输入房间号定位直播间
- **即时收藏反馈**：点击心形图标立刻变红，无需等待 API 响应
- **收藏分组管理**：区分直播中 / 未开播，支持搜索

### 4.4 直播状态监测

| 特性 | 说明 |
|------|------|
| **分批并发检测** | 每批 5 个直播间并行查询，避免阻塞 UI |
| **渐进式 UI 更新** | 每完成一个立即同步到列表，无需等全量刷新 |
| **实时进度反馈** | 刷新按钮内置环形进度 + 百分比文字 |
| **分组筛选栏** | 直播中 / 未开播 / 全部，带数量 badge |

### 4.5 录音文件管理

| 功能 | 说明 |
|------|------|
| **文件浏览** | 独立浏览器页面，按主播文件夹分组展示 |
| **TS → M4A 解包** | 一键将 TS 片段解包为 M4A 音频 |
| **批量解包** | 跨文件夹多选 TS 文件批量处理 |
| **音频播放** | 内置播放器（播放/暂停/快进快退/Seek 进度条） |
| **文件编辑** | 重命名、删除、批量删除 |
| **异常检测** | 启动时自动扫描异常中断的 TS 文件并标记 |

### 4.6 设置与权限

| 设置项 | 说明 |
|--------|------|
| **主题切换** | Material3 light/dark 模式 |
| **音频存储路径** | 自定义录音文件保存目录 |
| **主播文件夹** | 自动按主播名创建子文件夹 |
| **调试日志** | 实时日志查看、保存、清空 |
| **存储权限** | Android 11+ 自动请求"管理所有文件"权限 |

### 4.7 后台保活

- **前台服务**：Android 录制时启动前台服务通知
- **熄屏不中断**：防止系统在锁屏后杀死录制进程
- **生命周期管理**：切换页面或退出时自动停止录制

---

## 5. 核心模块解析

### 5.1 RecordingManager（录制管理器）

```dart
class RecordingManager extends GetxController {
  static final RecordingManager instance = RecordingManager._();
  
  final RxList<RecordingSession> activeSessions = <RecordingSession>[].obs;
  
  // 开始录制直播间
  Future<RecordingSession> startRecording(LiveRoom room);
  
  // 停止录制
  Future<void> stopRecording(String sessionId);
  
  // 取消录制（不保存文件）
  Future<void> cancelRecording(String sessionId);
  
  // 停止所有录制
  Future<void> stopAll();
  
  // 重连状态追踪
  int reconnectAttempts = 0;
  static const int maxReconnects = 3;
}
```

- 通过 `RxList` 响应式管理活跃录制会话
- UI 通过 `Obx(() { final _ = RecordingManager.instance.activeSessions.length; })` 触发重绘
- 支持并行录制多个直播间

### 5.2 RecordingSession（单次录制会话）

```dart
class RecordingSession {
  final String id;           // 唯一标识
  final LiveRoom room;       // 直播间信息
  final String outputPath;   // 输出路径
  final DateTime startedAt;  // 开始时间
  
  // 响应式状态
  final Rx<Duration> duration = Duration.zero.obs;
  final Rx<int> fileSize = 0.obs;
  final Rx<RecordingStatus> status = RecordingStatus.recording.obs;
  
  // FFmpeg 命令
  // -c:a copy -f mpegts output.ts
  Future<void> start();
  Future<void> stop();
  Future<void> cancel();
}
```

### 5.3 平台站点注册

```dart
// app/sites.dart — 站点注册表
static final sites = <BaseSite>[
  BilibiliSite(),
  DouyinSite(),
  DouyuSite(),
  HuyaSite(),
  MaoerFMSite(),
];
```

每个站点实现 `BaseSite` 抽象类，提供统一的搜索、房间信息、直播状态检测接口。

### 5.4 数据流

```
[用户点击"录制"] → RecordingManager.startRecording(room)
    │
    ▼
[RecordingSession.start()]
    ├── 1. simple_live_core 获取直播流地址
    ├── 2. 构造 FFmpeg 命令
    ├── 3. 启动 FFmpeg 进程
    ├── 4. 开始定时更新时长 + 文件大小
    └── 5. 注册到 RecordingManager.activeSessions
    │
    ▼
[UI 响应式更新]
    ├── 实时显示录制时长（Obx 绑定）
    ├── 实时显示文件大小
    └── 错误状态显示
    │
    ▼
[用户点击"停止"] → stop()
    ├── 1. FFmpeg 进程优雅停止
    ├── 2. TS 文件写入完成
    └── 3. 创建录制记录到 Hive
```

---

## 6. 录制引擎设计

### 6.1 FFmpeg 命令

```bash
# 核心录制命令：流拷贝，不重编码
ffmpeg -i {stream_url} \
  -c:a copy \
  -f mpegts \
  -reconnect 1 \
  -reconnect_at_eof 1 \
  -reconnect_streamed 1 \
  -reconnect_delay_max 5 \
  {output_path}.ts
```

| 参数 | 说明 |
|------|------|
| `-c:a copy` | 音频流拷贝，零编码损耗 |
| `-f mpegts` | TS 格式封装（支持断点续传） |
| `-reconnect 1` | 启用断线重连 |
| `-reconnect_delay_max 5` | 最大重连延迟 5 秒 |

### 6.2 录制状态机

```
IDLE → RECORDING → STOPPED (正常结束)
                 → CANCELLED (用户取消，不保存)
                 → ERROR → RECONNECTING (自动重连，最多3次)
                           ├── → RECORDING (重连成功)
                           └── → ERROR (重连耗尽)
```

### 6.3 TS 解包机制

录制时暂存为 TS 片段，停止后通过 `ffprobe` / FFmpeg 合成为 M4A：

```bash
# TS → M4A 解包
ffmpeg -i {input}.ts -c:a copy -y {output}.m4a
```

此举的优势：
- **断线保护**：TS 格式即使录制中断，已写入部分仍然可用
- **零编码损耗**：解包过程仅重新封装，不重新编码
- **批量处理**：支持跨文件夹多选 TS 文件批量解包

### 6.4 后台保活机制

Android 端通过 `flutter_background_service` 实现前台服务：

```kotlin
// MainActivity.kt — Android 前台服务
val serviceIntent = Intent(this, BackgroundService::class.java)
startForegroundService(serviceIntent)

// 前台服务通知
val notification = NotificationCompat.Builder(this, CHANNEL_ID)
    .setContentTitle("Simple Recorder")
    .setContentText("正在录制 ${sessionCount} 个直播间")
    .setSmallIcon(R.drawable.ic_record)
    .build()
startForeground(NOTIFICATION_ID, notification)
```

---

## 7. 性能优化

### 7.1 录制性能

| 优化项 | 优化前 | 优化后 | 效果 |
|--------|--------|--------|------|
| **FFmpeg 日志** | 实时回调到 Dart 层 | 录制期间不回调 | 降低跨语言调用开销 |
| **文件大小轮询** | 每秒查询 | 每 5 秒查询 | 减少 80% 系统调用 |
| **重连延迟** | 固定 2s | 递增 2s/4s/6s | 降低耗电 |
| **进程管理** | 无限制 | session 隔离 | 避免资源泄漏 |

### 7.2 UI 性能

- **响应式录制状态**：`Obx` 订阅 `activeSessions`，录制开始/停止即时刷新
- **一致 UI 约束**：`ConstrainedBox` 限制长文本溢出，设置页不崩溃
- **零编译警告**：`flutter analyze` 保持零 error/warning

### 7.3 启动性能

- **快速启动**：权限请求异步非阻塞
- **延迟加载**：直播状态在渲染后检测
- **非阻塞初始化**：Hive、权限、服务初始化不阻塞首帧渲染

---

## 8. 本地开发与构建

### 8.1 环境要求

- **Flutter SDK**: >= 3.10.0
- **Dart SDK**: >= 3.10.0

### 8.2 构建运行

```bash
# 获取依赖
flutter pub get

# 生成 Hive 适配器
dart run build_runner build --delete-conflicting-outputs

# 运行
flutter run

# 静态分析
flutter analyze

# 构建 APK
flutter build apk --release

# 构建 iOS
flutter build ios --release
```

### 8.3 平台支持

| 平台 | 支持状态 | 备注 |
|------|---------|------|
| Android | ✅ | 完整支持，含前台服务保活 |
| iOS | ✅ | 支持 |
| Linux | ✅ | 支持 |
| macOS | ✅ | 支持 |
| Windows | ✅ | 支持 |

### 8.4 项目初始化功能清单

项目初始化时已规划的功能清单记录在 `project_init_features.md` 中，涵盖：

- ✅ 纯音频录播（移除观看功能）
- ✅ 并行多直播间录制
- ✅ 搜索与收藏（移除首页推荐）
- ✅ 录制状态显示（时长、文件大小）
- ✅ 断线自动重连（最多 3 次）
- ✅ 后台运行 + 前台服务保活
- ✅ 按主播名自动创建文件夹
- ✅ 分组筛选（直播中/未开播/全部）
- ✅ 置顶收藏（绿色边框高亮）
- ✅ 录制完成提示
- ✅ 停止/取消确认对话框
- ✅ 搜索页即时收藏反馈
- ✅ TS → M4A 解包
- ✅ 批量多选解包
- ✅ 文件浏览器 + 音频播放器
- ✅ 异常中断 TS 检测
- ✅ 猫耳FM 支持
- ✅ Material3 主题切换

---

## 9. 免责声明

1. 本工具仅用于个人学习、研究和合法用途
2. **禁止将录播文件分发至互联网或用于商业用途**
3. 请尊重主播及平台的知识产权
4. 使用者需自行承担相关法律责任

---

## 附录：关键文件索引

| 文件 | 行数 | 功能 |
|------|------|------|
| `lib/main.dart` | - | 应用入口，多服务初始化 |
| `lib/services/recording_service.dart` | - | FFmpeg 录制核心 |
| `lib/services/recording_manager.dart` | - | 并行录制管理器 |
| `lib/app/sites.dart` | - | 多平台站点注册 |
| `lib/modules/home/` | - | 首页卡片列表 |
| `lib/modules/search/` | - | 多平台搜索 |
| `lib/modules/recordings/` | - | 录音文件浏览器 |
| `lib/modules/ts_unpack/` | - | TS 解包工具 |
| `lib/app/app_style.dart` | - | Material3 主题 |
