# 🔌 AGENT COMMUNICATIE & ORCHESTRATION

## Inleiding

Dit document beschrijft hoe agents met elkaar communiceren, hoe webhooks werken, en hoe het orchestration systeem orders en events routert naar de juiste agents.

---

## 1️⃣ Agent Communication Patterns

### Pattern 1: Sequential (Serie)

**Gebruik:** Normale order processing
- Stap 1 wacht tot Stap 2 klaar is
- Sync & predictable

```python
async def sequential_workflow(order):
    """
    A → B → C (wachten op elkaar)
    """
    
    # Step 1: Validation (wacht)
    validation = await runner.run_agent(
        "order_verwerking_agent",
        user_input=order_data
    )
    
    if not validation['success']:
        return {"error": "Order invalid"}
    
    # Step 2: Fraud check (wacht op validation)
    fraud = await runner.run_agent(
        "fraude_detectie_agent",
        user_input={
            **order_data,
            "validation_result": validation
        }
    )
    
    # Step 3: Email (wacht op fraud)
    if fraud['fraud_score'] < 0.8:
        email = await runner.run_agent(
            "email_template_agent",
            user_input={
                **order_data,
                "fraud_score": fraud['fraud_score']
            }
        )
    
    return {
        "success": True,
        "validation": validation,
        "fraud": fraud,
        "email": email
    }

# Usage
order = {
    "order_id": "ORD123",
    "customer_id": "CUST456",
    "items": [...],
    "total": 99.99
}

result = await sequential_workflow(order)
```

**Voordelen:**
- ✅ Deterministic
- ✅ Easy debugging
- ✅ Clear order of operations

**Nadelen:**
- ❌ Kan langzaam zijn (2-3 seconden)
- ❌ Gevoelig voor failures

---

### Pattern 2: Parallel (Gelijktijdig)

**Gebruik:** Onafhankelijke checks
- Stap 1 & 2 tegelijk
- Sneller (optimaal ~1.5 sec)

```python
async def parallel_workflow(order):
    """
    A → [B | C] (tegelijk, dan D)
    """
    
    # Step 1: Validation (altijd eerst)
    validation = await runner.run_agent(
        "order_verwerking_agent",
        user_input=order_data
    )
    
    if not validation['success']:
        return {"error": "Order invalid"}
    
    # Step 2 & 3: Parallel (tegelijk draaien)
    fraud_task = asyncio.create_task(
        runner.run_agent("fraude_detectie_agent", user_input=order_data)
    )
    
    inventory_task = asyncio.create_task(
        runner.run_agent("voorraad_advies_agent", user_input=order_data)
    )
    
    # Wait for both
    fraud_result, inventory_result = await asyncio.gather(
        fraud_task,
        inventory_task
    )
    
    # Step 4: Email (wacht op parallel results)
    email = await runner.run_agent(
        "email_template_agent",
        user_input={
            **order_data,
            "fraud_score": fraud_result['fraud_score'],
            "stock_status": inventory_result['stock_status']
        }
    )
    
    return {
        "success": True,
        "validation": validation,
        "fraud": fraud_result,
        "inventory": inventory_result,
        "email": email
    }

# Usage
result = await parallel_workflow(order)
# ~0.5 sec faster than sequential!
```

**Voordelen:**
- ✅ Sneller (parallel checks)
- ✅ Beter resource usage

**Nadelen:**
- ❌ Moeilijker debuggen
- ❌ Race conditions mogelijk

---

### Pattern 3: Conditional (Voorwaardelijk)

**Gebruik:** Klantenservice (retour → sub-agent)
- Welke stap volgt hangt af van vorige result

