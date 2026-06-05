# KirinWiki 📖

> Personal wiki & blog — 记录学习与探索的点滴。

基于 [Astro](https://astro.build) 构建的个人博客与知识维基站点。在这里记录技术探索、折腾笔记，以及一切值得留存的内容。

## ✨ 特性

- 🚀 **Astro 驱动** — 极快的静态生成与 Islands 架构
- 🎨 **Tailwind CSS v4** — 现代化 Utility-First 样式
- ⚡ **Preact 交互** — 轻量级交互组件
- 🗄️ **Cloudflare D1** — 数据库驱动的内容管理
- 🌐 **Cloudflare Workers** — 全球边缘部署

## 🛠 技术栈

| 分类 | 技术 |
|------|------|
| 框架 | [Astro](https://astro.build) |
| 样式 | [Tailwind CSS](https://tailwindcss.com) |
| 交互 | [Preact](https://preactjs.com) |
| 数据库 | [Cloudflare D1](https://developers.cloudflare.com/d1/) |
| 部署 | [Cloudflare Workers](https://workers.cloudflare.com) |

## 🚀 本地开发

```bash
# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:4321）
npm run dev

# 构建生产版本
npm run build

# 本地预览构建结果
npm run preview
```

## 📁 项目结构

```
/
├── public/           # 静态资源
├── src/
│   ├── pages/        # 页面路由
│   ├── components/   # UI 组件
│   └── ...
├── db/               # 数据库相关
├── functions/        # Cloudflare Functions
├── astro.config.mjs  # Astro 配置
├── wrangler.toml     # Cloudflare Workers 配置
└── package.json
```

## 🌐 部署

站点通过 Cloudflare Workers 部署，使用 Wrangler CLI 进行管理：

```bash
npm run build
npx wrangler deploy
```

## 📄 许可证

[MIT](LICENSE)
