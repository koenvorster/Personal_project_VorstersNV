# Fase 4 – Home Assistant + MCP AI Integration

## 📋 Overzicht

Deze fase breidt het VorstersNV-project uit met **Home Assistant** op een Linux-server met **MCP (Model Context Protocol) AI-integratie**. Dit biedt:

- **Lokale controle** van smart home-apparaten
- **AI-gestuurde automatisering** via MCP agents
- **Offline-first** architectuur (geen cloud-afhankelijkheid)
- **Integratie** met bestaande VorstersNV agents

---

## 🎯 Doelstelling

```
┌─────────────────────────────────────────────────────────┐
│           VorstersNV + Home Assistant Infra             │
├──────────────────┬──────────────────┬──────────────────┤
│  Webshop & API   │  MCP AI Layer    │ Smart Home (HA)  │
│  (Huidige setup) │  (Agents)        │  (Linux Server)  │
├──────────────────┼──────────────────┼──────────────────┤
│ - Orders/Inv     │ - Home control   │ - Lights         │
│ - Dashboard      │ - Energy mgmt    │ - Climate        │
│ - Payments       │ - Automations    │ - Security       │
│ - Notifications  │ - Learning       │ - Devices        │
└──────────────────┴──────────────────┴──────────────────┘
         │                  │                  │
         └──────────────────┴──────────────────┘
              Communicatie via REST/Webhooks
```

---

## 📦 Installatie-plan

### Stap 1: Linux Server voorbereiding (op oude laptop)

**Wat nodig:**
- [ ] Ubuntu 22.04 LTS (of recent Debian-variant)
- [ ] SSH-access configureren
- [ ] Docker + Docker Compose

**Commando's:**
```bash
# Update systeem
sudo apt update && sudo apt upgrade -y

# Docker installeren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Huidige user toevoegen aan docker groep
sudo usermod -aG docker $USER
newgrp docker

# Docker Compose installeren
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Stap 2: Home Assistant Setup

**docker-compose.yml voor Home Assistant:**
```yaml
version: '3.8'

services:
  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:latest
    container_name: homeassistant
    privileged: true
    restart: unless-stopped
    ports:
      - "8123:8123"
    environment:
      - TZ=Europe/Amsterdam
    volumes:
      - ./config:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro
    networks:
      - home_network

  # MCP Server (Python + FastAPI)
  mcp-server:
    build:
      context: ./mcp-server
      dockerfile: Dockerfile
    container_name: mcp-server
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - HA_URL=http://homeassistant:8123
      - HA_TOKEN=${HA_TOKEN}
      - OLLAMA_URL=${OLLAMA_URL:-http://ollama:11434}
    volumes:
      - ./mcp-server/agents:/app/agents
      - ./mcp-server/logs:/app/logs
    depends_on:
      - homeassistant
    networks:
      - home_network

  # Ollama (lokale LLM)
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - home_network
    # Optional: GPU support
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

networks:
  home_network:
    driver: bridge

volumes:
  ollama_data:
```

### Stap 3: MCP Server (Python FastAPI)

**Structuur:**
```
mcp-server/
├── Dockerfile
├── requirements.txt
├── main.py
├── agents/
│   ├── home_automation_agent.yml
│   ├── energy_management_agent.yml
│   └── security_agent.yml
├── integrations/
│   ├── homeassistant.py
│   ├── ollama.py
│   └── prometheus.py
└── logs/
    └── agent_runs/
```

**main.py (FastAPI MCP Server):**
```python
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import logging
from datetime import datetime

app = FastAPI(title="VorstersNV MCP Home Assistant Server")

# Configuratie
HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ Models ============

class HomeState(BaseModel):
    entity_id: str
    state: str
    attributes: dict

class AutomationRequest(BaseModel):
    trigger: str  # "motion", "schedule", "manual"
    action: str   # wat de agent moet doen
    entities: list[str]  # welke entities betrokken

class AgentResponse(BaseModel):
    success: bool
    message: str
    actions_taken: list[dict]
    next_state: Optional[dict]

# ============ Home Assistant Integration ============

async def get_ha_state(entity_id: str) -> dict:
    """Fetch entity state from Home Assistant"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {HA_TOKEN}"}
        response = await client.get(
            f"{HA_URL}/api/states/{entity_id}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def call_ha_service(domain: str, service: str, data: dict) -> dict:
    """Call Home Assistant service"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {HA_TOKEN}"}
        response = await client.post(
            f"{HA_URL}/api/services/{domain}/{service}",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

# ============ Endpoints ============

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "homeassistant": "connected",
            "ollama": "connected"
        }
    }

@app.get("/ha/state/{entity_id}")
async def get_state(entity_id: str):
    """Get Home Assistant entity state"""
    try:
        state = await get_ha_state(entity_id)
        return state
    except Exception as e:
        logger.error(f"Error fetching state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ha/service/{domain}/{service}")
async def call_service(domain: str, service: str, data: dict):
    """Call Home Assistant service"""
    try:
        result = await call_ha_service(domain, service, data)
        return result
    except Exception as e:
        logger.error(f"Error calling service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/automation/trigger")
