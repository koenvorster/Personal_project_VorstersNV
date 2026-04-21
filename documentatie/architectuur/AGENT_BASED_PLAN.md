# 📋 AGENT-GEBASEERD PLAN – VorstersNV Fase 3-5 Uitvoering

## 🎯 Inleiding

Dit plan beschrijft hoe je de **8 bestaande agents** in VorstersNV kunt gebruiken om Fase 3-5 in te vullen. Elk agent wordt gebruikt in specifieke workflows en use cases.

---

## 🤖 Agent Overzicht

### Jouw 8 Agents

| Agent | Model | Focus | Sub-Agents |
|-------|-------|-------|-----------|
| **1. Klantenservice Agent** | llama3 | Klantenvragen & support | Retour, Email, Fraude |
| **2. Order Verwerking Agent** | llama3 | Orderflow automation | Fraude, Email, Voorraad |
| **3. Product Beschrijving Agent** | mistral | SEO & product texts | Geen |
| **4. SEO Agent** | mistral | SEO optimalisatie | Product Beschrijving |
| **5. Fraude Detectie Agent** | llama3 | Verdachte patronen | Klantenservice |
| **6. Retour Verwerking Agent** | llama3 | Retouraanvragen | Email, Voorraad |
| **7. Email Template Agent** | mistral | Email generatie | Geen |
| **8. Voorraad Advies Agent** | llama3 | Inventory management | Geen |

---

## 🔄 Fase 3 – Agent Workflows

### **USE CASE 1: Nieuwe Klant Plaatst Order**

```
Customer buys product
    │
    ▼ (POST /api/orders)
Order Verwerking Agent
    │
    ├─► Fraude Detectie Agent
    │   └─ Analyze risk score
    │
    ├─► Email Template Agent  
    │   └─ Generate order confirmation
    │
    └─► Voorraad Advies Agent
        └─ Check stock levels
            │
            ▼ (Update DB)
        Inventory updated
            │
            ▼ (Send email)
        Customer notified
            │
            ▼ (Webhook)
        Warehouse receives pickup task
```

**Agent Execution Order:**
1. Order Verwerking Agent (validatie)
2. Fraude Detectie Agent (parallel)
3. Email Template Agent (confirmation)
4. Voorraad Advies Agent (stock)

**Expected Outcomes:**
- ✅ Order status: "confirmed" or "flagged"
- ✅ Email sent to customer
- ✅ Stock updated
- ✅ Warehouse notified

---

### **USE CASE 2: Klant Vraagt about Product**

```
Customer sends question
    │
    ▼ (Chat interface / email)
Klantenservice Agent
    │
    ├─ Parse customer question
    ├─ Analyze sentiment (angry/happy/neutral)
    │
    ├─ IF (retour aanvraag)
    │   │
    │   ▼
    │   Retour Verwerking Agent
    │   │
    │   ├─ Process return
    │   ├─ Update order status
    │   │
    │   ▼
    │   Email Template Agent
    │   └─ Send return label
    │
    ├─ IF (verdacht behavior)
    │   │
    │   ▼
    │   Fraude Detectie Agent
    │   └─ Flag account
    │
    └─ Compose & send response
        │
        ▼
    Customer receives answer
```

**Agent Execution Order:**
1. Klantenservice Agent (route question)
2. Sub-agents as needed (conditional)
3. Response sent

---

### **USE CASE 3: Product beschrijving maken**

```
New product added to shop
    │
    ▼ (Product ID + metadata)
Product Beschrijving Agent
    │
    ├─ Generate multiple versions
    │  ├─ Title
    │  ├─ Short description
    │  ├─ Long description
    │  ├─ USP list
    │  └─ FAQ section
    │
    ▼
SEO Agent
    │
    ├─ Optimize for keywords
    ├─ Generate meta tags
    ├─ Suggest internal links
    │
    ▼
Email Template Agent
    │
    ├─ Notify marketing team
    └─ Send product launch email
        │
        ▼
    Product live on website
```

**Agent Execution Order:**
1. Product Beschrijving Agent (content)
2. SEO Agent (optimization)
3. Email Template Agent (notification)

---