```python
async def conditional_workflow(customer_message):
    """
    A → (IF condition) B ELSE C
    """
    
    # Step 1: Analyze customer message
    analysis = await runner.run_agent(
        "klantenservice_agent",
        user_input=customer_message
    )
    
    response = analysis['output']
    
    # Step 2: Conditional routing
    if response['action'] == 'return_request':
        # Branch A: Retour
        retour = await runner.run_agent(
            "retour_verwerking_agent",
            user_input={
                "order_id": response['order_id'],
                "reason": response['reason'],
                "customer_id": response['customer_id']
            }
        )
        
        # Branch A2: Send email with return label
        email = await runner.run_agent(
            "email_template_agent",
            user_input={
                "template": "return_label",
                "return_id": retour['return_id'],
                "customer_email": response['customer_email']
            }
        )
        
        return {
            "action": "return_processed",
            "return_label": retour['return_label'],
            "email_sent": email['success']
        }
    
    elif response['action'] == 'product_question':
        # Branch B: Product info
        # (no sub-agent needed, just respond)
        return {
            "action": "question_answered",
            "answer": response['answer']
        }
    
    elif response['fraud_flag']:
        # Branch C: Fraud check
        fraude = await runner.run_agent(
            "fraude_detectie_agent",
            user_input={
                "customer_id": response['customer_id'],
                "message_content": customer_message,
                "customer_history": get_customer_history(...)
            }
        )
        
        return {
            "action": "fraud_review_needed",
            "fraud_score": fraude['fraud_score'],
            "escalate": True
        }
    
    else:
        # Default: Just send response
        return {
            "action": "message_sent",
            "response": response['message']
        }

# Usage
message = "Ik wil dit product retourneren"
result = await conditional_workflow(message)
```

**Voordelen:**
- ✅ Intelligent routing
- ✅ Resource-efficient

**Nadelen:**
- ❌ Complex logic
- ❌ Moeilijk testen

---

## 2️⃣ Webhook Architecture

### Webhook Triggers

```
Business Event → Webhook triggered → Agent called → Result saved
```

### Webhook 1: Order Created

```
POST /webhooks/order-created
Content-Type: application/json
X-Webhook-Signature: HMAC-SHA256

{
  "event": "order.created",
  "timestamp": "2026-04-18T14:32:00Z",
  "data": {
    "order_id": "ORD-2026-001",
    "customer_id": "CUST-123",
    "customer_email": "john@example.com",
    "customer_name": "John Doe",
    "items": [
      {
        "product_id": "PROD-456",
        "name": "Widget Pro",
        "quantity": 2,
        "price": 49.99
      }
    ],
    "total": 99.99,
    "payment_method": "credit_card",
    "shipping_address": {
      "street": "123 Main St",
      "city": "Amsterdam",
      "postal_code": "1012AB",
      "country": "NL"
    }
  }
}
```

### Webhook Handler Code

