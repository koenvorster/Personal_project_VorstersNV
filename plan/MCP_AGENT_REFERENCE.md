# 📚 VorstersNV – MCP Agent Reference Library

**Complete guide to building and deploying MCP agents for the platform**

---

## 🎯 Quick Start: Your First MCP Agent

### 1. Create Agent Structure

```bash
mkdir -p agents/crm_agent
cd agents/crm_agent

# Create files
touch __init__.py
touch server.py        # MCP server implementation
touch tools.py         # Tool definitions
touch config.yml       # Agent configuration
touch README.md
```

### 2. Implement MCP Server

```python
# agents/crm_agent/server.py
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import List
import asyncio

mcp = FastMCP("CRM Agent")

class CustomerModel(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    status: str  # active | inactive | vip
    created_at: str

class CustomerSearchInput(BaseModel):
    query: str
    limit: int = 10

# ============= TOOLS =============

@mcp.tool()
async def search_customers(input: CustomerSearchInput) -> List[CustomerModel]:
    """
    Search for customers by name, email, or phone.
    
    Perfect for finding existing customers quickly.
    """
    # TODO: Implement database query
    # return await db.customers.search(input.query, limit=input.limit)
    return []

@mcp.tool()
async def get_customer(customer_id: str) -> CustomerModel:
    """Get detailed customer information by ID"""
    # return await db.customers.get(customer_id)
    pass

@mcp.tool()
async def create_customer(name: str, email: str, phone: str) -> CustomerModel:
    """Create a new customer record"""
    # return await db.customers.create(name=name, email=email, phone=phone)
    pass

@mcp.tool()
async def update_customer(customer_id: str, **updates) -> CustomerModel:
    """Update customer information"""
    # return await db.customers.update(customer_id, updates)
    pass

@mcp.tool()
async def get_customer_orders(customer_id: str) -> List[dict]:
    """Get all orders from a specific customer"""
    # return await db.orders.filter(customer_id=customer_id)
    pass

@mcp.tool()
async def add_customer_note(customer_id: str, note: str) -> dict:
    """Add a note to customer record (e.g., preferences, issues, follow-ups)"""
    # return await db.customer_notes.create(customer_id, note)
    pass

# ============= RESOURCES =============

@mcp.resource("customer://templates/email")
async def get_email_templates() -> List[dict]:
    """
    Access email templates for customer communication.
    
    Returns template names, subjects, and placeholder variables.
    """
    # return await db.email_templates.list()
    pass

@mcp.resource("customer://settings")
async def get_customer_settings() -> dict:
    """Get CRM configuration and settings for this tenant"""
    # return await db.settings.get("crm")
    pass

# ============= ENTRY POINT =============

if __name__ == "__main__":
    import sys
    mcp.run(sys.stdin.buffer, sys.stdout.buffer)
```

### 3. Configure Agent

```yaml
# agents/crm_agent/config.yml
agent:
  id: crm_agent
  name: "CRM Agent"
  version: "1.0.0"
  description: "Customer Relationship Management with search, create, update capabilities"
  
  # Icon for UI
  icon: "👥"
  
  # Tags for discovery
  tags:
    - crm
    - customer
    - sales
    - support

# MCP Server configuration
mcp:
  type: stdio
  executable: python
  args:
    - agents/crm_agent/server.py
  
  # Timeout for tool execution
  tool_timeout_ms: 30000
  
  # Resource polling (optional)
  resource_sync_interval_ms: 60000

# LLM Configuration
llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  
  temperature: 0.7
  max_tokens: 2048
  
  # System prompt for this agent
  system_prompt: |
    You are a professional CRM assistant for customer relationship management.
    
    Your responsibilities:
    - Help users find and manage customer information
    - Maintain accurate customer records
    - Provide customer history and context
    - Suggest next best actions for customer engagement
    
    Always be professional, accurate, and customer-focused.
    Double-check information before making changes.
    Ask for clarification if needed.

# Capabilities
capabilities:
  - customer_search
  - customer_management
  - order_history
  - email_templates
  - note_taking

# API Endpoints
endpoints:
  run: POST /api/agents/crm/run
  status: GET /api/agents/crm/status
  tools: GET /api/agents/crm/tools

# Monitoring & Logging
monitoring:
  log_level: INFO
  track_metrics: true
  alert_on_errors: true
  
  # Cost tracking (for API calls)
  track_costs: true
  cost_limit_per_run_usd: 0.50

# Permissions required
permissions:
  - read:customers
  - write:customers
  - read:orders
  - write:notes
```