## 🛠️ Fase 3 Implementation – Agent Integration Points

### **Router: /api/orders** (Order Management)

```python
# api/routers/orders.py

from fastapi import APIRouter, HTTPException
from ollama.agent_runner import AgentRunner

router = APIRouter(prefix="/api/orders", tags=["orders"])
runner = AgentRunner()

@router.post("/")
async def create_order(order_data: OrderData):
    """
    Create order using agents
    1. Order Verwerking Agent validates
    2. Fraude Detectie Agent checks
    3. Email Template Agent notifies
    """
    
    # Step 1: Order Verification
    verification = await runner.run_agent(
        agent_name="order_verwerking_agent",
        user_input=f"""
        Validate this order:
        - Order ID: {order_data.order_id}
        - Customer: {order_data.customer_name}
        - Products: {order_data.products}
        - Total: {order_data.total}
        - Payment: {order_data.payment_method}
        
        Check if valid and ready to process.
        """
    )
    
    if not verification['success']:
        raise HTTPException(status_code=400, detail="Order validation failed")
    
    # Step 2: Fraud Check (parallel)
    fraud_check = await runner.run_agent(
        agent_name="fraude_detectie_agent",
        user_input=f"""
        Analyze fraud risk:
        - Order: {order_data.order_id}
        - Customer history: {customer_history}
        - Amount: {order_data.total}
        - Payment method: {order_data.payment_method}
        
        Provide fraud score (0.0 to 1.0).
        """
    )
    
    fraud_score = fraud_check['output'].get('fraud_score', 0.0)
    
    if fraud_score > 0.8:
        # Flag for manual review
        order_status = "pending_review"
    else:
        order_status = "confirmed"
    
    # Step 3: Send Confirmation Email
    email = await runner.run_agent(
        agent_name="email_template_agent",
        user_input=f"""
        Generate order confirmation email:
        - Order ID: {order_data.order_id}
        - Customer: {order_data.customer_name}
        - Total: {order_data.total}
        - Estimated delivery: {estimated_delivery}
        
        Make it professional and friendly.
        """
    )
    
    # Step 4: Update Inventory
    inventory = await runner.run_agent(
        agent_name="voorraad_advies_agent",
        user_input=f"""
        Update inventory for order:
        - Products: {order_data.products}
        
        Check stock levels and alert if low.
        """
    )
    
    # Save order to database
    db_order = Order(
        order_id=order_data.order_id,
        status=order_status,
        fraud_score=fraud_score,
        total=order_data.total
    )
    db.add(db_order)
    db.commit()
    
    return {
        "success": True,
        "order_id": order_data.order_id,
        "status": order_status,
        "fraud_score": fraud_score,
        "email_sent": email['success']
    }
```

### **Router: /api/products** (Product Management)

```python
# api/routers/products.py

@router.post("/generate-description")
async def generate_product_description(product_data: ProductData):
    """
    Generate product description using agents
    """
    
    # Step 1: Generate Description
    description = await runner.run_agent(
        agent_name="product_beschrijving_agent",
        user_input=f"""
        Create product description:
        - Name: {product_data.name}
        - Category: {product_data.category}
        - Features: {product_data.features}
        - Price range: {product_data.price_range}
        - Target audience: {product_data.target_audience}
        
        Generate professional, engaging description with USP and FAQ.
        """
    )
    
    # Step 2: SEO Optimization
    seo = await runner.run_agent(
        agent_name="seo_agent",
        user_input=f"""
        Optimize for SEO:
        - Description: {description['output']['lange_beschrijving']}
        - Target keywords: {product_data.keywords}
        - Category: {product_data.category}
        
        Suggest meta title, meta description, and internal links.
        """
    )
    
    # Step 3: Notify Team
    notification = await runner.run_agent(
        agent_name="email_template_agent",
        user_input=f"""
        Create notification email:
        - Product: {product_data.name}
        - Status: "Ready for review"
        
        Send to marketing team.
        """
    )
    
    return {
        "product_id": product_data.product_id,
        "description": description['output'],
        "seo": seo['output'],
        "notification_sent": notification['success']
    }
```

### **Router: /api/support** (Customer Support)

