# 🚀 Fase 4 – Quick Start Guide

## ✅ Status Check

Je hebt nu:
- ✅ VorstersNV webshop & API draaiend (Docker)
- ✅ Basis project-infra en agents
- 🔄 Linux server voorbereiding nodig
- 📦 MCP Server skeleton klaar

---

## 📋 Volgende Stappen (Deze Week)

### Stap 1: Linux Server Voorbereiding

Ga naar je oude laptop en run:

```bash
# SSH in als sudo user
ssh user@laptop_ip

# Update systeem
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose --version
```

### Stap 2: Clone VorstersNV Project

```bash
# Clone het project
git clone https://github.com/koenvorster/Personal_project_VorstersNV.git
cd Personal_project_VorstersNV

# Copy environment file
cp .env.example .env

# Edit .env met server-speficieke waarden
nano .env
```

### Stap 3: Start Home Assistant

```bash
# Maak config directory
mkdir -p config

# Start Home Assistant
docker compose -f docker-compose.yml up -d homeassistant

# Check logs
docker logs homeassistant -f

# Access op http://laptop_ip:8123
```

### Stap 4: Configure Home Assistant

1. Open http://laptop_ip:8123
2. Klik "Create My Smart Home"
3. Zet je locatie (Amsterdam, NL)
4. Voeg integraties toe:
   - MQTT (optioneel, voor Zigbee)
   - REST (optioneel, voor externe systemen)
5. Voeg devices toe via Integrations

### Stap 5: Genereer Home Assistant Token

```bash
# In Home Assistant UI:
# Profile → Security → Create Token
# Kopieer en sla op in .env:
HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Stap 6: Start MCP Server

```bash
# In project directory
docker compose -f docker-compose.yml up -d mcp-server

# Check status
curl http://localhost:8000/health

# Check logs
docker logs mcp-server -f
```

### Stap 7: Test Integration

```bash
# Test Home Assistant connection
curl -H "Authorization: Bearer $HA_TOKEN" \
     http://localhost:8123/api/

# Test MCP Server
curl http://localhost:8000/health

# Test agent execution
curl -X POST http://localhost:8000/automation/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "motion",
    "action": "turn_lights_on_with_brightness",
    "entities": ["light.living_room"],
    "context": {"brightness": 200}
  }'
```

---

## 🏠 Home Assistant Setup – Details

### Devices Toevoegen (Voorbeeld)

**Via Integrations > Add Integration:**

1. **Zigbee (SONOFF ZBDongle-P)**
   ```
   - Install Zigbee Home Automation
   - Select USB device /dev/ttyUSB0
   - Scan for devices
   ```

2. **WiFi Devices (IKEA TRADFRI)**
   ```
   - Install Tradfri integration
   - Add gateway IP
   - Accept pairing
   ```

3. **Cloud (Tuya, Meross)**
   ```
   - Install relevant integration
   - Login with account
   - Select region
   ```

### Scenes & Automations

**Voorbeeld Scene (Morning Routine):**

```yaml
# config/scenes.yaml
- id: morning_routine
  name: Morning Routine
  icon: mdi:sun
  entities:
    light.bedroom:
      state: on
      brightness: 255
      color_temp: 6500  # Blauw licht
    light.bathroom:
      state: on
      brightness: 200
    climate.heating:
      temperature: 21
    cover.blinds:
      position: 100  # Open
```

**Voorbeeld Automation (Motion at Night):**

```yaml
# config/automations.yaml
- id: motion_night_lights
  alias: Motion at Night - Lights
  description: Turn on lights on motion detection at night
  trigger:
    platform: state
    entity_id: binary_sensor.motion_living_room
    to: "on"
    after: "23:00"
    before: "06:00"
  action:
    service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness: 100
      color_temp: 3000
```

---

## 🤖 Agents Instellen

### Agent Execution Flow

```
┌─────────────────────────────────────┐
│  Home Assistant Event               │ (motion, schedule, webhook)
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  MCP Server receives event          │ (/automation/trigger)
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Load Agent YAML + Prompts          │ (home_automation_agent)
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Call Ollama LLM                    │ (llama3 model)
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Parse Agent Response               │ (JSON output)
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Execute Home Assistant Services    │ (light.turn_on, etc)
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Log Results & Metrics              │ (feedback loop)
└─────────────────────────────────────┘
```

### Test een Agent Handmatig

```bash
# 1. Connect to MCP server container
docker exec -it mcp-server bash

# 2. Test agent execution
python -c "
import asyncio
from ollama.agent_runner import AgentRunner

runner = AgentRunner()
result = asyncio.run(runner.run_agent(
    'home_automation_agent',
    'Motion detected in living room at 19:00. Turn on lights to 150 brightness.'
))
print(result)
"
```

---

## 📊 Monitoring & Logging

### Access Logs

```bash
# Home Assistant logs
docker logs homeassistant

# MCP Server logs
docker logs mcp-server

