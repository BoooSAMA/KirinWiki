---
title: "Day 29 — LiveRoomController 从 1445 行拆到 660 行：Flutter 上帝类重构实录"
date: 2026-06-25
tags: ["Flutter", "refactoring", "architecture", "MVC", "GetX", "God Class"]
description: "将 1445 行上帝类 LiveRoomController 拆分为 4 个专职文件，最终缩减至 660 行（-54%）。同时清理 AppSettingsController 模板代码（-19%）、迁移 UI Sheet 到 Page 层、全项目 91 文件零 analyzer 问题。"
---

# Day 29 — LiveRoomController 从 1445 行拆到 660 行：Flutter 上帝类重构实录

## 背景

上周的 [架构检查](/build-log/day28) 发现 `LiveRoomController` 有 **1445 行、194 个方法、8 个职责挤压**，是项目中最大的 God Class。这次集中重构的目标是把它的职责拆开，同时保持全项目零编译错误。

## 重构策略：逐层剥离

### 第一刀：RecordingService（-419 行）

录音功能涉及 FFmpeg 完整生命周期：启动、重连、重命名、取消、权限检测。这些逻辑和直播观看没有本质关系，第一个抽出来。

```dart
// 重构前：录音代码散落在 LiveRoomController 各处
void toggleRecording() { /* FFmpeg start/stop/retry... ~120 行 */ }
void cancelRecording() { /* 删除文件、清理状态... ~30 行 */ }
void _configureRecording() { /* 路径、权限、FFmpeg 参数... ~50 行 */ }

// 重构后：全部委托给 RecordingService
void toggleRecording() => RecordingService.instance.toggleRecording();
void cancelRecording() => RecordingService.instance.cancelRecording();
```

新建 `services/recording_service.dart`（481 行），所有 FFmpeg 逻辑、音视频统一切换、CDN 重连、写入权限检测、文件重命名、防误触对话框全部封装在内。

### 第二刀：AutoExitService（-35 行）

定时关闭的倒计时逻辑独立为 `services/auto_exit_service.dart`（63 行），包括倒计时、暂停/继续、全局设置检测。

### 第三刀：DanmakuFilter（25 行 → 控制器的 0 行）

弹幕关键词屏蔽的判断逻辑（普通匹配 + 正则）从控制器移到 `app/danmaku_filter.dart`（34 行），变成纯静态工具类，零状态。

```dart
// 重构前：控制器里 inline 正则匹配
if (shieldList.any((e) => msg.contains(e) || RegExp(e).hasMatch(msg))) return;

// 重构后：一行调用
if (DanmakuFilter.shouldBlock(msg)) return;
```

### 第四刀：AppSettingsController 模板清理（579 → 469 行，-19%）

45 个设置项每个需要 3 处重复代码：声明、初始化、setter。新建 `PersistedSetting<T>` 工具类：

```dart
// 重构前：每个设置项 3 处
var videoScaleMode = (-1).obs;
videoScaleMode.value = getValue('video_scale_mode', -1);
void setVideoScaleMode(int e) {
  videoScaleMode.value = e;
  setValue('video_scale_mode', e);
}

// 重构后：一行搞定
late final videoScaleMode = PersistedSetting<int>(this, 'video_scale_mode', -1);
```

`PersistedSetting` 自动持久化到 SharedPreferences——修改即存，无需手动调用 `setValue`。

### 第五刀：UI Sheet 迁移到 Page（-331 行）

8 个 `showXxxSheet()` 方法全部是 UI 构建代码，本质属于 View 层。将这些从 Controller 迁移到 `LiveRoomPage`，调用方（`player_controls.dart`）通过页面引用调用。

```
Controller → Page:
  showDanmuSettingsSheet()
  showVolumeSlider()
  showQualitySheet()
  showPlayUrlsSheet()
  showPlayerSettingsSheet()
  showDanmuShield()
  showFollowUserSheet()
  showAutoExitSheet()
```

### P3 代码异味修复

- `200` 硬编码 → `_maxMessageCache` 具名常量
- `catch (_) {}` 空吞异常 → `Log.logPrint` + 错误详情

## 数字对比

| 指标 | 重构前 | 重构后 | 变化 |
|------|--------|--------|------|
| **LiveRoomController** | **1,445 行 / 194 方法** | **660 行 / ~100 方法** | **-54%** |
| AppSettingsController | 579 行 | 469 行 | -19% |
| 新建服务文件 | — | 4 个（596 行） | 🆕 |
| 全项目 analyzer | 未记录 | **零问题** | ✅ |
| 最重文件排名 | LiveRoomController (1) | LiveRoomPage (1) | 不再是 God Class |

### 重构前后职责分布

