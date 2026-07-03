# Online Examination — 在线考试系统项目深度解析

> **项目**: 基于 ASP.NET Core Blazor 的在线考试 Web 应用
> **GitHub**: [BoooSAMA/Online-Examination](https://github.com/BoooSAMA/Online-Examination)
> **框架**: ASP.NET Core 8.0 + Blazor Interactive Server
> **数据库**: SQL Server
> **语言**: C# 12

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [系统架构](#3-系统架构)
4. [数据模型](#4-数据模型)
5. [功能详解](#5-功能详解)
6. [页面路由与权限](#6-页面路由与权限)
7. [核心业务流程](#7-核心业务流程)
8. [数据库迁移历史](#8-数据库迁移历史)
9. [本地开发与部署](#9-本地开发与部署)
10. [安全注意事项](#10-安全注意事项)
11. [面试要点](#11-面试要点)

---

## 1. 项目概述

### 一句话概括

> 基于 ASP.NET Core 8.0 Blazor Interactive Server 的在线考试平台，支持管理员创建和管理考试、学生通过访问码参加考试、自动评分、模拟测试与数据可视化分析。

### 项目背景

这是一个全栈 .NET Web 应用程序，旨在提供一个完整的在线考试解决方案。项目覆盖了从用户认证、角色权限管理、考试 CRUD、题目管理、计时答题、自动评分到数据可视化的全链路功能。

### 核心目标

- 实现**管理员 + 学生**双角色的在线考试平台
- 支持**计时考试**与**自动评分**
- 通过 **Chart.js** 仪表盘实现考试数据可视化
- 集成 ASP.NET Core Identity 实现完整的**用户认证与授权**
- 支持**模拟测试**与**自动生成数学题**

---

## 2. 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| **框架** | ASP.NET Core 8.0 | 跨平台 Web 框架 |
| **UI** | Blazor Interactive Server | 服务端渲染 + SignalR 实时通信 |
| **语言** | C# 12, HTML/Razor, CSS | 全栈 .NET 技术 |
| **数据库** | SQL Server | 关系型数据库 |
| **ORM** | Entity Framework Core 8.0 | 数据访问层 |
| **身份认证** | ASP.NET Core Identity | 基于角色的认证（Admin / Student） |
| **图表** | Chart.js (CDN) | 仪表盘数据可视化 |
| **邮件** | Gmail SMTP | 密码重置邮件发送 |

### NuGet 包

| 包名 | 版本 | 用途 |
|------|------|------|
| `Microsoft.AspNetCore.Identity.EntityFrameworkCore` | 8.0.22 | Identity 数据持久化 |
| `Microsoft.AspNetCore.Identity.UI` | 8.0.22 | Identity UI 脚手架 |
| `Microsoft.EntityFrameworkCore.SqlServer` | 8.0.22 | SQL Server 数据库提供程序 |
| `Microsoft.AspNetCore.Components.QuickGrid.EntityFrameworkAdapter` | 8.0.22 | 数据表格快速网格 |
| `Microsoft.AspNetCore.Diagnostics.EntityFrameworkCore` | 8.0.22 | EF Core 诊断与错误页 |

---

## 3. 系统架构

### 架构分层

```
┌──────────────────────────────────────────────┐
│           Blazor Components（UI 层）          │
│    Pages、Layouts、NavMenu、Razor 组件        │
│    服务端渲染 + SignalR 实时双向通信           │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│          Controllers（REST API 层）           │
│    POST /api/login — 用户登录                 │
│    POST /api/auth/forgot-password — 忘记密码  │
│    POST /api/auth/reset-password — 重置密码   │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│            Services（业务逻辑层）              │
│  ExamService          — 考试 CRUD 与评分      │
│  StudentService       — 学生注册、登录、答题   │
│  UserSession          — 用户会话管理          │
│  GmailEmailSender     — 邮件发送              │
│  LocalMathGenerator   — 数学题自动生成         │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│        Data / Entity Framework Core（数据层）  │
│  Online_ExaminationContext — DbContext        │
│  DatabaseSeeder — 种子数据（默认账号）         │
│  Migrations — 数据库迁移历史                   │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│               SQL Server 数据库               │
└──────────────────────────────────────────────┘
```

### Blazor Interactive Server 模式

本项目采用 **Blazor Interactive Server** 渲染模式，这意味着：

- **UI 逻辑在服务端执行**：C# 代码在服务器上运行，DOM 更新通过 SignalR 实时推送到浏览器
- **无需 WebAssembly 下载**：首次加载快，不需要下载 .NET 运行时
- **实时双向通信**：用户操作通过 SignalR 连接发送到服务端，服务端处理后推回 UI 更新
- **与 ASP.NET Core 无缝集成**：可以直接使用服务端中间件、认证、EF Core 等

### 项目结构

```
Online-Examination/
├── Online Examination.slnx                    # 解决方案文件
├── README.md                                  # 英文 README
├── README_CN.md                               # 中文 README
├── LICENSE                                    # MIT 许可证
│
└── Online Examination/                        # 主项目目录
    ├── Program.cs                             # 入口点、DI 注册、中间件管道
    ├── appsettings.json                       # 应用配置（连接字符串等）
    ├── appsettings.Development.json           # 开发环境配置
    ├── Online Examination.csproj              # 项目文件
    ├── Scaffolding-README.md                  # Identity 脚手架说明
    │
    ├── Domain/                                # 领域实体模型
    │   ├── BaseDomainModel.cs                 # 抽象基类（Id, 时间戳, 审计字段）
    │   ├── Exam.cs                            # 考试实体
    │   ├── Question.cs                        # 题目实体
    │   ├── Attempt.cs                         # 答题记录实体
    │   └── Online_ExaminationUser.cs          # 用户实体（继承 IdentityUser）
    │
    ├── Data/                                  # 数据访问层
    │   ├── Online_ExaminationContext.cs       # EF Core DbContext
    │   └── DatabaseSeeder.cs                  # 数据库种子数据初始化
    │
    ├── Migrations/                            # EF Core 迁移文件
    │   ├── 20260116000000_InitialCreate.cs
    │   ├── 20260118000000_AddAccessCodeToExam.cs
    │   ├── 20260118000001_AddEducationLevelToExam.cs
    │   ├── 20260121000000_AddExamSubject.cs
    │   └── 20260121000001_AddJCLevel.cs
    │
    ├── Controllers/                           # REST API 控制器
    │   ├── LoginController.cs                 # 登录 API
    │   └── AuthController.cs                  # 认证 API（忘记/重置密码）
    │
    ├── Services/                              # 业务逻辑服务
    │   ├── ExamService.cs                     # 考试管理、自动评分
    │   ├── StudentService.cs                  # 学生注册、登录、答题、历史
    │   ├── UserSession.cs                     # 用户会话状态管理
    │   ├── GmailEmailSender.cs                # Gmail SMTP 邮件发送
    │   └── QuestionGenerators/
    │       └── LocalMathGenerator.cs          # 数学题程序化生成器
    │
    ├── Configuration/                         # 配置类
    │
    ├── Components/                            # Blazor 组件（UI 层）
    │   ├── Layout/
    │   │   ├── MainLayout.razor               # 主布局
    │   │   └── NavMenu.razor                  # 导航菜单（基于角色）
    │   ├── Pages/
    │   │   ├── Home.razor                     # 首页
    │   │   ├── Login.razor                    # 登录
    │   │   ├── Register.razor                 # 注册
    │   │   ├── AdminDashboard.razor           # 管理员仪表盘（Chart.js）
    │   │   ├── UserDashboard.razor            # 学生仪表盘
    │   │   ├── ExamCreate.razor               # 创建考试
    │   │   ├── ExamPage.razor                 # 考试答题界面
    │   │   ├── ExamResult.razor               # 考试结果
    │   │   ├── JoinExam.razor                 # 加入考试
    │   │   ├── ExamHistory.razor              # 考试历史
    │   │   ├── ExamIndex.razor                # 考试列表管理
    │   │   ├── ModifyStudents.razor           # 学生管理
    │   │   ├── ModifyExam.razor               # 编辑考试
    │   │   ├── GlobalHistory.razor            # 全局答题历史
    │   │   ├── Payment.razor                  # 支付页面
    │   │   └── MockTest.razor                 # 模拟测试
    │   └── Account/                           # Identity 脚手架页面
    │       ├── Login.razor                    # Identity 登录
    │       ├── Register.razor                 # Identity 注册
    │       ├── ForgotPassword.razor           # 忘记密码
    │       └── ResetPassword.razor            # 重置密码
    │
    ├── Properties/                            # 启动配置
    │   └── launchSettings.json                # 开发服务器配置
    │
    └── wwwroot/                               # 静态资源
        ├── app.css                           # 应用主样式
        ├── css/
        │   ├── exams-page.css                # 考试页专用样式
        │   ├── indexstyle.css                # 首页样式
        │   └── site.css                      # 站点全局样式
        └── pics/                             # 图片资源
```

---

## 4. 数据模型

### 实体关系图

```
Online_ExaminationUser (继承 IdentityUser)
│  • Email, PasswordHash, UserName, ...
│  • Role: Admin | Student
│
├── CreatedExams (1:N) ──→ Exam
│       │
│       ├── Id (PK, Guid)
│       ├── Title — 考试标题
│       ├── Description — 考试描述
│       ├── TimeLimit — 限时（1–180 分钟）
│       ├── AccessCode — 唯一 8 位访问码
│       ├── EducationLevel — 学段（PSLE / N / O / Poly / JC）
│       ├── Subject — 科目
│       ├── IsPublished — 是否发布
│       ├── CreatedById (FK → Online_ExaminationUser)
│       │
│       ├── Questions (1:N) ──→ Question
│       │     • Id (PK, Guid)
│       │     • ExamId (FK)
│       │     • Text — 题目文本
│       │     • OptionA / OptionB / OptionC / OptionD — 四个选项
│       │     • CorrectAnswer — 正确答案（A/B/C/D）
│       │     • ImageUrl (可选) — 题目图片链接
│       │     • ReadingPassage (可选) — 阅读材料
│       │     • Order — 题目序号
│       │
│       └── Attempts (1:N) ──→ Attempt
│             • Id (PK, Guid)
│             • ExamId (FK)
│             • UserId (FK → Online_ExaminationUser)
│             • Score — 得分
│             • TotalQuestions — 总题数
│             • StartedAt — 开始时间
│             • CompletedAt — 完成时间
│             • Answers (JSON) — 答题明细
│
└── Attempts (1:N)
      （同上）
```

### BaseDomainModel（抽象基类）

所有实体继承自 `BaseDomainModel`，提供统一的审计字段：

```csharp
public abstract class BaseDomainModel
{
    public Guid Id { get; set; }
    public DateTime DateCreated { get; set; }
    public DateTime? DateUpdated { get; set; }
    public string CreatedBy { get; set; } = string.Empty;
    public string? UpdatedBy { get; set; }
}
```

---

## 5. 功能详解

### 5.1 管理员端

#### 仪表盘（AdminDashboard）

使用 **Chart.js** 实现的数据可视化面板：

- **柱状图**：各科目考试数量统计
- **折线图**：每日参考人数趋势
- **饼图**：通过率分布

数据来源：`ExamService.GetStatistics()` → EF Core 查询 SQL Server → JSON 序列化 → Chart.js `data` 配置。通过 Blazor JS Interop（`IJSRuntime.InvokeVoidAsync`）将数据传递给 Chart.js 渲染。

#### 考试管理（Exam CRUD）

| 功能 | 说明 |
|------|------|
| **创建考试** | 设置标题、描述、限时（1–180分钟）、访问码、学段、科目 |
| **编辑考试** | 修改考试基本信息、题目列表 |
| **管理题目** | 单选题，4 个选项（A–D），标记正确答案 |
| **题目附加** | 可选：图片上传（ImageUrl）、阅读材料（ReadingPassage） |
| **发布控制** | 设置考试状态（已发布/草稿） |

#### 学生管理

- 查看已注册学生列表
- 编辑学生信息
- 删除学生账号
- 使用 `QuickGrid` 组件实现高效的数据表格展示

#### 全局历史

- 查看所有学生在所有考试中的答题记录
- 按考试、学生、时间段筛选
- 展示得分、用时、完成状态

#### 自动评分

学生提交答卷后系统即时计算得分：

```
得分 = (正确答案数 / 总题数) × 100
```

评分逻辑在 `ExamService` 中实现，提交后立即返回结果页面。

### 5.2 学生端

#### 加入考试

- 通过管理员提供的 **8 位唯一访问码** 加入考试
- 验证访问码有效性 → 加载对应考试
- 在 `JoinExam.razor` 页面输入访问码后跳转到考试页

#### 参加考试

- **计时界面**：显示剩余时间，超时自动提交
- **浏览模式**：支持逐题切换或全页展示
- **答题交互**：点击选项选择答案
- **提交确认**：提交前二次确认，防止误操作

#### 考试历史

- 查看自己参加过的所有考试记录
- 显示得分、完成时间、排名（如有）

#### 模拟测试

- 按学段分类的模拟练习（PSLE / N-Level / O-Level / Poly / JC）
- 可反复练习，不记录正式成绩
- 自动生成题目，每次练习题目不同

#### 自动生成数学题

`LocalMathGenerator.cs` 实现程序化数学题生成：

| 难度 | 说明 | 示例 |
|------|------|------|
| **Easy（简单）** | 整数加减法，结果在 100 以内 | `23 + 45 = ?` |
| **Medium（中等）** | 整数加减乘除，含两位小数 | `12.5 × 3 = ?` |
| **Hard（困难）** | 多步运算，含括号与分数 | `(15 + 3) × (8 - 2) ÷ 4 = ?` |
| **Expert（专家）** | 复杂代数/几何问题 | 解方程、面积计算等 |

生成器确保：
- 每次生成不重复的题目
- 结果在规定范围内（避免过大/过小）
- 提供正确答案用于自动评分

### 5.3 通用功能

#### 基于角色的导航

`NavMenu.razor` 根据用户角色动态显示菜单：

```razor
@if (user.IsInRole("Admin"))
{
    <NavLink href="admin-dashboard">管理仪表盘</NavLink>
    <NavLink href="exam-index">考试管理</NavLink>
    <NavLink href="modify-students">学生管理</NavLink>
}

@if (user.IsInRole("Student"))
{
    <NavLink href="user-dashboard">我的仪表盘</NavLink>
    <NavLink href="student/join-exam">加入考试</NavLink>
    <NavLink href="exam-history">考试历史</NavLink>
}
```

#### 注册与登录

- 标准邮箱/密码注册
- 支持邮箱验证（可选启用）
- 通过 ASP.NET Core Identity 实现密码哈希存储

#### 忘记/重置密码

流程：用户输入注册邮箱 → 系统发送含重置链接的邮件（通过 Gmail SMTP）→ 用户点击链接设置新密码 → 密码更新成功。

---

## 6. 页面路由与权限

### 完整路由表

| 路由 | 组件 | 权限 | 说明 |
|------|------|------|------|
| `/` | `Home.razor` | 公开 | 首页 |
| `/about` | `About.razor` | 公开 | 关于我们 |
| `/Account/Login` | `Login.razor` | 公开 | 登录 |
| `/Account/Register` | `Register.razor` | 公开 | 注册 |
| `/forgot-password` | `ForgotPassword.razor` | 公开 | 忘记密码 |
| `/admin-dashboard` | `AdminDashboard.razor` | Admin | 管理仪表盘 |
| `/admin/exam-create` | `ExamCreate.razor` | Admin | 创建考试 |
| `/exam-index` | `ExamIndex.razor` | Admin | 考试列表管理 |
| `/modify-students` | `ModifyStudents.razor` | Admin | 学生管理 |
| `/modify-exam/{id}` | `ModifyExam.razor` | Admin | 编辑考试 |
| `/admin/global-history` | `GlobalHistory.razor` | Admin | 全局历史 |
| `/user-dashboard` | `UserDashboard.razor` | Student | 学生仪表盘 |
| `/student/join-exam` | `JoinExam.razor` | Student | 加入考试 |
| `/exams` | `Exams.razor` | Student | 可用考试列表 |
| `/take-exam/{id}` | `ExamPage.razor` | Student | 参加考试 |
| `/exam-history` | `ExamHistory.razor` | Student | 我的历史 |
| `/exam-result/{id}` | `ExamResult.razor` | 两者 | 查看结果 |
| `/payment` | `Payment.razor` | Student | 支付页 |
| `/mock-test/{level}` | `MockTest.razor` | Student | 模拟测试 |

### API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/login` | 用户登录 |
| POST | `/api/auth/forgot-password` | 发送密码重置邮件 |
| POST | `/api/auth/reset-password` | 使用令牌重置密码 |

---

## 7. 核心业务流程

### 7.1 考试完整生命周期

```
[管理员创建考试]
    │  设置标题、题目、限时、访问码
    ▼
[考试发布]
    │  学生可通过访问码看到考试
    ▼
[学生加入考试]
    │  输入 8 位访问码 → 验证通过 → 进入考试页
    ▼
[学生答题]
    │  计时器开始倒计时
    │  逐题作答 / 全页浏览
    ▼
[提交答卷] ← 超时自动提交
    │
    ├── [自动评分] → 返回成绩页面
    │   ExamService.CalculateScore()
    │
    └── [记录存储]
        Attempt 表写入得分 + 答题明细
    ▼
[查看结果]
    学生 → 个人历史
    管理员 → 全局历史
```

### 7.2 用户注册流程

```
[用户访问 /Account/Register]
    │
    ▼
[填写注册信息]（邮箱、密码、角色选择）
    │
    ▼
[ASP.NET Core Identity 验证]
    │  • 邮箱格式验证
    │  • 密码强度验证
    │  • 邮箱唯一性检查
    │
    ▼
[创建用户]
    │  UserManager.CreateAsync()
    │  密码自动哈希存储
    ▼
[分配角色]
    │  UserManager.AddToRoleAsync(user, "Student")
    ▼
[注册成功 → 跳转登录页]
```

### 7.3 密码重置流程

```
[用户请求重置密码]
    │
    ▼
[输入注册邮箱]
    │
    ▼
[Gmail SMTP 发送重置邮件]
    │  GmailEmailSender.SendEmailAsync()
    │  邮件包含带 token 的重置链接
    ▼
[用户点击链接 → 重置密码页]
    │
    ▼
[输入新密码]
    │  UserManager.ResetPasswordAsync()
    ▼
[密码更新成功 → 跳转登录]
```

---

## 8. 数据库迁移历史

| 迁移名称 | 日期 | 变更内容 |
|---------|------|---------|
| `InitialCreate` | 2026-01-16 | 创建基础表结构（User、Exam、Question、Attempt） |
| `AddAccessCodeToExam` | 2026-01-18 | 为 Exam 表添加 AccessCode 字段（唯一访问码） |
| `AddEducationLevelToExam` | 2026-01-18 | 添加 EducationLevel 字段（学段分类） |
| `AddExamSubject` | 2026-01-21 | 添加 Subject 字段（科目分类） |
| `AddJCLevel` | 2026-01-21 | 添加 JC（Junior College）学段支持 |

迁移命令：

```bash
# 创建迁移
dotnet ef migrations add MigrationName

# 应用到数据库
dotnet ef database update

# 回滚迁移
dotnet ef database update PreviousMigrationName
```

---

## 9. 本地开发与部署

### 9.1 环境要求

- [.NET 8.0 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- [SQL Server](https://www.microsoft.com/sql-server)（LocalDB、Express 或 Developer 版均可）
- [Visual Studio 2022](https://visualstudio.microsoft.com/)（推荐）或 VS Code / Rider

### 9.2 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/BoooSAMA/Online-Examination.git
cd Online-Examination

# 2. 配置数据库连接字符串
# 编辑 Online Examination/appsettings.json

# 3. 配置 Gmail SMTP
# 编辑 Online Examination/Services/GmailEmailSender.cs

# 4. 运行数据库迁移
cd "Online Examination"
dotnet ef database update

# 5. 启动应用
dotnet run
# 或 Visual Studio 中按 F5
```

应用默认在 `https://localhost:5001` 启动（端口以 `launchSettings.json` 为准）。

### 9.3 默认账号

首次运行时，`DatabaseSeeder.cs` 自动创建测试账号：

| 角色 | 邮箱 | 密码 |
|------|------|------|
| **管理员** | `admin@test.com` | `Admin123` |
| **学生** | `student@test.com` | `Student123` |

### 9.4 appsettings.json 配置

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=YOUR_SERVER;Database=OnlineExaminationDB;Trusted_Connection=True;TrustServerCertificate=True;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*"
}
```

---

## 10. 安全注意事项

### 已知安全事项

| 问题 | 说明 | 建议 |
|------|------|------|
| **邮件凭据硬编码** | `GmailEmailSender.cs` 中邮箱和 App Password 直接写在源码里 | 生产环境移至环境变量、Azure Key Vault 或 User Secrets |
| **密码策略宽松** | 开发阶段密码要求较低（最小长度可能不足） | 生产环境中在 `Program.cs` 加强 `PasswordOptions` 配置 |
| **CSRF 防护豁免** | LoginController 使用了 `[IgnoreAntiforgeryToken]` | 评估部署是否需要此标记，尽量启用防伪标记 |
| **连接字符串明文** | `appsettings.json` 中的数据库连接字符串包含凭据 | 使用 User Secrets（开发）或 Azure Key Vault（生产） |

### 生产环境强化建议

```csharp
// Program.cs — 加强密码策略
builder.Services.AddIdentity<Online_ExaminationUser, IdentityRole>(options =>
{
    // 密码策略
    options.Password.RequiredLength = 8;
    options.Password.RequireDigit = true;
    options.Password.RequireLowercase = true;
    options.Password.RequireUppercase = true;
    options.Password.RequireNonAlphanumeric = true;
    
    // 锁定策略
    options.Lockout.MaxFailedAccessAttempts = 5;
    options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(15);
    
    // 邮箱确认
    options.SignIn.RequireConfirmedEmail = true;
})
.AddEntityFrameworkStores<Online_ExaminationContext>();
```

---

## 11. 面试要点

### 11.1 项目亮点

| 亮点 | 说明 |
|------|------|
| **全栈 .NET** | 从数据库设计到前端 UI 全链路使用 .NET 技术栈 |
| **Blazor Interactive Server** | 使用 SignalR 实现实时 UI 更新，理解服务端渲染 vs 客户端渲染的取舍 |
| **角色权限系统** | ASP.NET Core Identity 的 Role-Based 授权实践 |
| **自动评分引擎** | 提交即评分的即时反馈机制 |
| **Chart.js 数据可视化** | 通过 JS Interop 在 Blazor 中集成第三方 JavaScript 图表库 |
| **程序化题目生成** | 数学题自动生成器，4 级难度体系 |

### 11.2 技术问答准备

#### Q: 为什么选择 Blazor Interactive Server 而不是 Blazor WebAssembly？

> 选择 Interactive Server 的原因：
> 1. **首次加载快** — 不需要下载 .NET 运行时（~2MB），WASM 模式首屏加载会慢很多
> 2. **开发效率高** — 可以直接使用服务端资源（EF Core、SMTP），不需要额外写 API
> 3. **实时性好** — SignalR 连接实现即时 UI 更新，适合考试计时的实时场景
> 4. **内存占用低** — 服务端渲染，客户端只是瘦浏览器端
>
> 缺点是服务器需要维护 SignalR 连接，扩展时需要有状态的路由（sticky session）。如果有大规模并发需求，可以考虑迁移到 Blazor WebAssembly + 独立的 Web API 后端。

#### Q: 考试计时是怎么实现的？

> 计时逻辑在 `ExamPage.razor` 中实现：
> 1. 考试开始时记录 `StartedAt` 时间戳
> 2. 客户端通过 SignalR 连接定期同步剩余时间
> 3. 前端显示倒计时，每秒更新
> 4. 超时后自动触发表单提交
> 5. 提交时验证时间有效性——防止客户端篡改时间

#### Q: 自动评分怎么处理主观题？

> 当前系统只支持**单选题**（A–D 四选一），评分逻辑是直接比对答案：
> ```csharp
> score = (correctCount / totalQuestions) * 100;
> ```
> 如果要支持主观题/简答题，可以引入：
> - 关键词匹配评分
> - 人工阅卷队列（管理员逐一评分）
> - AI 辅助评分（调用 LLM API）
>
> 但当前版本专注于选择题的自动评分，确保评分的绝对公平和即时性。

#### Q: 访问码的设计意图是什么？

> 8 位唯一访问码解决了几个问题：
> 1. **无需预先分配账号** — 学生不需要提前在系统中注册才能参加某个考试
> 2. **线下分发方便** — 老师可以在课堂上口头告知或写在黑板上
> 3. **考试隔离** — 每个考试独立访问码，不会进错考场
> 4. **防滥用** — 访问码可以控制谁有资格参加某个考试
>
> 实现上，访问码在创建考试时由系统自动生成（`Guid` 取前 8 位或随机字符串），并确保唯一性。

### 11.3 与 KirinWiki Blog（Astro）的技术对比

| 维度 | Online Examination | KirinWiki Blog |
|------|-------------------|----------------|
| **框架** | ASP.NET Core 8.0 + Blazor | Astro 6 |
| **语言** | C# 12 + Razor | TypeScript + Astro |
| **渲染** | 服务端实时渲染（SignalR） | 静态生成（SSG） |
| **数据库** | SQL Server + EF Core | Cloudflare D1 |
| **部署** | IIS / Azure / 自托管 | Cloudflare Pages |
| **前端交互** | SignalR 实时通信 | Preact Islands |
| **适用场景** | 动态交互型 Web 应用 | 内容型静态站点 |

---

## 附录：关键文件索引

| 文件 | 用途 |
|------|------|
| `Program.cs` | 应用入口、DI 容器、中间件管道 |
| `Domain/Exam.cs` | 考试实体定义 |
| `Domain/Question.cs` | 题目实体定义 |
| `Domain/Attempt.cs` | 答题记录实体 |
| `Data/Online_ExaminationContext.cs` | EF Core 数据库上下文 |
| `Data/DatabaseSeeder.cs` | 种子数据初始化 |
| `Services/ExamService.cs` | 考试 CRUD + 自动评分 |
| `Services/StudentService.cs` | 学生服务（注册、答题、历史） |
| `Services/GmailEmailSender.cs` | 邮件发送 |
| `Services/QuestionGenerators/LocalMathGenerator.cs` | 数学题自动生成 |
| `Controllers/LoginController.cs` | 登录 API |
| `Controllers/AuthController.cs` | 认证 API |
| `Components/Pages/AdminDashboard.razor` | 管理员仪表盘（Chart.js） |
| `Components/Pages/ExamPage.razor` | 考试答题页 |
| `Components/Pages/ExamResult.razor` | 考试结果页 |
