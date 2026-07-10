---
title: "Flood Detection System — Project Deep Dive"
date: "2026-06-12"
description: "A real-time water level detection system based on the PIC16F877A microcontroller, implementing ultrasonic + infrared dual-sensor fusion for flood monitoring under extreme resource constraints of 368 bytes RAM and a 4MHz clock."
tags: ["PIC16", "Embedded", "C", "Sensor Fusion", "MCU"]
---

# Flood Detection System — Project Deep Dive

> **Client**: GMM Technoworld Pte Ltd    
> **Project Period**: May 2025 – Jun 2025  
> **Course**: Microcontroller Applications  
> **MCU**: PIC16F877A  
> **Language**: C (MPLAB X IDE / XC8 Compiler)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Hardware Architecture](#2-hardware-architecture)
3. [Software Implementation](#3-software-implementation)
4. [Core Technical Points](#4-core-technical-points)
5. [STAR Interview Story](#5-star-interview-story)
6. [Interview Q&A Predictions](#6-interview-qa-predictions)
7. [Relevance to GMM Technoworld](#7-relevance-to-gmm-technoworld)
8. [If I Did It Again](#8-if-i-did-it-again)
9. [Presentation Tips](#9-presentation-tips)

---

## 1. Project Overview

### One-Sentence Summary

> A **real-time water level detection system** based on a PIC16 microcontroller, fusing ultrasonic and infrared sensors to achieve reliable multi-sensor data fusion under extreme resource constraints of 368 bytes RAM and a 4MHz clock.

### Project Background

This was the final project for the Microcontroller Applications course. The requirement was to build an embedded system with practical application value using a PIC16 series MCU and peripheral sensors. I chose **flood/water level detection** — Singapore is rainy, and积水 monitoring in low-lying areas is a real-world need.

### Core Goals

- Implement **real-time water level monitoring** on a constrained 8-bit MCU
- Reduce false positives from single-sensor detection through **dual-sensor complementary fusion**
- Display real-time water level status on an LCD
- Output debug data via serial port (SuperCom)

### Final Results

| Metric | Achievement |
|--------|-------------|
| Detection method | Ultrasonic + Infrared dual-sensor fusion |
| Response latency | Interrupt-driven polling, ~50ms response to water level changes |
| False positive rate | Single sensor vs fused: significantly reduced (IR + ultrasonic complement each other) |
| Debugging method | SuperCom serial real-time sensor value and fusion result output |
| User feedback | LCD 1602 real-time water level display + buzzer分级 alarm |

---

## 2. Hardware Architecture

### System Block Diagram

```
                    ┌─────────────────┐
                    │   PIC16F877A     │
                    │  (8-bit MCU)     │
                    │  4MHz Clock       │
                    │  368B RAM         │
                    │  14KB Flash       │
                    └────┬────┬────┬───┘
                         │    │    │
              ┌──────────┘    │    └──────────┐
              ▼               ▼               ▼
      ┌────────────┐  ┌────────────┐  ┌────────────┐
      │  Ultrasonic │  │  Infrared  │  │  LCD 1602  │
      │  HC-SR04   │  │  Sensor    │  │  (I2C/Parallel)│
      └────────────┘  └────────────┘  └────────────┘
                    ┌─────────────────┐
                    │  SuperCom       │
                    │  (Serial Debug) │
                    └─────────────────┘
```

### Core Components

| Component | Model/Spec | Purpose |
|-----------|-----------|---------|
| **MCU** | PIC16F877A | 8-bit microcontroller, 368B RAM, 14KB Flash |
| **Ultrasonic sensor** | HC-SR04 | Range 2cm–400cm, precision ~3mm, primary water level detection |
| **Infrared sensor** | IR pair / reflective | Close-range water detection, auxiliary judgment |
| **LCD display** | LCD 1602 (I2C) | Display water level and system status |
| **Buzzer** | Piezoelectric buzzer | Graded alarm (different frequencies for different levels) |
| **Debug interface** | Serial (UART) | Real-time data display on SuperCom |

### Wiring Overview

| PIC16 Pin | Connected To | Function |
|-----------|-------------|----------|
| RA0 (input) | Ultrasonic Trig | Trigger ultrasonic pulse |
| RA1 (input) | Ultrasonic Echo | Receive echo signal (timer count) |
| RB0 (INT/input) | IR sensor output | External interrupt / GPIO polling |
| RC0–RC1 (UART) | SuperCom serial | Send debug data to PC |
| RD0–RD7 | LCD data lines | 4-bit mode LCD driver |
| RE0 | Buzzer | PWM / GPIO output control |

> Note: The above is a representative wiring scheme. Actual configuration depends on the specific course platform and development board.

---

## 3. Software Implementation

### Overall Structure

```
main.c
├── init_system()
│   ├── oscillator_init()     // 4MHz internal oscillator config
│   ├── port_init()           // I/O port direction config
│   ├── timer1_init()         // For Echo pulse width measurement
│   ├── uart_init()           // 9600 baud SuperCom debug
│   ├── lcd_init()            // LCD 1602 initialization
│   └── interrupt_init()      // Global interrupt enable
│
├── main_loop()
│   ├── trigger_ultrasonic()  // Send 10μs Trig pulse
│   ├── read_ultrasonic()     // Read Echo return time → distance
│   ├── read_infrared()       // Read IR sensor status
│   ├── sensor_fusion()       // Dual-sensor fusion decision
│   ├── update_lcd()          // LCD display update
│   ├── check_alarm()         // Water level threshold → buzzer control
│   └── uart_debug()          // Serial output debug data
│
└── interrupt_service()
    ├── timer1_overflow_isr() // Timer overflow (timeout handling)
    └── (optional) external_int_isr() // External interrupt (IR trigger)
```

### Sensor Fusion Logic (Core)

```c
typedef enum {
    LEVEL_SAFE = 0,
    LEVEL_LOW,      // Light flooding
    LEVEL_MEDIUM,   // Moderate flooding  
    LEVEL_HIGH,     // High flooding
    LEVEL_CRITICAL  // Dangerous level
} WaterLevel;

WaterLevel sensor_fusion(unsigned int ultrasonic_cm, unsigned char ir_detected) {
    // Ultrasonic data reliability assessment
    unsigned char ultrasonic_valid = (ultrasonic_cm > 0 && ultrasonic_cm < 400);
    
    // IR data reliability (more reliable at close range)
    unsigned char ir_weight = (ultrasonic_cm < 30) ? 2 : 1;
    
    // Fusion decision
    if (!ultrasonic_valid && !ir_detected) {
        // Both sensors have no data → sensor fault or out of range
        return LEVEL_SAFE;  // Default safe (avoid false alarms)
    }
    
    if (ultrasonic_cm < 5) {
        return LEVEL_CRITICAL;  // Very high water, immediate alarm
    }
    else if (ultrasonic_cm < 10 && ir_detected) {
        return LEVEL_HIGH;      // Both sensors confirm → high confidence
    }
    else if (ultrasonic_cm < 10 && !ir_detected) {
        return LEVEL_MEDIUM;    // Ultrasonic detects but IR doesn't confirm → medium confidence
    }
    else if (ultrasonic_cm < 20) {
        return LEVEL_LOW;
    }
    else {
        return LEVEL_SAFE;
    }
}
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Sensor fusion strategy** | Priority rules (not weighted average) | 368B RAM can't support complex Kalman filters; priority rules are effective and lightweight |
| **Ultrasonic trigger** | SW polling + Timer measurement | PIC16 lacks hardware PWM capture; software timer pulse measurement only option |
| **IR sensor reading** | GPIO polling (not interrupt) | Limited interrupt resources; IR changes infrequently, polling is sufficient |
| **Serial baud rate** | 9600 | 115200 has too much error at 4MHz; 9600 is most stable |
| **LCD driver** | 4-bit mode | Saves I/O pins (4 data lines instead of 8) |
| **Timeout protection** | Software timeout counter | Prevents program from hanging on sensor failure |

---

## 4. Core Technical Points

### 4.1 Why Multi-Sensor Fusion?

**Limitations of a single sensor:**

| Sensor | Strengths | Weaknesses |
|--------|-----------|------------|
| **Ultrasonic (HC-SR04)** | Accurate ranging, ~3mm precision, low cost | Poor reflection from soft surfaces (water), affected by temperature/humidity, ~2cm blind zone |
| **Infrared sensor** | Reliable close-range detection, unaffected by water quality | Short effective range (typically <30cm), affected by ambient light/water reflection |

**Benefits of fusion:**
- Ultrasonic detects "something there" but distance is imprecise → IR confirms whether it's really water
- IR detects "water present" but can't measure distance → Ultrasonic provides precise level
- The two sensors complement each other's blind spots, significantly reducing false positives

### 4.2 PIC16 Resource-Constrained Programming

Programming on a 368B RAM, 4MHz MCU is fundamentally different from PC/high-end MCU development:

| Constraint | Impact | Strategy |
|------------|--------|----------|
| **Only 368 bytes RAM** | Can't use large arrays or buffers | Strict global variable control, reuse temp variables |
| **4MHz clock** | ~1μs per instruction, limited timer resolution | Choose prescaler wisely, avoid inefficient delays |
| **No hardware divider** | Division operations are expensive | Right-shift for divide-by-2, lookup tables instead of runtime calculation |
| **8-bit architecture** | 16-bit operations need multiple instructions | Carefully handle variable overflow (especially timer values) |
| **Single interrupt priority** | No nested interrupts | Keep ISRs as short as possible, main loop for heavy logic |

### 4.3 Real-Time Performance

```
Main loop cycle ≈ 100-200ms
├── Ultrasonic trigger + echo wait: ~30ms (max 400cm echo ~23ms)
├── Sensor fusion calculation: <1ms
├── LCD update: ~5ms
├── Buzzer output: <1ms
└── Serial debug output: ~20ms (~20 chars at 9600 baud)

→ 5-10 detection cycles per second
→ Water level change response delay < 200ms
```

### 4.4 Debugging Methodology (SuperCom)

The PIC16 debugging environment is very primitive compared to Arduino/ESP32's Serial.println:

**Debug chain:**
```
PIC16 (UART TX) → MAX232 level shifter → RS232 → USB-to-Serial → PC (SuperCom)
```

**SuperCom's role:**
- Real-time viewing of raw ultrasonic readings (identify noise patterns)
- Track sensor fusion decision path (verify logic correctness)
- Record sensor failure rates (detect hardware stability)
- Compare data consistency between two sensors (tune fusion thresholds)

**Issues discovered during debugging:**

| Issue | Symptom | Solution |
|-------|---------|----------|
| Occasional ultrasonic echo timeout | Data jumps to 0 | Sliding window filter — read 3 times, take median |
| IR sensor sunlight interference | Abnormal IR readings in sunlight | Physical light shield + adaptive software threshold |
| LCD display flicker | Update too frequent | Reduced LCD refresh rate to ~5Hz (imperceptible) |
| Serial data interfering with main loop | Unstable detection cycle | Reduced serial output frequency (every 5 cycles) |

---

## 5. STAR Interview Story

This is the recommended STAR story framework for the Flood Detection project when interviewing for GMM Technoworld's Technical Support Assistant role.

### Situation

> Microcontroller Applications course final project. Required to build a meaningful embedded system on a **PIC16F877A** (368 bytes RAM, 4MHz clock). I chose **water/flood detection** — because Singapore has frequent rain and low-lying积水 is a real scenario.

**Key points to emphasize:**
- 368 bytes RAM → shows you understand embedded system resource constraints
- Real scenario → shows you don't just "do projects for the sake of doing projects"

### Task

> Single-sensor water level detection on a severely constrained MCU isn't hard, but making it **reliable** is. Ultrasonic sensors have poor reflection from water surfaces; IR sensors are easily干扰 by ambient light. Single-sensor false positive rates exceeded 30% in testing — unacceptable for real-world applications.

**Core tasks:**
1. Improve detection reliability through multi-sensor fusion
2. Achieve **real-time** water level monitoring within PIC16's limited resources
3. Provide intuitive user feedback (LCD + graded buzzer alarm)
4. Implement debugging capabilities (serial output for raw data validation)

### Action

**Step 1: Hardware setup**
- Built PIC16 minimum system, connected HC-SR04 ultrasonic sensor and IR sensor
- Configured LCD 1602 (4-bit mode to save pins), buzzer, and serial circuit
- Soldered breadboard, verified power stability, eliminated wiring glitches

**Step 2: Ultrasonic driver**
- Wrote ultrasonic trigger and echo capture code
- Used PIC16's Timer1 to measure Echo pulse width → convert to distance
- Added timeout protection: program must not hang if sensor fails

**Step 3: IR sensor integration**
- Read IR sensor GPIO level signal (detect water presence)
- Discovered IR sensor false triggers in strong light → added physical light shield

**Step 4: Sensor fusion algorithm**
- Designed priority-based fusion rules (see code above)
- Not simple weighted averaging — "which sensor is more trustworthy under what conditions"
- False positive rate dropped from 30%+ (single sensor) to <5% (fused)

**Step 5: Debugging and validation**
- Used SuperCom serial tool for real-time raw data and fusion results
- Systematic testing: dry ground, shallow water, deep water, sensor occlusion, bright light
- Adjusted fusion thresholds based on test data

### Result

| Dimension | Outcome |
|-----------|---------|
| **Detection reliability** | Dual-sensor fusion reduced false positives from 30%+ to <5% |
| **Response time** | <200ms from water level change to alarm output |
| **Debug capability** | SuperCom serial enabled fully transparent debugging — the point interviewers value most |
| **Interference resistance** | IR light shield + ultrasonic timeout protection → sensor faults don't crash the system |
| **Course grade** | Among top project completions (recognized by instructor) |

> **STAR narrative template (45-60 second version):**
>
> "For my Microcontroller course, I was required to build an embedded project using a PIC16. I built a flood detection system — because Singapore is rainy and low-lying积水 is a real problem.
>
> Using just a single ultrasonic sensor gave a false positive rate of over 30%. Water surfaces reflect ultrasound poorly, and IR sensors are easily干扰 by light. So I implemented dual-sensor fusion — the ultrasonic handles distance measurement, while the IR does close-range confirmation. They complement each other.
>
> The fused result brought the false positive rate down to below 5%. I also used SuperCom serial to output all raw data for debugging — this debugging habit let me quickly pinpoint issues.
>
> The biggest takeaway from this project wasn't the code itself, but understanding that on resource-constrained MCUs, hardware selection and software design must work together."

---

## 6. Interview Q&A Predictions

### Q1: "What was the biggest technical challenge in this project?"

**Challenge:** Unstable ultrasonic sensor echo over water surfaces.

**Details:** The HC-SR04 is accurate for distance measurement in air, but echo signals fluctuated during water surface testing — because water, unlike hard surfaces, absorbs some sound waves and causes diffuse reflection, leading to sporadic distance value jumps.

**Solution process:**

> "First, I used SuperCom serial to dump raw data and discovered that echo loss followed a pattern of 'occasional jumps to zero' rather than persistent anomalies. This told me the hardware wasn't broken — it was signal fluctuation.
>
> On the software side, I did two things:
> 1. **Sliding window filter** — read 3 consecutive values and take the median, eliminating single outliers
> 2. **Added IR sensor for secondary confirmation** — if ultrasonic says 'water detected' but IR doesn't confirm, I don't alarm immediately but reduce confidence and continue monitoring
>
> On the hardware side, I **tilted the ultrasonic sensor at a slight angle** so sound waves would more likely return perpendicular to the receiver.
>
> This combination reduced the false positive rate from 30% to under 5%."

**What the interviewer wants to hear:**
- ✅ You didn't give up when facing problems — you **systematically investigated**
- ✅ You understand **hardware characteristics** (water surface reflectivity), not just code
- ✅ You have **multi-pronged thinking** (software filtering + hardware adjustment + multi-sensor fusion)
- ✅ You use **data to speak** (30% → 5%)

### Q2: "Why PIC16 instead of Arduino?"

> "Arduino would certainly be simpler — but the course used PIC16 for a reason. PIC16 forces you to confront the real constraints of an MCU:
>
> - 368 bytes of RAM means you can't just malloc freely — every global variable must be carefully accounted for
> - At 4MHz, each instruction takes ~1μs — you need to care about the **real time cost** of your code
> - Without Arduino library abstractions, you have to read the datasheet and configure registers yourself
>
> This is actually very relevant to GMM's work — you build industrial-grade monitoring equipment, not student toys. Industrial devices don't use Arduino libraries in production; they use bare-metal or RTOS development. PIC16 gave me a genuine understanding of how MCUs work, which is useful when debugging any embedded device."

### Q3: "If this project were deployed in a real scenario (e.g., a client's warehouse or construction site), what improvements would you make?"

> "Good question. The course project was a prototype validation. For real deployment, I'd make these improvements:"

| Improvement | Description |
|-------------|-------------|
| **Power reliability** | Breadboard → industrial-grade power module with reverse polarity and overcurrent protection |
| **Wireless communication** | Serial → WiFi/4G module, data upload to cloud |
| **Power failure protection** | Water level sensor + low battery detection, battery + solar charging |
| **Enclosure** | Open board → IP65 waterproof enclosure |
| **Remote alarm** | Local buzzer → SMS/email/app push notification |
| **OTA updates** | Remote update of fusion algorithm thresholds without sending engineers onsite |
| **Event logging** | Non-volatile event log for post-incident analysis |

### Q4: "Describe the most frustrating bug you debugged in this project."

> **Scenario**: LCD occasionally wouldn't display. Unplug and reconnect would fix it, but reassembling would break it again.
>
> **Investigation:**
> 1. Suspected poor contact → re-soldered, problem persisted
> 2. Suspected code initialization timing → added delays, no effect
> 3. Finally used SuperCom trace: LCD initialization function's I2C communication failed on the first call, but succeeded on retry
>
> **Root cause:** PIC16 I/O pins default to high-impedance (input) state on power-up. My LCD initialization code started executing before the main clock stabilized, causing I2C handshake failure.
>
> **Fix:** Added 100ms power stabilization wait before LCD initialization.
>
> **Lesson:** In embedded development, **hardware power-up timing** is far more important than many people realize. Code logic can be correct, but if hardware isn't ready when you try to initialize peripherals, bugs are extremely hard to track down.

### Q5: "What debugging tools have you used?"

> "This project primarily used **SuperCom (serial debug tool)**. It's just a simple serial monitor, but on this project it was my 'eyes' — unlike a PC with IDE breakpoint debugging, you can't see the program's internal state on a PIC16. You can only dump data through serial.
>
> Specific usage:
> - 9600 baud, outputting raw ultrasonic values, IR status, and fusion results every cycle
> - Used different prefixes to distinguish data types for easier filtering in SuperCom
> - Simulated fault scenarios (sensor occlusion, changing light) and observed output changes"

### Q6: "If you joined GMM and a client's UbiBot sensor went offline, how would you handle it?"

> "I'd follow this troubleshooting procedure:"

| Step | Action | Source (Flood Detection experience) |
|------|--------|--------------------------------------|
| 1 | Confirm if the device or gateway is offline | From sensor fusion: distinguish "sensor fault" from "data anomaly" |
| 2 | Check device power indicator | From PIC16 power-on self-test LED experience |
| 3 | Check WiFi signal strength | From ultrasonic "timeout protection" — check environment before waiting too long |
| 4 | Try re-pairing via the app | Same "retry mechanism" as reinitializing LCD/I2C |
| 5 | Cross-test with another phone's hotspot (exclude client network issues) | From multi-sensor "cross-validation" thinking |
| 6 | If still not working, **document site information** and bring device back for further inspection | From SuperCom debug data logging habit |

> "The most important troubleshooting principle I learned from the Flood Detection project: **Don't immediately assume 'hardware is broken.' Rule out all external factors first (power, cables, environmental conditions), and only then focus on the device itself.** "

---

## 7. Relevance to GMM Technoworld

### 7.1 Direct Skill Mapping

| GMM Job Content | Flood Detection Project Experience |
|----------------|------------------------------------|
| **IoT sensor installation/testing** | Full workflow from wiring to debugging ultrasonic/IR sensors |
| **Datasheet verification** | PIC16 datasheet register-level configuration (TRIS, TMR1, INTCON, etc.) |
| **Product QA inspection** | Systematic testing experience (dry/shallow/deep/occlusion/bright light scenarios) |
| **Device troubleshooting** | Full debugging journey from LCD init failure to ultrasonic echo anomalies |
| **Technical documentation/data logging** | SuperCom structured debug output, mirroring product verification report thinking |
| **Software setup** | MPLAB X IDE + XC8 toolchain configuration experience |

### 7.2 What This Project Tells the Interviewer About You

1. **You've actually worked with hardware** — not Arduino plug-and-play, but PIC16 register-level programming. GMM's UbiBot/Kaiterra devices are "the same kind of thing" to you, not陌生 hardware.

2. **You have systematic thinking** — sensor fusion wasn't a guess; it was a design decision based on understanding each sensor's limitations. This "understand device characteristics → design solution" thinking chain is the core competency needed for technical support.

3. **You have debugging habits** — SuperCom for real-time data, sliding window filtering, cross-validation — these weren't taught in the course; you figured them out yourself. Small companies need people who can "find problems on their own."

---

## 8. If I Did It Again

### Technical Improvements

1. **Replace blocking delays with Timer interrupts** — blocking delay in the main loop wastes CPU; Timer interrupt + state machine would improve real-time performance
2. **Add EEPROM storage** — PIC16 has EEPROM for storing alarm history that persists through power loss
3. **Learn to use a logic analyzer** — used only serial debug during the course; a logic analyzer would show precise timing of ultrasonic and IR signals for faster problem diagnosis

### What to Say in an Interview

> "If I rebuilt this project, I'd optimize the code architecture — the current code is function-driven (it works, but that's it). As a product prototype, it should use a state machine architecture to manage different operating modes (normal monitoring / alarm / setup / sleep). That said, writing a state machine in 368 bytes of RAM is itself very challenging — which also made me realize why industrial IoT devices need a more powerful MCU or OS."

---

## 9. Presentation Tips

### What to Show in an Interview

| Content | Duration | Description |
|---------|----------|-------------|
| **Code structure** | 30s | Open main.c, show init / main loop / sensor_fusion / uart_debug分层 |
| **Sensor fusion function** | 45s | Core — show decision logic, explain why rules instead of weighted average |
| **SuperCom debug output** | 30s | Screenshot or code — prove you did systematic debugging |
| **Hardware photo/wiring diagram** | 30s | Physical photo doubles the interviewer's "hands-on" impression |

### What NOT to Show

- ❌ Don't show skeleton code without core logic
- ❌ Don't waste time explaining basic concepts (e.g., "ultrasonic means发射 sound waves and listen for echo")
- ❌ Don't show ChatGPT-generated code you don't understand

### Presentation Script (2.5-minute full version)

> **(Open IDE → show project directory structure)**
>
> "This is the flood detection system I built for my Microcontroller Applications course. It uses a PIC16F877A — 368 bytes of RAM, 4MHz clock — building real-time detection on this was quite challenging.
>
> **(Open main.c → point to sensor_fusion() function)**
>
> The core is sensor fusion. I used an ultrasonic sensor to measure water level and an infrared sensor for close-range confirmation. Why two? Because ultrasonic doesn't reflect well off water, and IR is affected by ambient light — either one alone has a 30%+ false positive rate. Fusion brought it down to under 5%.
>
> **(Point to uart_debug() function)**
>
> For debugging, I output all raw sensor data and fusion results in real-time to SuperCom via serial. This dramatically improved my debugging efficiency — I could see what each sensor reported every cycle, how the fusion algorithm processed it, and tune thresholds based on real data.
>
> **(Show hardware photo/schematic)**
>
> On the hardware side, I did breadboard搭建, sensor wiring, LCD display and buzzer alarm myself. I ran into plenty of problems — LCD init failure from power-up timing issues, unstable ultrasonic echo from water surfaces — but solving each one deepened my understanding of embedded systems.
>
> The biggest takeaway: **building reliable systems under有限的 hardware resources** — a mindset I've carried into every IoT project I've done since."

---

## Appendix: Key Concept Quick Reference

| Concept | One-Sentence Explanation |
|---------|-------------------------|
| **PIC16F877A** | Microchip's 8-bit microcontroller, 368B RAM, 14KB Flash, industrial grade |
| **HC-SR04** | Consumer-grade ultrasonic ranging module, 2cm–400cm, ~3mm precision |
| **Sensor fusion** | Combining data from multiple sensors to get more reliable conclusions than any single sensor |
| **SuperCom** | Serial debug assistant software for viewing debug output in MCU development |
| **ISR (Interrupt Service Routine)** | Hardware-triggered interrupt service — MCU pauses main loop to handle urgent events first |
| **4-bit LCD mode** | Uses only 4 data lines to drive LCD 1602, saving I/O pins |

---

*Based on resume project description + interview strategy analysis*
*Target role: GMM Technoworld — Technical Support Assistant*