```python
# api/routers/support.py

@router.post("/chat")
async def customer_support(message: CustomerMessage):
    """
    Handle customer support using Klantenservice Agent
    """
    
    # Step 1: Process with Klantenservice Agent
    response = await runner.run_agent(
        agent_name="klantenservice_agent",
        user_input=f"""
        Customer message: "{message.content}"
        Customer ID: {message.customer_id}
        Order history: {get_customer_orders(message.customer_id)}
        
        Analyze the question and provide helpful response.
        Include appropriate actions (refund, return, etc).
        """
    )
    
    agent_response = response['output']
    
    # Step 2: Check if return request
    if agent_response.get('action') == 'return_request':
        retour = await runner.run_agent(
            agent_name="retour_verwerking_agent",
            user_input=f"""
            Process return request:
            - Order ID: {agent_response['order_id']}
            - Reason: {agent_response['return_reason']}
            - Items: {agent_response['items']}
            
            Generate return label and instructions.
            """
        )
        
        agent_response['return_label'] = retour['output']['return_label']
    
    # Step 3: Check if fraud-suspicious
    if agent_response.get('fraud_flag'):
        fraude = await runner.run_agent(
            agent_name="fraude_detectie_agent",
            user_input=f"""
            Analyze suspicious behavior:
            - Customer: {message.customer_id}
            - Message: {message.content}
            - History: {get_customer_history(message.customer_id)}
            
            Provide risk assessment.
            """
        )
        
        agent_response['fraud_assessment'] = fraude['output']
    
    return {
        "message": agent_response['response'],
        "actions": agent_response.get('actions', []),
        "requires_escalation": agent_response.get('escalate_to_human', False)
    }
```

---

## 📊 Fase 4 – Home Assistant + MCP AI Agents

### **Integration Pattern**

```
Home Assistant Event
    │
    ▼
MCP Server
    │
    ├─ Home Automation Agent
    │  (van mcp-server/agents/)
    │
    └─ (Optional: Call VorstersNV Agents)
       │
       └─ Use existing agents for business logic
          - Order status notifications
          - Inventory alerts
          - Customer service escalations
```

### **Use Case: Order → Smart Home**

```python
# ollama/orchestrator.py

class WorkflowOrchestrator:
    async def handle_order_created(self, order_data):
        """
        1. Process order with agents
        2. Notify smart home warehouse
        """
        
        # Step 1: Run VorstersNV agents
        order_result = await self.run_order_workflow(order_data)
        
        # Step 2: Trigger smart home
        if order_result['success']:
            # Call MCP Server (on Linux server)
            await self.call_mcp_server(
                trigger="order_created",
                action="warehouse_lights_on",
                context={
                    "order_id": order_data.order_id,
                    "priority": "high" if order_data.total > 1000 else "normal"
                }
            )
```

---

## 🔗 Fase 5 – Multi-Agent Orchestration

### **Advanced Workflow: Complete Order → Fulfillment**

```
Customer Order
    │
    ├─► Order Verwerking Agent
    │   └─ Validate & confirm
    │
    ├─► Fraude Detectie Agent (parallel)
    │   └─ Risk assessment
    │
    ├─► Email Template Agent (if clear)
    │   └─ Send confirmation
    │
    ├─► Voorraad Advies Agent
    │   └─ Check & update inventory
    │
    ├─► MCP Server (if warehouse)
    │   └─ Turn on lights
    │
    └─► Klantenservice Agent (if needed)
        └─ Handle special requests
            │
            ├─► Retour Verwerking Agent (if return)
            │   └─ Generate label
            │
            └─► Email Template Agent
                └─ Send follow-up
```

### **Agent Chaining Pattern**