async def trigger_automation(request: AutomationRequest) -> AgentResponse:
    """
    Trigger an automation via MCP Agent
    
    Example:
    {
        "trigger": "motion",
        "action": "turn_lights_on_with_brightness",
        "entities": ["light.living_room", "light.hallway"]
    }
    """
    try:
        logger.info(f"Automation triggered: {request.trigger} -> {request.action}")
        
        # Hier komt je agent-logica
        # 1. Load YAML agent definition
        # 2. Fetch current state van entities
        # 3. Build prompt for Ollama
        # 4. Get AI response
        # 5. Execute Home Assistant services
        # 6. Log results
        
        actions_taken = []
        
        # Dummy implementation voor nu
        for entity in request.entities:
            action = {
                "entity_id": entity,
                "service": "light.turn_on",
                "data": {"brightness": 200, "color_temp": 3000}
            }
            result = await call_ha_service("light", "turn_on", {
                "entity_id": entity,
                "brightness": 200
            })
            actions_taken.append(action)
        
        return AgentResponse(
            success=True,
            message=f"Automation executed: {request.action}",
            actions_taken=actions_taken,
            next_state={"status": "complete"}
        )
        
    except Exception as e:
        logger.error(f"Automation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/status")
async def agent_status():
    """Get status van alle MCP agents"""
    return {
        "agents": [
            {"name": "home_automation_agent", "status": "idle", "last_run": None},
            {"name": "energy_management_agent", "status": "idle", "last_run": None},
            {"name": "security_agent", "status": "idle", "last_run": None}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Stap 4: Agent Definities (YAML)

**home_automation_agent.yml:**
```yaml
name: Home Automation Agent
model: llama3
system_prompt_ref: ./prompts/system/home_automation_system.txt
preprompt_ref: ./prompts/preprompt/home_automation_v1.yml

capabilities:
  - control_lights
  - adjust_temperature
  - manage_scenes
  - execute_routines

triggers:
  - motion_detected
  - time_based
  - voice_command
  - manual_request

evaluation:
  feedback_loop: true
  metrics:
    - response_time
    - action_success_rate
    - user_satisfaction
```

**energy_management_agent.yml:**
```yaml
name: Energy Management Agent
model: mistral
system_prompt_ref: ./prompts/system/energy_management_system.txt
preprompt_ref: ./prompts/preprompt/energy_management_v1.yml

capabilities:
  - monitor_consumption
  - optimize_schedules
  - predict_usage
  - suggest_savings

data_sources:
  - energy_meter
  - weather_api
  - schedule_data

evaluation:
  feedback_loop: true
  metrics:
    - energy_saved_kwh
    - cost_reduction
    - prediction_accuracy
```

---

## 🔧 Technische Integratie

### VorstersNV ↔ Home Assistant

**Flow:**
```
VorstersNV API
    ↓
REST Call naar MCP Server
    ↓
MCP Agent (Ollama LLM)
    ↓
Home Assistant Service Calls
    ↓
Smart Home Devices
    ↓
Feedback terug naar VorstersNV
```

**Voorbeeld API Call van VorstersNV:**
```python
import httpx

# Vanuit VorstersNV order_handler
async def notify_smart_home_about_order(order_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://mcp-server:8000/automation/trigger",
            json={
                "trigger": "order_received",
                "action": "notify_warehouse_lights",
                "entities": ["light.warehouse_zone_1", "light.warehouse_zone_2"]
            }
        )
    return response.json()
```

### Monitoring & Logging

**Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge

agent_executions = Counter(
    'mcp_agent_executions_total',
    'Total agent executions',
    ['agent_name']
)

agent_duration = Histogram(
    'mcp_agent_duration_seconds',
    'Agent execution time',
    ['agent_name']
)

home_state = Gauge(
    'home_state_value',
    'Current home state value',
    ['entity_id']
)
```

---

## 📅 Implementatie-roadmap

### Week 1: Voorbereiding
- [ ] Linux server opzetten op oude laptop
- [ ] Docker + Docker Compose installeren
- [ ] SSH-access testen

### Week 2: Home Assistant
- [ ] Home Assistant container starten
- [ ] Initiële setup (user, integrations)
- [ ] Smart home devices configureren
- [ ] MQTT/Zigbee hub opzetten (optioneel)

### Week 3: MCP Server
- [ ] FastAPI server bouwen
- [ ] Home Assistant API integratie
- [ ] Ollama integratie
- [ ] Basis endpoints implementeren

### Week 4: Agents
- [ ] Home Automation Agent
- [ ] Energy Management Agent
- [ ] Security Agent
- [ ] Testen & itereren

### Week 5: VorstersNV Integratie
- [ ] Webhook-handlers uitbreiden
- [ ] MCP Server calls integreren
- [ ] End-to-end testing

### Week 6: Polish & Deploy
- [ ] Monitoring instellen
- [ ] Documentation updaten
- [ ] Performance tuning

---

## 🛠️ Tools & Dependencies

**Server (Linux):**
- Ubuntu 22.04 LTS
- Docker CE 24+
- Docker Compose 2.20+
- Python 3.11+

**Home Assistant:**
- Home Assistant Core 2024.x
- HACS (Community store)
- Custom integrations

**MCP Server:**
```
fastapi==0.104.1
httpx==0.25.0
pydantic==2.5.0
prometheus-client==0.19.0
pyyaml==6.0.1
ollama==0.0.x  (when available)
```

---

## 📝 Volgende Stappen

1. **Nu:** Maak de Linux server klaar
2. **Volgende:** Home Assistant instaleren en configureren
3. **Daarna:** MCP Server bouwen
4. **Tot slot:** Agents implementeren en testen

Klaar om te starten? 🚀
