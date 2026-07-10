---
title: "KirinWiki Blog Project — Architecture & Technical Implementation"
date: "2026-07-03"
description: "Complete technical implementation and architecture analysis of a personal blog built with Astro 6 + Tailwind CSS v4 + Three.js. Covers time-based themes, 3D scenes, and a custom-built music player."
tags: ["Astro", "Tailwind CSS", "Three.js", "Cloudflare", "Blog"]
---

# KirinWiki Blog Project — Architecture & Technical Implementation

> **Project**: Personal blog and knowledge wiki site
> **URL**: `kirinwiki.tech`
> **Framework**: Astro 6
> **Deployment**: Cloudflare Pages
> **GitHub**: [BoooSAMA/my-blog](https://github.com/BoooSAMA/my-blog)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Architecture](#3-project-architecture)
4. [Page Routes](#4-page-routes)
5. [Core Features](#5-core-features)
6. [Data Management](#6-data-management)
7. [UI/UX Design](#7-uiux-design)
8. [Local Development & Deployment](#8-local-development--deployment)
9. [Development Roadmap](#9-development-roadmap)
10. [Lessons Learned](#10-lessons-learned)

---

## 1. Project Overview

### One-Sentence Summary

> A static blog built with Astro 6, combining Tailwind CSS v4, Preact interactive components, and Cloudflare edge infrastructure — a personal knowledge wiki created to learn the full web development process from scratch.

### Project Background

This is a **learn web development from scratch** project. Technology choices follow the philosophy of "understand principles first, then adopt complex frameworks":

1. **Phase 1**: Pure static blog with Astro, understanding SSG, Markdown-driven content, and CSS systems
2. **Phase 2**: Add dynamic features (likes, search), understanding frontend-backend communication and databases
3. **Phase 3**: Horizontal expansion to React/Next.js, building cross-framework understanding

### Core Goals

- Own a fully controllable personal website
- Understand the entire web chain (DNS → CDN → static generation → deployment)
- Build a foundation for learning complex frontend frameworks (React/Next.js)
- Document technical exploration and learning notes

---

## 2. Tech Stack

| Category | Technology | Description |
|----------|-----------|-------------|
| **Framework** | [Astro 6](https://astro.build) | Static site generator, Islands architecture |
| **Styling** | [Tailwind CSS v4](https://tailwindcss.com) | Utility-First CSS, integrated via `@tailwindcss/vite` |
| **Interactivity** | [Preact](https://preactjs.com) | Lightweight React alternative (3KB), used for interactive components like likes |
| **3D Graphics** | [Three.js](https://threejs.org) | Homepage crystal scene animation (`r184`) |
| **Language** | TypeScript (strict) | Full-site TypeScript |
| **Package Manager** | npm | Node >= 22.12 |
| **Database** | Cloudflare D1 | SQLite-compatible edge database |
| **Storage** | Cloudflare R2 | Image and media file storage |
| **Deployment** | Cloudflare Pages | Global edge network static hosting |
| **Domain** | Cloudflare DNS | DNS management & HTTPS |

### Key Dependencies

```json
{
  "dependencies": {
    "@astrojs/cloudflare": "^13.7.0",
    "@astrojs/preact": "^5.1.4",
    "@tailwindcss/vite": "^4.3.0",
    "astro": "^6.3.8",
    "preact": "^10.29.2",
    "tailwindcss": "^4.3.0",
    "three": "^0.184.0"
  },
  "devDependencies": {
    "wrangler": "^4.100.0"
  }
}
```

### Tailwind CSS v4 Notes

This project uses **Tailwind v4**, key differences from v3:

- **No `tailwind.config.js`** — configuration is done via CSS `@theme { ... }` directives
- CSS entry file `src/styles/global.css` imports with `@import "tailwindcss"`
- Basic class names (`flex`, `p-4`, `text-lg`, etc.) are compatible with v3
- Import in `.astro` components via `import '../styles/global.css'`

---

## 3. Project Architecture

### Directory Structure

```
my-blog/
├── public/                    # Static assets (copied directly to dist)
│   ├── favicon.ico
│   ├── favicon.svg
│   └── music/                 # Music player playlist files
├── src/
│   ├── pages/                 # File-based routing (each file = one URL)
│   │   ├── index.astro        # Home
│   │   ├── about.astro        # About
│   │   ├── pictures.astro     # Pictures
│   │   ├── shares.astro       # Shares/links
│   │   ├── blog/              # Blog section
│   │   │   ├── index.astro    # Blog category overview
│   │   │   ├── [category].astro     # Category page
│   │   │   ├── [category]/          # Category article detail
│   │   │   └── tags/          # Tags page
│   │   └── projects/          # Projects page
│   │       └── index.astro
│   ├── layouts/
│   │   └── BaseLayout.astro   # Global layout (nav, footer, player, 3D bg)
│   ├── components/            # Reusable components
│   │   ├── Navbar.astro
│   │   ├── Footer.astro
│   │   ├── MusicPlayer.astro
│   │   ├── LikeButton.tsx     # Preact interactive component
│   │   ├── PostCard.astro
│   │   ├── SmallPostCard.astro
│   │   ├── CategoryDisplay.astro
│   │   └── ReadingBackdrop.astro
│   ├── content/               # Content collections (Markdown-driven)
│   │   └── categories/        # Articles organized by category
│   │       ├── blog/
│   │       ├── projects/
│   │       ├── interview/
│   │       ├── build-log/
│   │       └── bible/
│   ├── lib/                   # Client-side JavaScript
│   │   ├── crystalScene.js    # Three.js 3D scene
│   │   ├── timeTheme.js       # Time-based theme switching
│   │   └── colorPalette.js    # 24-color palette
│   └── styles/
│       └── global.css         # Global styles + Tailwind entry point
├── db/                        # Database related
├── functions/                 # Cloudflare Functions
├── astro.config.mjs           # Astro configuration
├── wrangler.jsonc             # Cloudflare Workers configuration
├── AGENTS.md                  # AI assistant project context
├── 阶段学习搭建计划.md         # Multi-phase learning roadmap
└── package.json
```

### Architecture Characteristics

```
[User request] → [Cloudflare CDN] → [Cloudflare Pages] → [Static HTML]
                                    │
                            [Astro build time]
                            ├── Markdown → HTML pages
                            ├── Tailwind → compiled CSS
                            └── Preact/JS → hydrated interactive components
```

- **Static-first**: Full HTML generated at build time, no server runtime needed
- **Islands architecture**: JavaScript loaded only where interaction is needed (e.g., like buttons)
- **View Transitions**: Astro's `<ClientRouter />` for SPA-style page transitions
- **Persistent state**: Music player state maintained across navigations via `data-astro-transition-persist`

---

## 4. Page Routes

| Route | File | Description |
|-------|------|-------------|
| `/` | `src/pages/index.astro` | Home: welcome + nav cards + likes + social links |
| `/about` | `src/pages/about.astro` | Personal introduction |
| `/blog` | `src/pages/blog/index.astro` | Blog category overview, articles grouped by category |
| `/blog/[category]` | `src/pages/blog/[category].astro` | Article list for a category |
| `/blog/[category]/[slug]` | Dynamic route | Article detail (Markdown rendered) |
| `/blog/tags` | `src/pages/blog/tags/` | Tags page |
| `/projects` | `src/pages/projects/index.astro` | Project portfolio |
| `/pictures` | `src/pages/pictures.astro` | Picture wall |
| `/shares` | `src/pages/shares.astro` | Share/recommendation links |

### Content Category System

Blog content is organized under `src/content/categories/` subdirectories, currently 5 categories:

| Category | ID | Description |
|----------|-----|-------------|
| Build Log | `build-log` | Site build process documentation |
| Blog | `blog` | General articles |
| Projects | `projects` | Project deep dives |
| Interview | `interview` | Interview experience |
| Bible | `bible` | Bible study notes |

---

## 5. Core Features

### 5.1 Time-Based Theme System

Automatically switches page background color and theme based on Singapore time (`Asia/Singapore`):

- 24-color palette simulating natural color changes from midnight to sunrise
- Automatically switches to night theme (`data-theme="night"`) when brightness drops below threshold
- Background controlled via CSS custom property `--time-bg-color`
- Checks time every minute, with smooth color transitions between hours
- Driven by `requestAnimationFrame` loop, paused when page is not visible

**Key files**:
- `src/lib/timeTheme.js` — Time calculation and color interpolation
- `src/lib/colorPalette.js` — 24-color palette
- `src/styles/global.css` — CSS variable definitions (`:root` / `[data-theme="night"]`)

### 5.2 3D Crystal Scene

Full-screen 3D background scene built with Three.js:

- Curved floor (based on sphere curvature calculation)
- Crystal-like geometry as visual focal point
- Slow camera orbit animation
- Scene background color synchronized with time-based theme
- Responds to theme changes via `window.__setSceneBackground()` API

**Key files**:
- `src/lib/crystalScene.js` (303 lines, Three.js scene construction)
- Initialized in `BaseLayout.astro`, persisted across pages via `data-astro-transition-persist="bg3d"`

### 5.3 Music Player

Custom-built global music player using the `<audio>` API with a custom UI:

- **Persistence**: Maintains playback state across View Transitions via `data-astro-transition-persist`
- **Playlist loading**: Supports `playlist.json` (local dev) and `playlist.r2.json` (production R2 URLs)
- **Play modes**: Single track, album play, previous/next track
- **UI hierarchy**: Artist → Album → Song three-level tree structure
- **State recovery**: Stores playback state, volume, and collapsed/expanded state via `localStorage`
- **Glow border**: Bottom player bar has a gradient flow animation during playback
- **Collapse/expand**: Can collapse into mini-player mode
- **Keyboard shortcuts**: Spacebar to toggle play/pause

**Key files**:
- `src/components/MusicPlayer.astro` (682 lines, full player implementation)
- `public/music/playlist.json` / `playlist.r2.json` — playlist data

### 5.4 Like Functionality

Homepage like feature using a Preact interactive component:

- **Component**: `src/components/LikeButton.tsx` (Preact, `client:load` hydration)
- **Backend**: Cloudflare D1 database stores like count
- **Persistence**: `localStorage` tracks whether user has already liked

### 5.5 Glassmorphism UI

Full-site glassmorphism design:

- Cards use `backdrop-blur-md` + semi-transparent backgrounds
- CSS variable system manages color themes
- Hover border glow animation (`ring-glow` class, `conic-gradient` + CSS `@property`)
- Dark/light mode auto-adapts via CSS variables

### 5.6 Debug Panel

Hidden developer tools (Ctrl+Shift+F to toggle):

- Real-time FPS display (green ≥55, yellow ≥30, red <30)
- Three.js camera coordinates (pos + lookAt)
- Click to copy coordinates to clipboard

---

## 6. Data Management

### 6.1 Content Collections

Currently uses Astro's `import.meta.glob` pattern to read Markdown files:

```typescript
const postModules = import.meta.glob("../../content/categories/**/*.md", {
  eager: true,
}) as Record<string, { frontmatter: Record<string, any>; file: string }>
```

Articles are organized in `src/content/categories/{category}/` directories, with each `.md` file automatically mapped to a page.

### 6.2 Cloudflare D1 Database

Used for dynamic data (like counts):

```sql
CREATE TABLE likes (
  slug TEXT PRIMARY KEY,
  count INTEGER DEFAULT 0
);
```

API endpoints provided via Cloudflare Functions, called at Astro build/runtime.

### 6.3 Cloudflare R2 Object Storage

- Images and media files stored in R2 bucket
- Production music file URLs point to R2
- Markdown articles reference images via full URLs

### 6.4 Media Separation Strategy

**No media files stored in Git**:
- Images → Cloudflare R2
- Videos → YouTube / Bilibili (embedded via iframe)
- Music → Playlist JSON + R2 audio files

---

## 7. UI/UX Design

### 7.1 Design Language

| Dimension | Style |
|-----------|-------|
| **Overall style** | Glassmorphism |
| **Color scheme** | Time-based dynamic background + CSS variable theme |
| **Typography** | System font stack (`font-sans`) |
| **Interaction feedback** | Hover glow, micro-animations, smooth transitions |
| **Responsive** | Tailwind breakpoints (`max-sm:` etc.) |

### 7.2 CSS Variable System

```css
:root {
  --glass-bg: rgba(255, 255, 255, 0.85);
  --glass-border: rgba(255, 255, 255, 0.3);
  --glass-text: #374151;
  --glass-text-secondary: #6b7280;
  --glass-text-muted: #9ca3af;
  --glass-bg-secondary: rgba(243, 244, 246, 0.85);
}

[data-theme="night"] {
  --glass-bg: rgba(0, 0, 0, 0.65);
  --glass-text: #e5e7eb;
  /* …dark variants */
}
```

### 7.3 Article Typography

The `.article-content` class defines a complete article排版 system:

- Line height 2.0 for comfortable reading
- Multi-level heading (h2/h3/h4) spacing hierarchy
- Unified styling for blockquotes, code blocks, tables, and images
- List indentation and spacing

### 7.4 Glow Hover Effect

Uses CSS `@property` + `conic-gradient` for card border animation on hover:

```css
@property --p {
  syntax: '<percentage>';
  initial-value: 0%;
  inherits: false;
}

.ring-glow:hover::before {
  --p: 100%;  /* triggers 0.6s transition animation */
}
```

---

## 8. Local Development & Deployment

### 8.1 Requirements

- **Node.js** >= 22.12
- **npm** (included with Node)

### 8.2 Common Commands

```bash
# Start development server
npm run dev          # http://localhost:4321

# Build for production
npm run build        # outputs to dist/

# Preview build locally
npm run preview

# Generate Wrangler types
npm run generate-types
```

### 8.3 Dev Proxy Configuration

Development server has a reverse proxy for music files:

```js
// astro.config.mjs
server: {
  proxy: {
    '/music/audio': {
      target: 'http://127.0.0.1:8765',
      changeOrigin: true,
    }
  }
}
```

### 8.4 Build & Deploy

**Build command**: `npm run build`
**Output directory**: `dist/`

**Deployment flow** (Cloudflare Pages):
1. Push code to GitHub
2. Cloudflare Pages auto-detects repository
3. Executes `npm run build`, outputs to `dist/`
4. Auto-deploys to global edge network
5. Binds custom domain (via Cloudflare DNS)

### 8.5 Configuration Files

| File | Purpose |
|------|---------|
| `astro.config.mjs` | Astro framework config (integrations, Vite, adapter, proxy) |
| `wrangler.jsonc` | Cloudflare Workers config (D1/R2 bindings) |
| `.env` / `.env.production` | Environment variables (gitignored) |
| `tsconfig.json` | TypeScript strict mode config |

---

## 9. Development Roadmap

### Current Status: Phase 1 (Static Blog Scaffold)

Completed milestones:
- [x] Astro 6 project initialization
- [x] Tailwind CSS v4 integration
- [x] Page routing (home, blog, projects, about, etc.)
- [x] Markdown content collections
- [x] Global navigation and layout
- [x] Music player (custom-built)
- [x] Three.js 3D background
- [x] Time-based theme system
- [x] Glassmorphism UI theme
- [x] Cloudflare Pages deployment
- [x] Custom domain binding

### Phase 2 Plan: Dynamic Features

- [ ] Like functionality (D1 database)
- [ ] Search (Pagefind or D1 + Worker)
- [ ] Contact form
- [ ] Tag system improvements

### Phase 3 Plan: Horizontal Expansion

- [ ] Try Next.js rewrite or new project
- [ ] Deep React learning
- [ ] More Cloudflare Workers practice

---

## 10. Lessons Learned

### 10.1 Astro + Tailwind v4 Integration

**Issue**: `npx astro add tailwind` in Astro 6 uses Tailwind v3, but the project needed v4.

**Solution**: Manually integrated via `@tailwindcss/vite` Vite plugin, added to `astro.config.mjs` `vite.plugins`. CSS entry uses `@import "tailwindcss"`.

### 10.2 View Transitions & Component Persistence

**Issue**: Music player needs to maintain playback state uninterrupted when navigating between pages.

**Solution**: Used Astro's `data-astro-transition-persist` attribute on persistent elements (`<audio>` and float container), combined with `localStorage` to save and restore playback state. On each page switch, JS checks `window.__playerReady` to avoid duplicate initialization.

### 10.3 Flash of Unstyled Content (FOUC)

**Issue**: Time-based background color shows a brief white flash on page load.

**Solution**: Used an inline blocking script (`is:inline`) in `<head>` to calculate the current time's background color and set it on `document.documentElement` before the first paint, avoiding FOUC.

### 10.4 Tailwind v4 Night Mode

**Issue**: Tailwind v4 removed the `darkMode: 'class'` configuration option.

**Solution**: Used CSS variables + `data-theme` attribute to manually control themes, rather than relying on Tailwind's `dark:` variant. All colors are referenced through custom properties like `var(--glass-text)`.

### 10.5 Three.js Scene Cross-Page Reuse

**Issue**: Recreating the Three.js scene on every page navigation causes performance issues and flickering.

**Solution**: Persisted the Canvas element via `data-astro-transition-persist="bg3d"`, used `window.__bg3dInitialized` flag to prevent duplicate initialization, and provided a `window.__setSceneBackground` function interface for the scene to respond to theme changes.

### 10.6 Astro 6 + Cloudflare Adapter

**Issue**: The `@astrojs/cloudflare` adapter has specific version requirements in Astro 6.

**Solution**: Locked `@astrojs/cloudflare@^13.7.0` with `astro@^6.3.8`, used `wrangler@^4.100.0` for Cloudflare resource management.

---

## Appendix: Key File Index

| File | Lines | Function |
|------|-------|----------|
| `src/layouts/BaseLayout.astro` | 154 | Global layout (nav, 3D scene, player, FOUC protection, debug panel) |
| `src/components/MusicPlayer.astro` | 682 | Complete music player implementation |
| `src/components/LikeButton.tsx` | - | Preact like component |
| `src/lib/crystalScene.js` | 303 | Three.js 3D crystal scene |
| `src/lib/timeTheme.js` | 118 | Time-based theme switching |
| `src/styles/global.css` | 207 | Global styles + Tailwind v4 entry |
| `src/pages/blog/index.astro` | 119 | Blog category overview |
| `src/pages/index.astro` | 89 | Homepage |
| `astro.config.mjs` | 27 | Astro + Vite + Preact + Cloudflare config |