```
重构前：
  LiveRoomController (1445 行)
  ├── 弹幕处理
  ├── 播放线路
  ├── 录音 (FFmpeg)
  ├── 关键词屏蔽
  ├── 自动关闭
  ├── UI Sheet ×8
  ├── 关注/分享/历史
  └── 设置面板

重构后：
  LiveRoomController (660 行 — 编排层)
  ├── 弹幕消息处理
  ├── 播放线路管理
  ├── 录音 ───── 委托 → RecordingService (481 行)
  ├── 关键词屏蔽 ─ 委托 → DanmakuFilter (34 行)
  ├── 自动关闭 ─── 委托 → AutoExitService (63 行)
  ├── 关注/分享/历史
  └── UI Sheet ─── 迁移 → LiveRoomPage (8 个方法)

  新增 4 个专职文件，各司其职
```

## 学到的原则

### 1. God Class 的渐进式剥离策略

不要一次拆完。按**依赖度从低到高**逐步抽离：

| 顺序 | 模块 | 耦合度 | 提取行数 | 是否顺利 |
|------|------|--------|----------|----------|
| 1 | RecordingService | 低 | 419 | ✅ 独立 GetX Service，只依赖 Controller 的几个回调 |
| 2 | AutoExitService | 低 | 35 | ✅ 纯定时器逻辑，零耦 |
| 3 | DanmakuFilter | 低 | 25 | ✅ 纯函数，零状态 |
| 4 | AppSettings 模板 | 中 | 110 | ✅ 引入 PersistedSetting 工具类 |
| 5 | UI Sheet 迁移 | 高 | 331 | ⚠️ 需要跨文件（player_controls.dart）协调 |

RecordingService 最容易拆（独立服务），UI Sheet 最难拆（被多个文件调用）。先做容易的建立信心，同时也验证了抽取模式可行。

### 2. GetX 服务定位器模式的代价

所有服务通过 `.instance` 全局访问，不需要构造函数注入。好处是抽取时改动量小（直接 `RecordingService.instance.xxx`），**坏处是不可测试**。

```dart
// 重构前后，调用方不变
RecordingService.instance.toggleRecording();
```

如果以后要写单元测试，需要给所有服务添加 `abstract class` 接口，并改为构造函数注入。这是下一步的优化方向，但**不是今天的瓶颈**。

### 3. `PersistedSetting<T>` — 模板消除的通用方案

Flutter 设置页面的典型模板代码：

```dart
var someSetting = defaultValue.obs;
someSetting.value = getValue('key', defaultValue);
void setSomeSetting(T e) {
  someSetting.value = e;
  setValue('key', e);
}
```

45 个设置项 × 3 处 = 135 个重复片段。`PersistedSetting` 封装成一个泛型类：

```dart
class PersistedSetting<T> {
  final Rx<T> _value;
  T get value => _value.value;
  set value(T v) { _value.value = v; _save(); }
}
```

15 行代码消灭了 ~200 行模板，68% 的代码量消灭率。

### 4. `Expanded` vs `Flexible`：Flutter 布局的溢出陷阱

录音按钮在工具栏出现时，`Expanded`（强制占满）导致两个按钮挤在一个槽位中溢出。换成 `Flexible(fit: FlexFit.loose)` + `mainAxisSize: Min` 后，Row 只取子元素的实际宽度，不再溢出。

```
Expanded:   [   ❤   ][   ↻   ][   ↗   ][   ⏹  ✕    ]  ← 溢出
Flexible:   [   ❤   ][   ↻   ][   ↗   ][⏹ ✕]        ← 自然宽度 72dp
```

## 最终架构评分：B- → B+

| 维度 | 重构前 | 重构后 |
|------|--------|--------|
| 职责分离 | ⚠ 上帝类 | ✅ 5 个文件各司其职 |
| 可扩展性 | 🟡 往上帝类加方法 | ✅ 加功能即加服务 |
| 可读性 | ⚠ 1,445 行大海捞针 | ✅ 660 行编排 + 596 行专职服务 |
| 可调试性 | ⚠ 录音 bug 淹没在 200 个方法中 | ✅ 录音 bug → RecordingService 定位 |
| 模板代码 | ⚠ 45 个设置 135 处重复 | ✅ PersistedSetting 消灭 ~70% |
| 可测试性 | ❌ 所有 GetX 单例 | 🟡 仍是单例，但职责更清晰 |

## 之后可做（ROI 递减）

1. PlayQualityManager 提取（~100 行）— 播放器线路/清晰度逻辑，状态耦合深
2. 服务抽象接口 + 构造函数注入 — 解决可测试性唯一短板
3. 弹幕消息处理独立 — Controller 中剩余最大块