---

## 🏗️ Agent Patterns & Templates

### Pattern 1: Search & Retrieve

```python
# Use case: Find information quickly

@mcp.tool()
async def search_products(query: str, category: str = None) -> List[dict]:
    """Search product catalog"""
    filters = {"name__icontains": query}
    if category:
        filters["category"] = category
    return await db.products.filter(**filters).limit(20)

# Claude will understand:
# - "Find me red shoes"
# - "Show me all electronics under $50"
# - "Search for coffee makers"
```

### Pattern 2: Create & Update

```python
# Use case: Modify data based on user request

@mcp.tool()
async def create_order(
    customer_id: str,
    items: List[dict],  # [{product_id, quantity}]
    shipping_address: str
) -> dict:
    """Create new customer order"""
    order = await db.orders.create(
        customer_id=customer_id,
        items=items,
        status="pending",
        shipping_address=shipping_address
    )
    return {"order_id": order.id, "total": order.total}

@mcp.tool()
async def update_order_status(order_id: str, status: str) -> dict:
    """Update order status (pending|processing|shipped|delivered)"""
    await db.orders.update(order_id, status=status)
    return {"message": f"Order updated to {status}"}

# Claude will understand natural language:
# - "Create an order for customer #123 with 2 units of product #456"
# - "Mark order #ABC as shipped"
```

### Pattern 3: Analysis & Reporting

```python
# Use case: Generate insights and reports

@mcp.tool()
async def get_sales_analytics(period: str = "month") -> dict:
    """
    Get sales analytics for specified period.
    
    Args:
        period: 'day' | 'week' | 'month' | 'quarter' | 'year'
    """
    return {
        "total_revenue": 45000.50,
        "total_orders": 340,
        "average_order_value": 132.35,
        "top_products": [
            {"name": "Premium Plan", "units": 120},
            {"name": "Basic Plan", "units": 95}
        ],
        "growth_vs_previous": 12.5  # percentage
    }

@mcp.tool()
async def predict_revenue(months_ahead: int = 3) -> dict:
    """
    Predict revenue for next N months using ML model.
    """
    # Uses historical data + ML model
    return {
        "predictions": [
            {"month": "May", "predicted_revenue": 48500},
            {"month": "June", "predicted_revenue": 52000},
            {"month": "July", "predicted_revenue": 55500}
        ],
        "confidence": 0.87
    }

# Claude will understand:
# - "What's our revenue this month?"
# - "Show me sales trends for the quarter"
# - "Predict next 6 months revenue"
```

### Pattern 4: Multi-Step Workflows

```python
# Use case: Complex processes requiring multiple steps

@mcp.tool()
async def process_return_request(
    order_id: str,
    reason: str,
    requested_action: str = "refund"  # refund | exchange | store_credit
) -> dict:
    """
    Process return request with multiple steps:
    1. Validate order and return policy
    2. Create return request
    3. Generate return label
    4. Process refund
    """
    
    # Step 1: Validate
    order = await db.orders.get(order_id)
    if not order:
        return {"error": "Order not found"}
    
    if not is_within_return_window(order.created_at):
        return {"error": "Return window expired"}
    
    # Step 2: Create return
    return_request = await db.return_requests.create(
        order_id=order_id,
        reason=reason,
        status="approved"
    )
    
    # Step 3: Generate label
    label = await shipping_service.generate_return_label(order_id)
    
    # Step 4: Process refund
    if requested_action == "refund":
        await payment_service.process_refund(order.payment_id)
    
    return {
        "return_request_id": return_request.id,
        "return_label": label.url,
        "status": "approved",
        "refund_amount": order.total
    }

# Claude understands the workflow:
# - "Process a return for order #12345, customer wants a refund"
# - Claude automatically calls the tool and handles each step
```

