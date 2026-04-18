"""
MCP Server for VorstersNV Home Assistant Integration

This FastAPI server bridges VorstersNV with Home Assistant and Ollama.
It manages agent execution, Home Assistant API calls, and automation workflows.
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import os
import logging
from datetime import datetime
import json
import asyncio
from pathlib import Path

# Configuration
HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="VorstersNV MCP Home Assistant Server",
    description="AI-powered Home Assistant integration via MCP",
    version="1.0.0"
)

# ============ Models ============

class HAServiceCall(BaseModel):
    """Home Assistant service call"""
    domain: str
    service: str
    data: Dict[str, Any]

class AutomationRequest(BaseModel):
    """Request to trigger an automation"""
    trigger: str  # motion, schedule, manual, webhook
    action: str   # what the agent should do
    entities: List[str]  # which entities are involved
    context: Optional[Dict[str, Any]] = None

class AgentExecution(BaseModel):
    """Agent execution request"""
    agent_name: str
    task: str
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    """Agent execution response"""
    success: bool
    message: str
    execution_time: float
    actions_taken: List[Dict[str, Any]]
    next_state: Optional[Dict[str, Any]]

# ============ Home Assistant Integration ============

async def get_ha_state(entity_id: str) -> Dict[str, Any]:
    """Fetch entity state from Home Assistant"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"Authorization": f"Bearer {HA_TOKEN}"}
            response = await client.get(
                f"{HA_URL}/api/states/{entity_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching HA state: {e}")
        raise

async def call_ha_service(domain: str, service: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Call Home Assistant service"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"Authorization": f"Bearer {HA_TOKEN}"}
            response = await client.post(
                f"{HA_URL}/api/services/{domain}/{service}",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error calling HA service: {e}")
        raise

async def get_ha_states() -> List[Dict[str, Any]]:
    """Get all entity states from Home Assistant"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"Authorization": f"Bearer {HA_TOKEN}"}
            response = await client.get(
                f"{HA_URL}/api/states",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching HA states: {e}")
        raise

# ============ Health Checks ============

@app.get("/health")
async def health():
    """Health check endpoint"""
    services_status = {
        "homeassistant": "unknown",
        "ollama": "unknown"
    }
    
    # Check Home Assistant
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            headers = {"Authorization": f"Bearer {HA_TOKEN}"}
            response = await client.get(
                f"{HA_URL}/api/",
                headers=headers
            )
            services_status["homeassistant"] = "connected" if response.status_code == 200 else "error"
    except Exception as e:
        services_status["homeassistant"] = "error"
        logger.warning(f"HA health check failed: {e}")
    
    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            services_status["ollama"] = "connected" if response.status_code == 200 else "error"
    except Exception as e:
        services_status["ollama"] = "error"
        logger.warning(f"Ollama health check failed: {e}")
    
    return {
        "status": "healthy" if all(s == "connected" for s in services_status.values()) else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": services_status,
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "VorstersNV MCP Home Assistant Server",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/ha/state/{entity_id}",
            "/ha/service/{domain}/{service}",
            "/ha/entities",
            "/automation/trigger",
            "/agent/execute",
            "/agent/status",
            "/docs"
        ]
    }

# ============ Home Assistant Endpoints ============

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
async def call_service(domain: str, service: str, request: HAServiceCall):
    """Call Home Assistant service"""
    try:
        result = await call_ha_service(domain, service, request.data)
        return {
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calling service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ha/entities")
async def get_entities():
    """Get all Home Assistant entities"""
    try:
        states = await get_ha_states()
        
        # Group by domain
        entities_by_domain = {}
        for entity in states:
            entity_id = entity.get('entity_id', '')
            domain = entity_id.split('.')[0] if '.' in entity_id else 'unknown'
            
            if domain not in entities_by_domain:
                entities_by_domain[domain] = []
            
            entities_by_domain[domain].append({
                "entity_id": entity_id,
                "state": entity.get('state'),
                "attributes": entity.get('attributes', {})
            })
        
        return {
            "total_entities": len(states),
            "domains": list(entities_by_domain.keys()),
            "entities": entities_by_domain
        }
    except Exception as e:
        logger.error(f"Error fetching entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ Automation Endpoints ============

@app.post("/automation/trigger")
async def trigger_automation(request: AutomationRequest) -> AgentResponse:
    """
    Trigger an automation via MCP Agent
    
    Example request:
    {
        "trigger": "motion",
        "action": "turn_lights_on_with_brightness",
        "entities": ["light.living_room", "light.hallway"],
        "context": {"brightness": 200, "color_temp": 3000}
    }
    """
    try:
        logger.info(f"Automation triggered: {request.trigger} -> {request.action}")
        
        start_time = datetime.now()
        actions_taken = []
        
        # Example implementation: Control lights on motion
        if request.action == "turn_lights_on_with_brightness":
            brightness = request.context.get("brightness", 200) if request.context else 200
            color_temp = request.context.get("color_temp", 3000) if request.context else 3000
            
            for entity in request.entities:
                try:
                    result = await call_ha_service("light", "turn_on", {
                        "entity_id": entity,
                        "brightness": brightness,
                        "color_temp": color_temp
                    })
                    actions_taken.append({
                        "entity_id": entity,
                        "service": "light.turn_on",
                        "status": "success"
                    })
                except Exception as e:
                    logger.error(f"Error controlling {entity}: {e}")
                    actions_taken.append({
                        "entity_id": entity,
                        "service": "light.turn_on",
                        "status": "error",
                        "error": str(e)
                    })
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResponse(
            success=True,
            message=f"Automation executed: {request.action}",
            execution_time=execution_time,
            actions_taken=actions_taken,
            next_state={"status": "complete", "entities_affected": len(request.entities)}
        )
        
    except Exception as e:
        logger.error(f"Automation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ Agent Endpoints ============

@app.post("/agent/execute")
async def execute_agent(request: AgentExecution):
    """Execute an agent"""
    try:
        logger.info(f"Executing agent: {request.agent_name}")
        
        # TODO: Implement actual agent execution
        # For now, return mock response
        
        return {
            "success": True,
            "agent": request.agent_name,
            "task": request.task,
            "output": {
                "status": "completed",
                "message": f"Agent {request.agent_name} executed successfully"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/status")
async def agent_status():
    """Get status of all MCP agents"""
    return {
        "agents": [
            {
                "name": "home_automation_agent",
                "status": "idle",
                "last_run": None,
                "version": "1.0"
            },
            {
                "name": "energy_management_agent",
                "status": "idle",
                "last_run": None,
                "version": "1.0"
            },
            {
                "name": "security_agent",
                "status": "idle",
                "last_run": None,
                "version": "1.0"
            }
        ],
        "timestamp": datetime.now().isoformat()
    }

# ============ Metrics Endpoints ============

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # TODO: Implement Prometheus metrics
    return {
        "message": "Metrics endpoint - implement Prometheus integration"
    }

# ============ Startup/Shutdown ============

@app.on_event("startup")
async def startup_event():
    logger.info("MCP Server starting...")
    logger.info(f"Home Assistant URL: {HA_URL}")
    logger.info(f"Ollama URL: {OLLAMA_URL}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("MCP Server shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