```python
# webhooks/handlers/order_handler.py

import hmac
import hashlib
from fastapi import HTTPException
from ollama.agent_runner import AgentRunner

runner = AgentRunner()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify webhook came from Mollie/Shop system"""
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)

@app.post("/webhooks/order-created")
async def handle_order_created(request: Request):
    """
    Triggered when new order created
    Starts the agent workflow
    """
    
    # Verify signature
    body = await request.body()
    signature = request.headers.get("X-Webhook-Signature")
    
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse data
    data = await request.json()
    
    try:
        # Call agent workflow
        result = await handle_order_workflow(data)
        
        # Save to database
        order = Order(
            order_id=data['order_id'],
            customer_id=data['customer_id'],
            status=result['order_status'],
            fraud_score=result.get('fraud_score', 0.0),
            total=data['total'],
            agent_result=result
        )
        db.add(order)
        db.commit()
        
        # Log for debugging
        logger.info(f"Order {data['order_id']} processed: {result['order_status']}")
        
        return {"success": True, "order_id": data['order_id']}
        
    except Exception as e:
        logger.error(f"Order processing failed: {str(e)}")
        
        # Save error state
        db_order = OrderProcessingError(
            order_id=data['order_id'],
            error_message=str(e),
            timestamp=datetime.now()
        )
        db.add(db_order)
        db.commit()
        
        raise HTTPException(status_code=500, detail="Processing failed")

async def handle_order_workflow(order_data: dict):
    """
    Main workflow: Order → Agents → Database
    """
    
    print(f"[ORDER] Starting workflow for {order_data['order_id']}")
    
    # STEP 1: Validation
    print("  [1/4] Validating with order_verwerking_agent...")
    
    validation = await runner.run_agent(
        agent_name="order_verwerking_agent",
        user_input=f"""
        Validate new order:
        
        Order ID: {order_data['order_id']}
        Customer: {order_data['customer_name']}
        Email: {order_data['customer_email']}
        Items: {json.dumps(order_data['items'])}
        Total: €{order_data['total']}
        Payment: {order_data['payment_method']}
        
        Check if everything is correct. Return JSON:
        {{
          "valid": true/false,
          "reason": "...",
          "estimated_delivery": "2026-04-21"
        }}
        """
    )
    
    if not validation['output']['valid']:
        return {
            "order_status": "rejected",
            "reason": validation['output']['reason'],
            "agents_called": ["order_verwerking_agent"]
        }
    
    # STEP 2: Fraud Detection (parallel)
    print("  [2/4] Fraud check with fraude_detectie_agent...")
    
    fraud = await runner.run_agent(
        agent_name="fraude_detectie_agent",
        user_input=f"""
        Analyze fraud risk:
        
        Order: {order_data['order_id']}
        Customer: {order_data['customer_id']}
        Amount: €{order_data['total']}
        Payment: {order_data['payment_method']}
        Country: {order_data['shipping_address']['country']}
        
        Return fraud_score (0.0 to 1.0) and reasoning.
        """
    )
    
    fraud_score = fraud['output'].get('fraud_score', 0.0)
    
    if fraud_score > 0.8:
        order_status = "pending_review"  # Manual review needed
    else:
        order_status = "confirmed"
    
    # STEP 3: Send confirmation email
    print(f"  [3/4] Sending confirmation with email_template_agent...")
    
    email = await runner.run_agent(
        agent_name="email_template_agent",
        user_input=f"""
        Generate order confirmation email:
        
        Customer: {order_data['customer_name']}
        Order ID: {order_data['order_id']}
        Total: €{order_data['total']}
        Estimated Delivery: {validation['output']['estimated_delivery']}
        Items: {json.dumps(order_data['items'])}
        
        Make it professional, friendly, and include order details.
        """
    )
    
    # Actually send email
    try:
        send_email(
            to=order_data['customer_email'],
            subject=f"Order Confirmation - {order_data['order_id']}",
            html_body=email['output']['html']
        )
        email_sent = True
    except:
        email_sent = False
    
    # STEP 4: Update inventory
    print("  [4/4] Updating inventory with voorraad_advies_agent...")
    
    inventory = await runner.run_agent(
        agent_name="voorraad_advies_agent",
        user_input=f"""
        Update inventory for order:
        
        Order: {order_data['order_id']}
        Items: {json.dumps(order_data['items'])}
        
        Deduct from stock. Alert if low stock (<5 items remaining).
        """
    )
    
    print(f"  ✅ Workflow complete for {order_data['order_id']}")
    
    return {
        "order_status": order_status,
        "fraud_score": fraud_score,
        "email_sent": email_sent,
        "inventory_updated": inventory['output']['success'],
        "agents_called": [
            "order_verwerking_agent",
            "fraude_detectie_agent",
            "email_template_agent",
            "voorraad_advies_agent"
        ],
        "execution_time": validation['execution_time'] + fraud['execution_time'] + 
                         email['execution_time'] + inventory['execution_time']
    }
```

---

### Webhook 2: Payment Received

```
POST /webhooks/payment-received
```

```python
@app.post("/webhooks/payment-received")
async def handle_payment_received(request: Request):
    """
    Triggered when payment confirmed
    Update order status
    """
    
    body = await request.body()
    data = await request.json()
    
    # Verify
    if not verify_webhook_signature(body, request.headers.get("X-Webhook-Signature")):
        raise HTTPException(status_code=401)
    
    # Get order
    order = db.query(Order).filter_by(order_id=data['order_id']).first()
    
    if not order:
        raise HTTPException(status_code=404)
    
    # Update status
    order.status = "paid"
    
    # Notify via email
    email = await runner.run_agent(
        "email_template_agent",
        user_input=f"""
        Generate payment confirmation email for order {order.order_id}.
        Customer name: {order.customer_name}
        """
    )
    
    send_email(
        to=order.customer_email,
        subject=f"Payment Received - {order.order_id}",
        html_body=email['output']['html']
    )
    
    db.commit()
    
    return {"success": True}
```

