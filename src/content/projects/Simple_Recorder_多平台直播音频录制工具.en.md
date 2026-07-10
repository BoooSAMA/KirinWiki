---
title: "Simple Recorder — Multi-Platform Live Audio Recording Tool: Project Deep Dive"
date: "2026-07-03"
description: "A Flutter-based multi-platform live audio recording tool supporting Bilibili, Douyin, Douyu, Huya, and MaoerFM. Uses FFmpeg for pure audio stream copy, with parallel recording, background keep-alive, and file management."
tags: ["Flutter", "Dart", "FFmpeg", "Live Streaming", "Audio Recording", "Cross-Platform"]
---

# Simple Recorder — Multi-Platform Live Audio Recording Tool: Project Deep Dive

> **Project**: Flutter-based multi-platform live audio recording tool
> **GitHub**: [BoooSAMA/simple_recorder](https://github.com/BoooSAMA/simple_recorder)
> **Framework**: Flutter + Dart
> **License**: GPL-3.0
> **Supported Platforms**: Android / iOS / Linux / macOS / Windows

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Architecture](#3-project-architecture)
4. [Feature Details](#4-feature-details)
5. [Core Module Analysis](#5-core-module-analysis)
6. [Recording Engine Design](#6-recording-engine-design)
7. [Performance Optimization](#7-performance-optimization)
8. [Local Development & Build](#8-local-development--build)
9. [Disclaimer](#9-disclaimer)

---

## 1. Project Overview

### One-Sentence Summary

> Simple Recorder is a cross-platform live audio recording tool supporting Bilibili, Douyin, Douyu, Huya, and MaoerFM live room audio recording. Based on FFmpeg pure audio stream copy (no re-encoding), it supports parallel recording, background keep-alive, and file management.

### Project Background

This project merges core capabilities from two open-source projects:

| Source | Contribution |
|--------|-------------|
| **[Simple Live](https://github.com/xiaoyaocz/dart_simple_live)** | Multi-platform live search and room info retrieval |
| **[Bililive](https://github.com/BoooSAMA/bililive)** | FFmpeg-based live room audio recording core |

The project is positioned as a "pure recording tool" — **no live viewing, no video recording** — focused solely on audio capture and file management.

### Core Design Principles

1. **Recording-first** — audio recording only, no streaming/playback
2. **Zero encoding loss** — FFmpeg `-c:a copy` stream copy, preserves original AAC quality
3. **Parallel recording** — record multiple rooms simultaneously without interference
4. **Background keep-alive** — Android foreground service prevents interruption when screen is off
5. **Purely local** — all data stored locally, no account needed

---

## 2. Tech Stack

| Category | Technology | Description |
|----------|-----------|-------------|
| **Framework** | Flutter | Cross-platform UI (6 platforms) |
| **Language** | Dart | Application logic & UI |
| **Recording engine** | FFmpeg (ffmpeg_kit_flutter) | Audio stream copy recording |
| **Live API** | simple_live_core | Multi-platform live API wrapper |
| **Local storage** | Hive | NoSQL local database |
| **State management** | GetX | Reactive state management & routing |
| **Background service** | flutter_background_service | Android foreground service keep-alive |
| **Permissions** | permission_handler | Runtime permissions |
| **Wake lock** | wakelock_plus | Prevent device sleep |

### Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `ffmpeg_kit_flutter_full_gpl` | - | FFmpeg recording engine (GPL variant) |
| `simple_live_core` | - | Multi-platform live API |
| `flutter_background_service` | - | Android foreground service |
| `hive` / `hive_flutter` | - | Local data persistence |
| `get` | - | State management & routing |
| `permission_handler` | - | Runtime permissions |
| `wakelock_plus` | - | Prevent sleep |

---

## 3. Project Architecture

### Directory Structure

```
simple_recorder/
├── lib/
│   ├── main.dart                           # Entry: Hive/GetX/Permissions/Service init
│   │
│   ├── app/                                # App infrastructure
│   │   ├── app_style.dart                  # Material3 light/dark themes
│   │   ├── constant.dart                   # Global constants
│   │   ├── log.dart                        # Logging utility
│   │   ├── sites.dart                      # Multi-platform site registry
│   │   ├── event_bus.dart                  # Cross-module event bus
│   │   └── controller/
│   │       └── app_settings_controller.dart  # Global settings (path, theme, pin)
│   │
│   ├── models/                             # Data models
│   │   └── db/
│   │       ├── follow_user.dart            # Favorite user model (Hive adapter)
│   │       └── recording_task.dart         # Recording task model
│   │
│   ├── services/                           # Business service layer
│   │   ├── db_service.dart                 # Hive CRUD operations
│   │   ├── local_storage_service.dart      # Hive settings box
│   │   ├── recording_service.dart          # RecordingSession — FFmpeg core
│   │   ├── recording_manager.dart          # Parallel recording manager (RxList reactive)
│   │   └── follow_export_service.dart      # Favorite data import/export
│   │
│   ├── modules/                            # Feature modules (pages)
│   │   ├── home/                           # Home: card list + recording control + filter bar
│   │   ├── search/                         # Multi-platform search + instant favorite feedback
│   │   ├── settings/                       # Settings: storage path/appearance/data/logs
│   │   ├── recordings/                     # Recording file browser + built-in audio player
│   │   ├── ts_unpack/                      # TS unpack tool (supports batch multi-select)
│   │   └── debug_log/                      # Debug log page
│   │
│   ├── routes/                             # Route configuration
│   │   ├── app_pages.dart                  # Page route table
│   │   └── route_path.dart                 # Route path constants
│   │
│   └── widgets/                            # Reusable components
│       └── settings/                       # Settings page components
│
├── android/app/src/main/.../
│   └── MainActivity.kt                     # Android MethodChannel
│
├── docs/superpowers/                       # Design documents
├── test/                                   # Test files
├── pubspec.yaml                            # Project config
└── README.md
```

### Architecture Layers

```
┌─────────────────────────────────────────────┐
│              UI Layer (Flutter Widgets)       │
│  • Home card list (room status + recording)  │
│  • Search page (multi-platform + favorites)  │
│  • Recording file browser + audio player    │
│  • Settings page (theme, path, logs)        │
│  • TS unpack tool page                      │
└──────────────────┬──────────────────────────┘
                   │  GetX reactive bindings
┌──────────────────▼──────────────────────────┐
│        Service Layer (Services/Controllers)   │
│  • RecordingManager — parallel recording     │
│  • RecordingSession — single room session    │
│  • DbService — Hive CRUD                     │
│  • AppSettingsController — global settings   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Core Engine / External Dependencies  │
│  • FFmpeg (ffmpeg_kit) — audio recording    │
│  • simple_live_core — live API              │
│  • Hive — local persistence                 │
│  • flutter_background_service — keep-alive   │
└──────────────────────────────────────────────┘
```

---

## 4. Feature Details

### 4.1 Home Card Layout

| Element | Description |
|---------|-------------|
| **Streamer info** | Avatar + username + live status indicator |
| **Live status** | Live / Offline |
| **Recording control** | "Stop" + "Cancel" dual buttons when recording, with confirmation dialog |
| **Pin feature** | 📌 pin icon, green border highlight |
| **Recording status** | Real-time duration (HH:MM:SS) + file size |
| **Error log** | Red error log area on recording failure, clickable for details |
| **Reconnect status** | Shows "Reconnecting (N/3)" during reconnection |
| **Layout** | Non-grid, single card vertical排列, one per row |

### 4.2 Recording Core

See [Recording Engine Design](#6-recording-engine-design).

### 4.3 Search & Favorites

- **Multi-platform search**: Search Bilibili/Douyin/Douyu/Huya/MaoerFM live rooms
- **MaoerFM room ID**: Direct room number input supported
- **Instant favorite feedback**: Heart icon turns red immediately on click, no need to wait for API response
- **Favorite group management**: Differentiate live / offline, supports search

### 4.4 Live Status Monitoring

| Feature | Description |
|---------|-------------|
| **Batch concurrent detection** | 5 rooms queried in parallel per batch to avoid UI blocking |
| **Progressive UI update** | Each result syncs immediately, no need to wait for full refresh |
| **Real-time progress feedback** | Refresh button has built-in circular progress + percentage text |
| **Group filter bar** | Live / Offline / All, with count badges |

### 4.5 Recording File Management

| Feature | Description |
|---------|-------------|
| **File browsing** | Independent browser page, grouped by streamer folder |
| **TS → M4A unpack** | One-click TS segment unpack to M4A audio |
| **Batch unpack** | Cross-folder multi-select TS files for batch processing |
| **Audio playback** | Built-in player (play/pause/快进快退/seek progress bar) |
| **File editing** | Rename, delete, batch delete |
| **Anomaly detection** | Auto-scan for abnormally terminated TS files on startup |

### 4.6 Settings & Permissions

| Setting | Description |
|---------|-------------|
| **Theme switch** | Material3 light/dark mode |
| **Audio storage path** | Custom recording save directory |
| **Streamer folder** | Auto-create subfolders by streamer name |
| **Debug logs** | Real-time log viewing, saving, clearing |
| **Storage permission** | Android 11+ auto-request "Manage all files" permission |

### 4.7 Background Keep-Alive

- **Foreground service**: Android shows foreground service notification during recording
- **Screen-off uninterrupted**: Prevents system from killing recording process when screen is locked
- **Lifecycle management**: Auto-stop recording when switching pages or exiting

---

## 5. Core Module Analysis

### 5.1 RecordingManager

```dart
class RecordingManager extends GetxController {
  static final RecordingManager instance = RecordingManager._();
  
  final RxList<RecordingSession> activeSessions = <RecordingSession>[].obs;
  
  // Start recording a room
  Future<RecordingSession> startRecording(LiveRoom room);
  
  // Stop recording
  Future<void> stopRecording(String sessionId);
  
  // Cancel recording (don't save file)
  Future<void> cancelRecording(String sessionId);
  
  // Stop all recordings
  Future<void> stopAll();
  
  // Reconnect tracking
  int reconnectAttempts = 0;
  static const int maxReconnects = 3;
}
```

- Manages active recording sessions reactively via `RxList`
- UI triggered via `Obx(() { final _ = RecordingManager.instance.activeSessions.length; })`
- Supports parallel recording of multiple rooms

### 5.2 RecordingSession

```dart
class RecordingSession {
  final String id;           // Unique identifier
  final LiveRoom room;       // Room info
  final String outputPath;   // Output path
  final DateTime startedAt;  // Start time
  
  // Reactive state
  final Rx<Duration> duration = Duration.zero.obs;
  final Rx<int> fileSize = 0.obs;
  final Rx<RecordingStatus> status = RecordingStatus.recording.obs;
  
  // FFmpeg command
  // -c:a copy -f mpegts output.ts
  Future<void> start();
  Future<void> stop();
  Future<void> cancel();
}
```

### 5.3 Platform Site Registry

```dart
// app/sites.dart — Site registry
static final sites = <BaseSite>[
  BilibiliSite(),
  DouyinSite(),
  DouyuSite(),
  HuyaSite(),
  MaoerFMSite(),
];
```

Each site implements the `BaseSite` abstract class, providing unified search, room info, and live status detection interfaces.

### 5.4 Data Flow

```
[User taps "Record"] → RecordingManager.startRecording(room)
    │
    ▼
[RecordingSession.start()]
    ├── 1. simple_live_core fetches stream URL
    ├── 2. Constructs FFmpeg command
    ├── 3. Starts FFmpeg process
    ├── 4. Starts periodic duration + file size updates
    └── 5. Registers with RecordingManager.activeSessions
    │
    ▼
[UI reactive update]
    ├── Real-time recording duration (Obx binding)
    ├── Real-time file size display
    └── Error status display
    │
    ▼
[User taps "Stop"] → stop()
    ├── 1. FFmpeg process gracefully stops
    ├── 2. TS file write complete
    └── 3. Recording record created in Hive
```

---

## 6. Recording Engine Design

### 6.1 FFmpeg Command

```bash
# Core recording command: stream copy, no re-encoding
ffmpeg -i {stream_url} \
  -c:a copy \
  -f mpegts \
  -reconnect 1 \
  -reconnect_at_eof 1 \
  -reconnect_streamed 1 \
  -reconnect_delay_max 5 \
  {output_path}.ts
```

| Parameter | Description |
|-----------|-------------|
| `-c:a copy` | Audio stream copy, zero encoding loss |
| `-f mpegts` | TS format container (supports断点续传) |
| `-reconnect 1` | Enable reconnection |
| `-reconnect_delay_max 5` | Max reconnect delay 5 seconds |

### 6.2 Recording State Machine

```
IDLE → RECORDING → STOPPED (normal end)
                 → CANCELLED (user cancelled, don't save)
                 → ERROR → RECONNECTING (auto-reconnect, max 3 times)
                            ├── → RECORDING (reconnect success)
                            └── → ERROR (reconnect exhausted)
```

### 6.3 TS Unpack Mechanism

Recordings are暂存 as TS segments. After stopping, they are converted to M4A via `ffprobe` / FFmpeg:

```bash
# TS → M4A unpack
ffmpeg -i {input}.ts -c:a copy -y {output}.m4a
```

Advantages:
- **Interruption protection**: TS format remains usable even if recording is interrupted
- **Zero encoding loss**: Only re-muxing, no re-encoding
- **Batch processing**: Supports cross-folder multi-select batch unpack

### 6.4 Background Keep-Alive Mechanism

Android implements foreground service via `flutter_background_service`:

```kotlin
// MainActivity.kt — Android foreground service
val serviceIntent = Intent(this, BackgroundService::class.java)
startForegroundService(serviceIntent)

// Foreground service notification
val notification = NotificationCompat.Builder(this, CHANNEL_ID)
    .setContentTitle("Simple Recorder")
    .setContentText("Recording ${sessionCount} rooms")
    .setSmallIcon(R.drawable.ic_record)
    .build()
startForeground(NOTIFICATION_ID, notification)
```

---

## 7. Performance Optimization

### 7.1 Recording Performance

| Optimization | Before | After | Effect |
|-------------|--------|-------|--------|
| **FFmpeg logs** | Real-time callback to Dart | No callback during recording | Reduced cross-language call overhead |
| **File size polling** | Every second | Every 5 seconds | 80% fewer system calls |
| **Reconnect delay** | Fixed 2s | Incremental 2s/4s/6s | Lower power consumption |
| **Process management** | Unlimited | Session isolation | Prevents resource leaks |

### 7.2 UI Performance

- **Reactive recording status**: `Obx` subscribes to `activeSessions`, instant refresh on start/stop
- **Consistent UI constraints**: `ConstrainedBox` prevents text overflow, settings page won't crash
- **Zero compilation warnings**: `flutter analyze` maintains zero errors/warnings

### 7.3 Startup Performance

- **Fast startup**: Permission requests are async and non-blocking
- **Lazy loading**: Live status detection occurs after rendering
- **Non-blocking init**: Hive, permissions, service initialization don't block first frame rendering

---

## 8. Local Development & Build

### 8.1 Requirements

- **Flutter SDK**: >= 3.10.0
- **Dart SDK**: >= 3.10.0

### 8.2 Build & Run

```bash
# Get dependencies
flutter pub get

# Generate Hive adapters
dart run build_runner build --delete-conflicting-outputs

# Run
flutter run

# Static analysis
flutter analyze

# Build APK
flutter build apk --release

# Build iOS
flutter build ios --release
```

### 8.3 Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Android | ✅ | Full support with foreground service |
| iOS | ✅ | Supported |
| Linux | ✅ | Supported |
| macOS | ✅ | Supported |
| Windows | ✅ | Supported |

### 8.4 Feature Checklist

The project initialization feature checklist is recorded in `project_init_features.md`, covering:

- ✅ Pure audio recording (removed viewing functionality)
- ✅ Parallel multi-room recording
- ✅ Search + favorites (removed home recommendation)
- ✅ Recording status display (duration, file size)
- ✅ Auto-reconnect on断线 (max 3 times)
- ✅ Background operation + foreground service
- ✅ Auto-create folders by streamer name
- ✅ Group filtering (Live/Offline/All)
- ✅ Pin favorites (green border highlight)
- ✅ Recording complete notification
- ✅ Stop/cancel confirmation dialog
- ✅ Instant favorite feedback on search page
- ✅ TS → M4A unpack
- ✅ Batch multi-select unpack
- ✅ File browser + audio player
- ✅ Anomalous TS detection
- ✅ MaoerFM support
- ✅ Material3 theme switching

---

## 9. Disclaimer

1. This tool is for personal learning, research, and lawful purposes only
2. **Do not distribute recorded files on the internet or use them commercially**
3. Please respect the intellectual property rights of streamers and platforms
4. Users assume all related legal responsibilities

---

## Appendix: Key File Index

| File | Lines | Function |
|------|-------|----------|
| `lib/main.dart` | - | App entry, multi-service initialization |
| `lib/services/recording_service.dart` | - | FFmpeg recording core |
| `lib/services/recording_manager.dart` | - | Parallel recording manager |
| `lib/app/sites.dart` | - | Multi-platform site registry |
| `lib/modules/home/` | - | Home card list |
| `lib/modules/search/` | - | Multi-platform search |
| `lib/modules/recordings/` | - | Recording file browser |
| `lib/modules/ts_unpack/` | - | TS unpack tool |
| `lib/app/app_style.dart` | - | Material3 themes |