```yaml
# orchestration/workflows/complete_order_flow.yml

name: Complete Order Workflow
version: 1.0

steps:
  - id: "validate"
    agent: "order_verwerking_agent"
    input:
      - $order.customer_email
      - $order.total
      - $order.items
    output: $order_validation
    
  - id: "fraud_check"
    agent: "fraude_detectie_agent"
    input:
      - $order_validation.order_id
      - $customer.history
      - $order.payment_method
    output: $fraud_result
    parallel: true  # Run alongside other steps
    
  - id: "send_confirmation"
    agent: "email_template_agent"
    input:
      - $order_validation
      - $customer.name
      - $customer.email
    output: $email_sent
    depends_on:
      - validate
      - fraud_check
    condition: "$fraud_result.fraud_score < 0.8"
    
  - id: "update_inventory"
    agent: "voorraad_advies_agent"
    input:
      - $order.items
      - $warehouse_id
    output: $inventory_updated
    depends_on:
      - validate
    
  - id: "notify_warehouse"
    type: "webhook"
    url: "http://mcp-server:8000/automation/trigger"
    input:
      - trigger: "order_created"
      - order_id: $order.order_id
      - priority: "$order.total > 1000 ? 'high' : 'normal'"
    depends_on:
      - send_confirmation

  - id: "log_metrics"
    type: "database"
    operation: "insert"
    table: "order_metrics"
    input:
      - order_id: $order.order_id
      - validation_time: $validate.execution_time
      - fraud_score: $fraud_result.fraud_score
      - email_sent: $email_sent.success
```

---

## 📈 Performance & Metrics

### **Agent Performance Tracking**

```python
# api/analytics/agent_metrics.py

class AgentMetrics:
    async def track_execution(self, agent_name, execution_time, success):
        """Track agent performance"""
        
        metrics = {
            "agent_name": agent_name,
            "execution_time": execution_time,
            "success": success,
            "timestamp": datetime.now(),
            "model": agents_config[agent_name]['model'],
            "temperature": agents_config[agent_name]['temperature']
        }
        
        # Save to database
        db.add(AgentExecutionMetric(**metrics))
        
        # Check if needs optimization
        avg_time = db.query(AgentExecutionMetric).filter_by(
            agent_name=agent_name
        ).average('execution_time')
        
        if execution_time > avg_time * 1.5:
            # Alert: Performance degradation
            await notify_admin(f"Agent {agent_name} is slow")

@app.get("/analytics/agents")
async def agent_dashboard():
    """Dashboard showing all agent metrics"""
    
    agents_stats = {}
    
    for agent_name in AGENTS_LIST:
        stats = db.query(AgentExecutionMetric).filter_by(
            agent_name=agent_name
        ).all()
        
        agents_stats[agent_name] = {
            "total_executions": len(stats),
            "success_rate": sum(1 for s in stats if s.success) / len(stats),
            "avg_time": avg(s.execution_time for s in stats),
            "last_execution": stats[-1].timestamp if stats else None,
            "model": agents_config[agent_name]['model']
        }
    
    return agents_stats
```

### **Example Metrics Output**

```json
{
  "order_verwerking_agent": {
    "total_executions": 1247,
    "success_rate": 0.98,
    "avg_time": 2.3,
    "last_execution": "2026-04-18T14:32:00",
    "model": "llama3"
  },
  "klantenservice_agent": {
    "total_executions": 342,
    "success_rate": 0.94,
    "avg_time": 3.1,
    "last_execution": "2026-04-18T14:31:45",
    "model": "llama3"
  },
  "fraude_detectie_agent": {
    "total_executions": 1247,
    "success_rate": 0.99,
    "avg_time": 0.8,
    "last_execution": "2026-04-18T14:32:00",
    "model": "llama3"
  }
}
```

---

## 🧠 Fase 5+ – Advanced Features

### **Agent Learning & Optimization**

```python
# ollama/agent_optimizer.py

class AgentOptimizer:
    async def analyze_feedback(self, agent_name):
        """
        Collect feedback and optimize agent
        """
        
        # Get recent executions
        recent = db.query(AgentExecutionMetric).filter_by(
            agent_name=agent_name
        ).order_by(desc(timestamp)).limit(100).all()
        
        # Analyze patterns
        failures = [r for r in recent if not r.success]
        slow_executions = [r for r in recent if r.execution_time > 5.0]
        
        # Suggest improvements
        suggestions = {
            "lower_temperature": failures > len(recent) * 0.1,
            "reduce_max_tokens": slow_executions > len(recent) * 0.2,
            "improve_prompt": analyze_failures(failures),
            "add_examples": need_more_context(failures)
        }
        
        return suggestions
    
    async def update_agent_config(self, agent_name, changes):
        """Update agent configuration based on performance"""
        
        config = load_agent_config(agent_name)
        
        if changes['lower_temperature']:
            config['temperature'] = max(0.0, config['temperature'] - 0.1)
        
        if changes['reduce_max_tokens']:
            config['max_tokens'] = max(256, config['max_tokens'] - 256)
        
        save_agent_config(agent_name, config)
```