---

### Webhook 3: Return Request

```
POST /webhooks/return-request
```

```python
@app.post("/webhooks/return-request")
async def handle_return_request(request: Request):
    """
    Triggered when customer requests return
    """
    
    body = await request.body()
    data = await request.json()
    
    if not verify_webhook_signature(body, request.headers.get("X-Webhook-Signature")):
        raise HTTPException(status_code=401)
    
    # Call retour agent
    retour = await runner.run_agent(
        "retour_verwerking_agent",
        user_input=f"""
        Process return request:
        
        Order: {data['order_id']}
        Customer: {data['customer_id']}
        Reason: {data['return_reason']}
        Items: {json.dumps(data['items'])}
        
        Generate return label and instructions.
        """
    )
    
    # Send return label via email
    email = await runner.run_agent(
        "email_template_agent",
        user_input=f"""
        Generate return label email with tracking number {retour['output']['tracking_number']}.
        """
    )
    
    # Save return to database
    return_record = Return(
        order_id=data['order_id'],
        return_id=retour['output']['return_id'],
        status="label_sent",
        tracking_number=retour['output']['tracking_number']
    )
    db.add(return_record)
    db.commit()
    
    return {
        "success": True,
        "return_id": retour['output']['return_id'],
        "tracking_number": retour['output']['tracking_number']
    }
```

---

## 3️⃣ Agent Runner Implementation

### Core AgentRunner Class

```python
# ollama/agent_runner.py

import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from ollama.client import OllamaClient

logger = logging.getLogger(__name__)

class AgentRunner:
    def __init__(self):
        self.client = OllamaClient()
        self.agents_dir = Path("agents")
        self.prompts_dir = Path("prompts")
        self.logs_dir = Path("logs")
        
        # Create logs dir if not exists
        self.logs_dir.mkdir(exist_ok=True)
        
        # Load all agent configs
        self.agents_config = self._load_all_agents()
    
    def _load_all_agents(self) -> dict:
        """Load all agent YAML files"""
        
        agents = {}
        
        for agent_file in self.agents_dir.glob("*.yml"):
            with open(agent_file) as f:
                agent_config = yaml.safe_load(f)
                agent_name = agent_config['name']
                agents[agent_name] = agent_config
        
        logger.info(f"Loaded {len(agents)} agents")
        return agents
    
    async def run_agent(self, agent_name: str, user_input: str) -> dict:
        """
        Run an agent and return result
        
        Returns:
        {
            "success": bool,
            "output": dict or str,
            "execution_time": float,
            "model": str,
            "tokens_used": int
        }
        """
        
        start_time = datetime.now()
        
        # Get agent config
        if agent_name not in self.agents_config:
            return {
                "success": False,
                "error": f"Agent {agent_name} not found",
                "execution_time": 0
            }
        
        config = self.agents_config[agent_name]
        
        # Load system prompt
        system_prompt = self._load_prompt(config['system_prompt_ref'])
        
        # Load preprompt
        preprompt = self._load_prompt(config['preprompt_ref'])
        
        # Combine prompts
        full_prompt = f"""{system_prompt}

---

{preprompt}

---

USER REQUEST:
{user_input}
"""
        
        logger.info(f"Running {agent_name} with model {config['model']}")
        
        # Call Ollama
        try:
            response = await self.client.generate(
                model=config['model'],
                prompt=full_prompt,
                temperature=config.get('temperature', 0.5),
                top_p=config.get('top_p', 0.9),
                max_tokens=config.get('max_tokens', 2048),
                stream=False
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Parse response
            output_text = response['response']
            
            # Try to parse as JSON
            try:
                output = json.loads(output_text)
            except json.JSONDecodeError:
                output = {"text": output_text}
            
            # Log execution
            self._log_execution(
                agent_name=agent_name,
                user_input=user_input,
                output=output,
                execution_time=execution_time,
                tokens=response.get('tokens_used', 0),
                model=config['model']
            )
            
            return {
                "success": True,
                "output": output,
                "execution_time": execution_time,
                "model": config['model'],
                "tokens_used": response.get('tokens_used', 0)
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "model": config['model']
            }
    
    def _load_prompt(self, prompt_ref: str) -> str:
        """Load prompt from file"""
        
        prompt_path = self.prompts_dir / prompt_ref
        
        if not prompt_path.exists():
            logger.warning(f"Prompt not found: {prompt_path}")
            return ""
        
        with open(prompt_path) as f:
            return f.read()
    
    def _log_execution(self, agent_name: str, user_input: str, output: any,
                       execution_time: float, tokens: int, model: str):
        """Log agent execution for analysis"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "model": model,
            "input_length": len(user_input),
            "tokens_used": tokens,
            "execution_time": execution_time,
            "success": True
        }
        
        # Save to database
        db_log = AgentExecutionLog(**log_entry)
        db.add(db_log)
        db.commit()
        
        # Also save to YAML for debugging
        agent_log_dir = self.logs_dir / agent_name
        agent_log_dir.mkdir(exist_ok=True)
        
        log_file = agent_log_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml"
        
        with open(log_file, 'w') as f:
            yaml.dump(log_entry, f)
```

