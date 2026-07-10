---
title: "Online Examination — Project Deep Dive"
date: "2026-07-03"
description: "An online examination platform built with ASP.NET Core 8.0 + Blazor Interactive Server, supporting admin exam creation and management, student participation via access codes, automatic grading, Chart.js data visualization, and mock tests."
tags: ["ASP.NET Core", "Blazor", "C#", "SQL Server", "Entity Framework Core", "Chart.js"]
---

# Online Examination — Project Deep Dive

> **Project**: ASP.NET Core Blazor online examination web application
> **GitHub**: [BoooSAMA/Online-Examination](https://github.com/BoooSAMA/Online-Examination)
> **Framework**: ASP.NET Core 8.0 + Blazor Interactive Server
> **Database**: SQL Server
> **Language**: C# 12

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [System Architecture](#3-system-architecture)
4. [Data Model](#4-data-model)
5. [Feature Details](#5-feature-details)
6. [Page Routes & Permissions](#6-page-routes--permissions)
7. [Core Business Processes](#7-core-business-processes)
8. [Database Migration History](#8-database-migration-history)
9. [Local Development & Deployment](#9-local-development--deployment)
10. [Security Considerations](#10-security-considerations)
11. [Interview Points](#11-interview-points)

---

## 1. Project Overview

### One-Sentence Summary

> An online examination platform built with ASP.NET Core 8.0 Blazor Interactive Server, supporting admin exam creation and management, student participation via access codes, automatic grading, mock tests, and data visualization analysis.

### Project Background

This is a full-stack .NET web application providing a complete online examination solution. The project covers the full chain from user authentication, role-based permissions, exam CRUD, question management, timed答题, automatic grading, to data visualization.

### Core Goals

- Implement a **dual-role** (Admin + Student) online examination platform
- Support **timed exams** and **automatic grading**
- Enable exam data visualization via **Chart.js** dashboards
- Integrate ASP.NET Core Identity for complete **user authentication and authorization**
- Support **mock tests** and **auto-generated math questions**

---

## 2. Tech Stack

| Category | Technology | Description |
|----------|-----------|-------------|
| **Framework** | ASP.NET Core 8.0 | Cross-platform web framework |
| **UI** | Blazor Interactive Server | Server-side rendering + SignalR real-time communication |
| **Language** | C# 12, HTML/Razor, CSS | Full-stack .NET |
| **Database** | SQL Server | Relational database |
| **ORM** | Entity Framework Core 8.0 | Data access layer |
| **Authentication** | ASP.NET Core Identity | Role-based auth (Admin / Student) |
| **Charts** | Chart.js (CDN) | Dashboard data visualization |
| **Email** | Gmail SMTP | Password reset email delivery |

### NuGet Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `Microsoft.AspNetCore.Identity.EntityFrameworkCore` | 8.0.22 | Identity data persistence |
| `Microsoft.AspNetCore.Identity.UI` | 8.0.22 | Identity UI scaffolding |
| `Microsoft.EntityFrameworkCore.SqlServer` | 8.0.22 | SQL Server database provider |
| `Microsoft.AspNetCore.Components.QuickGrid.EntityFrameworkAdapter` | 8.0.22 | Data table quick grid |
| `Microsoft.AspNetCore.Diagnostics.EntityFrameworkCore` | 8.0.22 | EF Core diagnostics & error pages |

---

## 3. System Architecture

### Architecture Layers

```
┌──────────────────────────────────────────────┐
│           Blazor Components（UI Layer）        │
│    Pages, Layouts, NavMenu, Razor Components  │
│    Server-side rendering + SignalR real-time   │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│          Controllers (REST API Layer)         │
│    POST /api/login — User login               │
│    POST /api/auth/forgot-password — Forgot PW │
│    POST /api/auth/reset-password — Reset PW   │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│            Services (Business Logic Layer)     │
│  ExamService          — Exam CRUD & grading   │
│  StudentService       — Student registration,  │
│                         login, answering       │
│  UserSession          — User session mgmt     │
│  GmailEmailSender     — Email sending         │
│  LocalMathGenerator   — Math question generator │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│        Data / Entity Framework Core            │
│  Online_ExaminationContext — DbContext         │
│  DatabaseSeeder — Seed data (default accounts) │
│  Migrations — Database migration history       │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│               SQL Server Database              │
└──────────────────────────────────────────────┘
```

### Blazor Interactive Server Mode

This project uses **Blazor Interactive Server** rendering mode:

- **UI logic runs on the server**: C# code executes on the server, DOM updates pushed to the browser via SignalR in real time
- **No WebAssembly download**: Fast initial load, no .NET runtime download needed
- **Real-time bidirectional communication**: User actions sent to the server via SignalR, server processes and pushes UI updates back
- **Seamless ASP.NET Core integration**: Can directly use server-side middleware, authentication, EF Core, etc.

### Project Structure

```
Online-Examination/
├── Online Examination.slnx                    # Solution file
├── README.md                                  # English README
├── README_CN.md                               # Chinese README
├── LICENSE                                    # MIT License
│
└── Online Examination/                        # Main project directory
    ├── Program.cs                             # Entry point, DI registration, middleware pipeline
    ├── appsettings.json                       # App config (connection strings, etc.)
    ├── appsettings.Development.json           # Development environment config
    ├── Online Examination.csproj              # Project file
    ├── Scaffolding-README.md                  # Identity scaffolding notes
    │
    ├── Domain/                                # Domain entity models
    │   ├── BaseDomainModel.cs                 # Abstract base (Id, timestamps, audit fields)
    │   ├── Exam.cs                            # Exam entity
    │   ├── Question.cs                        # Question entity
    │   ├── Attempt.cs                         # Attempt record entity
    │   └── Online_ExaminationUser.cs          # User entity (inherits IdentityUser)
    │
    ├── Data/                                  # Data access layer
    │   ├── Online_ExaminationContext.cs       # EF Core DbContext
    │   └── DatabaseSeeder.cs                  # Database seed data initialization
    │
    ├── Migrations/                            # EF Core migration files
    │   ├── 20260116000000_InitialCreate.cs
    │   ├── 20260118000000_AddAccessCodeToExam.cs
    │   ├── 20260118000001_AddEducationLevelToExam.cs
    │   ├── 20260121000000_AddExamSubject.cs
    │   └── 20260121000001_AddJCLevel.cs
    │
    ├── Controllers/                           # REST API controllers
    │   ├── LoginController.cs                 # Login API
    │   └── AuthController.cs                  # Auth API (forgot/reset password)
    │
    ├── Services/                              # Business logic services
    │   ├── ExamService.cs                     # Exam management, auto-grading
    │   ├── StudentService.cs                  # Student registration, login,答题, history
    │   ├── UserSession.cs                     # User session state management
    │   ├── GmailEmailSender.cs                # Gmail SMTP email sending
    │   └── QuestionGenerators/
    │       └── LocalMathGenerator.cs          # Programmatic math question generator
    │
    ├── Configuration/                         # Configuration classes
    │
    ├── Components/                            # Blazor components (UI layer)
    │   ├── Layout/
    │   │   ├── MainLayout.razor               # Main layout
    │   │   └── NavMenu.razor                  # Navigation menu (role-based)
    │   ├── Pages/
    │   │   ├── Home.razor                     # Homepage
    │   │   ├── Login.razor                    # Login
    │   │   ├── Register.razor                 # Registration
    │   │   ├── AdminDashboard.razor           # Admin dashboard (Chart.js)
    │   │   ├── UserDashboard.razor            # Student dashboard
    │   │   ├── ExamCreate.razor               # Create exam
    │   │   ├── ExamPage.razor                 # Exam答题 interface
    │   │   ├── ExamResult.razor               # Exam results
    │   │   ├── JoinExam.razor                 # Join exam
    │   │   ├── ExamHistory.razor              # Exam history
    │   │   ├── ExamIndex.razor                # Exam list management
    │   │   ├── ModifyStudents.razor           # Student management
    │   │   ├── ModifyExam.razor               # Edit exam
    │   │   ├── GlobalHistory.razor            # Global answer history
    │   │   ├── Payment.razor                  # Payment page
    │   │   └── MockTest.razor                 # Mock test
    │   └── Account/                           # Identity scaffold pages
    │       ├── Login.razor                    # Identity login
    │       ├── Register.razor                 # Identity registration
    │       ├── ForgotPassword.razor           # Forgot password
    │       └── ResetPassword.razor            # Reset password
    │
    ├── Properties/                            # Launch configuration
    │   └── launchSettings.json                # Dev server configuration
    │
    └── wwwroot/                               # Static resources
        ├── app.css                           # Main application styles
        ├── css/
        │   ├── exams-page.css                # Exam page styles
        │   ├── indexstyle.css                # Homepage styles
        │   └── site.css                      # Global site styles
        └── pics/                             # Image resources
```

---

## 4. Data Model

### Entity Relationship Diagram

```
Online_ExaminationUser (inherits IdentityUser)
│  • Email, PasswordHash, UserName, ...
│  • Role: Admin | Student
│
├── CreatedExams (1:N) ──→ Exam
│       │
│       ├── Id (PK, Guid)
│       ├── Title
│       ├── Description
│       ├── TimeLimit (1–180 minutes)
│       ├── AccessCode (unique 8-digit code)
│       ├── EducationLevel (PSLE / N / O / Poly / JC)
│       ├── Subject
│       ├── IsPublished
│       ├── CreatedById (FK → Online_ExaminationUser)
│       │
│       ├── Questions (1:N) ──→ Question
│       │     • Id (PK, Guid)
│       │     • ExamId (FK)
│       │     • Text
│       │     • OptionA / OptionB / OptionC / OptionD
│       │     • CorrectAnswer (A/B/C/D)
│       │     • ImageUrl (optional)
│       │     • ReadingPassage (optional)
│       │     • Order
│       │
│       └── Attempts (1:N) ──→ Attempt
│             • Id (PK, Guid)
│             • ExamId (FK)
│             • UserId (FK → Online_ExaminationUser)
│             • Score
│             • TotalQuestions
│             • StartedAt
│             • CompletedAt
│             • Answers (JSON)
│
└── Attempts (1:N)
      (same as above)
```

### BaseDomainModel (Abstract Base Class)

All entities inherit from `BaseDomainModel`, providing uniform audit fields:

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

## 5. Feature Details

### 5.1 Admin Side

#### Dashboard (AdminDashboard)

Data visualization panel using **Chart.js**:

- **Bar chart**: Exam count by subject
- **Line chart**: Daily exam-taker trends
- **Pie chart**: Pass rate distribution

Data source: `ExamService.GetStatistics()` → EF Core query SQL Server → JSON serialization → Chart.js `data` config. Passed to Chart.js rendering via Blazor JS Interop (`IJSRuntime.InvokeVoidAsync`).

#### Exam Management (Exam CRUD)

| Feature | Description |
|---------|-------------|
| **Create exam** | Set title, description, time limit (1–180 min), access code, education level, subject |
| **Edit exam** | Modify basic info, question list |
| **Manage questions** | Multiple choice, 4 options (A–D), mark correct answer |
| **Question extras** | Optional: image upload (ImageUrl), reading passage (ReadingPassage) |
| **Publish control** | Set exam status (published/draft) |

#### Student Management

- View registered student list
- Edit student info
- Delete student accounts
- Uses `QuickGrid` component for efficient data table display

#### Global History

- View all students' answer records across exams
- Filter by exam, student, time period
- Display score, time taken, completion status

#### Automatic Grading

Instant score calculation after student submission:

```
Score = (correct answers / total questions) × 100
```

Grading logic implemented in `ExamService`, returns result page immediately after submission.

### 5.2 Student Side

#### Join Exam

- Join exam via admin-provided **8-digit unique access code**
- Validate access code → load corresponding exam
- Enter access code in `JoinExam.razor` page, then navigate to exam page

#### Take Exam

- **Timed interface**: Shows remaining time, auto-submits on timeout
- **Navigation mode**: Single question or full-page display
- **Answer interaction**: Click options to select answer
- **Submit confirmation**: Double confirmation before submission

#### Exam History

- View all past exam records
- Display score, completion time, ranking (if available)

#### Mock Tests

- Mock practice by education level (PSLE / N-Level / O-Level / Poly / JC)
- Repeatable practice, no formal score recorded
- Auto-generates questions, different each time

#### Auto-Generated Math Questions

`LocalMathGenerator.cs` implements programmatic math question generation:

| Difficulty | Description | Example |
|------------|-------------|---------|
| **Easy** | Integer addition/subtraction, result within 100 | `23 + 45 = ?` |
| **Medium** | Integer加减乘除, includes 2 decimal places | `12.5 × 3 = ?` |
| **Hard** | Multi-step operations with parentheses and fractions | `(15 + 3) × (8 - 2) ÷ 4 = ?` |
| **Expert** | Complex algebra/geometry problems | Equation solving, area calculation, etc. |

The generator ensures:
- Non-repeating questions each time
- Results within specified range
- Correct answer provided for auto-grading

### 5.3 General Features

#### Role-Based Navigation

`NavMenu.razor` dynamically displays menu based on user role:

```razor
@if (user.IsInRole("Admin"))
{
    <NavLink href="admin-dashboard">Admin Dashboard</NavLink>
    <NavLink href="exam-index">Exam Management</NavLink>
    <NavLink href="modify-students">Student Management</NavLink>
}

@if (user.IsInRole("Student"))
{
    <NavLink href="user-dashboard">My Dashboard</NavLink>
    <NavLink href="student/join-exam">Join Exam</NavLink>
    <NavLink href="exam-history">Exam History</NavLink>
}
```

#### Registration & Login

- Standard email/password registration
- Optional email verification
- Password hashing via ASP.NET Core Identity

#### Forgot/Reset Password

Flow: User enters registered email → System sends reset link via email (Gmail SMTP) → User clicks link to set new password → Password updated.

---

## 6. Page Routes & Permissions

### Complete Route Table

| Route | Component | Permission | Description |
|-------|-----------|------------|-------------|
| `/` | `Home.razor` | Public | Homepage |
| `/about` | `About.razor` | Public | About us |
| `/Account/Login` | `Login.razor` | Public | Login |
| `/Account/Register` | `Register.razor` | Public | Register |
| `/forgot-password` | `ForgotPassword.razor` | Public | Forgot password |
| `/admin-dashboard` | `AdminDashboard.razor` | Admin | Admin dashboard |
| `/admin/exam-create` | `ExamCreate.razor` | Admin | Create exam |
| `/exam-index` | `ExamIndex.razor` | Admin | Exam list management |
| `/modify-students` | `ModifyStudents.razor` | Admin | Student management |
| `/modify-exam/{id}` | `ModifyExam.razor` | Admin | Edit exam |
| `/admin/global-history` | `GlobalHistory.razor` | Admin | Global history |
| `/user-dashboard` | `UserDashboard.razor` | Student | Student dashboard |
| `/student/join-exam` | `JoinExam.razor` | Student | Join exam |
| `/exams` | `Exams.razor` | Student | Available exams |
| `/take-exam/{id}` | `ExamPage.razor` | Student | Take exam |
| `/exam-history` | `ExamHistory.razor` | Student | My history |
| `/exam-result/{id}` | `ExamResult.razor` | Both | View results |
| `/payment` | `Payment.razor` | Student | Payment page |
| `/mock-test/{level}` | `MockTest.razor` | Student | Mock test |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | User login |
| POST | `/api/auth/forgot-password` | Send password reset email |
| POST | `/api/auth/reset-password` | Reset password with token |

---

## 7. Core Business Processes

### 7.1 Complete Exam Lifecycle

```
[Admin creates exam]
    │  Sets title, questions, time limit, access code
    ▼
[Exam published]
    │  Students can see exam via access code
    ▼
[Student joins exam]
    │  Enters 8-digit access code → validated → enters exam page
    ▼
[Student answers questions]
    │  Timer starts countdown
    │  Answer per question / full-page browsing
    ▼
[Submit answers] ← Auto-submit on timeout
    │
    ├── [Auto-grading] → Result page returned
    │   ExamService.CalculateScore()
    │
    └── [Record stored]
        Attempt table saves score + answer details
    ▼
[View results]
     Student → Personal history
     Admin → Global history
```

### 7.2 User Registration Flow

```
[User visits /Account/Register]
    │
    ▼
[Fill registration info] (email, password, role selection)
    │
    ▼
[ASP.NET Core Identity validation]
    │  • Email format validation
    │  • Password strength validation
    │  • Email uniqueness check
    │
    ▼
[Create user]
    │  UserManager.CreateAsync()
    │  Password automatically hashed
    ▼
[Assign role]
    │  UserManager.AddToRoleAsync(user, "Student")
    ▼
[Registration success → redirect to login]
```

### 7.3 Password Reset Flow

```
[User requests password reset]
    │
    ▼
[Enter registered email]
    │
    ▼
[Gmail SMTP sends reset email]
    │  GmailEmailSender.SendEmailAsync()
    │  Email contains reset link with token
    ▼
[User clicks link → reset password page]
    │
    ▼
[Enter new password]
    │  UserManager.ResetPasswordAsync()
    ▼
[Password updated → redirect to login]
```

---

## 8. Database Migration History

| Migration Name | Date | Changes |
|---------------|------|---------|
| `InitialCreate` | 2026-01-16 | Create base table structure (User, Exam, Question, Attempt) |
| `AddAccessCodeToExam` | 2026-01-18 | Add AccessCode field to Exam table (unique access code) |
| `AddEducationLevelToExam` | 2026-01-18 | Add EducationLevel field |
| `AddExamSubject` | 2026-01-21 | Add Subject field |
| `AddJCLevel` | 2026-01-21 | Add JC (Junior College) education level support |

Migration commands:

```bash
# Create migration
dotnet ef migrations add MigrationName

# Apply to database
dotnet ef database update

# Rollback migration
dotnet ef database update PreviousMigrationName
```

---

## 9. Local Development & Deployment

### 9.1 Requirements

- [.NET 8.0 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- [SQL Server](https://www.microsoft.com/sql-server) (LocalDB, Express, or Developer edition)
- [Visual Studio 2022](https://visualstudio.microsoft.com/) (recommended) or VS Code / Rider

### 9.2 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/BoooSAMA/Online-Examination.git
cd Online-Examination

# 2. Configure database connection string
# Edit Online Examination/appsettings.json

# 3. Configure Gmail SMTP
# Edit Online Examination/Services/GmailEmailSender.cs

# 4. Run database migration
cd "Online Examination"
dotnet ef database update

# 5. Start the application
dotnet run
# Or press F5 in Visual Studio
```

The application starts at `https://localhost:5001` by default (port depends on `launchSettings.json`).

### 9.3 Default Accounts

On first run, `DatabaseSeeder.cs` automatically creates test accounts:

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@test.com` | `Admin123` |
| **Student** | `student@test.com` | `Student123` |

### 9.4 appsettings.json Configuration

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

## 10. Security Considerations

### Known Security Concerns

| Issue | Description | Recommendation |
|-------|-------------|----------------|
| **Hardcoded email credentials** | Email and App Password in `GmailEmailSender.cs` source code | Move to environment variables, Azure Key Vault, or User Secrets in production |
| **Loose password policy** | Development phase has low password requirements | Strengthen `PasswordOptions` in `Program.cs` for production |
| **CSRF protection exemption** | LoginController uses `[IgnoreAntiforgeryToken]` | Evaluate whether deployment needs this; enable anti-forgery when possible |
| **Connection string in plaintext** | Database connection string in `appsettings.json` contains credentials | Use User Secrets (dev) or Azure Key Vault (production) |

### Production Hardening Suggestions

```csharp
// Program.cs — Strengthen password policy
builder.Services.AddIdentity<Online_ExaminationUser, IdentityRole>(options =>
{
    // Password policy
    options.Password.RequiredLength = 8;
    options.Password.RequireDigit = true;
    options.Password.RequireLowercase = true;
    options.Password.RequireUppercase = true;
    options.Password.RequireNonAlphanumeric = true;
    
    // Lockout policy
    options.Lockout.MaxFailedAccessAttempts = 5;
    options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(15);
    
    // Email confirmation
    options.SignIn.RequireConfirmedEmail = true;
})
.AddEntityFrameworkStores<Online_ExaminationContext>();
```

---

## 11. Interview Points

### 11.1 Project Highlights

| Highlight | Description |
|-----------|-------------|
| **Full-stack .NET** | End-to-end .NET tech stack from database design to frontend UI |
| **Blazor Interactive Server** | Real-time UI updates via SignalR, understanding server vs client rendering trade-offs |
| **Role-based permissions** | ASP.NET Core Identity Role-Based authorization in practice |
| **Auto-grading engine** | Instant feedback mechanism grading on submission |
| **Chart.js data visualization** | Third-party JS chart library integration via JS Interop in Blazor |
| **Programmatic question generation** | Auto math question generator with 4-level difficulty system |

### 11.2 Technical Q&A Preparation

#### Q: Why Blazor Interactive Server instead of Blazor WebAssembly?

> Reasons for choosing Interactive Server:
> 1. **Faster initial load** — no need to download .NET runtime (~2MB); WASM would be much slower on first load
> 2. **Higher development efficiency** — direct access to server resources (EF Core, SMTP) without extra API development
> 3. **Good real-time performance** — SignalR connection for instant UI updates, suitable for exam timing scenarios
> 4. **Lower memory usage** — server-side rendering, client is just a thin browser
>
> The downside is the server must maintain SignalR connections, requiring sticky sessions for scaling. For large-scale concurrency, consider migrating to Blazor WebAssembly + separate Web API backend.

#### Q: How is exam timing implemented?

> Timing logic is implemented in `ExamPage.razor`:
> 1. Record `StartedAt` timestamp when exam begins
> 2. Client periodically syncs remaining time via SignalR
> 3. Frontend displays countdown, updates every second
> 4. Auto-submits form on timeout
> 5. Validates time on submission — prevents client-side time tampering

#### Q: How does auto-grading handle subjective questions?

> The current system only supports **multiple choice questions** (A–D four options). Grading logic is straightforward answer comparison:
> ```csharp
> score = (correctCount / totalQuestions) * 100;
> ```
> To support subjective/short-answer questions, possible enhancements include:
> - Keyword matching scoring
> - Manual grading queue (admin grades one by one)
> - AI-assisted grading (LLM API)
>
> However, the current version focuses on multiple choice auto-grading for absolute fairness and instant results.

#### Q: What is the design intent behind the access code?

> The 8-digit unique access code solves several problems:
> 1. **No pre-assigned accounts needed** — students don't need prior registration to take an exam
> 2. **Easy offline distribution** — teachers can verbally announce or write on the board
> 3. **Exam isolation** — each exam has an independent access code, preventing wrong exam entry
> 4. **Abuse prevention** — access codes control who can take a specific exam
>
> Implementation-wise, access codes are auto-generated on exam creation (first 8 chars of Guid or random string) with uniqueness guarantees.

### 11.3 Technical Comparison with KirinWiki Blog (Astro)

| Dimension | Online Examination | KirinWiki Blog |
|-----------|-------------------|----------------|
| **Framework** | ASP.NET Core 8.0 + Blazor | Astro 6 |
| **Language** | C# 12 + Razor | TypeScript + Astro |
| **Rendering** | Server-side real-time (SignalR) | Static generation (SSG) |
| **Database** | SQL Server + EF Core | Cloudflare D1 |
| **Deployment** | IIS / Azure / Self-hosted | Cloudflare Pages |
| **Frontend interaction** | SignalR real-time communication | Preact Islands |
| **Use case** | Dynamic interactive web app | Content-oriented static site |

---

## Appendix: Key File Index

| File | Purpose |
|------|---------|
| `Program.cs` | Application entry, DI container, middleware pipeline |
| `Domain/Exam.cs` | Exam entity definition |
| `Domain/Question.cs` | Question entity definition |
| `Domain/Attempt.cs` | Answer record entity |
| `Data/Online_ExaminationContext.cs` | EF Core database context |
| `Data/DatabaseSeeder.cs` | Seed data initialization |
| `Services/ExamService.cs` | Exam CRUD + auto-grading |
| `Services/StudentService.cs` | Student service (registration,答题, history) |
| `Services/GmailEmailSender.cs` | Email sending |
| `Services/QuestionGenerators/LocalMathGenerator.cs` | Math question auto-generation |
| `Controllers/LoginController.cs` | Login API |
| `Controllers/AuthController.cs` | Auth API |
| `Components/Pages/AdminDashboard.razor` | Admin dashboard (Chart.js) |
| `Components/Pages/ExamPage.razor` | Exam答题 page |
| `Components/Pages/ExamResult.razor` | Exam results page |