### **Multi-Agent Collaboration**

```python
# ollama/agent_collaboration.py

class AgentCollab:
    async def solve_complex_problem(self, problem_description):
        """
        Use multiple agents to solve a complex problem
        Example: Analyze customer churn
        """
        
        agents_involved = [
            "klantenservice_agent",      # Understand customer issues
            "order_verwerking_agent",    # Check order patterns
            "product_beschrijving_agent", # Product quality issues
            "seo_agent"                  # Market positioning
        ]
        
        insights = {}
        
        for agent in agents_involved:
            result = await runner.run_agent(
                agent_name=agent,
                user_input=f"""
                Analyze customer churn:
                {problem_description}
                
                From your perspective as {agent}, what's causing this?
                """
            )
            
            insights[agent] = result['output']
        
        # Synthesize insights
        synthesis = await runner.run_agent(
            agent_name="klantenservice_agent",  # Lead agent
            user_input=f"""
            Synthesize these insights about customer churn:
            
            {json.dumps(insights, indent=2)}
            
            Provide actionable recommendations.
            """
        )
        
        return {
            "problem": problem_description,
            "individual_insights": insights,
            "recommendations": synthesis['output']
        }
```

---

## 📋 Implementation Checklist

### **Phase 3: Agent Integration (Weeks 1-4)**

- [ ] **Order Router Integration**
  - [ ] Connect Order Verwerking Agent
  - [ ] Connect Fraude Detectie Agent
  - [ ] Connect Email Template Agent
  - [ ] Connect Voorraad Advies Agent
  - [ ] Test complete workflow

- [ ] **Product Router Integration**
  - [ ] Connect Product Beschrijving Agent
  - [ ] Connect SEO Agent
  - [ ] Test description generation
  - [ ] Test SEO optimization

- [ ] **Support Router Integration**
  - [ ] Connect Klantenservice Agent
  - [ ] Connect conditional sub-agents
  - [ ] Test chat functionality
  - [ ] Test escalation flow

- [ ] **Analytics & Monitoring**
  - [ ] Setup agent metrics tracking
  - [ ] Create dashboard
  - [ ] Setup alerts

### **Phase 4: Smart Home Integration (Weeks 5-8)**

- [ ] **MCP Server agents**
  - [ ] Deploy home_automation_agent
  - [ ] Deploy energy_management_agent
  - [ ] Deploy security_agent

- [ ] **Integration points**
  - [ ] Order → warehouse lights
  - [ ] Payment → device notifications
  - [ ] Customer alerts → smart devices

### **Phase 5: Advanced Features (Weeks 9+)**

- [ ] **Agent optimization**
  - [ ] Feedback loop implementation
  - [ ] Performance tuning
  - [ ] Prompt optimization

- [ ] **Multi-agent features**
  - [ ] Complex problem solving
  - [ ] Agent collaboration
  - [ ] Cross-agent learning

---

## 🎯 Success Criteria

✅ **Fase 3:**
- All 8 agents integrated and responding
- Order workflow fully automated
- Customer support via Klantenservice Agent
- 95%+ order processing success rate
- < 2 second average agent response time

✅ **Fase 4:**
- Smart home agents deployed on Linux server
- Order → warehouse automation working
- MCP Server responding to events

✅ **Fase 5:**
- Agent optimization improving performance
- Multi-agent collaboration on complex problems
- Advanced analytics dashboard

---

## 📞 Next Steps

1. **Implement Use Case 1** (Order processing) → test all 5 agents
2. **Implement Use Case 2** (Customer support) → test conditional routing
3. **Implement Use Case 3** (Product description) → test content generation
4. **Add analytics** → track performance
5. **Optimize** → improve based on metrics

Ready to start implementation? 🚀
