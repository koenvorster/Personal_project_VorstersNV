# 📚 How-To: Werken met Agents in VorstersNV

## 🎯 Inleiding

Dit document leert je hoe je **agents** kunt bouwen, configureren, testen en optimaliseren in het VorstersNV-platform. Agents zijn AI-gestuurde modules die automatische taken uitvoeren op basis van prompts en feedback.

---

## 📋 Inhoudsopgave

1. [Agent-Anatomie](#agent-anatomie)
2. [YAML-Configuratie](#yaml-configuratie)
3. [Prompts Schrijven](#prompts-schrijven)
4. [Agent Uitvoering](#agent-uitvoering)
5. [Testen & Debugging](#testen--debugging)
6. [Feedback-Loop & Iteratie](#feedback-loop--iteratie)
7. [Multi-Agent Orkestratie](#multi-agent-orkestratie)
8. [Best Practices](#best-practices)

---

## Agent-Anatomie

Elke agent bestaat uit **5 componenten**:

```
Agent
├── 1. YAML Config (agent definition)
├── 2. System Prompt (wat is de agent)
├── 3. Pre-prompt (context + voorbeelden)
├── 4. User Input (taak/vraag van gebruiker)
└── 5. Execution & Feedback Loop
```

### Voorbeeld Flow

```
┌─────────────────────────────────────────┐
│  User Trigger (order, webhook event)    │
└──────────┬──────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│  Load agent YAML config                  │
│  (model, capabilities, evaluation)       │
└──────────┬───────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│  Combine prompts:                        │
│  - System Prompt (rollen/regels)        │
│  - Pre-prompt (context/voorbeelden)     │
│  - User Input (taak)                     │
└──────────┬───────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│  Send to Ollama LLM                      │
│  (llama3, mistral, etc)                  │
└──────────┬───────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│  Parse & Execute Output                  │
│  (perform actions, update DB)            │
└──────────┬───────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│  Evaluate & Log Results                  │
│  (score, feedback for next iteration)    │
└──────────────────────────────────────────┘
```

---

## YAML-Configuratie

### Basisstructuur

Elke agent begint met een `.yml` bestand in `/agents/`:

```yaml
# agents/my_agent.yml

name: My Custom Agent
description: Wat deze agent doet
version: 1.0

# Het LLM-model om te gebruiken
model: llama3  # of: mistral, codellama, neural-chat

# Verwijzingen naar prompt-bestanden
system_prompt_ref: ./prompts/system/my_agent_system.txt
preprompt_ref: ./prompts/preprompt/my_agent_v1.yml

# Temperatuur (0.0 = deterministisch, 1.0 = creatief)
temperature: 0.7

# Max tokens voor response
max_tokens: 2048

# Wat kan deze agent doen
capabilities:
  - capability_1
  - capability_2
  - capability_3

# Wanneer de agent wordt geactiveerd
triggers:
  - webhook_event: order_created
  - webhook_event: payment_received
  - schedule: daily_at_09:00

# Input die de agent nodig heeft
required_inputs:
  - customer_name
  - order_id
  - product_list

# Output die de agent genereert
output_format:
  type: json  # json, text, structured
  schema:
    - field_1: string
    - field_2: number

# Evaluatie van resultaten
evaluation:
  feedback_loop: true  # Agent leren van feedback
  metrics:
    - accuracy
    - response_time
    - customer_satisfaction
  
  # Wanneer wordt output als "goed" beschouwd
  quality_threshold: 0.8

# Integraties
integrations:
  - name: database
    type: postgresql
  - name: email
    type: smtp
  - name: webhook
    type: http

# Sub-agents die dit agent orkestreert
sub_agents: []  # Bijvoorbeeld: [fraud_detector, email_sender]
```

### Volledig Praktijkvoorbeeld

**agents/order_processing_agent.yml:**

```yaml
name: Order Processing Agent
description: Verwerkt orders, valideert betaling, genereert confirmatie
version: 1.1

model: llama3
system_prompt_ref: ./prompts/system/order_processing_system.txt
preprompt_ref: ./prompts/preprompt/order_processing_v1.1.yml

temperature: 0.3  # Laag = consistenter, betrouwbaarder

max_tokens: 1024

capabilities:
  - validate_order_data
  - check_payment_status
  - verify_inventory
  - generate_confirmation_email
  - create_warehouse_manifest
  - detect_fraud_signals

triggers:
  - webhook_event: payment_webhook
  - webhook_event: order_api_call
  - schedule: batch_process_daily

required_inputs:
  - order_id: string
  - customer_email: string
  - product_skus: array
  - payment_method: string
  - delivery_address: string

output_format:
  type: json
  schema:
    status: "accepted|rejected|needs_review"
    confirmation_message: string
    email_subject: string
    email_body: string
    warehouse_instructions: array
    fraud_score: number  # 0.0 to 1.0
    next_steps: array

evaluation:
  feedback_loop: true
  metrics:
    - order_acceptance_accuracy
    - fraud_detection_accuracy
    - email_quality_score
    - processing_time_seconds
  
  quality_threshold: 0.85

integrations:
  - name: postgresql_db
    type: database
    connection: DB_URL
  - name: smtp_mail
    type: email
    connection: SMTP_URL
  - name: stripe_api
    type: payment
    connection: STRIPE_KEY

sub_agents:
  - fraud_detectie_agent
  - email_template_agent
  - voorraad_advies_agent

performance_targets:
  max_execution_time: 30  # seconds
  min_accuracy: 0.90
  acceptable_error_rate: 0.02
```

---

## Prompts Schrijven

### System Prompt (Rollen & Regels)

**prompts/system/order_processing_system.txt:**

```
You are the Order Processing Agent for VorstersNV, an e-commerce platform.

=== YOUR ROLE ===
You are responsible for:
1. Validating incoming orders
2. Checking payment status
3. Verifying inventory availability
4. Detecting fraudulent activity
5. Generating professional confirmation emails
6. Creating warehouse picking instructions

=== YOUR CAPABILITIES ===
- Analyze structured order data
- Query inventory status
- Evaluate payment transactions
- Assess fraud risk indicators
- Generate clear, professional communication

=== YOUR CONSTRAINTS ===
- Never approve orders with fraud score > 0.8
- Always verify product SKUs against inventory
- Flag orders for manual review if fraud score > 0.5
- Generate emails within 1000 characters
- Output must be valid JSON

=== TONE & STYLE ===
- Professional but friendly
- Clear and concise
- Data-driven decisions
- Always explain your reasoning

=== OUTPUT FORMAT ===
Always respond with valid JSON containing:
- status: "accepted" | "rejected" | "needs_review"
- confidence: 0.0 to 1.0
- reasoning: explanation of your decision
- actions: list of actions to take
- fraud_score: 0.0 to 1.0
- email_template: confirmation email content

Remember: Your decisions directly impact customer satisfaction and business revenue.
```

### Pre-Prompt (Context & Voorbeelden)

**prompts/preprompt/order_processing_v1.1.yml:**

```yaml
version: 1.1
iteration: 3
created_at: 2026-04-15

# Context voor de agent
context:
  company: VorstersNV
  industry: e-commerce
  market: Netherlands
  language: Dutch
  customer_base: B2C + B2B

# Richtlijnen voor dit specifieke model/versie
guidelines:
  - Use JSON format for all outputs
  - Be concise but complete
  - Prioritize clarity over creativity
  - Flag suspicious patterns immediately

# Voorbeelden van goede input/output
examples:
  - input: |
      Order Data:
      - Order ID: ORD-2026-001
      - Customer: Jan Jansen
      - Email: jan@example.com
      - Products: 
        * PROD-123 (qty: 2, price: €19.99)
        * PROD-456 (qty: 1, price: €49.99)
      - Total: €89.97
      - Payment Method: iDEAL
      - Payment Status: VERIFIED
      - Delivery Address: Amsterdam, NL
      - Customer History: 5 previous orders, 100% positive
      
    output: |
      {
        "status": "accepted",
        "confidence": 0.97,
        "reasoning": "Valid customer with verified payment and positive history",
        "fraud_score": 0.05,
        "actions": [
          "Create warehouse picking list",
          "Send confirmation email",
          "Update inventory",
          "Schedule shipment"
        ],
        "email_template": {
          "subject": "Bestelling ORD-2026-001 bevestigd",
          "body": "Beste Jan,\n\nBedankt voor je bestelling. Wij hebben ontvangen..."
        }
      }

  - input: |
      Order Data:
      - Order ID: ORD-2026-999
      - Customer: Unknown New Customer
      - Email: suspicious@temp-email.com
      - Products:
        * PROD-789 (qty: 50, price: €500)
      - Total: €25,000
      - Payment Method: Cryptocurrency
      - Delivery Address: Forwarding Service, UK
      - Customer History: No previous orders
      
    output: |
      {
        "status": "needs_review",
        "confidence": 0.45,
        "reasoning": "High-value order from unknown customer, suspicious patterns detected",
        "fraud_score": 0.78,
        "actions": [
          "Flag for manual review",
          "Verify customer identity",
          "Check with fraud team",
          "Hold shipment pending approval"
        ],
        "email_template": {
          "subject": "Bestelling in behandeling - verificatie vereist",
          "body": "Beste klant,\n\nDank u voor uw bestelling. Wij voeren verificatie uit..."
        }
      }

# Iteratiegeschiedenis
iterations:
  - version: 1.0
    date: 2026-04-01
    feedback: "Too conservative with fraud detection"
    change: "Adjusted fraud_score thresholds"
  
  - version: 1.1
    date: 2026-04-15
    feedback: "Better accuracy on edge cases"
    change: "Added cryptocurrency payment flag, improved context window"
```

---

## Agent Uitvoering

### Code: Agent Runner

**ollama/agent_runner.py:**

```python
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json
from ollama import OllamaClient

logger = logging.getLogger(__name__)

class AgentRunner:
    def __init__(self, agents_dir: str = "./agents", prompts_dir: str = "./prompts"):
        self.agents_dir = Path(agents_dir)
        self.prompts_dir = Path(prompts_dir)
        self.client = OllamaClient()
    
    def load_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Laad agent YAML configuratie"""
        config_path = self.agents_dir / f"{agent_name}.yml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Agent config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def load_prompt(self, prompt_ref: str) -> str:
        """Laad prompt-bestand"""
        prompt_path = self.prompts_dir / prompt_ref.lstrip("./")
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        
        with open(prompt_path, 'r') as f:
            return f.read()
    
    def build_full_prompt(
        self,
        system_prompt: str,
        preprompt: Dict[str, Any],
        user_input: str
    ) -> str:
        """Combineer system + pre + user prompts"""
        
        full_prompt = f"""SYSTEM INSTRUCTIONS:
{system_prompt}

=== CONTEXT ===
Company: {preprompt.get('context', {}).get('company', 'VorstersNV')}
Model: {preprompt.get('model', 'unknown')}

=== GUIDELINES ===
{chr(10).join('- ' + g for g in preprompt.get('guidelines', []))}

=== EXAMPLES ===
{self._format_examples(preprompt.get('examples', []))}

=== YOUR TASK ===
{user_input}

Please respond in the specified output format.
"""
        return full_prompt
    
    def _format_examples(self, examples: list) -> str:
        """Format examples voor de prompt"""
        formatted = []
        for i, example in enumerate(examples, 1):
            formatted.append(f"Example {i}:\nInput:\n{example['input']}\n\nOutput:\n{example['output']}")
        return "\n\n".join(formatted)
    
    async def run_agent(
        self,
        agent_name: str,
        user_input: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Voer een agent uit
        
        Args:
            agent_name: Naam van de agent (YAML bestand)
            user_input: Taakbeschrijving voor de agent
            context: Extra context data
        
        Returns:
            Resultaat van agent execution
        """
        
        try:
            # 1. Laad agent configuratie
            config = self.load_agent_config(agent_name)
            logger.info(f"Loaded agent: {agent_name} (v{config.get('version')})")
            
            # 2. Laad prompts
            system_prompt = self.load_prompt(config['system_prompt_ref'])
            preprompt_path = config.get('preprompt_ref', '')
            
            with open(self.prompts_dir / preprompt_path.lstrip("./"), 'r') as f:
                preprompt_data = yaml.safe_load(f)
            
            # 3. Bouw volledige prompt
            full_prompt = self.build_full_prompt(system_prompt, preprompt_data, user_input)
            
            # 4. Roep Ollama aan
            logger.info(f"Calling model: {config['model']}")
            start_time = datetime.now()
            
            response = await self.client.generate(
                model=config['model'],
                prompt=full_prompt,
                temperature=config.get('temperature', 0.7),
                num_predict=config.get('max_tokens', 2048),
                stream=False
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 5. Parse output
            try:
                output = json.loads(response['response'])
            except json.JSONDecodeError:
                output = {"raw_text": response['response']}
            
            # 6. Bouw resultaat
            result = {
                "agent": agent_name,
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time,
                "model": config['model'],
                "output": output,
                "metrics": {
                    "tokens_used": response.get('eval_count', 0),
                    "temperature": config.get('temperature', 0.7),
                }
            }
            
            # 7. Log execution
            self._log_execution(agent_name, result)
            
            return result
        
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "agent": agent_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _log_execution(self, agent_name: str, result: Dict[str, Any]):
        """Log agent execution voor later review"""
        logs_dir = Path("./logs") / agent_name
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = logs_dir / f"{datetime.now().isoformat()}.json"
        
        with open(log_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Logged execution to: {log_file}")
```

### Praktijkvoorbeeld: Agent Aanroepen

```python
# Vanuit FastAPI endpoint
from ollama.agent_runner import AgentRunner

runner = AgentRunner()

@app.post("/api/agents/order-processing")
async def process_order(order_data: OrderData):
    """
    Roep order_processing_agent aan
    """
    
    user_input = f"""
    Process this order:
    - Order ID: {order_data.order_id}
    - Customer: {order_data.customer_name}
    - Products: {json.dumps(order_data.products)}
    - Payment Status: {order_data.payment_status}
    - Delivery Address: {order_data.delivery_address}
    
    Please analyze and decide: accept, reject, or flag for review?
    """
    
    result = await runner.run_agent(
        agent_name="order_processing_agent",
        user_input=user_input,
        context={"order_id": order_data.order_id}
    )
    
    return result
```

---

## Testen & Debugging

### Unit Tests

**tests/test_agents.py:**

```python
import pytest
import asyncio
from ollama.agent_runner import AgentRunner

@pytest.fixture
def runner():
    return AgentRunner()

@pytest.mark.asyncio
async def test_order_processing_agent_accepts_valid_order(runner):
    """Test dat agent geldige orders accepteert"""
    
    user_input = """
    Process this order:
    - Order ID: TEST-001
    - Customer: Test Customer
    - Products: [{"sku": "PROD-123", "qty": 1, "price": 19.99}]
    - Payment Status: VERIFIED
    - Delivery Address: Amsterdam, NL
    """
    
    result = await runner.run_agent("order_processing_agent", user_input)
    
    assert result['success'] == True
    assert result['output']['status'] in ['accepted', 'rejected', 'needs_review']
    assert 'fraud_score' in result['output']

@pytest.mark.asyncio
async def test_agent_flags_suspicious_order(runner):
    """Test dat agent verdachte orders flaggt"""
    
    user_input = """
    Process this order:
    - Order ID: TEST-999
    - Customer: Unknown Customer
    - Products: [{"sku": "PROD-789", "qty": 100, "price": 500}]
    - Payment Status: PENDING
    - Delivery Address: Forwarding Service, UK
    """
    
    result = await runner.run_agent("order_processing_agent", user_input)
    
    assert result['success'] == True
    # Verwachten dat agent dit vlaggt
    assert result['output']['fraud_score'] > 0.5 or result['output']['status'] == 'needs_review'
```

### Manual Testing

```bash
# Test agent via CLI
python scripts/test_agent.py --agent order_processing_agent --input "order_test.json"

# Debug prompts
python scripts/debug_prompts.py --agent order_processing_agent --show-full-prompt
```

---

## Feedback-Loop & Iteratie

### Feedback Verzamelen

```python
class AgentFeedback:
    def __init__(self, agent_name: str, execution_id: str):
        self.agent_name = agent_name
        self.execution_id = execution_id
    
    def log_feedback(self, score: float, comments: str, corrections: dict):
        """
        Log feedback voor deze execution
        
        Args:
            score: 0.0 (slecht) tot 1.0 (perfect)
            comments: Wat ging goed/fout
            corrections: Wat moet anders
        """
        feedback_data = {
            "execution_id": self.execution_id,
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "comments": comments,
            "corrections": corrections
        }
        
        # Save to iterations log
        iterations_file = Path(f"prompts/preprompt/{self.agent_name}_iterations.yml")
        
        with open(iterations_file, 'a') as f:
            yaml.dump({"feedback": feedback_data}, f)
```

### Agent Verbetering

1. **Verzamel feedback** van 10+ executions
2. **Analyseer patterns** in corrections
3. **Update pre-prompt** met beter examples
4. **Verhoog temperature** if too strict, verlaag if too creative
5. **Test nieuw versie** tegen baseline
6. **Deploy** als improvement >= 5%

---

## Multi-Agent Orkestratie

### Orchestrator Voorbeeld

```yaml
# agents/orchestrator_order_workflow.yml
name: Order Processing Workflow Orchestrator
type: workflow

steps:
  - name: "validate_order"
    agent: order_processing_agent
    input_from: webhook_event
    
  - name: "detect_fraud"
    agent: fraude_detectie_agent
    input_from: validate_order.output
    
  - name: "generate_email"
    agent: email_template_agent
    input_from: detect_fraud.output
    if: detect_fraud.fraud_score < 0.5
    
  - name: "update_inventory"
    agent: voorraad_advies_agent
    input_from: validate_order.output
    
  - name: "send_notification"
    type: webhook
    url: "{{ env.NOTIFICATION_SERVICE }}"
    input_from: generate_email.output
```

### Orchestrator Implementatie

```python
class WorkflowOrchestrator:
    def __init__(self, runner: AgentRunner):
        self.runner = runner
    
    async def execute_workflow(self, workflow_name: str, initial_data: dict):
        """Voer complete workflow uit"""
        
        # Load workflow config
        workflow_config = self.load_workflow_config(workflow_name)
        
        results = {}
        
        for step in workflow_config['steps']:
            # Execute stap
            input_data = self._resolve_input(step, results)
            
            result = await self.runner.run_agent(
                step['agent'],
                json.dumps(input_data)
            )
            
            results[step['name']] = result
            
            # Check conditions
            if step.get('if'):
                if not self._evaluate_condition(step['if'], result):
                    continue
        
        return results
```

---

## Best Practices

### ✅ DO's

1. **Temperature tunen naar use case**
   - 0.3-0.5: Consistente, regelgevolging taken (orders, betalingen)
   - 0.7: Balans (customer service, tekst generatie)
   - 0.9+: Creatieve taken (brainstorming, content)

2. **Always provide examples**
   - Agents leren van voorbeelden
   - Include edge cases
   - Show expected output format

3. **Monitor execution**
   - Log alles
   - Track metrics (tijd, kwaliteit, errors)
   - Set up alerts

4. **Iterate regularly**
   - Verzamel user feedback
   - Update prompts elke week
   - Version control alles

5. **Use sub-agents**
   - Splits complexe taken
   - Specialize agents
   - Easier to test & debug

### ❌ DON'Ts

1. **Don't use vague prompts**
   - ❌ "Generate a good email"
   - ✅ "Generate a professional order confirmation email in Dutch, max 150 words, include order ID and tracking link"

2. **Don't ignore errors**
   - Always log failures
   - Analyze error patterns
   - Update error handling

3. **Don't skip testing**
   - Test with edge cases
   - Verify output format
   - Check performance

4. **Don't over-engineer**
   - Start simple
   - Add complexity when needed
   - Document what you do

5. **Don't forget about users**
   - Collect feedback
   - Show confidence scores
   - Allow overrides

---

## Samenvatting

```
Agent Workflow:
┌─ YAML Config
├─ System Prompt (rollen/regels)
├─ Pre-prompt (context/voorbeelden)
├─ User Input (taak)
├─ Ollama LLM
├─ Parse & Execute
├─ Log Results
└─ Feedback Loop
```

**Volgende stap:** Kies een use case en bouw je eerste agent! 🚀
