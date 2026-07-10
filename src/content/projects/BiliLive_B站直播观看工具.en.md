---
title: "BiliLive — Bilibili Live Streaming Viewer: Project Deep Dive"
date: "2026-07-03"
description: "A Flutter-based Bilibili live streaming Android client. Forked from Simple Live, streamlined and optimized to focus exclusively on Bilibili live streaming, featuring category browsing, local favorites, and live room audio recording."
tags: ["Flutter", "Dart", "Bilibili", "Live Streaming", "FFmpeg", "Android"]
---

# BiliLive — Bilibili Live Streaming Viewer: Project Deep Dive

> **Project**: Flutter-based Bilibili live streaming Android client
> **GitHub**: [BoooSAMA/dart_simple_live_bilibili](https://github.com/BoooSAMA/dart_simple_live_bilibili)
> **Framework**: Flutter 3.38 + Dart
> **Upstream**: [xiaoyaocz/dart_simple_live](https://github.com/xiaoyaocz/dart_simple_live) (GPL-3.0)
> **License**: GPL-3.0

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Architecture](#3-project-architecture)
4. [Feature Details](#4-feature-details)
5. [Core API & Data Flow](#5-core-api--data-flow)
6. [v2.0 Refactoring Highlights](#6-v20-refactoring-highlights)
7. [v2.1 New Features](#7-v21-new-features)
8. [Local Development & Build](#8-local-development--build)
9. [Comparison with the Original Project](#9-comparison-with-the-original-project)

---

## 1. Project Overview

### One-Sentence Summary

> BiliLive is an Android Bilibili live streaming viewer, streamlined and optimized from Simple Live, focused on delivering a clean and efficient Bilibili live browsing experience.

### Project Background

The original project [Simple Live](https://github.com/xiaoyaocz/dart_simple_live) is a multi-platform live streaming aggregation client supporting Bilibili, Huya, Douyu, Douyin, and more. This project was forked and heavily customized:

- **Removed** multi-platform support (Huya, Douyu, Douyin, etc.)
- **Removed** non-core features requiring a backend server (account login, synced follows)
- **Retained and optimized** the core Bilibili live streaming experience
- **Added** differentiated features like live room audio recording, pinned homepage categories, and local favorites

### Core Goals

- Provide a pure Bilibili live streaming browsing experience
- Zero account dependency — all favorites and follows stored locally
- Live room audio recording — save live audio as M4A files in real time
- Optimized category browsing system — subcategory browsing and favorites
- Overseas-friendly — bypass API endpoints that block overseas IPs

---

## 2. Tech Stack

| Category | Technology | Description |
|----------|-----------|-------------|
| **Framework** | Flutter 3.38 | Cross-platform UI (currently Android only) |
| **Language** | Dart | Application logic & UI |
| **Live API** | Bilibili Live API | Room info, danmaku, stream URLs |
| **Local Storage** | Hive | Lightweight NoSQL local database |
| **FFmpeg** | ffmpeg_kit_flutter | Live audio recording engine |
| **State Management** | GetX | Reactive state management |
| **Platform Channel** | MethodChannel | Flutter ↔ Native communication |

### Key Dependencies

| Package | Purpose |
|---------|---------|
| `ffmpeg_kit_flutter_new_https_gpl` | FFmpeg audio recording engine |
| `file_picker` | File picker (recording storage path) |
| `open_filex` | Open files |
| `share_plus` | File sharing |
| `hive` / `hive_flutter` | Local data persistence |
| `get` (GetX) | State management & routing |
| `wakelock_plus` | Prevent device sleep |

---

## 3. Project Architecture

### Overall Structure

```
dart_simple_live_bilibili/
├── simple_live_core/                # Core library (Bilibili only)
│   ├── lib/src/
│   │   ├── bilibili/
│   │   │   ├── bilibili_site.dart         # Site registration
│   │   │   ├── bilibili_live_api.dart     # Bilibili live API wrapper
│   │   │   ├── bilibili_message.dart      # Danmaku/message protocol
│   │   │   └── models/                    # Data models
│   │   └── base/                          # Abstract base classes
│   └── pubspec.yaml
│
└── simple_live_app/                  # Flutter APP client
    ├── lib/
    │   ├── main.dart                        # App entry point
    │   ├── app.dart                         # App component
    │   ├── store/                           # GetX state management
    │   ├── pages/
    │   │   ├── home/                        # Home (recommendation + pinned tabs)
    │   │   ├── live_room/                   # Live room detail page
    │   │   ├── search/                      # Search page
    │   │   ├── follow/                      # Local favorites list
    │   │   ├── history/                     # Watch history
    │   │   └── settings/                    # Settings (including audio config)
    │   ├── widgets/                         # Reusable components
    │   └── utils/                           # Utility functions
    ├── android/
    └── pubspec.yaml
```

### Architecture Layers

```
┌─────────────────────────────────────────────┐
│              UI Layer (Flutter Widgets)       │
│   Pages / Widgets / GetX Controllers          │
│   • Home recommendation + pinned tabs        │
│   • Live room (player + danmaku + recording)  │
│   • Search / Follow / History / Settings     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          Business Logic Layer                │
│  • LiveRoomStore — room state management    │
│  • FollowStore — local favorites storage    │
│  • HistoryStore — watch history             │
│  • RecordingService — FFmpeg recording mgmt │
│  • SettingsStore — appearance/audio config  │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  simple_live_core (Bilibili API Layer)       │
│  • Room info API (base info / stream URL)   │
│  • Recommendation API (recommend / areas)    │
│  • Danmaku WebSocket protocol               │
│  • Search API                               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          Native Layer / External Services    │
│  • FFmpeg (audio recording engine)          │
│  • Bilibili Live API (HTTP + WebSocket)     │
│  • Hive (local persistence)                 │
│  • Platform Channel communication           │
└──────────────────────────────────────────────┘
```

---

## 4. Feature Details

### 4.1 Live Room Browsing

| Feature | Description |
|---------|-------------|
| **Recommendation Feed** | Home recommendation tab, loads data immediately on startup |
| **Category Browsing** | Top category dropdown, expand to view subcategories |
| **Subcategory Detail** | Click subcategory to enter detail page, fetch room list by area_id |
| **Category Favorites** | Star favorite subcategories, shown in "My Favorites" section |
| **Pin Category to Home** | Pin subcategories as home tabs for instant loading |
| **Search** | Search live rooms and streamers |
| **Profile Page** | View streamer info and room list |

### 4.2 Live Playback

- **Multiple quality levels**: Supports Bilibili's available quality options
- **Danmaku display**: WebSocket real-time danmaku with keyword blocking
- **Playback controls**: Play/pause, fullscreen toggle

### 4.3 Local Features (No Account Needed)

All personal data stored locally, no Bilibili account required:

| Feature | Storage Method |
|---------|---------------|
| **Follow/Favorite rooms** | Hive local database |
| **Watch history** | Hive local database |
| **Category favorites** | Hive JSON serialization |
| **Pinned category config** | Hive persistence |
| **Appearance settings** | Hive / SharedPreferences |
| **Audio settings** | Hive / File system |

### 4.4 Live Room Recording

See [v2.1 New Features](#72-live-room-recording).

### 4.5 Sleep Timer

- Set a timer to automatically stop playback or exit the app
- Countdown display in the UI

---

## 5. Core API & Data Flow

### 5.1 API Endpoints

| API | Endpoint | Purpose |
|-----|----------|---------|
| Recommendation | `webMain/getMoreRecList` | Home recommendation room list |
| Area room list | `room/v1/area/getRoomList` | Get subcategory rooms by area_id |
| Room info | `room/v1/Room/get_info` | Get basic room information |
| Stream URL | `room/v1/Room/playUrl` | Get live stream URL |
| Search | `live/v1/room/search` | Search live rooms |
| Danmaku WebSocket | `broadcastlv.chat.bilibili.com` | Real-time danmaku push |

### 5.2 API Upgrade (v2.0)

v2.0 introduced significant API migration:

- **Recommendation**: Migrated from `second/getList` and `second/getListByArea` to `webMain/getMoreRecList` (less IP blocking for overseas users)
- **Area rooms**: Added `getAreaRooms` (`room/v1/area/getRoomList`), no WBI signature required, globally accessible, 30 rooms per page
- **Category matching**: Three-level matching strategy (exact parent name → fuzzy parent name → fuzzy subcategory name) for improved accuracy

### 5.3 Image Loading Optimization

- Cover image decoding resolution limit (`cacheWidth: 400px`)
- Significantly reduced memory usage, fixed list scroll stutter

---

## 6. v2.0 Refactoring Highlights

### 6.1 Category Browsing System

**Old issue**: Category classification was not granular enough — no way to browse subcategory content directly.

**New solution**:
1. Current category name displayed at top; click to open **category picker**
2. Category picker supports expand/collapse for parent categories, showing all subcategories
3. Click subcategory to enter a dedicated detail page using `getAreaRooms` API
4. Subcategories can be starred as favorites, appearing in "My Favorites"

### 6.2 Local Favorites

**Old issue**: The original project removed the follow feature, requiring login.

**New solution**:
1. Purely local favorites, persisted with Hive
2. Restored "Follow" tab in bottom navigation
3. Restored "Follow/Unfollow" button on live room detail page
4. Follow list supports filtering (All / Live / Offline)
5. Optimized cover image loading, reduced memory usage

### 6.3 Performance Optimization

- **Concurrency control**: Fixed `ConcurrentModificationError` from concurrent `loadData` calls
- **Async safety**: Generation counter prevents data corruption from async races
- **Image decoding**: Cover image `cacheWidth` limited to 400px, greatly reducing memory
- **Kotlin upgrade**: Upgraded to 2.3.21 for `screen_brightness_android` plugin compatibility

---

## 7. v2.1 New Features

### 7.1 Pinned Home Categories

- **Pin subcategories to home**: Add a pin marker to any subcategory in the category picker, turning it into an independent home tab
- **Independent loading**: Pinned subcategories load content automatically, pin icon shown in bottom menu
- **Persistence**: Pin info saved to Hive via JSON serialization, auto-restored on restart
- **Unpin**: Clear via bottom menu or settings page

### 7.2 Live Room Recording

Real-time live audio recording to M4A files:

| Feature | Description |
|---------|-------------|
| **Audio format** | M4A (AAC encoding) |
| **Recording engine** | FFmpeg `-c:a copy` stream copy, zero encoding loss |
| **Recording control** | Start/stop, recording duration in status bar |
| **Accidental tap prevention** | Confirmation dialog on first recording, supports "Don't show again" |
| **Auto-reconnect** | FFmpeg `-reconnect` parameters for automatic reconnection |
| **Save path** | Custom directory via file picker, with write permission validation |
| **File management** | View recorded files list, share, open folder |
| **Lifecycle** | Auto-stop recording when switching rooms or exiting |
| **Wake lock** | Wakelock keeps device awake during recording |

### 7.3 Home Loading Optimization

- **Immediate startup load**: `_initDefaultController` triggers initial data request in `onInit`
- **Loading progress percentage**: Refresh button shows current loading progress (e.g., `42%`)
- **Custom tab preloading**: Pinned subcategories participate in startup preloading, staggered 500ms apart to avoid high concurrency

---

## 8. Local Development & Build

### 8.1 Requirements

- **Flutter SDK**: 3.38
- **Dart SDK**: Included with Flutter

### 8.2 Build & Run

```bash
# Clone repository
git clone https://github.com/BoooSAMA/dart_simple_live_bilibili.git
cd dart_simple_live_bilibili

# Get dependencies
flutter pub get

# Run (connect Android device or start emulator)
flutter run

# Build APK
flutter build apk --release
```

> **Note**: This project does not provide pre-built Release packages — you need to compile it yourself.

### 8.3 Project Structure

```
simple_live_core/          # Core library
  lib/src/bilibili/
    bilibili_site.dart         # Site registration & configuration
    bilibili_live_api.dart     # Bilibili live API wrapper
    bilibili_message.dart      # Danmaku WebSocket protocol

simple_live_app/           # Flutter APP
  lib/
    store/                     # GetX state management
    pages/                     # Pages
    widgets/                   # Components
    utils/                     # Utilities
```

---

## 9. Comparison with the Original Project

| Dimension | Original (xiaoyaocz/dart_simple_live) | This Project (BoooSAMA/dart_simple_live_bilibili) |
|-----------|---------------------------------------|---------------------------------------------------|
| **Platforms** | Bilibili + Huya + Douyu + Douyin etc. | Bilibili only |
| **Account system** | Login required | Purely local, no login needed |
| **Follow/Favorites** | Server-synced | Hive local storage |
| **Category browsing** | Basic categories | Subcategory details + favorites + pinned tabs |
| **Recording** | None | v2.1 FFmpeg recording |
| **Code complexity** | High (multi-platform) | Streamlined (Bilibili only) |
| **Overseas compatibility** | Some APIs blocked | Alternative APIs, globally accessible |
| **Performance** | Basic | v2.0 greatly improved image loading & concurrency |

### Key Post-Fork Changes

1. **Removed multi-platform code**: Kept only Bilibili-related code
2. **Removed account features**: Login, follow sync, etc.
3. **Added local favorites**: Hive-stored purely local favorites
4. **Category system overhaul**: Subcategory browsing + favorites + home pinning
5. **API migration**: Used overseas-friendly API endpoints
6. **Recording feature**: FFmpeg audio recording

---

## Appendix: Key File Index

| File | Purpose |
|------|---------|
| `simple_live_core/lib/src/bilibili/bilibili_live_api.dart` | Bilibili live API wrapper |
| `simple_live_core/lib/src/bilibili/bilibili_message.dart` | Danmaku WebSocket protocol |
| `simple_live_app/lib/pages/live_room/` | Live room detail (player + danmaku + recording) |
| `simple_live_app/lib/pages/home/` | Home (recommendation + pinned tabs) |
| `simple_live_app/lib/pages/follow/` | Local favorites list |
| `simple_live_app/lib/store/` | GetX state management |
