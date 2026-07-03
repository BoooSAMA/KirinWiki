# Smart Bakery 项目技术栈详解 — Python / FastAPI / RESTful API / Chart.js / Linux 自动化

> **目的**：本文档从 Smart Bakery（智能面包房 IoT 监控系统）和 Online Exam Platform（在线考试平台）两个项目出发，系统梳理 Python 后端开发、RESTful API 设计、FastAPI 框架、Chart.js 数据可视化、Linux 操作与树莓派自动化部署等技术的核心知识点，用于面试 QA Engineer / 后端开发岗位时的技术问答准备。

---

## 目录

1. [项目系统架构总览](#1-项目系统架构总览)
2. [Python 后端开发](#2-python-后端开发)
3. [FastAPI 框架](#3-fastapi-框架)
4. [RESTful API 设计](#4-restful-api-设计)
5. [Chart.js 数据可视化](#5-chartjs-数据可视化)
6. [Linux 基础与树莓派运维](#6-linux-基础与树莓派运维)
7. [自动化部署与 CI/CD 思维](#7-自动化部署与-cicd-思维)
8. [从项目到 QA 面试：常见问答](#8-从项目到-qa-面试常见问答)
9. [面试实战代码片段](#9-面试实战代码片段)

---

## 1. 项目系统架构总览

### Smart Bakery（智能面包房）

```
┌─────────────────────────────────────────────────┐
│               Flutter 移动端 (Dart)              │
│                                                   │
│  BakeryService (HTTP Client) ←→ NetworkScanner    │
│       │                                           │
│       │  GET  /api/status  ← 拉取传感器数据         │
│       │  POST /api/control → 发送控制指令           │
│       │                                           │
└───────┬─────────────────────────────────────────┘
        │  HTTP (局域网, port 5000)
┌───────▼─────────────────────────────────────────┐
│            Raspberry Pi 后端 (Python)             │
│                                                   │
│  FastAPI  Server                                  │
│    ├── GET  /api/status                           │
│    │     └── 读取 GPIO 传感器 → 返回 JSON          │
│    └── POST /api/control                          │
│          └── 解析 JSON → 控制 GPIO 设备            │
│                                                   │
│  传感器: DHT22 (温湿度)                             │
│  执行器: 风扇 (GPIO 17), 蜂鸣器 (GPIO 27)          │
└─────────────────────────────────────────────────┘
```

### Online Exam Platform（在线考试平台）— Chart.js 部分

```
┌─────────────────────────────────────────────────┐
│           Blazor Server (C# / Razor)              │
│                                                   │
│  AdminDashboard.razor                             │
│    ├── Chart.js (CDN) ← Canvas 渲染               │
│    │     ├── 柱状图: 各科目考试数量                 │
│    │     ├── 折线图: 每日考生人数趋势               │
│    │     └── 饼图:   通过率分布                    │
│    │                                              │
│    └── 数据来源:                                   │
│          ExamService.GetStatistics()              │
│            → EF Core → SQL Server                 │
│            → JSON 序列化 → Chart.js data          │
└─────────────────────────────────────────────────┘
```

---

## 2. Python 后端开发

### 2.1 Python 在 Smart Bakery 中的角色

Smart Bakery 的 Raspberry Pi 后端使用 Python 作为主要开发语言，承担以下职责：

| 模块 | 职责 | 关键技术 |
|------|------|---------|
| **传感器驱动** | 读取 DHT22 温湿度传感器数据 | `Adafruit_DHT` / `pigpio` |
| **GPIO 控制** | 控制风扇、蜂鸣器等执行器 | `RPi.GPIO` / `gpiozero` |
| **API 服务** | 提供 RESTful 接口供 Flutter 前端调用 | FastAPI / Flask |
| **数据处理** | 传感器数据格式化、缓存、阈值判断 | Python 标准库 |
| **自动运行** | 系统启动时自动启动后端服务 | systemd / crontab |

### 2.2 Python 核心语法速查（面试高频）

#### 数据类型与结构

```python
# 列表推导式 (List Comprehension) — 最常考
squared = [x**2 for x in range(10) if x % 2 == 0]
# 结果: [0, 4, 16, 36, 64]

# 字典操作
sensor_data = {"temperature": 25.5, "humidity": 60.2}
sensor_data["temperature"]  # 取值 → 25.5
sensor_data.get("pressure", 1013)  # 安全取值，带默认值

# 解包 (Unpacking)
temp, humid = 25.5, 60.2
# 等价于 temp = 25.5, humid = 60.2
```

#### 函数与装饰器

```python
# 类型注解 (Type Hints) — FastAPI 大量使用
def read_sensor(pin: int) -> dict[str, float]:
    """读取传感器并返回温湿度字典。"""
    temperature = 25.5  # 模拟读取
    humidity = 60.2
    return {"temperature": temperature, "humidity": humidity}

# *args 和 **kwargs
def log_sensors(*values: float, **metadata: str) -> None:
    """*args 接收多个数值，**kwargs 接收键值对元数据。"""
    print(f"Values: {values}")        # (25.5, 60.2)
    print(f"Metadata: {metadata}")    # {"unit": "celsius", "location": "bakery"}

# 装饰器 — 用于日志/鉴权
def log_call(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_call
def get_status():
    return {"status": "ok"}
```

#### 上下文管理器

```python
# with 语句 — 资源管理（文件、GPIO、数据库连接）
# 文件读写
with open("sensor_log.csv", "r") as f:
    data = f.readlines()

# GPIO 操作（确保异常时释放引脚）
from contextlib import contextmanager

@contextmanager
def gpio_pin(pin_number: int):
    """安全使用 GPIO 引脚的上下文管理器。"""
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin_number, GPIO.OUT)
    try:
        yield GPIO
    finally:
        GPIO.cleanup(pin_number)

with gpio_pin(17) as gpio:
    gpio.output(17, GPIO.HIGH)  # 控制风扇
# 退出 with 块后自动清理 GPIO
```

#### 异常处理

```python
def read_dht22(pin: int) -> tuple[float, float]:
    """健壮地读取 DHT22 传感器（可能失败）。"""
    import Adafruit_DHT
    for attempt in range(3):  # 重试 3 次
        try:
            humidity, temperature = Adafruit_DHT.read_retry(
                Adafruit_DHT.DHT22, pin
            )
            if humidity is not None and temperature is not None:
                return round(temperature, 1), round(humidity, 1)
        except RuntimeError as e:
            # DHT22 读取有时会失败（时序问题），重试即可
            print(f"Read failed (attempt {attempt + 1}): {e}")
            time.sleep(2)
    raise Exception("Failed to read DHT22 after 3 attempts")
```

### 2.3 Python 面试常见问题

| 问题 | 核心要点 |
|------|---------|
| `list` 和 `tuple` 的区别？ | `list` 可变，`tuple` 不可变；`tuple` 可做字典键 |
| 浅拷贝 vs 深拷贝？ | `copy.copy()` vs `copy.deepcopy()`；嵌套对象时区别大 |
| `__init__` 和 `__call__`？ | `__init__` 构造函数，`__call__` 使对象可调用 |
| GIL 是什么？ | Global Interpreter Lock，CPython 线程安全机制，多线程 CPU 密集任务受限 |
| `is` 和 `==` 的区别？ | `is` 比较内存地址（身份），`==` 比较值（相等性） |
| 生成器 vs 迭代器？ | 生成器用 `yield`，懒加载，节省内存 |

---

## 3. FastAPI 框架

### 3.1 FastAPI 简介

FastAPI 是一个现代、高性能的 Python Web 框架，专为构建 API 而设计。它与 Smart Bakery 场景高度契合的原因：

| 特性 | 为什么适合 IoT 后端 |
|------|-------------------|
| **异步原生** | 传感器读取可能是 I/O 阻塞的，异步可以同时处理多个请求 |
| **自动生成 OpenAPI 文档** | 调试 API 时可直接访问 `/docs` 交互式文档 |
| **Pydantic 模型校验** | 确保前端发来的控制指令格式正确 |
| **高性能** | 基于 Starlette + Uvicorn，性能接近 Node.js/Go |

### 3.2 Smart Bakery FastAPI 后端 (参考实现)

```python
# main.py — Smart Bakery 后端核心
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import RPi.GPIO as GPIO
from typing import Optional
import asyncio

# ============================================================
# 应用初始化
# ============================================================
app = FastAPI(
    title="Smart Bakery API",
    description="Raspberry Pi 智能面包房温湿度监控与控制 API",
    version="1.0.0",
)

# CORS — 允许 Flutter 移动端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 局域网环境，允许所有来源
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# GPIO 初始化
# ============================================================
FAN_PIN = 17
BUZZER_PIN = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# ============================================================
# Pydantic 数据模型（自动校验 + 文档生成）
# ============================================================
class ControlCommand(BaseModel):
    """控制指令数据模型。"""
    device: str  # "fan" | "buzzer" | "silent_mode"
    mode: str    # "AUTO" | "ON" | "OFF"

class BakeryStatus(BaseModel):
    """传感器状态数据模型。"""
    temperature: float
    humidity: float
    fan_state: str
    buzzer_state: str
    fan_mode: str
    buzzer_mode: str
    silent_mode: str

# ============================================================
# 模拟传感器状态（生产环境从 GPIO 读取）
# ============================================================
current_status = {
    "temperature": 25.5,
    "humidity": 60.2,
    "fan_state": "ON",
    "buzzer_state": "OFF",
    "fan_mode": "AUTO",
    "buzzer_mode": "AUTO",
    "silent_mode": "OFF",
}

# ============================================================
# API 端点
# ============================================================

@app.get("/api/status", response_model=BakeryStatus)
async def get_status():
    """
    获取当前传感器状态。
    
    - **temperature**: 当前温度 (°C)
    - **humidity**: 当前湿度 (%)
    - **fan_state**: 风扇状态 (ON/OFF/--)
    - **buzzer_state**: 蜂鸣器状态 (ON/OFF/--)
    """
    # 实际项目中：读取 DHT22 传感器
    # humidity, temperature = Adafruit_DHT.read_retry(DHT22, 4)
    return current_status


@app.post("/api/control")
async def control_device(command: ControlCommand):
    """
    控制设备。
    
    **请求体示例**:
    ```json
    {"device": "fan", "mode": "ON"}
    ```
    
    - **device**: 目标设备 (fan / buzzer / silent_mode)
    - **mode**: 控制模式 (AUTO / ON / OFF)
    """
    device = command.device
    mode = command.mode
    
    # 参数校验
    valid_devices = {"fan", "buzzer", "silent_mode"}
    valid_modes = {"AUTO", "ON", "OFF"}
    
    if device not in valid_devices:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid device: {device}. Must be one of {valid_devices}"
        )
    if mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {mode}. Must be one of {valid_modes}"
        )
    
    # 更新状态
    if device == "fan":
        current_status["fan_mode"] = mode
        current_status["fan_state"] = "ON" if mode == "ON" else \
                                      "OFF" if mode == "OFF" else "--"
        # GPIO.output(FAN_PIN, GPIO.HIGH if mode == "ON" else GPIO.LOW)
    elif device == "buzzer":
        current_status["buzzer_mode"] = mode
        current_status["buzzer_state"] = "ON" if mode == "ON" else \
                                        "OFF" if mode == "OFF" else "--"
    elif device == "silent_mode":
        current_status["silent_mode"] = mode
        # 静音模式下蜂鸣器不响
    
    return {"status": "ok", "message": f"{device} set to {mode}"}


@app.get("/health")
async def health_check():
    """健康检查端点。"""
    return {"status": "healthy", "service": "smart-bakery-backend"}


# ============================================================
# 启动入口
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
```

### 3.3 FastAPI 核心概念

| 概念 | 说明 | Smart Bakery 中的应用 |
|------|------|---------------------|
| **Path Operation** | `@app.get()` / `@app.post()` 定义 API 端点和 HTTP 方法 | `GET /api/status`, `POST /api/control` |
| **Pydantic Model** | 用 `BaseModel` 定义请求/响应数据模型，自动校验类型 | `ControlCommand`, `BakeryStatus` |
| **Dependency Injection** | `Depends()` 注入共享依赖 | 可注入数据库连接、传感器对象 |
| **Async/Await** | 异步处理请求，不阻塞事件循环 | `async def get_status()` |
| **自动文档** | 访问 `/docs` (Swagger) 或 `/redoc` 获取交互式 API 文档 | 调试 API 时的利器 |
| **CORS Middleware** | 允许跨源请求 | 移动端和 Pi 在不同设备上 |

### 3.4 FastAPI vs Flask — 面试对比

| 维度 | FastAPI | Flask |
|------|---------|-------|
| **性能** | 异步 + Uvicorn，高并发 | 同步 WSGI，默认单线程 |
| **数据校验** | 内置 Pydantic 自动校验 | 需手动校验或装 marshmallow |
| **文档生成** | 自动生成 OpenAPI + Swagger UI | 需额外装 flasgger |
| **异步支持** | 原生 async/await | 需装 Quart（Flask 的异步版） |
| **学习曲线** | 平缓（有 Python 基础即可） | 平缓（简单但功能少） |
| **适用场景** | IoT 后端、微服务、高并发 API | 传统 Web 应用、小型业务 |

> **面试回答范例**：
> "Smart Bakery 我选择 FastAPI 而不是 Flask，因为：
> 1. IoT 场景下多个传感器可能同时上报数据，异步架构更合适
> 2. Pydantic 模型校验让我不用手动写参数检查代码
> 3. 自动生成的 `/docs` 页面在调试时非常方便
> 4. 部署时用 Uvicorn，资源占用低，适合树莓派"

### 3.5 Uvicorn 启动方式

```bash
# 基本启动
uvicorn main:app --host 0.0.0.0 --port 5000

# 热重载（开发模式）
uvicorn main:app --reload --host 0.0.0.0 --port 5000

# 生产模式（多 worker，但树莓派建议单 worker 省资源）
uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1
```

---

## 4. RESTful API 设计

### 4.1 核心原则

REST（Representational State Transfer）是一种 API 设计风格，核心原则：

| 原则 | 说明 | Smart Bakery 中的实践 |
|------|------|---------------------|
| **资源导向** | 每个 URL 代表一个资源（resource） | `/api/status`（状态资源）, `/api/control`（控制资源） |
| **HTTP 方法语义** | GET 查 / POST 创 / PUT 改 / DELETE 删 | `GET /api/status` 查状态, `POST /api/control` 创控制指令 |
| **无状态** | 每个请求包含所有需要的信息（不依赖服务端 session） | 每次请求都携带完整 IP 信息 |
| **统一接口** | 使用标准 HTTP 状态码和响应格式 | 200 OK, 400 Bad Request, 404 Not Found |
| **JSON 作为数据格式** | 请求/响应使用 JSON | `{ "temperature": 25.5, "humidity": 60.2 }` |

### 4.2 Smart Bakery API 设计详解

#### GET /api/status — 获取状态

```json
// 请求: GET http://192.168.1.166:5000/api/status

// 响应 200 OK
{
  "temperature": 25.5,
  "humidity": 60.2,
  "fan_state": "ON",
  "buzzer_state": "OFF",
  "fan_mode": "AUTO",
  "buzzer_mode": "AUTO",
  "silent_mode": "OFF"
}
```

#### POST /api/control — 发送控制指令

```json
// 请求: POST http://192.168.1.166:5000/api/control
// Content-Type: application/json
{
  "device": "fan",
  "mode": "ON"
}

// 响应 200 OK
{
  "status": "ok",
  "message": "fan set to ON"
}

// 错误响应 400 Bad Request
{
  "detail": "Invalid device: light. Must be one of {'fan', 'buzzer', 'silent_mode'}"
}
```

### 4.3 RESTful API 设计原则（面试必问）

| 问题 | 正确答案 |
|------|---------|
| GET 和 POST 的区别？ | GET 幂等、安全（不修改资源）、可缓存；POST 不幂等、会修改资源、不可缓存 |
| 状态码怎么用？ | 200 成功 / 201 创建成功 / 400 客户端错误 / 401 未认证 / 403 无权限 / 404 不存在 / 500 服务端错误 |
| URL 命名规范？ | 小写 + 连字符：`/api/sensor-data`；用复数名词：`/api/devices`；层级关系：`/api/devices/fan/status` |
| 为什么要无状态？ | 易于水平扩展（任意服务器都可处理任意请求）；减少服务端内存占用；客户端责任明确 |
| 版本管理？ | URL 前缀：`/api/v1/status`；或 Header：`Accept: application/vnd.smartbakery.v1+json` |

### 4.4 完整数据流（前端 → 后端 → 数据库/硬件）

```
[用户点击 "开启风扇" 按钮]
        │
        ▼
[Flutter 端: BakeryService.sendControl()]
        │  HTTP POST {device: "fan", mode: "ON"}
        │  Content-Type: application/json
        ▼
[Raspberry Pi: FastAPI @app.post("/api/control")]
        │
        ├── 1. FastAPI 自动解析 JSON → Pydantic ControlCommand 模型
        ├── 2. 校验 device 和 mode 是否合法
        ├── 3. 更新内存中的 current_status 字典
        ├── 4. GPIO.output(FAN_PIN, GPIO.HIGH)  — 物理控制风扇
        │
        ▼
[返回 JSON 响应]
        │  HTTP 200 {status: "ok", message: "fan set to ON"}
        ▼
[Flutter 端: 收到响应 → 乐观 UI 更新图标状态]
```

---

## 5. Chart.js 数据可视化

### 5.1 Chart.js 简介

Chart.js 是一个轻量级的 **JavaScript 图表库**，基于 HTML5 Canvas 渲染，无需任何插件。

| 特性 | 说明 |
|------|------|
| **渲染方式** | HTML5 Canvas（非 SVG，性能更好） |
| **文件大小** | 压缩后约 70KB |
| **图表类型** | 折线图、柱状图、饼图、雷达图、散点图、气泡图等 |
| **响应式** | 默认响应式，自动适配容器大小 |
| **动画** | 内置动画效果，交互流畅 |

### 5.2 Online Exam Platform 中的 Chart.js 使用

```html
<!-- AdminDashboard.razor 中的 Chart.js 使用 -->
@* Chart.js 通过 CDN 引入 *@
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

@* Canvas 元素 — Chart.js 的渲染容器 *@
<canvas id="examChart" width="400" height="200"></canvas>

@code {
    // Blazor 中的 JavaScript Interop
    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if (firstRender)
        {
            await LoadChartData();
        }
    }

    private async Task LoadChartData()
    {
        // 1. 从 Service 层获取统计数据
        var stats = await ExamService.GetExamStatisticsAsync();
        
        // 2. 通过 JS Interop 将数据传递给 Chart.js
        await JSRuntime.InvokeVoidAsync("renderExamChart", stats);
    }
}
```

```javascript
// wwwroot/js/chart-setup.js — Chart.js 渲染逻辑

function renderExamChart(stats) {
    const ctx = document.getElementById('examChart').getContext('2d');
    
    // Chart.js 配置对象
    new Chart(ctx, {
        // 1. 图表类型
        type: 'bar',  // 柱状图
        
        // 2. 数据
        data: {
            labels: stats.labels,  // ['数学', '英语', '科学', ...]
            datasets: [{
                label: '考试数量',
                data: stats.counts,  // [12, 8, 15, ...]
                backgroundColor: [
                    'rgba(54, 162, 235, 0.5)',  // 半透明蓝色
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(255, 206, 86, 0.5)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 206, 86, 1)'
                ],
                borderWidth: 1
            }]
        },
        
        // 3. 配置选项
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '各科目考试数量统计'
                },
                legend: {
                    display: false  // 单数据集时隐藏图例
                }
            },
            scales: {
                y: {
                    beginAtZero: true,  // Y 轴从 0 开始
                    title: {
                        display: true,
                        text: '数量 (场)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '科目'
                    }
                }
            }
        }
    });
}
```

### 5.3 Chart.js 核心概念

| 概念 | 说明 | 代码示例 |
|------|------|---------|
| **Chart 实例** | `new Chart(ctx, config)` 创建图表 | `new Chart(ctx, { type, data, options })` |
| **type** | 图表类型 | `'bar'` / `'line'` / `'pie'` / `'radar'` |
| **data.labels** | X 轴标签数组 | `['数学', '英语', '科学']` |
| **data.datasets** | 数据集数组，可多组 | `[{ label: '...', data: [...], backgroundColor: '...' }]` |
| **options** | 配置：响应式、动画、轴标题、图例 | `{ responsive: true, scales: { y: { beginAtZero: true } } }` |
| **Canvas** | `<canvas>` 元素是图表渲染容器 | `<canvas id="myChart">` |

### 5.4 面试常见 Chart.js 问题

| 问题 | 答案 |
|------|------|
| Chart.js 和 ECharts 的区别？ | Chart.js 轻量(70KB)、Canvas 渲染、API 简洁；ECharts 功能更全面、支持更多图表类型、SVG/Canvas 双引擎 |
| Chart.js 如何处理大量数据？ | 开启 `animation: false`（数据多时动画卡）；使用 `decimation` 插件自动降采样 |
| 如何更新图表数据？ | `chart.data.datasets[0].data = newData; chart.update();` |
| Chart.js 的响应式原理？ | 监听容器尺寸变化 → 重绘 Canvas；`maintainAspectRatio: false` 可自定义宽高比 |
| 在 Blazor 中使用 Chart.js 要注意什么？ | 需要用 `IJSRuntime` 做 JS Interop；在 `OnAfterRenderAsync` 中初始化（确保 DOM 已渲染） |

---

## 6. Linux 基础与树莓派运维

### 6.1 树莓派环境概览

Smart Bakery 的 Raspberry Pi 运行 **Raspberry Pi OS**（基于 Debian Linux），使用以下核心组件：

| 组件 | 用途 |
|------|------|
| **Raspberry Pi OS (Debian)** | 基础操作系统 |
| **Python 3** | 后端开发语言 |
| **pip / pip3** | Python 包管理器 |
| **GPIO** (General Purpose Input/Output) | 通用输入输出引脚，连接传感器和执行器 |
| **systemd** | 系统服务管理（使后端随系统启动） |
| **WiFi (wlan0)** | 局域网通信接口 |
| **SSH** | 远程登录管理树莓派 |

### 6.2 常用 Linux 命令（树莓派运维必须掌握）

#### 文件与目录操作

```bash
# 导航
pwd                           # 显示当前路径
ls -la                        # 列出所有文件（含隐藏文件）+ 详细信息
cd /home/pi/smart-bakery/     # 切换目录
tree -L 2                     # 显示目录树（深度 2 层）

# 文件操作
cat main.py                   # 查看文件内容（短文件）
less main.py                  # 分页查看（长文件，q 退出）
head -20 main.py              # 查看前 20 行
tail -f logs/app.log          # 实时追踪日志输出
nano main.py                  # 编辑文件（轻量级编辑器）
vim main.py                   # 编辑文件（功能更强）

# 权限
chmod +x deploy.sh            # 给脚本添加执行权限
chown -R pi:pi /home/pi/app/  # 递归修改文件所有者
```

#### 进程与服务管理

```bash
# 查看进程
ps aux                        # 查看所有进程
ps aux | grep python          # 查找 Python 相关进程
top                           # 实时进程监控（按 q 退出）
htop                          # 增强版 top（需安装）

# 终止进程
kill 1234                     # 终止 PID 1234
kill -9 1234                  # 强制终止
pkill -f "uvicorn"            # 按名字杀死所有 uvicorn 进程

# systemd 服务管理
sudo systemctl status smart-bakery    # 查看服务状态
sudo systemctl start smart-bakery     # 启动服务
sudo systemctl stop smart-bakery      # 停止服务
sudo systemctl restart smart-bakery   # 重启服务
sudo systemctl enable smart-bakery    # 设置开机自启
sudo systemctl disable smart-bakery   # 取消开机自启
sudo journalctl -u smart-bakery -f    # 查看服务日志（-f 实时追踪）
```

#### 网络与调试

```bash
# 网络配置
ifconfig                      # 查看网络接口（IP 地址等）
ip addr show                  # 新版网络配置查看
iwconfig                      # WiFi 连接信息
ping 192.168.1.100            # 测试网络连通性

# SSH 远程登录
ssh pi@192.168.1.166          # 远程登录树莓派
scp main.py pi@192.168.1.166:/home/pi/app/  # 安全拷贝文件到树莓派

# API 测试（面试必会！）
curl http://192.168.1.166:5000/api/status    # GET 请求测试
curl -X POST http://192.168.1.166:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"device": "fan", "mode": "ON"}'        # POST 请求测试

# 端口检查
netstat -tlnp                  # 查看监听端口
ss -tlnp                       # 新版端口查看
lsof -i :5000                  # 查看占用端口 5000 的进程
```

### 6.3 systemd 服务配置（开机自启）

```ini
# /etc/systemd/system/smart-bakery.service
[Unit]
Description=Smart Bakery Backend Service
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smart-bakery
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 5000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# 安全限制
NoNewPrivileges=true
ProtectHome=false
ProtectSystem=full

[Install]
WantedBy=multi-user.target
```

```bash
# 部署 flow
# 1. 创建服务文件
sudo nano /etc/systemd/system/smart-bakery.service

# 2. 重新加载 systemd
sudo systemctl daemon-reload

# 3. 启用并启动
sudo systemctl enable smart-bakery
sudo systemctl start smart-bakery

# 4. 确认运行
sudo systemctl status smart-bakery
# 输出: ● smart-bakery.service - Smart Bakery Backend Service
#        Loaded: loaded /etc/systemd/system/smart-bakery.service (enabled)
#        Active: active (running) since ...

# 5. 设置失败自动重启
# Restart=always 已在 service 文件中配置
```

### 6.4 GPIO 操作（硬件控制）

```python
# gpio_control.py — Smart Bakery GPIO 控制模块
import RPi.GPIO as GPIO
import time

# 引脚定义（BCM 编号模式）
FAN_PIN = 17
BUZZER_PIN = 27
DHT22_PIN = 4

class BakeryHardware:
    """烘焙硬件控制层。"""
    
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)
        self._fan_state = False
        self._buzzer_state = False
    
    def set_fan(self, state: bool):
        """控制风扇开关。"""
        GPIO.output(FAN_PIN, GPIO.HIGH if state else GPIO.LOW)
        self._fan_state = state
    
    def set_buzzer(self, state: bool):
        """控制蜂鸣器开关。"""
        GPIO.output(BUZZER_PIN, GPIO.HIGH if state else GPIO.LOW)
        self._buzzer_state = state
    
    def read_dht22(self):
        """读取温湿度传感器。"""
        import Adafruit_DHT
        humidity, temperature = Adafruit_DHT.read_retry(
            Adafruit_DHT.DHT22, DHT22_PIN
        )
        return temperature, humidity
    
    def cleanup(self):
        """清理 GPIO 资源。"""
        GPIO.cleanup()
```

### 6.5 GPIO 引脚图

```
Raspberry Pi 4 (BCM 编号)
┌──────────────────────────────┐
│ 3.3V   (1) (2)  5V          │
│ GPIO2  (3) (4)  5V          │
│ GPIO3  (5) (6)  GND         │
│ GPIO4  (7) (8)  GPIO14      │ ← DHT22 传感器
│ GND    (9) (10) GPIO15      │
│ GPIO17 (11) (12) GPIO18     │ ← 风扇控制
│ GPIO27 (13) (14) GND        │ ← 蜂鸣器控制
│ GPIO22 (15) (16) GPIO23     │
│ 3.3V   (17) (18) GPIO24     │
│ GPIO10 (19) (20) GND        │
└──────────────────────────────┘
```

---

## 7. 自动化部署与 CI/CD 思维

### 7.1 树莓派自动部署脚本

```bash
#!/bin/bash
# deploy.sh — Smart Bakery 一键部署脚本
# 用法: ./deploy.sh [pi_ip_address]

set -e  # 任何命令失败立即退出

PI_USER="pi"
PI_HOST="${1:-192.168.1.166}"
APP_DIR="/home/pi/smart-bakery"
LOCAL_DIR="."

echo "=== Smart Bakery 部署脚本 ==="
echo "目标: ${PI_USER}@${PI_HOST}:${APP_DIR}"
echo ""

# 1. 本地测试
echo "[1/5] 本地语法检查..."
python3 -m py_compile main.py || { echo "❌ Python 语法错误"; exit 1; }
echo "✅ 语法检查通过"

# 2. 同步代码到树莓派
echo "[2/5] 同步代码到树莓派..."
rsync -avz --delete \
    --exclude="__pycache__" \
    --exclude=".git" \
    --exclude="*.pyc" \
    -e ssh ${LOCAL_DIR}/ ${PI_USER}@${PI_HOST}:${APP_DIR}/
echo "✅ 代码同步完成"

# 3. 安装 Python 依赖
echo "[3/5] 安装依赖..."
ssh ${PI_USER}@${PI_HOST} "cd ${APP_DIR} && pip3 install -r requirements.txt --quiet"
echo "✅ 依赖安装完成"

# 4. 重启服务
echo "[4/5] 重启服务..."
ssh ${PI_USER}@${PI_HOST} "sudo systemctl restart smart-bakery"
echo "✅ 服务已重启"

# 5. 健康检查
echo "[5/5] 健康检查..."
sleep 2
HEALTH=$(curl -s http://${PI_HOST}:5000/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ 服务运行正常! 响应: $HEALTH"
else
    echo "❌ 健康检查失败"
    exit 1
fi

echo ""
echo "=== 部署完成! ==="
echo "API: http://${PI_HOST}:5000/api/status"
echo "文档: http://${PI_HOST}:5000/docs"
```

### 7.2 Git Hooks 自动化

```bash
#!/bin/bash
# .git/hooks/pre-commit — 提交前自动检查 Python 语法
# 将本文件放在 .git/hooks/pre-commit 并 chmod +x

echo "🔍 运行 pre-commit 检查..."

# 检查 Python 语法
for file in $(git diff --cached --name-only | grep '\.py$'); do
    if [ -f "$file" ]; then
        python3 -m py_compile "$file"
        if [ $? -ne 0 ]; then
            echo "❌ $file 语法错误"
            exit 1
        fi
        echo "✅ $file 语法检查通过"
    fi
done

# 检查包含调试代码
if git diff --cached | grep -E "print\(|console\.log" | grep -v "# allow"; then
    echo "⚠️  警告: 提交中包含调试打印语句"
    # 不阻止提交，只是警告
fi

echo "✅ pre-commit 检查全部通过"
```

### 7.3 日志轮转配置

```ini
# /etc/logrotate.d/smart-bakery
# 自动轮转 Smart Bakery 日志，防止日志占满磁盘

/home/pi/smart-bakery/logs/*.log {
    daily              # 每天轮转一次
    rotate 7           # 保留 7 天
    compress           # 压缩旧日志
    delaycompress      # 延迟一天压缩
    missingok          # 文件不存在不报错
    notifempty         # 空文件不轮转
    copytruncate       # 复制并截断（不影响程序写日志）
}
```

### 7.4 CI/CD 思维（适用于 QA 面试）

Smart Bakery 虽然是小项目，但体现了持续集成/持续部署的核心思想：

| 实践 | Smart Bakery 中的体现 | QA 面试中可以怎么说 |
|------|---------------------|-------------------|
| **自动化测试** | 提交前语法检查 | "我习惯在提交前自动运行静态检查和单元测试" |
| **自动化部署** | `deploy.sh` 一键部署 | "我写了一个部署脚本，自动完成代码同步、依赖安装、服务重启和健康检查" |
| **监控** | `/health` 端点 + 日志轮转 | "我用 `/health` 做健康检查，logrotate 管理日志，防止磁盘写满" |
| **回滚能力** | Git 版本控制 | "出问题时可以快速 `git revert` 回滚到上一个稳定版本" |
| **环境一致** | `requirements.txt` 固定依赖 | "用 requirements.txt 锁死依赖版本，确保开发和生产环境一致" |

---

## 8. 从项目到 QA 面试：常见问答

### 8.1 项目相关

#### Q: "你的 Smart Bakery 项目数据传输流程是怎样的？"

> **答**：
> "整体数据流分三部分：
> 
> **状态获取（前端拉取）**：
> Flutter 端每 800ms 向 `GET /api/status` 发送 HTTP 请求 → FastAPI 后端读取 DHT22 传感器数据 → 序列化为 JSON 返回 → Flutter 解析 JSON 并更新 UI。
> 
> **设备控制（前端推送）**：
> 用户点击按钮 → Flutter 发送 `POST /api/control` 请求，body 为 `{"device": "fan", "mode": "ON"}` → FastAPI 接收后校验参数 → 设置 GPIO 引脚高低电平 → 物理控制设备 → 返回 `200 OK`。
> 
> **网络发现**：
> 首次连接时，Flutter 端暴力扫描 `192.168.x.166` 网段（800ms 超时），找到开放端口 5000 的树莓派 IP，存入 SharedPreferences 持久化。"

#### Q: "如果传感器读不到数据，你怎么排查？"

> **答**：
> "我会分三层排查：
> 1. **硬件层**：检查 DHT22 接线是否正确（VCC→3.3V, GND→GND, DATA→GPIO4）；用万用表测引脚电压
> 2. **系统层**：`dmesg | grep gpio` 看内核有没有 GPIO 报错；`ls /sys/class/gpio/` 检查 sysfs 接口
> 3. **软件层**：`curl http://localhost:5000/api/status` 测试 API；查看 `journalctl -u smart-bakery -f` 日志——DHT22 有时序要求，如果读取间隔太短会失败"

#### Q: "你怎么保证 API 的健壮性？"

> **答**：
> "三个方面：
> 1. **输入校验**：FastAPI 的 Pydantic 模型自动校验请求格式，无效请求直接 400 返回，不进业务逻辑
> 2. **异常处理**：传感器读取有 try/except + 重试机制（3 次），避免单次失败导致 500
> 3. **服务自愈**：systemd 配置了 `Restart=always`，进程崩溃后 5 秒自动重启"

### 8.2 Python 基础

#### Q: "Python 的 GIL 是什么？对你的 IoT 后端有什么影响？"

> **答**：
> "GIL（Global Interpreter Lock）是 CPython 的机制：同一时刻只有一个线程能执行 Python 字节码。
> 
> 对 Smart Bakery 来说，FastAPI 是异步 I/O 模型（asyncio + Uvicorn），不是多线程模型。传感器读取主要是 I/O 等待（传感器响应时间），所以 GIL 影响很小。
> 
> 如果需要真正的并行计算（比如视频推流分析），我会用多进程 `multiprocessing` 或把计算密集部分用 C 扩展/Cython 实现。"

#### Q: "讲一下 Python 的装饰器，你项目中用到了吗？"

> **答**：
> "装饰器本质上是一个高阶函数——它接受一个函数作为参数，返回一个增强后的函数。
> 
> 项目中我可以用装饰器做 API 请求日志、执行时间统计、或错误重试：
> 
> ```python
> def retry_on_failure(max_attempts=3):
>     def decorator(func):
>         def wrapper(*args, **kwargs):
>             for i in range(max_attempts):
>                 try:
>                     return func(*args, **kwargs)
>                 except Exception as e:
>                     if i == max_attempts - 1:
>                         raise
>                     time.sleep(1)
>         return wrapper
>     return decorator
> 
> @retry_on_failure(max_attempts=3)
> def read_sensor():
>     return Adafruit_DHT.read_retry(DHT22, 4)
> ```
> 
> FastAPI 本身也大量使用装饰器：`@app.get()`, `@app.post()` 等。"

### 8.3 RESTful API

#### Q: "GET 和 POST 有什么区别？什么时候用 PUT 和 DELETE？"

> **答**：
> - **GET**：获取资源，幂等、安全、可缓存。参数在 URL 中。如 `GET /api/status`
> - **POST**：创建资源，不幂等。参数在 Request Body 中。如 `POST /api/control`
> - **PUT**：更新资源（全量替换），幂等。如 `PUT /api/device/fan` 替换整个风扇配置
> - **DELETE**：删除资源，幂等。如 `DELETE /api/device/fan` 移除风扇设备
> - **PATCH**：部分更新。如 `PATCH /api/device/fan` 只修改风扇模式字段

#### Q: "你的 API 是 RESTful 的吗？为什么？"

> **答**：
> "Smart Bakery 的 API 遵循了 REST 原则（资源导向、JSON 格式、HTTP 方法语义化），但从严格意义上说不是完整的 RESTful API——因为它是 IoT 控制场景，不是 CRUD 数据管理。
> 
> 如果严格 RESTful 化，会变成：
> - `GET /api/devices` — 列出所有设备
> - `GET /api/devices/fan` — 获取风扇详情
> - `PATCH /api/devices/fan` — 部分更新风扇状态
> 
> 但对于 IoT 控制场景，我们的设计（统一 `/api/control` 端点 + device/mode 参数）更实用。REST 是指导原则，不是教条——根据实际场景灵活调整。"

### 8.4 Linux / 树莓派

#### Q: "如果树莓派连不上 WiFi，你怎么排查？"

> **答**：
> "按 OSI 模型自底向上排查：
> ```
> 1. 物理层: 树莓派电源灯亮否？WiFi 模块指示灯？
> 2. 链路层: iwconfig wlan0 看是否连上路由器
> 3. 网络层: ping 网关 (ping 192.168.1.1) 
> 4. 传输层: curl http://localhost:5000/api/status (本地测试)
> 5. 应用层: 手机 app 能 ping 通树莓派 IP 吗？
> ```
> 
> 常见问题：WiFi 配置文件 `/etc/wpa_supplicant/wpa_supplicant.conf` 密码错误；路由器 DHCP 地址池满了；树莓派 5GHz WiFi 信道不支持。"

#### Q: "你用过哪些 Linux 命令来调试项目？"

> **答**：
> "日常调试用得最多的几个：
> - `curl`：测试 API 端点，验证响应格式
> - `journalctl -u smart-bakery -f`：实时查看错误日志
> - `ps aux | grep python`：确认 Python 进程在运行
> - `netstat -tlnp`：确认端口 5000 在监听
> - `htop`：看 CPU/内存，树莓派资源有限容易满
> - `ping`：确认手机和树莓派在同一网段"

---

## 9. 面试实战代码片段

### 9.1 手写一个简单的 FastAPI 应用（面试高频）

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# 数据模型
class Item(BaseModel):
    name: str
    price: float
    in_stock: bool = True

# 模拟数据库
items_db = {}

@app.get("/")
def root():
    return {"message": "Hello from Smart Bakery API"}

@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

@app.post("/items", status_code=201)
def create_item(item: Item):
    item_id = len(items_db) + 1
    items_db[item_id] = item
    return {"id": item_id, **item.model_dump()}
```

### 9.2 RESTful API 测试（用 curl）

```bash
# 测试完整 API 生命周期

# 1. 健康检查
curl http://localhost:5000/health

# 2. 获取传感器状态
curl http://localhost:5000/api/status | jq .
# jq 格式化 JSON 输出

# 3. 控制设备
curl -X POST http://localhost:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"device": "fan", "mode": "ON"}'

# 4. 错误测试（参数非法）
curl -X POST http://localhost:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"device": "light", "mode": "ON"}'
# 预期返回 400 Bad Request

# 5. 负载测试（10 并发请求）
for i in $(seq 1 10); do
    curl -s http://localhost:5000/api/status > /dev/null &
done
wait
echo "10 并发请求完成"
```

### 9.3 Python 自动化测试脚本

```python
# test_api.py — Smart Bakery API 自动化测试
import requests
import json
import time

BASE_URL = "http://192.168.1.166:5000"

def test_get_status():
    """测试 GET /api/status 端点"""
    print("\n[Test] GET /api/status")
    
    response = requests.get(f"{BASE_URL}/api/status", timeout=5)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "temperature" in data, "Response missing 'temperature'"
    assert "humidity" in data, "Response missing 'humidity'"
    assert isinstance(data["temperature"], (int, float)), "temperature should be numeric"
    
    print(f"  ✅ 状态码: {response.status_code}")
    print(f"  ✅ 温度: {data['temperature']}°C")
    print(f"  ✅ 湿度: {data['humidity']}%")
    return data

def test_control_device(device: str, mode: str):
    """测试 POST /api/control 端点"""
    print(f"\n[Test] POST /api/control (device={device}, mode={mode})")
    
    payload = {"device": device, "mode": mode}
    response = requests.post(
        f"{BASE_URL}/api/control",
        json=payload,
        timeout=5
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["status"] == "ok", f"Expected status 'ok', got '{data['status']}'"
    
    print(f"  ✅ 状态码: {response.status_code}")
    print(f"  ✅ 响应: {data['message']}")
    return data

def test_invalid_control():
    """测试无效参数（预期 400）"""
    print(f"\n[Test] POST /api/control (invalid device)")
    
    payload = {"device": "invalid_device", "mode": "ON"}
    response = requests.post(
        f"{BASE_URL}/api/control",
        json=payload,
        timeout=5
    )
    
    assert response.status_code == 400, f"Expected 400 for invalid device"
    print(f"  ✅ 正确返回 400: {response.json()['detail']}")

def test_health():
    """测试健康检查端点"""
    print(f"\n[Test] GET /health")
    
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    
    print(f"  ✅ 服务状态: {data['status']}")

def run_all_tests():
    """运行全部测试"""
    print("=" * 50)
    print("Smart Bakery API 自动化测试")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        test_health()
        test_get_status()
        test_control_device("fan", "ON")
        test_control_device("buzzer", "OFF")
        test_invalid_control()
        
        elapsed = time.time() - start_time
        print(f"\n{'=' * 50}")
        print(f"✅ 全部测试通过! (耗时: {elapsed:.2f}s)")
        print(f"{'=' * 50}")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接服务器: {BASE_URL}")
        print("   请确认树莓派在线且服务已启动")
        exit(1)
    except Exception as e:
        print(f"\n❌ 意外错误: {e}")
        exit(1)

if __name__ == "__main__":
    run_all_tests()
```

### 9.4 requirements.txt（依赖管理）

```txt
# Smart Bakery Python 依赖
fastapi==0.110.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
RPi.GPIO==0.7.1
Adafruit-DHT==1.4.0
gpiozero==2.0
# 开发/测试依赖
pytest==8.0.0
requests==2.31.0
httpx==0.27.0  # FastAPI 测试客户端
```

---

## 附录：面试高频技术概念速查卡

### HTTP 状态码速记

| 状态码 | 含义 | 场景 |
|--------|------|------|
| **200 OK** | 成功 | `GET /api/status` 返回数据 |
| **201 Created** | 创建成功 | `POST /api/items` 新增资源 |
| **204 No Content** | 成功无返回体 | `DELETE` 删除成功 |
| **400 Bad Request** | 请求格式错误 | `POST /api/control` 参数无效 |
| **401 Unauthorized** | 未认证 | 没有登录或 token 过期 |
| **403 Forbidden** | 无权限 | 角色不够 |
| **404 Not Found** | 资源不存在 | 请求了不存在的端点 |
| **429 Too Many Requests** | 请求频率限制 | 短时间大量请求被限流 |
| **500 Internal Server Error** | 服务端内部错误 | 传感器读取异常未处理 |

### Python -> FastAPI -> RESTful API 架构层次

```
┌─────────────────────────────────────────────┐
│             Flutter 移动端 (Dart)             │
│    http package → BakeryService              │
└─────────────────┬───────────────────────────┘
                  │  HTTP/JSON
┌─────────────────▼───────────────────────────┐
│          FastAPI (Python Backend)             │
│                                               │
│  [路由层] @app.get("/api/status")             │
│      → 参数提取、请求分发                      │
│                                               │
│  [控制器层] async def get_status():           │
│      → 调用 Service 层                        │
│                                               │
│  [服务层] read_sensor_data()                  │
│      → 业务逻辑、数据聚合                      │
│                                               │
│  [数据层] GPIO / DHT22 / Adafruit_DHT        │
│      → 物理硬件交互                            │
└─────────────────┬───────────────────────────┘
                  │  GPIO 信号
┌─────────────────▼───────────────────────────┐
│           Raspberry Pi 硬件                    │
│    DHT22 (传感器) / 风扇 / 蜂鸣器              │
└─────────────────────────────────────────────┘
```

### Linux 排查流程（API 不通时）

```
手机 App 显示 "离线"
        │
        ▼
手机能 ping 通树莓派 IP 吗？
   ├── No  → 检查 WiFi 连接、同一网段
   └── Yes
        │
        ▼
树莓派上 curl localhost:5000/api/status 能通吗？
   ├── No  → systemctl status smart-bakery 查看服务状态
   │          journalctl -u smart-bakery -f 查看日志
   └── Yes
        │
        ▼
树莓派上 ss -tlnp | grep 5000 在监听吗？
   ├── No  → uvicorn 没启动 / 端口被占用
   └── Yes
        │
        ▼
手机 curl http://[pi-ip]:5000/api/status 能通吗？
   ├── No  → 防火墙 (sudo ufw status)
   │          uvicorn 绑了 127.0.0.1 而非 0.0.0.0
   └── Yes
        │
        ▼
问题在 Flutter 端：IP 配置 / 网络权限
```

---

> **文档说明**：本文档基于 https://github.com/BoooSAMA 的 Smart Bakery（Flutter + Raspberry Pi IoT 项目）和 Online Exam Platform（Blazor + Chart.js 项目）的技术栈整理，旨在为 NCS Quality Engineer Intern 面试提供系统性的 Python、FastAPI、RESTful API、Chart.js、Linux 自动化等领域的技术知识储备。

> 准备用于 NCS QA Engineer Intern 面试