---

## 4️⃣ Agent State Management

### Conversation Memory

```python
# ollama/agent_memory.py

class ConversationMemory:
    """Store conversation history for stateful agents"""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.messages = []
        self.context = {}
    
    def add_message(self, role: str, content: str):
        """Add message to history"""
        
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save to database
        db_msg = ConversationMessage(
            customer_id=self.customer_id,
            role=role,
            content=content
        )
        db.add(db_msg)
        db.commit()
    
    def get_context_prompt(self) -> str:
        """Get formatted context for agent"""
        
        if not self.messages:
            return "New conversation"
        
        recent = self.messages[-10:]  # Last 10 messages
        
        formatted = "Conversation history:\n\n"
        
        for msg in recent:
            formatted += f"{msg['role'].upper()}: {msg['content']}\n"
        
        return formatted
```

---

## 5️⃣ Error Handling & Retries

### Robust Agent Calling

```python
# ollama/agent_resilience.py

class ResilientAgentRunner:
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    async def run_with_retry(self, agent_name: str, user_input: str):
        """
        Run agent with automatic retry on failure
        """
        
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await runner.run_agent(agent_name, user_input)
                
                if result['success']:
                    return result
                
                logger.warning(
                    f"Agent {agent_name} failed on attempt {attempt + 1}: "
                    f"{result.get('error', 'Unknown error')}"
                )
                
                # Wait before retry
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))
            
            except Exception as e:
                logger.error(f"Exception in agent call: {str(e)}")
                
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))
        
        # All retries failed
        logger.error(f"Agent {agent_name} failed after {self.MAX_RETRIES} attempts")
        
        return {
            "success": False,
            "error": f"Failed after {self.MAX_RETRIES} attempts",
            "execution_time": 0
        }
    
    async def run_with_fallback(self, primary_agent: str, 
                               fallback_agent: str, user_input: str):
        """
        Try primary agent, use fallback if it fails
        """
        
        result = await self.run_with_retry(primary_agent, user_input)
        
        if result['success']:
            return result
        
        logger.info(f"Primary agent {primary_agent} failed, trying fallback {fallback_agent}")
        
        return await self.run_with_retry(fallback_agent, user_input)
```

---