---

## 🔗 Agent Communication Patterns

### Pattern 1: Agent Calling Another Agent

```python
# In your MCP tool, call another agent service

@mcp.tool()
async def send_customer_email(customer_id: str, template: str) -> dict:
    """
    Send email using email_template_agent
    """
    
    # Get customer
    customer = await db.customers.get(customer_id)
    
    # Call email agent
    email_agent = EmailTemplateAgent(tenant_id)
    email_result = await email_agent.run(
        f"Send {template} email to {customer.email}"
    )
    
    return {
        "sent": True,
        "email": customer.email,
        "template": template
    }
```

### Pattern 2: Event-Triggered Workflows

```python
# Trigger agent on business events

@router.post("/api/orders")
async def create_order(...):
    # ... create order ...
    
    # Trigger order agent
    await trigger_agent_async(
        tenant_id=current_user.tenant_id,
        agent_name="order_agent",
        event="order.created",
        context={
            "order_id": order.id,
            "customer_id": order.customer_id,
            "total": order.total
        }
    )
    
    return {"order_id": order.id}
```

---

## 📦 Built-in Agents Specification

### 1. CRM Agent

**Purpose**: Customer data management

**Tools**:
- `search_customers(query, limit)`
- `get_customer(id)`
- `create_customer(name, email, phone)`
- `update_customer(id, **updates)`
- `get_customer_orders(customer_id)`
- `add_customer_note(customer_id, note)`
- `segment_customers(criteria)` - AI-powered segmentation

**Example Use Cases**:
```
"Find all VIP customers who haven't ordered in 3 months"
"Create a customer record for John Doe"
"What's the lifetime value of customer #123?"
"Add a note that this customer prefers email communication"
```

---

### 2. SEO Agent

**Purpose**: Search optimization and content management

**Tools**:
- `analyze_seo(url)` - Returns SEO score, issues
- `suggest_keywords(topic)` - AI-powered keyword research
- `generate_meta_description(title, content)` - Create meta tags
- `check_rankings(keywords)` - Monitor search positions
- `optimize_content(content_id, target_keywords)` - Improve content

**Example Use Cases**:
```
"Analyze the SEO of our homepage"
"What keywords should we target for 'coffee makers'?"
"Generate meta descriptions for all products"
"Check our Google ranking for 'sustainable fashion'"
```

---

### 3. Analytics Agent

**Purpose**: Business intelligence and reporting

**Tools**:
- `get_kpis(period)` - Revenue, orders, customers, etc.
- `forecast_revenue(months)` - ML-powered prediction
- `analyze_trends(metric, period)` - Trend analysis
- `segment_analysis(segment)` - Performance by segment
- `export_report(type, format)` - Generate reports (PDF, CSV)
- `get_cohort_analysis(created_after, created_before)` - Cohort metrics

**Example Use Cases**:
```
"What were our sales last quarter?"
"Forecast revenue for the next 6 months"
"Show me top-selling products by region"
"Export a monthly revenue report as PDF"
"Which customer cohort has the highest lifetime value?"
```

---

### 4. Support Agent

**Purpose**: Customer support automation

**Tools**:
- `search_knowledge_base(query)` - Find FAQs/docs
- `create_support_ticket(customer_id, issue, priority)` - Create ticket
- `get_ticket_history(customer_id)` - Ticket history
- `send_support_email(customer_id, message)` - Send reply
- `resolve_ticket(ticket_id, resolution)` - Close ticket
- `get_suggested_solution(issue)` - AI suggests answer

