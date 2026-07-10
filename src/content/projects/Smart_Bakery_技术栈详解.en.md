---
title: "Smart Bakery Project Tech Stack — Python / FastAPI / RESTful API / Chart.js / Linux Automation"
date: "2026-06-10"
description: "A systematic breakdown of core knowledge points in Python backend development, FastAPI, RESTful APIs, Chart.js data visualization, and Linux automation, drawing from the Smart Bakery (Flutter + Raspberry Pi IoT) and Online Exam Platform (Blazor + Chart.js) projects."
tags: ["Python", "FastAPI", "RESTful API", "Chart.js", "Raspberry Pi", "Linux"]
---

# Smart Bakery Project Tech Stack — Python / FastAPI / RESTful API / Chart.js / Linux Automation

> **Purpose**: This document systematically covers core knowledge in Python backend development, RESTful API design, FastAPI framework, Chart.js data visualization, Linux operations, and Raspberry Pi automation deployment, drawing from the Smart Bakery (smart bakery IoT monitoring system) and Online Exam Platform projects — for interview preparation targeting QA Engineer / Backend Developer roles.

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Python Backend Development](#2-python-backend-development)
3. [FastAPI Framework](#3-fastapi-framework)
4. [RESTful API Design](#4-restful-api-design)
5. [Chart.js Data Visualization](#5-chartjs-data-visualization)
6. [Linux Basics & Raspberry Pi Operations](#6-linux-basics--raspberry-pi-operations)
7. [Automated Deployment & CI/CD Thinking](#7-automated-deployment--cicd-thinking)
8. [From Projects to QA Interview: Common Q&A](#8-from-projects-to-qa-interview-common-qa)
9. [Interview Practical Code Snippets](#9-interview-practical-code-snippets)

---

## 1. System Architecture Overview

### Smart Bakery

```
+---------------------------------------------------+
|               Flutter Mobile (Dart)                |
|                                                     |
|  BakeryService (HTTP Client) <-> NetworkScanner     |
|       |                                             |
|       |  GET  /api/status   <- Fetch sensor data    |
|       |  POST /api/control  -> Send control cmds    |
|       |                                             |
+-------+-------------------------------------------+
        |  HTTP (LAN, port 5000)
+-------v-------------------------------------------+
|            Raspberry Pi Backend (Python)            |
|                                                     |
|  FastAPI  Server                                    |
|    +-- GET  /api/status                             |
|    |     +-- Read GPIO sensor -> return JSON        |
|    +-- POST /api/control                            |
|          +-- Parse JSON -> control GPIO device       |
|                                                     |
|  Sensors: DHT22 (temp/humidity)                     |
|  Actuators: Fan (GPIO 17), Buzzer (GPIO 27)        |
+---------------------------------------------------+
```

### Online Exam Platform -- Chart.js Part

```
+---------------------------------------------------+
|           Blazor Server (C# / Razor)                |
|                                                     |
|  AdminDashboard.razor                               |
|    +-- Chart.js (CDN) <- Canvas rendering           |
|    |     +-- Bar chart: exam count by subject       |
|    |     +-- Line chart: daily candidate trends     |
|    |     +-- Pie chart: pass rate distribution      |
|    |                                                |
|    +-- Data source:                                 |
|          ExamService.GetStatistics()                |
|            -> EF Core -> SQL Server                  |
|            -> JSON serialization -> Chart.js data   |
+---------------------------------------------------+
```

---

## 2. Python Backend Development

### 2.1 Python's Role in Smart Bakery

The Smart Bakery Raspberry Pi backend uses Python as its primary language:

| Module | Responsibility | Key Technology |
|--------|---------------|----------------|
| **Sensor driver** | Read DHT22 temp/humidity sensor | `Adafruit_DHT` / `pigpio` |
| **GPIO control** | Control fan, buzzer, etc. | `RPi.GPIO` / `gpiozero` |
| **API service** | Provide RESTful interface for Flutter | FastAPI / Flask |
| **Data processing** | Sensor data formatting, caching, thresholding | Python standard library |
| **Auto-start** | Auto-start backend on system boot | systemd / crontab |

### 2.2 Python Core Syntax (Interview High-Frequency)

#### Data Types & Structures

```python
# List Comprehension -- most commonly tested
squared = [x**2 for x in range(10) if x % 2 == 0]
# Result: [0, 4, 16, 36, 64]

# Dictionary operations
sensor_data = {"temperature": 25.5, "humidity": 60.2}
sensor_data["temperature"]  # -> 25.5
sensor_data.get("pressure", 1013)  # Safe access with default

# Unpacking
temp, humid = 25.5, 60.2
# Equivalent to temp = 25.5, humid = 60.2
```

#### Functions & Decorators

```python
# Type Hints -- heavily used in FastAPI
def read_sensor(pin: int) -> dict[str, float]:
    \"\"\"Read sensor and return temp/humidity dict.\"\"\"
    temperature = 25.5  # Simulated reading
    humidity = 60.2
    return {"temperature": temperature, "humidity": humidity}

# *args and **kwargs
def log_sensors(*values: float, **metadata: str) -> None:
    \"\"\"*args receives multiple values, **kwargs receives key-value metadata.\"\"\"
    print(f"Values: {values}")        # (25.5, 60.2)
    print(f"Metadata: {metadata}")    # {"unit": "celsius", "location": "bakery"}

# Decorator -- for logging/auth
def log_call(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_call
def get_status():
    return {"status": "ok"}
```

#### Context Managers

```python
# with statement -- resource management (files, GPIO, DB connections)
# File I/O
with open("sensor_log.csv", "r") as f:
    data = f.readlines()

# GPIO operations (ensure pin cleanup on exception)
from contextlib import contextmanager

@contextmanager
def gpio_pin(pin_number: int):
    \"\"\"Safe GPIO pin context manager.\"\"\"
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin_number, GPIO.OUT)
    try:
        yield GPIO
    finally:
        GPIO.cleanup(pin_number)

with gpio_pin(17) as gpio:
    gpio.output(17, GPIO.HIGH)  # Control fan
# GPIO auto-cleaned on exit
```

#### Exception Handling

```python
def read_dht22(pin: int) -> tuple[float, float]:
    \"\"\"Robust DHT22 sensor reading (may fail).\"\"\"
    import Adafruit_DHT
    for attempt in range(3):  # Retry 3 times
        try:
            humidity, temperature = Adafruit_DHT.read_retry(
                Adafruit_DHT.DHT22, pin
            )
            if humidity is not None and temperature is not None:
                return round(temperature, 1), round(humidity, 1)
        except RuntimeError as e:
            print(f"Read failed (attempt {attempt + 1}): {e}")
            time.sleep(2)
    raise Exception("Failed to read DHT22 after 3 attempts")
```

### 2.3 Common Python Interview Questions

| Question | Key Points |
|----------|------------|
| Difference between `list` and `tuple`? | `list` mutable, `tuple` immutable; `tuple` can be dict key |
| Shallow vs deep copy? | `copy.copy()` vs `copy.deepcopy()`; nested objects matter |
| `__init__` vs `__call__`? | `__init__` constructor, `__call__` makes object callable |
| What is GIL? | Global Interpreter Lock, CPython thread safety mechanism, limits multi-threaded CPU-bound tasks |
| `is` vs `==`? | `is` compares memory address (identity), `==` compares value (equality) |
| Generator vs iterator? | Generator uses `yield`, lazy evaluation, memory efficient |

---

## 3. FastAPI Framework

### 3.1 FastAPI Introduction

FastAPI is a modern, high-performance Python web framework designed for building APIs. Why it's well-suited for Smart Bakery:

| Feature | Why It Fits IoT Backend |
|---------|------------------------|
| **Async native** | Sensor reads may be I/O blocking; async handles multiple requests simultaneously |
| **Auto-generated OpenAPI docs** | Interactive `/docs` page for API debugging |
| **Pydantic model validation** | Ensures control commands from frontend are correctly formatted |
| **High performance** | Based on Starlette + Uvicorn, performance near Node.js/Go |

### 3.2 Smart Bakery FastAPI Backend (Reference Implementation)

```python
# main.py -- Smart Bakery backend core
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import RPi.GPIO as GPIO
from typing import Optional
import asyncio

# Application initialization
app = FastAPI(
    title="Smart Bakery API",
    description="Raspberry Pi smart bakery temp/humidity monitoring & control API",
    version="1.0.0",
)

# CORS -- allow Flutter mobile cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # LAN environment, allow all origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# GPIO initialization
FAN_PIN = 17
BUZZER_PIN = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Pydantic data models (auto-validation + docs generation)
class ControlCommand(BaseModel):
    device: str  # "fan" | "buzzer" | "silent_mode"
    mode: str    # "AUTO" | "ON" | "OFF"

class BakeryStatus(BaseModel):
    temperature: float
    humidity: float
    fan_state: str
    buzzer_state: str
    fan_mode: str
    buzzer_mode: str
    silent_mode: str

# Simulated sensor state (production: read from GPIO)
current_status = {
    "temperature": 25.5,
    "humidity": 60.2,
    "fan_state": "ON",
    "buzzer_state": "OFF",
    "fan_mode": "AUTO",
    "buzzer_mode": "AUTO",
    "silent_mode": "OFF",
}

@app.get("/api/status", response_model=BakeryStatus)
async def get_status():
    return current_status

@app.post("/api/control")
async def control_device(command: ControlCommand):
    device = command.device
    mode = command.mode
    valid_devices = {"fan", "buzzer", "silent_mode"}
    valid_modes = {"AUTO", "ON", "OFF"}
    if device not in valid_devices:
        raise HTTPException(status_code=400, detail=f"Invalid device: {device}")
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")
    if device == "fan":
        current_status["fan_mode"] = mode
        current_status["fan_state"] = "ON" if mode == "ON" else "OFF" if mode == "OFF" else "--"
    elif device == "buzzer":
        current_status["buzzer_mode"] = mode
        current_status["buzzer_state"] = "ON" if mode == "ON" else "OFF" if mode == "OFF" else "--"
    elif device == "silent_mode":
        current_status["silent_mode"] = mode
    return {"status": "ok", "message": f"{device} set to {mode}"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "smart-bakery-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
```

### 3.3 FastAPI Core Concepts

| Concept | Description | Smart Bakery Application |
|---------|-------------|-------------------------|
| **Path Operation** | `@app.get()` / `@app.post()` defines API endpoint & HTTP method | `GET /api/status`, `POST /api/control` |
| **Pydantic Model** | `BaseModel` defines request/response data models, auto-validates types | `ControlCommand`, `BakeryStatus` |
| **Dependency Injection** | `Depends()` injects shared dependencies | Can inject DB connections, sensor objects |
| **Async/Await** | Async request handling, non-blocking event loop | `async def get_status()` |
| **Auto docs** | Access `/docs` (Swagger) or `/redoc` for interactive API docs | Invaluable for API debugging |
| **CORS Middleware** | Allow cross-origin requests | Mobile and Pi on different devices |

### 3.4 FastAPI vs Flask -- Interview Comparison

| Dimension | FastAPI | Flask |
|-----------|---------|-------|
| **Performance** | Async + Uvicorn, high concurrency | Sync WSGI, single-threaded by default |
| **Data validation** | Built-in Pydantic auto-validation | Manual validation or marshmallow |
| **Doc generation** | Auto-generated OpenAPI + Swagger UI | Requires flasgger plugin |
| **Async support** | Native async/await | Requires Quart (async Flask) |
| **Learning curve** | Gentle (with Python basics) | Gentle (simpler but fewer features) |
| **Use case** | IoT backends, microservices, high-concurrency APIs | Traditional web apps, small projects |

### 3.5 Uvicorn Startup

```bash
# Basic startup
uvicorn main:app --host 0.0.0.0 --port 5000

# Hot reload (development mode)
uvicorn main:app --reload --host 0.0.0.0 --port 5000

# Production mode (single worker recommended for Raspberry Pi)
uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1
```

---

## 4. RESTful API Design

### 4.1 Core Principles

| Principle | Description | Smart Bakery Practice |
|-----------|-------------|----------------------|
| **Resource-oriented** | Each URL represents a resource | `/api/status`, `/api/control` |
| **HTTP method semantics** | GET read / POST create / PUT update / DELETE delete | `GET /api/status` read, `POST /api/control` create control command |
| **Stateless** | Each request contains all needed info | Every request carries complete IP info |
| **Uniform interface** | Standard HTTP status codes & response format | 200 OK, 400 Bad Request, 404 Not Found |
| **JSON format** | Request/response use JSON | `{ "temperature": 25.5, "humidity": 60.2 }` |

### 4.2 RESTful API Design Principles (Interview Must-Know)

| Question | Correct Answer |
|----------|---------------|
| Difference between GET and POST? | GET is idempotent, safe, cacheable; POST is non-idempotent, modifies resources, not cacheable |
| How to use status codes? | 200 success / 201 created / 400 client error / 401 unauthorized / 403 forbidden / 404 not found / 500 server error |
| URL naming conventions? | Lowercase + hyphens; plural nouns; hierarchy: `/api/devices/fan/status` |
| Why stateless? | Easy horizontal scaling; reduces server memory; clear client responsibility |
| Version management? | URL prefix: `/api/v1/status`; or Header: `Accept: application/vnd.smartbakery.v1+json` |

---

## 5. Chart.js Data Visualization

### 5.1 Chart.js Introduction

Chart.js is a lightweight **JavaScript charting library** based on HTML5 Canvas rendering.

| Feature | Description |
|---------|-------------|
| **Rendering** | HTML5 Canvas (not SVG, better performance) |
| **File size** | ~70KB minified |
| **Chart types** | Line, bar, pie, radar, scatter, bubble, etc. |
| **Responsive** | Responsive by default, auto-adapts to container size |
| **Animation** | Built-in animations, smooth interaction |

### 5.2 Chart.js in Online Exam Platform

```javascript
// Chart.js rendering logic
function renderExamChart(stats) {
    const ctx = document.getElementById('examChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: stats.labels,
            datasets: [{
                label: 'Exam Count',
                data: stats.counts,
                backgroundColor: [
                    'rgba(54, 162, 235, 0.5)',
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
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: 'Exam Count by Subject' },
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Count' } },
                x: { title: { display: true, text: 'Subject' } }
            }
        }
    });
}
```

---

## 6. Linux Basics & Raspberry Pi Operations

### 6.1 Raspberry Pi Environment Overview

| Component | Purpose |
|-----------|---------|
| **Raspberry Pi OS (Debian)** | Base operating system |
| **Python 3** | Backend development language |
| **GPIO** | Pins connecting sensors and actuators |
| **systemd** | System service manager (auto-start on boot) |
| **SSH** | Remote login for Pi management |

### 6.2 Essential Linux Commands

```bash
# Navigation
pwd                           # Show current path
ls -la                        # List all files (incl. hidden)
cd /home/pi/smart-bakery/     # Change directory

# File operations
cat main.py                   # View short file content
less main.py                  # Page through long files
tail -f logs/app.log          # Real-time log tracking

# Process management
ps aux | grep python          # Find Python processes
top                           # Real-time process monitor

# systemd service management
sudo systemctl status smart-bakery    # Check service status
sudo systemctl restart smart-bakery   # Restart service
sudo journalctl -u smart-bakery -f    # View service logs

# Network & API testing
curl http://192.168.1.166:5000/api/status
curl -X POST http://192.168.1.166:5000/api/control \\
  -H "Content-Type: application/json" \\
  -d '{"device": "fan", "mode": "ON"}'

# Port checking
netstat -tlnp                  # View listening ports
ss -tlnp                       # Modern port view
lsof -i :5000                  # Check process on port 5000
```

### 6.3 systemd Service Configuration (Auto-Start on Boot)

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
NoNewPrivileges=true
ProtectHome=false
ProtectSystem=full

[Install]
WantedBy=multi-user.target
```

### 6.4 GPIO Operations (Hardware Control)

```python
import RPi.GPIO as GPIO

FAN_PIN = 17
BUZZER_PIN = 27
DHT22_PIN = 4

GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)

def set_fan(state: bool):
    GPIO.output(FAN_PIN, GPIO.HIGH if state else GPIO.LOW)

def set_buzzer(state: bool):
    GPIO.output(BUZZER_PIN, GPIO.HIGH if state else GPIO.LOW)

def read_dht22():
    import Adafruit_DHT
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, DHT22_PIN)
    return temperature, humidity
```

---

## 7. Automated Deployment & CI/CD Thinking

### 7.1 Raspberry Pi Deployment Script

```bash
#!/bin/bash
# deploy.sh -- Smart Bakery one-click deployment
set -e

PI_USER="pi"
PI_HOST="${1:-192.168.1.166}"
APP_DIR="/home/pi/smart-bakery"

# 1. Local syntax check
python3 -m py_compile main.py || { echo "Python syntax error"; exit 1; }

# 2. Sync code to Pi
rsync -avz --delete --exclude="__pycache__" --exclude=".git" \\
    -e ssh ./ ${PI_USER}@${PI_HOST}:${APP_DIR}/

# 3. Install dependencies
ssh ${PI_USER}@${PI_HOST} "cd ${APP_DIR} && pip3 install -r requirements.txt --quiet"

# 4. Restart service
ssh ${PI_USER}@${PI_HOST} "sudo systemctl restart smart-bakery"

# 5. Health check
sleep 2
HEALTH=$(curl -s http://${PI_HOST}:5000/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "Service running normally!"
else
    echo "Health check failed"
    exit 1
fi
```

### 7.2 CI/CD Thinking (For QA Interview)

| Practice | Smart Bakery Implementation |
|----------|----------------------------|
| **Automated testing** | Pre-commit syntax check |
| **Automated deployment** | `deploy.sh` one-click deploy with code sync, deps install, restart, health check |
| **Monitoring** | `/health` endpoint + log rotation via logrotate |
| **Rollback capability** | Git version control for quick revert |
| **Environment consistency** | `requirements.txt` locks dependency versions |

---

## 8. From Projects to QA Interview: Common Q&A

### 8.1 Project-Related

#### Q: "What is the data flow in your Smart Bakery project?"

> **Answer**: The overall data flow has three parts:
>
> **Status retrieval (frontend pulls)**: Flutter sends `GET /api/status` every 800ms -> FastAPI backend reads DHT22 sensor data -> serializes to JSON -> Flutter parses JSON and updates UI.
>
> **Device control (frontend pushes)**: User taps a button -> Flutter sends `POST /api/control` with body `{"device": "fan", "mode": "ON"}` -> FastAPI receives and validates -> sets GPIO pin -> physically controls device -> returns `200 OK`.
>
> **Network discovery**: On first connection, Flutter scans the `192.168.x.166` subnet (800ms timeout) to find the Pi on port 5000.

#### Q: "How do you ensure API robustness?"

> **Answer**: Three approaches:
> 1. **Input validation**: FastAPI's Pydantic models auto-validate request format; invalid requests get 400
> 2. **Exception handling**: Sensor reads have try/except + retry mechanism (3 attempts)
> 3. **Service self-healing**: systemd configured with `Restart=always`, auto-restarts within 5 seconds

### 8.2 Python & RESTful API Basics

#### Q: "What is Python's GIL? How does it affect your IoT backend?"

> **Answer**: GIL (Global Interpreter Lock) means only one thread can execute Python bytecode at a time. For Smart Bakery, FastAPI uses async I/O (asyncio + Uvicorn), not multi-threading. Sensor reads are primarily I/O waits, so GIL impact is minimal. For true parallel computation, use `multiprocessing` or C extensions.

#### Q: "What's the difference between GET and POST?"

> **Answer**: GET is idempotent, safe, cacheable (params in URL). POST is non-idempotent, modifies resources (params in body). PUT is idempotent full replacement. DELETE is idempotent removal. PATCH is partial update.

### 8.3 Linux / Raspberry Pi

#### Q: "If the Raspberry Pi can't connect to WiFi, how do you debug?"

> **Answer**: Bottom-up OSI model:
> 1. Physical: Power LED? WiFi module indicator?
> 2. Link: `iwconfig wlan0` -- connected to router?
> 3. Network: `ping 192.168.1.1` (gateway)
> 4. Transport: `curl http://localhost:5000/api/status` (local test)
> 5. Application: Can phone app ping the Pi IP?

---

## 9. Interview Practical Code Snippets

### 9.1 Simple FastAPI Application (Interview High-Frequency)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    in_stock: bool = True

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

### 9.2 RESTful API Testing with curl

```bash
# Health check
curl http://localhost:5000/health

# Get sensor status
curl http://localhost:5000/api/status | jq .

# Control device
curl -X POST http://localhost:5000/api/control \\
  -H "Content-Type: application/json" \\
  -d '{"device": "fan", "mode": "ON"}'

# Error test (invalid param)
curl -X POST http://localhost:5000/api/control \\
  -H "Content-Type: application/json" \\
  -d '{"device": "light", "mode": "ON"}'
# Expected: 400 Bad Request
```

### 9.3 Python API Automated Test Script

```python
import requests

BASE_URL = "http://192.168.1.166:5000"

def test_get_status():
    response = requests.get(f"{BASE_URL}/api/status", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "temperature" in data
    assert "humidity" in data
    print(f"Temp: {data['temperature']}C, Humidity: {data['humidity']}%")

def test_control_device(device: str, mode: str):
    payload = {"device": device, "mode": mode}
    response = requests.post(f"{BASE_URL}/api/control", json=payload, timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_invalid_control():
    payload = {"device": "invalid", "mode": "ON"}
    response = requests.post(f"{BASE_URL}/api/control", json=payload, timeout=5)
    assert response.status_code == 400

def test_health():
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

if __name__ == "__main__":
    test_health()
    test_get_status()
    test_control_device("fan", "ON")
    test_invalid_control()
    print("All tests passed!")
```

### 9.4 requirements.txt (Dependency Management)

```txt
fastapi==0.110.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
RPi.GPIO==0.7.1
Adafruit-DHT==1.4.0
gpiozero==2.0
pytest==8.0.0
requests==2.31.0
httpx==0.27.0
```

---

## Appendix: Interview High-Frequency Tech Concepts Quick Reference

### HTTP Status Codes

| Code | Meaning | Scenario |
|------|---------|----------|
| **200 OK** | Success | `GET /api/status` returns data |
| **201 Created** | Created | `POST /api/items` new resource |
| **204 No Content** | Success, no body | `DELETE` successful |
| **400 Bad Request** | Bad request | `POST /api/control` invalid params |
| **401 Unauthorized** | Not authenticated | No login or expired token |
| **403 Forbidden** | No permission | Insufficient role |
| **404 Not Found** | Resource not found | Non-existent endpoint |
| **500 Internal Server Error** | Server internal error | Unhandled sensor exception |

### Linux Troubleshooting Flow (When API is Down)

```
Phone app shows "Offline"
        |
        v
Can phone ping the Pi IP?
   +-- No  -> Check WiFi, same network
   +-- Yes
        |
        v
Can `curl localhost:5000/api/status` work on Pi?
   +-- No  -> `systemctl status smart-bakery`, `journalctl -u smart-bakery -f`
   +-- Yes
        |
        v
Is port 5000 listening? (`ss -tlnp | grep 5000`)
   +-- No  -> uvicorn not started / port occupied
   +-- Yes
        |
        v
Can `curl http://[pi-ip]:5000/api/status` work from phone?
   +-- No  -> Firewall (`sudo ufw status`) / uvicorn bound to 127.0.0.1 instead of 0.0.0.0
   +-- Yes -> Problem is in Flutter app: IP config / network permissions
```

---

> **Document note**: Based on Smart Bakery (Flutter + Raspberry Pi IoT) and Online Exam Platform (Blazor + Chart.js) projects from https://github.com/BoooSAMA, providing systematic tech knowledge preparation for Python, FastAPI, RESTful API, Chart.js, Linux automation areas.

> Prepared for QA Engineer Intern interview