## 📊 Communication Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEBHOOK SYSTEM                               │
│  (Mollie, Shop, Customer Service)                               │
└────────────────┬────────────────────────────────────────────────┘
                 │
         ┌───────┴──────────┬──────────────┬──────────────┐
         │                  │              │              │
    Order Created    Payment Received   Return Request   Chat Message
         │                  │              │              │
    ┌────▼────┐        ┌────▼────┐   ┌────▼────┐    ┌────▼────┐
    │Webhook 1│        │Webhook 2│   │Webhook 3│    │Webhook 4│
    └────┬────┘        └────┬────┘   └────┬────┘    └────┬────┘
         │                  │              │              │
         └──────────────────┼──────────────┼──────────────┘
                            │
                    ┌───────▼──────────┐
                    │  Agent Runner    │
                    │  (Orchestrator)  │
                    └───────┬──────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼──────┐      ┌────▼──────┐     ┌────▼──────┐
    │ Agent 1   │      │ Agent 2   │     │ Agent N   │
    │ (Llamama) │      │ (Mistral) │     │ (Llamama) │
    └────┬──────┘      └────┬──────┘     └────┬──────┘
         │                  │                  │
    Ollama (local LLM server - port 11434)
         │                  │                  │
    ┌────▼──────────────────▼──────────────────▼────┐
    │        Database & Logging System               │
    │    (PostgreSQL + Agent Execution Logs)         │
    └───────────────────────────────────────────────┘
```

---

## 📝 Message Flow Example

### Complete Order Processing Flow

```
1. CUSTOMER ACTION
   └─ Clicks "Buy Now"
   
2. WEBHOOK TRIGGER
   └─ POST /webhooks/order-created
   └─ Body: {order_id, customer_id, items, total}
   
3. SIGNATURE VERIFICATION
   └─ HMAC-SHA256 check
   └─ Continue if valid
   
4. AGENT RUNNER RECEIVES REQUEST
   └─ Load order_verwerking_agent config
   └─ Prepare full prompt (system + preprompt + order data)
   
5. AGENT 1: ORDER VERIFICATION
   └─ Model: llama3, Temperature: 0.1
   └─ Validates order structure
   └─ Returns: {valid: true/false}
   
6. AGENT 2: FRAUD DETECTION (parallel)
   └─ Model: llama3, Temperature: 0.1
   └─ Analyzes customer & payment data
   └─ Returns: {fraud_score: 0.3}
   
7. AGENT 3: EMAIL CONFIRMATION
   └─ Model: mistral, Temperature: 0.7
   └─ Generates professional email
   └─ Returns: {html: "..."}
   
8. AGENT 4: INVENTORY UPDATE
   └─ Model: llama3, Temperature: 0.1
   └─ Deducts from stock
   └─ Returns: {stock_updated: true}
   
9. DATABASE UPDATE
   └─ Insert Order row
   └─ Insert AgentExecutionLog rows
   └─ Update inventory tables
   
10. RESPONSE TO WEBHOOK CALLER
    └─ HTTP 200 OK
    └─ {success: true, order_id: "ORD123"}
    
11. CUSTOMER NOTIFICATIONS
    └─ Email sent to customer
    └─ Warehouse notified via webhook
    └─ Dashboard updated in real-time

Total Time: ~2-3 seconds
```

---

## 🎯 Best Practices

1. **Always verify webhook signatures** → Prevent spoofing
2. **Use parallel agents** where possible → Faster execution
3. **Implement retries** for resilience → Handle Ollama timeouts
4. **Log everything** → Debug issues later
5. **Use specific temperatures** → 0.1 for deterministic, 0.7+ for creative
6. **Handle errors gracefully** → Graceful degradation
7. **Monitor agent performance** → Track metrics continuously

---

## 🔧 Testing

```python
# tests/test_agent_communication.py

@pytest.mark.asyncio
async def test_order_workflow():
    """Test complete order workflow"""
    
    order_data = {
        "order_id": "TEST001",
        "customer_id": "CUST001",
        "items": [{"product_id": "PROD001", "quantity": 1}],
        "total": 99.99
    }
    
    result = await handle_order_workflow(order_data)
    
    assert result['order_status'] in ["confirmed", "pending_review"]
    assert result['fraud_score'] >= 0.0
    assert result['fraud_score'] <= 1.0
    assert len(result['agents_called']) > 0
```

---

## ✅ Next Steps

1. Implement webhook signature verification
2. Build agent runner with Ollama integration
3. Create database models for orders & executions
4. Test with sample orders
5. Monitor performance & optimize

Ready? 🚀