**Example Use Cases**:
```
"How do I return an item?" (searches KB)
"Create a support ticket for shipping issue"
"What's the status of ticket #456?"
"This customer keeps asking about refunds - find similar cases"
```

---

### 5. Marketing Agent

**Purpose**: Campaign automation and engagement

**Tools**:
- `create_email_campaign(name, target_segment, template)` - Campaign setup
- `schedule_post(platform, content, date_time)` - Social media
- `analyze_campaign_performance(campaign_id)` - Metrics
- `segment_for_campaign(criteria)` - Create target audience
- `generate_subject_line(topic, tone)` - AI-powered copy
- `a_b_test_campaign(variant_a, variant_b)` - A/B testing

**Example Use Cases**:
```
"Create email campaign for our VIP customers"
"Schedule a post on LinkedIn about our new feature"
"Show me performance of last month's campaign"
"Generate 5 subject line options for our newsletter"
"A/B test two email designs"
```

---

### 6. Inventory Agent

**Purpose**: Stock optimization and supply chain

**Tools**:
- `get_stock_levels()` - Current inventory
- `forecast_demand(product_id, weeks)` - Predict demand
- `set_reorder_point(product_id, quantity)` - Auto-reorder settings
- `reorder_products(product_ids)` - Create purchase order
- `get_low_stock_alerts()` - Items below threshold
- `optimize_stock(cost_per_unit, storage_cost)` - Calculate optimal levels

**Example Use Cases**:
```
"Show all products with low stock"
"What's our demand forecast for Product #123?"
"Set low stock alert for when inventory drops below 10"
"Recommend optimal stock levels for all products"
```

---

## 🚀 Deployment

### Docker Container

```dockerfile
# agents/crm_agent/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy agent code
COPY . .

# Run MCP server
CMD ["python", "server.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crm-agent
  namespace: vorsters
spec:
  replicas: 2
  selector:
    matchLabels:
      app: crm-agent
  template:
    metadata:
      labels:
        app: crm-agent
    spec:
      containers:
      - name: agent
        image: ghcr.io/koenvorster/vorsters-crm-agent:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 📊 Testing Your Agent

```python
# tests/test_crm_agent.py
import pytest
from agents.crm_agent.server import mcp

@pytest.mark.asyncio
async def test_search_customers():
    """Test customer search tool"""
    result = await mcp.call_tool(
        "search_customers",
        input={"query": "John", "limit": 10}
    )
    assert isinstance(result, list)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_create_customer():
    """Test customer creation"""
    result = await mcp.call_tool(
        "create_customer",
        name="Jane Doe",
        email="jane@example.com",
        phone="+31612345678"
    )
    assert result["id"] is not None
    assert result["email"] == "jane@example.com"

@pytest.mark.asyncio
async def test_agent_agentic_loop():
    """Test full Claude + MCP agentic loop"""
    from agents.crm_agent import CRMAgentService
    
    agent = CRMAgentService(tenant_id=UUID("..."))
    response = await agent.run("Find customers named John")
    
    assert "John" in response or "customer" in response.lower()
```

---

## 📝 Publishing Your Agent

### 1. Package as Python Module

```toml
# agents/crm_agent/pyproject.toml
[project]
name = "vorsters-crm-agent"
version = "1.0.0"
description = "CRM Agent for VorstersNV Platform"
authors = [{name = "Koen Vorsters"}]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]
```

### 2. Push to GitHub Packages

```bash
# Build
python -m build

# Push
python -m twine upload --repository github dist/*
```

### 3. Users Can Install

```bash
pip install vorsters-crm-agent
```

---

## 🎓 Learning Resources

- **MCP Documentation**: https://modelcontextprotocol.io/
- **Claude Agent Patterns**: https://docs.anthropic.com/agents
- **Async Python**: https://docs.python.org/3/library/asyncio.html
- **FastMCP**: https://github.com/jlowin/FastMCP

---

**Last Updated**: April 18, 2026  
**Version**: 1.0.0
