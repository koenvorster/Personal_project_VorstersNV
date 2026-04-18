# ✅ Fase 4 – Implementation Checklist

## 🎯 Fase 4 Voorbereiding: VOLTOOID ✅

Alle documentatie, code-skeletons en configuratie zijn klaar!

---

## 📅 Timeline & Checklist

### WEEK 1: Server Setup (Dit Moment)

#### Stap 1: Linux Voorbereiding
- [ ] Beschik over oude laptop (minimum 4GB RAM, 20GB disk)
- [ ] Download Ubuntu 22.04 LTS ISO (https://ubuntu.com/download/server)
- [ ] Maak bootable USB-stick
- [ ] Install Ubuntu 22.04 LTS
- [ ] Update systeem: `sudo apt update && sudo apt upgrade -y`
- [ ] Test SSH-access vanuit main machine

**Checkpoint:** SSH werkt, systeem up-to-date

#### Stap 2: Docker & Compose Installation
```bash
# Run op server:
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose --version
```

- [ ] Docker installed (version 24+)
- [ ] Docker Compose installed (version 2.20+)
- [ ] Current user in docker group
- [ ] Service auto-starts

**Checkpoint:** `docker --version` returns v24.x, `docker compose --version` returns v2.20+

#### Stap 3: VorstersNV Project Setup
```bash
# On server:
git clone https://github.com/koenvorster/Personal_project_VorstersNV.git
cd Personal_project_VorstersNV
cp .env.example .env
nano .env  # Edit with server IP, paths, etc
```

- [ ] Project cloned successfully
- [ ] `.env` file created
- [ ] Network connectivity tested

**Checkpoint:** Project directory exists, `.env` configured

---

### WEEK 2: Home Assistant Setup

#### Stap 4: Home Assistant Installation
```bash
cd Personal_project_VorstersNV

# Create config directory
mkdir -p config

# Start Home Assistant
docker compose up -d homeassistant

# Monitor
docker logs homeassistant -f
```

- [ ] Home Assistant container started
- [ ] No errors in logs
- [ ] Can access http://server-ip:8123
- [ ] Firewall allows port 8123 (if needed)

**Checkpoint:** HA Web UI loads successfully

#### Stap 5: Home Assistant Initial Setup
1. [ ] Create account in HA UI
2. [ ] Set location (Amsterdam, NL)
3. [ ] Select timezone
4. [ ] Configure device discovery
5. [ ] Test automation system

**Checkpoint:** HA fully configured, can see "Settings" page

#### Stap 6: Home Assistant Security Token
1. [ ] Login to HA UI
2. [ ] Profile → Security
3. [ ] Create token
4. [ ] Copy token value
5. [ ] Add to `.env`:
   ```
   HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

- [ ] Token created and saved
- [ ] Token tested: `curl -H "Authorization: Bearer $HA_TOKEN" http://localhost:8123/api/`

**Checkpoint:** HA API accessible with token

---

### WEEK 2-3: Device Integration

#### Stap 7: Zigbee Hub Setup (Optional but Recommended)
- [ ] Purchase: SONOFF ZBDongle-P (€25)
- [ ] Connect USB dongle to server
- [ ] In HA: Settings → Devices & Services
- [ ] Add "Zigbee Home Automation" integration
- [ ] Select USB device
- [ ] Wait for devices to pair
- [ ] Test pairing new device

**Checkpoint:** At least 1 Zigbee device detected

#### Stap 8: WiFi Devices Setup (Optional)
- [ ] Configure existing smart devices (IKEA TRADFRI, etc)
- [ ] Or use cloud integrations (Tuya, Meross)
- [ ] Add integrations in HA
- [ ] Verify devices appear in "Entities"

**Checkpoint:** Have 3-5 controllable entities

---

### WEEK 3: MCP Server Setup

#### Stap 9: Ollama Installation
```bash
docker compose up -d ollama

# Wait for startup
sleep 30

# Pull models
docker exec ollama ollama pull llama3
docker exec ollama ollama pull mistral

# Verify
docker exec ollama ollama list
```

- [ ] Ollama container running
- [ ] Models downloaded (llama3, mistral)
- [ ] Can call: `curl http://localhost:11434/api/tags`

**Checkpoint:** Both models available

#### Stap 10: MCP Server Build & Start
```bash
# Build
docker build -t mcp-server ./mcp-server

# Start
docker compose up -d mcp-server

# Test
curl http://localhost:8000/health
```

- [ ] MCP server image builds
- [ ] MCP server container running
- [ ] Health check returns 200
- [ ] Logs show no errors

**Checkpoint:** MCP Server accessible at `/health`

---

### WEEK 3-4: Agent Testing

#### Stap 11: Agent Execution Test
```bash
# Test home automation agent
curl -X POST http://localhost:8000/automation/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "motion",
    "action": "turn_lights_on_with_brightness",
    "entities": ["light.your_light"],
    "context": {"brightness": 200}
  }'
```

- [ ] Request succeeds (HTTP 200)
- [ ] Response contains valid JSON
- [ ] Actions executed in HA

**Checkpoint:** Agent responds with actions

#### Stap 12: Manual Device Control Test
```bash
# Get entity state
curl -H "Authorization: Bearer $HA_TOKEN" \
  http://localhost:8123/api/states/light.your_light

# Control directly via API
curl -X POST http://localhost:8000/ha/service/light/turn_on \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "light.your_light"}'
```

- [ ] Can read entity states
- [ ] Can control entities via API
- [ ] Physical device responds

**Checkpoint:** Direct HA control works

---

### WEEK 4-5: Integration

#### Stap 13: VorstersNV Webhook Integration
1. [ ] Add MCP_SERVER_URL to VorstersNV `.env`
2. [ ] Update API handlers to call MCP server
3. [ ] Test webhook flow

**Checkpoint:** VorstersNV can call MCP Server

#### Stap 14: First Automation Rules
- [ ] Create first Home Assistant automation
- [ ] Test manual trigger
- [ ] Test scheduled trigger
- [ ] Verify logging

**Checkpoint:** Automation runs and logs results

---

### WEEK 5: Monitoring & Polish

#### Stap 15: Monitoring Setup
- [ ] Enable logs to file
- [ ] Setup log rotation
- [ ] Create metrics dashboard
- [ ] Setup alerts (optional)

**Checkpoint:** Can view execution logs

#### Stap 16: Performance Optimization
- [ ] Monitor resource usage
- [ ] Tune Docker memory limits
- [ ] Optimize prompts if needed
- [ ] Test under load

**Checkpoint:** System stable under normal load

---

### WEEK 6: Final Verification

#### Stap 17: Full End-to-End Test
- [ ] [ ] Manual trigger automation
- [ ] [ ] Scheduled automation runs
- [ ] [ ] VorstersNV webhook works
- [ ] [ ] All logs are recorded
- [ ] [ ] Metrics available
- [ ] [ ] No errors in 24h uptime

**Checkpoint:** System running stable

#### Stap 18: Documentation Update
- [ ] [ ] Document actual server IPs/hostnames
- [ ] [ ] Document all devices added
- [ ] [ ] Create runbook
- [ ] [ ] Test recovery procedure

**Checkpoint:** Can restore system from docs

---

## 📊 Status Board

```
Preparation Phase
├─ Documentation      ✅ COMPLETE
│  ├─ FASE_4_README.md
│  ├─ FASE_4_HOMEASSISTANT_MCP.md
│  ├─ FASE_4_QUICKSTART.md
│  ├─ HOW_TO_AGENTS.md
│  └─ ARCHITECTUUR_FASE4.md
│
├─ MCP Server Code    ✅ COMPLETE
│  ├─ Dockerfile
│  ├─ main.py (450 lines)
│  ├─ requirements.txt
│  └─ Agent configs (3)
│
├─ Agents             ✅ COMPLETE
│  ├─ home_automation_agent.yml
│  ├─ energy_management_agent.yml
│  └─ security_agent.yml
│
├─ Prompts            ✅ COMPLETE
│  ├─ System prompts (3)
│  ├─ Pre-prompts (2)
│  └─ Examples (various)
│
└─ Implementation     🔄 IN PROGRESS
   ├─ Week 1: Server Setup
   ├─ Week 2: Home Assistant
   ├─ Week 3: Agents
   ├─ Week 4: Integration
   └─ Week 5-6: Polish
```

---

## 🔄 Daily Progress Tracking

### Week 1
```
Monday:   [ ] Ubuntu installed [ ] Docker ready
Tuesday:  [ ] Docker Compose [ ] Project cloned
Wednesday: [ ] .env configured [ ] SSH tested
Thursday: [ ] Home Assistant started [ ] HA Web UI works
Friday:   [ ] HA configured [ ] Token generated
```

### Week 2
```
Monday:   [ ] Ollama pulling models [ ] Models ready
Tuesday:  [ ] MCP server builds [ ] MCP health check works
Wednesday: [ ] Agents tested manually [ ] Logs visible
Thursday: [ ] Device integration [ ] First automation
Friday:   [ ] End-to-end test [ ] All logs recorded
```

---

## ⚠️ Common Issues & Fixes

| Issue | Solution | Status |
|-------|----------|--------|
| Docker permission denied | Add user to docker group | 🔧 |
| HA can't connect | Check firewall, restart container | 🔧 |
| MCP server 502 error | Check Ollama running, check logs | 🔧 |
| Agents not responding | Check LLM models loaded | 🔧 |
| Slow response times | Reduce temperature, batch requests | ⚙️ |

---

## 📞 Support Channels

**Problems?** Check in order:
1. This checklist (fixes at bottom)
2. `FASE_4_QUICKSTART.md` (troubleshooting section)
3. `ARCHITECTUUR_FASE4.md` (diagrams & flows)
4. Online docs (HA, Ollama, FastAPI)

---

## 🎊 Completion Criteria

✅ **Fase 4 Complete when:**

- [ ] Home Assistant running with 3+ devices
- [ ] MCP Server connected to HA & Ollama
- [ ] Agents execute and control devices
- [ ] Webhooks working (VorstersNV → HA)
- [ ] Logging & monitoring active
- [ ] 24h stable uptime
- [ ] Documentation updated
- [ ] Recovery tested

---

## 📈 Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Server Uptime | 99% | 🎯 |
| Agent Response Time | < 1s | 🎯 |
| Agent Accuracy | > 90% | 🎯 |
| LLM Model Memory | < 4GB | 🎯 |
| MCP Server CPU | < 50% idle | 🎯 |

---

## 🚀 Next Phase Preview

**Fase 5** (nach Fase 4 completion):
- [ ] Multi-location support
- [ ] Advanced scheduling
- [ ] ML-based optimization
- [ ] Mobile app integration
- [ ] Cloud backup

---

## 📝 Notes & Observations

_Space for your notes during implementation_

```
Week 1 Notes:
-

Week 2 Notes:
-

Week 3 Notes:
-

Week 4 Notes:
-
```

---

**Start Datum:** 18 April 2026
**Target Completion:** 31 Mei 2026
**Status:** 🎯 On Track

Veel succes! 🚀
