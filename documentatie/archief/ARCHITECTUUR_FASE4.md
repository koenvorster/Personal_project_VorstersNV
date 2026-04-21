# 🏗️ Fase 4 – Architectuur Diagram

## Volledige Systeem-Overzicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│           VorstersNV Platform + Smart Home Integration                     │
│                                                                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                        🖥️ DEVELOPMENT MACHINE (Windows)                   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  VorstersNV Project (Docker)                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │  Frontend    │  │  API/Backend │  │  Database    │             │  │
│  │  │  (Next.js)   │  │  (FastAPI)   │  │  (PostgreSQL)│             │  │
│  │  │  :3000       │  │  :8080       │  │  :5432       │             │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │  │
│  │                                                                     │  │
│  │  Status: ✅ RUNNING                                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│                        HTTP/HTTPS Links                                │
│                        (Port Forwarding)                               │
│                                                                         │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     │ Network (LAN)
                     │ 192.168.x.x
                     │
┌────────────────────▼────────────────────────────────────────────────────┐
│                                                                          │
│              🖥️ LINUX SERVER (Old Laptop - Ubuntu 22.04)               │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Home Network (Docker Compose)                                    │ │
│  │                                                                    │ │
│  │  ┌──────────────────────────────────────────────────────────────┐ │ │
│  │  │                  Home Assistant Network                      │ │ │
│  │  │                                                              │ │ │
│  │  │  ┌──────────────┐    ┌─────────────┐    ┌──────────────┐  │ │ │
│  │  │  │ Home         │    │ MCP Server  │    │ Ollama       │  │ │ │
│  │  │  │ Assistant    │◄──►│ (FastAPI)   │◄──►│ (LLM)        │  │ │ │
│  │  │  │ :8123        │    │ :8000       │    │ :11434       │  │ │ │
│  │  │  └──────────────┘    └─────────────┘    └──────────────┘  │ │ │
│  │  │         ▲                   ▲                      ▲         │ │ │
│  │  │         │                   │                      │         │ │ │
│  │  │    Configs        Agents + Prompts        Models        │ │ │
│  │  │    Devices        REST API                 llama3         │ │ │
│  │  │    Scenes         Webhooks                 mistral        │ │ │
│  │  │    Automations    Metrics                               │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Smart Home Devices (Connected to HA)                         │   │
│  │                                                                │   │
│  │  ├─ Zigbee Hub (SONOFF ZBDongle)                             │   │
│  │  │  ├─ Light Bulbs (IKEA TRADFRI)                            │   │
│  │  │  ├─ Motion Sensors                                        │   │
│  │  │  ├─ Door/Window Sensors                                   │   │
│  │  │  └─ Temperature Sensors                                   │   │
│  │  │                                                             │   │
│  │  ├─ WiFi Devices                                             │   │
│  │  │  ├─ Smart Plugs                                           │   │
│  │  │  ├─ Thermostats                                           │   │
│  │  │  └─ Cameras                                               │   │
│  │  │                                                             │   │
│  │  └─ Cloud Devices (via integrations)                         │   │
│  │     ├─ Tuya Smart Devices                                    │   │
│  │     ├─ Meross Devices                                        │   │
│  │     └─ Google Home                                           │   │
│  │                                                                │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📡 Communication Flow

### 1️⃣ Motion Detection → Lights On

```
Physical World
    │
    ▼ (Zigbee Signal)
┌─────────────────────────────────────────────────────────────┐
│ Motion Sensor                                               │
│ (binary_sensor.motion_living_room = 'on')                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ (HA Automation)
┌─────────────────────────────────────────────────────────────┐
│ Home Assistant                                              │
│ (Automation: motion at night → call service)                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ (REST API POST)
┌─────────────────────────────────────────────────────────────┐
│ MCP Server                                                  │
│ POST /automation/trigger                                    │
│ {trigger: "motion", action: "turn_lights_on", ...}         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ (Load YAML + Prompts)
┌─────────────────────────────────────────────────────────────┐
│ Home Automation Agent                                       │
│ - System Prompt: "You are the Home Automation Agent..."     │
│ - Pre-Prompt: Examples of light control                     │
│ - User Input: "Motion detected at 23:45 in living room"    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ (HTTP POST)
┌─────────────────────────────────────────────────────────────┐
│ Ollama (LLM)                                                │
│ Model: llama3                                               │
│ Task: "Decide how to control lights"                       │
│ Response: {"status": "success", "actions": [...]}          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ (Parse JSON Response)
┌─────────────────────────────────────────────────────────────┐
│ MCP Server                                                  │
│ Execute Home Assistant Services                            │
│ {entity_id: "light.living_room", brightness: 100, ...}    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ (REST API Call)
┌─────────────────────────────────────────────────────────────┐
│ Home Assistant                                              │
│ Service: light.turn_on                                      │
│ Data: {entity_id: "light.living_room", ...}                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ (Zigbee Signal)
┌─────────────────────────────────────────────────────────────┐
│ Light Bulb                                                  │
│ State: ON, Brightness: 100, Color Temp: 3000K             │
└─────────────────────────────────────────────────────────────┘
    │
    ▼ (Physical Light)
💡 Light is ON!
```