# Ollama logs
docker logs ollama

# All logs live
docker compose logs -f
```

### Metrics Dashboard

MCP Server exposed metrics op `/metrics`:

```bash
curl http://localhost:8000/metrics
```

### Database Queries (Agent Executions)

```bash
# Connect to PostgreSQL
psql -h localhost -U vorstersNV -d vorstersNV

# View agent execution logs
SELECT * FROM agent_logs ORDER BY created_at DESC LIMIT 10;

# Agent performance metrics
SELECT 
  agent_name,
  COUNT(*) as executions,
  AVG(execution_time) as avg_time,
  AVG(success_rate) as avg_success
FROM agent_logs
GROUP BY agent_name;
```

---

## 🔌 Integratie met VorstersNV

### Webhook Setup

**Vanuit FastAPI naar MCP Server:**

```python
# api/webhooks/handlers.py

import httpx

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000")

async def on_order_created(order_data: OrderData):
    """Notify smart home when order is created"""
    
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{MCP_SERVER_URL}/automation/trigger",
            json={
                "trigger": "order_created",
                "action": "warehouse_lights_on",
                "entities": ["light.warehouse_zone_1"],
                "context": {
                    "order_id": order_data.order_id,
                    "priority": "high" if order_data.total > 1000 else "normal"
                }
            }
        )

async def on_payment_received(payment_data: PaymentData):
    """Notify when payment received"""
    
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{MCP_SERVER_URL}/automation/trigger",
            json={
                "trigger": "payment_received",
                "action": "send_confirmation_email",
                "entities": [],
                "context": {
                    "payment_id": payment_data.id,
                    "amount": payment_data.amount
                }
            }
        )
```

### Reverse Integration (Home Assistant → VorstersNV)

**VorstersNV API endpoint voor HA:**

```python
# api/routers/smart_home.py

from fastapi import APIRouter, Webhook

router = APIRouter(prefix="/smart-home", tags=["smart-home"])

@router.post("/webhook/motion-detected")
async def motion_webhook(data: dict):
    """HA sends motion events via webhook"""
    
    motion_data = data.get("entity_id")  # binary_sensor.motion_living_room
    
    # Log in database
    # Trigger notifications
    # Update customer dashboards
    
    return {"status": "received"}

@router.post("/webhook/energy-alert")
async def energy_webhook(data: dict):
    """HA sends energy alerts"""
    
    consumption = data.get("consumption_kwh")
    
    # Alert if exceeds threshold
    # Suggest optimizations
    # Update analytics
    
    return {"status": "processed"}
```

---

## 📝 Environment Variables

**Server .env bestand:**

```env
# Home Assistant
HA_URL=http://homeassistant:8123
HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Ollama
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3

# MCP Server
MCP_SERVER_URL=http://mcp-server:8000

# Database
DB_URL=postgresql+asyncpg://vorstersNV:dev-password@localhost:5432/vorstersNV

# Logging
LOG_LEVEL=INFO
LOG_DIR=/app/logs

# Security
WEBHOOK_SECRET=your-secret-here
API_KEY=your-api-key-here
```

---

## 🐛 Troubleshooting

### MCP Server geeft "502 Bad Gateway"

```bash
# Check if server is running
docker ps | grep mcp-server

# Check logs
docker logs mcp-server

# Restart service
docker compose restart mcp-server

# Check connectivity
docker exec mcp-server curl http://homeassistant:8123/api/
```

### Home Assistant kan Home Assistant API niet bereiken

```bash
# Check HA logs
docker logs homeassistant

# Verify token
docker exec homeassistant curl -H "Authorization: Bearer $HA_TOKEN" \
  http://localhost:8123/api/

# Check network
docker network ls
docker network inspect personal_project_vorstersnv_home_network
```

### Agent response is "null" of leeg

```bash
# Check Ollama is running
docker logs ollama

# Verify model is loaded
docker exec ollama ollama list

# Pull model if needed
docker exec ollama ollama pull llama3
docker exec ollama ollama pull mistral

# Test Ollama directly
curl http://localhost:11434/api/tags
```

### Permission issues met Docker

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Restart docker daemon
sudo systemctl restart docker

# Logout and login again
logout
```

---

## ✨ Volgende Fase-Doel

Aan het einde van deze week moet je hebben:

- ✅ Linux server klaar (Ubuntu 22.04)
- ✅ Docker + Compose draaiend
- ✅ Home Assistant actief met devices
- ✅ MCP Server verbonden met HA
- ✅ Ollama draaiend met models
- ✅ Eerste agents getest
- ✅ Webhooks werkend van/naar VorstersNV

**Deadline voor Fase 4.1:** Volgende vrijdag

---

## 📞 Support

- **Home Assistant Docs:** https://www.home-assistant.io/docs/
- **Ollama Guide:** https://ollama.ai
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Docker Compose:** https://docs.docker.com/compose/

Veel succes! 🎉
