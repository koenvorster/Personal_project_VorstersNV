# 🛠️ VorstersNV Cloud – Technical Implementation Guide

**Detailed technical specifications for cloud platform development**

---

## 📋 Table of Contents

1. [MCP Agent Development](#mcp-agent-development)
2. [Microservices Setup](#microservices-setup)
3. [Cloud Infrastructure](#cloud-infrastructure)
4. [API Specifications](#api-specifications)
5. [Database Design](#database-design)
6. [Security Implementation](#security-implementation)
7. [DevOps & CI/CD](#devops--cicd)

---

## 🤖 MCP Agent Development

### MCP Server Structure

```python
# agents/mcp_server.py
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
import asyncio

# Initialize MCP server
mcp = FastMCP("CRM Agent")

class SearchCustomersInput(BaseModel):
    query: str
    limit: int = 10

class Customer(BaseModel):
    id: str
    name: str
    email: str
    created_at: str

@mcp.tool()
async def search_customers(input: SearchCustomersInput) -> List[Customer]:
    """
    Search customers by name, email, or ID.
    
    Args:
        query: Search term (name, email, phone)
        limit: Maximum results
    
    Returns:
        List of matching customers
    """
    # Implementation connects to tenant-scoped DB
    results = await db.query_customers(
        tenant_id=current_tenant_id,
        query=input.query,
        limit=input.limit
    )
    return [Customer(**r) for r in results]

@mcp.tool()
async def get_customer_orders(customer_id: str) -> List[dict]:
    """Get all orders for a customer"""
    return await db.get_orders(current_tenant_id, customer_id)

@mcp.tool()
async def create_customer(name: str, email: str) -> Customer:
    """Create a new customer"""
    result = await db.create_customer(
        tenant_id=current_tenant_id,
        name=name,
        email=email
    )
    return Customer(**result)

if __name__ == "__main__":
    mcp.run()
```

### Agent Service Entry Point

```python
# services/agents/crm_agent.py
from anthropic import AsyncAnthropic
from mcp.client.stdio import StdioClientTransport
from mcp.client.session import ClientSession
import json

class CRMAgentService:
    def __init__(self, tenant_id: UUID, mcp_server_path: str):
        self.tenant_id = tenant_id
        self.client = AsyncAnthropic()
        self.mcp_server_path = mcp_server_path
        self.session: Optional[ClientSession] = None
    
    async def initialize(self):
        """Start MCP server and establish connection"""
        transport = StdioClientTransport(
            command=self.mcp_server_path,
            args=["--tenant-id", str(self.tenant_id)]
        )
        self.session = ClientSession(transport)
        await self.session.initialize()
        
        # Discover available tools from MCP server
        tools_response = await self.session.list_tools()
        self.tools = tools_response.tools
    
    async def run(self, user_message: str) -> str:
        """
        Main agent loop with Claude + MCP tools
        Implements agentic loop with tool calling
        """
        messages = [
            {"role": "user", "content": user_message}
        ]
        
        system_prompt = """You are a helpful CRM assistant. You can:
        - Search for customers
        - View customer order history
        - Create new customers
        - Update customer information
        
        Always be polite and accurate. If you can't find information,
        say so clearly."""
        
        while True:
            # Call Claude with available tools
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=system_prompt,
                tools=[
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": json.loads(tool.inputSchema)
                    }
                    for tool in self.tools
                ],
                messages=messages
            )
            
            # Check if Claude wants to use a tool
            if response.stop_reason == "tool_use":
                # Extract tool use blocks
                tool_results = []
                
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        
                        # Execute tool via MCP
                        result = await self.session.call_tool(
                            name=tool_name,
                            arguments=tool_input
                        )
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result)
                        })
                
                # Add Claude response + tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            
            else:
                # Claude finished, extract text response
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text
                return "No response generated"

# API endpoint to trigger agent
@router.post("/api/agents/crm/run")
async def run_crm_agent(
    request: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Run CRM agent for current tenant"""
    
    agent = CRMAgentService(
        tenant_id=current_user.tenant_id,
        mcp_server_path="/app/agents/crm_agent_server.py"
    )
    
    await agent.initialize()
    result = await agent.run(request.message)
    
    # Log agent run
    await db.create(AgentRun(
        tenant_id=current_user.tenant_id,
        agent_name="crm_agent",
        input=request.message,
        output=result,
        status="success",
        tokens_used=0
    ))
    
    return {"response": result, "agent": "crm_agent"}
```

### Agent Configuration (YAML)

```yaml
# agents/configs/crm_agent.yml
agent:
  id: crm_agent
  name: CRM Agent
  version: 1.0.0
  description: Customer Relationship Management Agent
  
mcp_server:
  type: stdio
  path: /app/agents/crm_agent_server.py
  args:
    - "--tenant-id"
    - "{tenant_id}"
  
llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 2048
  
tools:
  - name: search_customers
    description: Search for customers
    enabled: true
  - name: get_customer_orders
    description: Get customer order history
    enabled: true
  - name: create_customer
    description: Create new customer
    enabled: true
  
system_prompt: |
  You are a helpful CRM assistant. You have access to tools
  to manage customer relationships and view order history.
  Always be accurate and professional.
  
monitoring:
  log_level: INFO
  track_tokens: true
  track_errors: true
```

---

## 🏗️ Microservices Setup

### API Service (FastAPI)

```python
# services/api/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connections
    logger.info("Starting API service...")
    
    # Connect to databases
    await init_db()
    await init_redis()
    
    # Load MCP servers
    await load_mcp_servers()
    
    yield
    
    # Shutdown: Cleanup
    logger.info("Shutting down API service...")
    await cleanup_db()
    await cleanup_redis()

app = FastAPI(
    title="VorstersNV API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://vorsters.nl", "https://*.vorsters.nl"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(tenants_router, prefix="/api/tenants", tags=["tenants"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(products_router, prefix="/api/products", tags=["products"])
app.include_router(orders_router, prefix="/api/orders", tags=["orders"])
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0"
    }

@app.get("/ready")
async def readiness_check():
    # Check all dependencies
    db_ok = await check_db()
    redis_ok = await check_redis()
    
    if db_ok and redis_ok:
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Agent Service (Async Queue)

```python
# services/agents/orchestrator.py
from celery import Celery
from redis import Redis
import asyncio
import json

celery = Celery(
    "agents",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

@celery.task(bind=True, max_retries=3)
def run_agent_task(self, tenant_id: str, agent_name: str, user_input: str):
    """
    Async task to run an agent
    Retries up to 3 times on failure
    """
    try:
        # Load agent
        agent = load_agent(tenant_id, agent_name)
        
        # Run agent (blocking call)
        result = asyncio.run(agent.run(user_input))
        
        # Store result
        store_agent_result(tenant_id, agent_name, user_input, result)
        
        return {"status": "success", "result": result}
    
    except Exception as exc:
        # Retry with exponential backoff
        self.retry(exc=exc, countdown=2 ** self.request.retries)

@celery.task
def process_webhook(webhook_id: str, payload: dict):
    """Process incoming webhook asynchronously"""
    # Trigger agents based on webhook type
    if payload.get("type") == "order.created":
        run_agent_task.delay(
            tenant_id=payload["tenant_id"],
            agent_name="order_agent",
            user_input=f"Process order: {payload['order_id']}"
        )

# Periodic tasks
@celery.task
def sync_inventory():
    """Sync inventory levels every hour"""
    logger.info("Running inventory sync...")

@celery.task
def generate_daily_report():
    """Generate daily business report"""
    logger.info("Generating daily report...")

# Schedule
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'sync-inventory': {
        'task': 'services.agents.orchestrator.sync_inventory',
        'schedule': crontab(minute=0),  # Every hour
    },
    'daily-report': {
        'task': 'services.agents.orchestrator.generate_daily_report',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
    },
}
```

### Real-time Service (WebSocket)

```python
# services/realtime/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from redis import Redis
import json

@app.websocket("/ws/dashboard/{tenant_id}")
async def websocket_dashboard(websocket: WebSocket, tenant_id: str):
    """WebSocket endpoint for real-time dashboard updates"""
    
    await websocket.accept()
    client_id = str(uuid.uuid4())
    redis = Redis(host="redis")
    
    # Subscribe to tenant events
    pubsub = redis.pubsub()
    pubsub.subscribe(f"tenant:{tenant_id}:events")
    
    try:
        while True:
            # Forward Redis events to WebSocket
            message = pubsub.get_message()
            if message:
                await websocket.send_json({
                    "type": message["data"].get("type"),
                    "data": json.loads(message["data"].get("payload", "{}"))
                })
            
            # Check for client messages (ping/pong)
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=1.0
                )
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                pass
            
            await asyncio.sleep(0.1)
    
    except WebSocketDisconnect:
        pubsub.unsubscribe()
        logger.info(f"Client {client_id} disconnected")

# Emit events to WebSocket subscribers
async def emit_event(tenant_id: str, event_type: str, data: dict):
    """Send real-time event to all connected clients"""
    redis = Redis(host="redis")
    redis.publish(
        f"tenant:{tenant_id}:events",
        json.dumps({"type": event_type, "payload": json.dumps(data)})
    )
```

---

## ☁️ Cloud Infrastructure

### Kubernetes Manifests

```yaml
# infra/kubernetes/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: vorsters
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
    spec:
      containers:
      - name: api
        image: ghcr.io/koenvorster/vorsters-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: connection-string
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: vorsters
spec:
  selector:
    app: api-service
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: autoscaling.k8s.io/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: vorsters
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Terraform (Infrastructure-as-Code)

```hcl
# infra/terraform/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name            = "vorsters-cloud"
  version         = "1.28"
  role_arn        = aws_iam_role.eks_role.arn
  
  vpc_config {
    subnet_ids = [
      aws_subnet.private_1.id,
      aws_subnet.private_2.id,
    ]
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "main" {
  identifier              = "vorsters-db"
  engine                  = "postgres"
  engine_version          = "16.1"
  instance_class          = "db.r6i.xlarge"
  allocated_storage       = 100
  storage_type            = "gp3"
  multi_az                = true
  
  username                = var.db_username
  password                = var.db_password
  db_name                 = "vorsters"
  
  skip_final_snapshot     = false
  final_snapshot_identifier = "vorsters-db-final"
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "vorsters-redis"
  engine              = "redis"
  engine_version      = "7.0"
  node_type           = "cache.r7i.xlarge"
  num_cache_nodes     = 3
  parameter_group_name = "default.redis7"
  port                = 6379
}

# S3 for file storage
resource "aws_s3_bucket" "files" {
  bucket = "vorsters-files"
}

variable "aws_region" {
  default = "eu-west-1"
}

variable "db_username" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

output "eks_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "rds_endpoint" {
  value = aws_db_instance.main.endpoint
}
```

---

## 🔐 Security Implementation

### API Authentication

```python
# services/api/auth/jwt_handler.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

security = HTTPBearer()

class TokenPayload(BaseModel):
    tenant_id: UUID
    user_id: UUID
    email: str
    roles: List[str]
    permissions: List[str]
    exp: datetime

async def create_access_token(
    user: User,
    tenant_id: UUID,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    
    if expires_delta is None:
        expires_delta = timedelta(hours=24)
    
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "tenant_id": str(tenant_id),
        "user_id": str(user.id),
        "email": user.email,
        "roles": user.roles,
        "permissions": user.permissions,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security)
) -> TokenPayload:
    """Verify JWT and return current user"""
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        
        token = TokenPayload(**payload)
        
        # Check expiration
        if datetime.fromtimestamp(token.exp) < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token expired")
        
        return token
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_permission(
    permission: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Dependency to check user permissions"""
    if permission not in current_user.permissions:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )
    
    return current_user
```

### Multi-Tenant Row-Level Security

```sql
-- Enable RLS on all tables
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see data from their tenant
CREATE POLICY tenant_isolation ON customers
FOR SELECT
USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY tenant_isolation_insert ON customers
FOR INSERT
WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Set tenant context per request
SET app.current_tenant_id = '550e8400-e29b-41d4-a716-446655440000';
```

---

## 📊 API Specifications

### Order Endpoints

```python
# services/api/routers/orders.py

@router.post("/api/orders")
async def create_order(
    request: CreateOrderRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Create new order"""
    order = Order(
        tenant_id=current_user.tenant_id,
        customer_id=request.customer_id,
        total=request.total,
        status="pending"
    )
    db.add(order)
    await db.commit()
    return OrderResponse.from_orm(order)

@router.get("/api/orders")
async def list_orders(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[OrderResponse]:
    """List all orders for tenant with pagination"""
    
    query = db.query(Order).filter(
        Order.tenant_id == current_user.tenant_id
    )
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = await query.offset(skip).limit(limit).all()
    return [OrderResponse.from_orm(o) for o in orders]

@router.get("/api/orders/{order_id}")
async def get_order(
    order_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OrderDetailResponse:
    """Get single order with items"""
    
    order = await db.query(Order).filter(
        Order.id == order_id,
        Order.tenant_id == current_user.tenant_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderDetailResponse.from_orm(order)

@router.patch("/api/orders/{order_id}")
async def update_order(
    order_id: UUID,
    update: UpdateOrderRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """Update order status"""
    
    order = await db.query(Order).filter(
        Order.id == order_id,
        Order.tenant_id == current_user.tenant_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Trigger agent on status change
    if update.status != order.status:
        trigger_agent.delay(
            tenant_id=str(current_user.tenant_id),
            agent_name="order_agent",
            event="order.status_changed",
            order_id=str(order_id),
            new_status=update.status
        )
    
    order.status = update.status
    await db.commit()
    return OrderResponse.from_orm(order)
```

---

## 🚀 DevOps & CI/CD

### GitHub Actions Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
      redis:
        image: redis:7
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: pytest tests/ -v --cov
      env:
        DATABASE_URL: postgresql://postgres:test@localhost/test
        REDIS_URL: redis://localhost:6379
    
    - name: Run linting
      run: ruff check .
    
    - name: Run type checking
      run: mypy services/
  
  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t vorsters-api:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        docker tag vorsters-api:${{ github.sha }} ghcr.io/koenvorster/vorsters-api:latest
        docker push ghcr.io/koenvorster/vorsters-api:latest
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to ArgoCD
      run: |
        kubectl set image deployment/api-service \
          api=ghcr.io/koenvorster/vorsters-api:latest \
          -n vorsters
        kubectl rollout status deployment/api-service -n vorsters
```

---

**Continue in next section for Database Design & Complete Specs**