### 2️⃣ VorstersNV Order → Smart Home

```
Customer Places Order
    │
    ▼
VorstersNV API
    │
    ├─► Webhook Event: order_created
    │
    ▼ (HTTP POST to MCP)
MCP Server
/automation/trigger
    │
    ├─ Trigger: "order_created"
    ├─ Action: "warehouse_lights_on"
    ├─ Entities: ["light.warehouse_zone_1"]
    │
    ▼
Home Automation Agent
    │
    ├─ Check business logic
    ├─ Call Ollama for decision
    │
    ▼
Execute HA Service
    │
    ▼
Warehouse Lights ON
    │
    ▼
Employee Gets Notification
```

---

## 🔄 Agent Execution Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Load Configuration                                  │
│ - Read YAML file (home_automation_agent.yml)               │
│ - Extract: model, temperature, capabilities               │
└────────────────┬────────────────────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────────────────────┐
│ Step 2: Load Prompts                                        │
│ - System Prompt: Define agent role                         │
│ - Pre-Prompt: Add context + examples                       │
│ - User Input: The actual task                              │
└────────────────┬────────────────────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────────────────────┐
│ Step 3: Build Full Prompt                                   │
│ Combine all prompts into single request                    │
│ Format: Clear instructions + context + task                │
└────────────────┬────────────────────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────────────────────┐
│ Step 4: Call Ollama LLM                                     │
│ - Model: llama3                                             │
│ - Temperature: 0.5                                          │
│ - Max tokens: 1024                                          │
│ - Timeout: 30s                                              │
└────────────────┬────────────────────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────────────────────┐
│ Step 5: Parse Response                                      │
│ - Extract JSON output                                       │
│ - Validate against schema                                   │
│ - Check for errors                                          │
└────────────────┬────────────────────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────────────────────┐
│ Step 6: Execute Actions                                     │
│ - Call Home Assistant services                              │
│ - Update database                                           │
│ - Send notifications                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────────────────────┐
│ Step 7: Log & Evaluate                                      │
│ - Save execution log                                        │
│ - Calculate metrics                                         │
│ - Record feedback for next iteration                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
            ✅ Complete
```

---

## 🔌 API Endpoints

### MCP Server Endpoints

```
┌─────────────────────────────────────────────────────────────┐
│ Health & Info                                               │
├─────────────────────────────────────────────────────────────┤
│ GET  /health                   → Server status             │
│ GET  /                         → API info                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Home Assistant Integration                                  │
├─────────────────────────────────────────────────────────────┤
│ GET  /ha/state/{entity_id}     → Get entity state         │
│ POST /ha/service/{domain}/{service} → Call HA service    │
│ GET  /ha/entities              → List all entities        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Automations                                                 │
├─────────────────────────────────────────────────────────────┤
│ POST /automation/trigger       → Trigger automation        │
│ GET  /automation/status        → Automation status         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Agents                                                      │
├─────────────────────────────────────────────────────────────┤
│ POST /agent/execute            → Execute agent             │
│ GET  /agent/status             → Agent status              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Monitoring                                                  │
├─────────────────────────────────────────────────────────────┤
│ GET  /metrics                  → Prometheus metrics        │
│ GET  /logs                     → Recent execution logs    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagram

```
┌──────────────────┐
│   Web Browser    │
│   :3000 (HA)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│   Home Assistant Core                    │
│   - Device Management                    │
│   - State Management                     │
│   - Automation Engine                    │
│   - History/Logging                      │
└────────┬─────────────────────────────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────┐          ┌──────────────────┐
│  Zigbee Devices  │          │  WiFi Devices    │
│  - Lights        │          │  - Plugs         │
│  - Sensors       │          │  - Thermostats   │
│  - Switches      │          │  - Cameras       │
└──────────────────┘          └──────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│   MCP Server (FastAPI)                   │
│   - REST API                             │
│   - Agent Orchestration                  │
│   - HA Service Calls                     │
│   - Logging                              │
└────────┬──────────────────────────────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────┐          ┌──────────────────┐
│   Ollama LLM     │          │  PostgreSQL DB   │
│   - llama3       │          │  - Logs          │
│   - mistral      │          │  - Metrics       │
│   - Inference    │          │  - History       │
└──────────────────┘          └──────────────────┘
         ▲
         │
┌──────────────────────────────────────────┐
│   Agents (YAML + Prompts)                │
│   - home_automation_agent                │
│   - energy_management_agent              │
│   - security_agent                       │
└──────────────────────────────────────────┘
```

---

## 🌐 Network Topology

```
┌──────────────────────────────────────────────────────────────────┐
│                     Home Network (192.168.x.0/24)                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Router (Gateway: 192.168.x.1)                          │   │
│  │  - DHCP Server                                          │   │
│  │  - DNS                                                  │   │
│  │  - Port Forwarding (if needed)                          │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                     │
│       ┌───────────────────┼───────────────────┐                │
│       │                   │                   │                │
│  192.168.x.100       192.168.x.101       192.168.x.102         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │ Linux Server │   │ Smart Bulbs  │   │ Smart Plugs  │        │
│  │ (Docker)     │   │ (Zigbee)     │   │ (WiFi)       │        │
│  │              │   │              │   │              │        │
│  │ HA:8123 ◄──┐│   └──────────────┘   └──────────────┘        │
│  │ MCP:8000    ││                                              │
│  │ Ollama:11434││   ┌──────────────┐                           │
│  │ DB:5432     └┼──►│ Zigbee Hub   │                           │
│  └──────────────┘   │ (SONOFF)     │                           │
│                     └──────────────┘                           │
│                                                                │
└──────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Services & Ports

| Service | Port | Protocol | Host | Status |
|---------|------|----------|------|--------|
| Home Assistant | 8123 | HTTP | localhost | :3000 → Linux |
| MCP Server | 8000 | HTTP | 0.0.0.0 | Internal |
| Ollama | 11434 | HTTP | 0.0.0.0 | Internal |
| PostgreSQL | 5432 | TCP | localhost | Internal |
| Redis | 6379 | TCP | localhost | Optional |

---

## 🎯 Use Case Examples

### Morning Routine

```
┌─────────────────────────────────┐
│ Time Trigger: 07:00             │
└──────────────┬──────────────────┘
               ▼
┌─────────────────────────────────┐
│ Home Automation Agent           │
│ Load morning_routine scene      │
└──────────────┬──────────────────┘
               ▼
    ┌─────────────────────────┐
    ├─ Lights: 255 (bright)   │
    ├─ Color Temp: 6500K      │
    ├─ Heating: 21°C          │
    ├─ Blinds: Open           │
    └─────────────────────────┘
               ▼
          👤 Awake!
```

### Energy Optimization

```
┌──────────────────────────────────┐
│ High Consumption Detected         │
│ 22:00 - Peak Hours                │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│ Energy Management Agent          │
│ Analyze patterns                 │
│ Predict usage                    │
└──────────────┬───────────────────┘
               ▼
    ┌────────────────────────────┐
    ├─ Reduce heating to 18°C    │
    ├─ Defer water heating       │
    ├─ Turn off non-essential    │
    └────────────────────────────┘
               ▼
         💰 Savings!
```

---

## 📈 Metrics & Performance

```
Agent Execution Metrics:
├─ Response Time: < 1 second (goal)
├─ Accuracy: > 90% (target)
├─ Uptime: 99.9% (SLA)
├─ Error Rate: < 1% (acceptable)
└─ User Satisfaction: > 85% (feedback)

System Performance:
├─ CPU Usage: < 50% (idle), < 80% (load)
├─ Memory: < 70% (target)
├─ Disk: < 80% (warning)
└─ Network Latency: < 50ms (target)

HA Device Responsiveness:
├─ Light Control: < 100ms
├─ Sensor Updates: < 500ms
├─ Climate Control: < 1s
└─ Overall: 99.5% responsive
```

---

Tot ziens! 🏡✨
