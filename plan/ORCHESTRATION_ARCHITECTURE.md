# ⚙️ AGENT ORCHESTRATION ARCHITECTURE

## 📐 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       VorstersNV Platform                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Event/Webhook Layer                         │   │
│  │  (Mollie, Shop, Customer Service, Home Assistant)       │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                               │
│  ┌────────────────▼─────────────────────────────────────────┐   │
│  │           FastAPI Router Layer                           │   │
│  │  (/api/orders, /api/products, /api/support)            │   │
│  │  (Validates requests, checks auth)                      │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                               │
│  ┌────────────────▼─────────────────────────────────────────┐   │
│  │      AGENT ORCHESTRATOR (Core)                          │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │ 1. Determine workflow                             │ │   │
│  │  │ 2. Schedule agents (seq/parallel/conditional)    │ │   │
│  │  │ 3. Pass data between agents                       │ │   │
│  │  │ 4. Handle errors & retries                        │ │   │
│  │  │ 5. Collect metrics & logs                         │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                               │
│  ┌────────────────┼─────────────────────────────────────────┐   │
│  │  ┌────────┐ ┌──────────┐ ┌──────────┐ ... ┌──────────┐ │   │
│  │  │Agent 1 │ │ Agent 2  │ │ Agent 3  │     │ Agent 8  │ │   │
│  │  │(llama3)│ │(mistral) │ │(llama3)  │     │(llama3)  │ │   │
│  │  └────────┘ └──────────┘ └──────────┘     └──────────┘ │   │
│  │         Ollama (Local LLM Server)                        │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                               │
│  ┌────────────────▼─────────────────────────────────────────┐   │
│  │    Data Persistence Layer                               │   │
│  │  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐ │   │
│  │  │ PostgreSQL   │  │ Agent Logs    │  │ Cache (Redis)│ │   │
│  │  │ (Orders,     │  │ & Metrics     │  │              │ │   │
│  │  │  Products)   │  │               │  │              │ │   │
│  │  └──────────────┘  └───────────────┘  └──────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Agent Orchestrator – Core Logic

### 1. Orchestrator Class

```python
# ollama/orchestrator.py

import asyncio
import json
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from datetime import datetime
from logging import getLogger

logger = getLogger(__name__)

class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"

@dataclass
class AgentTask:
    """Single agent execution task"""
    agent_name: str
    input_data: Dict
    mode: ExecutionMode
    depends_on: List[str] = None  # Task IDs this depends on
    condition: Optional[Callable] = None  # Conditional execution
    priority: int = 0  # Higher = more important
    timeout: float = 30.0  # Max seconds to wait
    retries: int = 3  # Retry count

class AgentOrchestrator:
    """
    Central orchestration engine for multi-agent workflows
    """
    
    def __init__(self):
        self.runner = AgentRunner()
        self.task_queue = []
        self.execution_history = {}
        self.active_tasks = {}
    
    # ──────────────────────────────────────────────────────────
    # WORKFLOW EXECUTION
    # ──────────────────────────────────────────────────────────
    
    async def execute_workflow(self, workflow_name: str, initial_data: Dict):
        """
        Execute a complete workflow
        """
        
        logger.info(f"Starting workflow: {workflow_name}")
        start_time = datetime.now()
        
        # Load workflow definition
        workflow = self._load_workflow(workflow_name)
        
        if not workflow:
            return {
                "success": False,
                "error": f"Workflow not found: {workflow_name}"
            }
        
        # Execute tasks
        results = {}
        context = initial_data.copy()
        
        for task_config in workflow['tasks']:
            task = AgentTask(**task_config)
            
            # Check conditions
            if task.condition:
                if not task.condition(context):
                    logger.info(f"Skipping task {task.agent_name} due to condition")
                    continue
            
            # Wait for dependencies
            if task.depends_on:
                for dep_id in task.depends_on:
                    if dep_id not in results:
                        logger.warning(f"Dependency {dep_id} not executed")
                        continue
                    
                    # Merge dependent results into context
                    context[f"_{dep_id}"] = results[dep_id]
            
            # Execute agent
            if task.mode == ExecutionMode.SEQUENTIAL:
                result = await self._execute_task(task, context)
                results[task.agent_name] = result
                context[task.agent_name] = result
            
            elif task.mode == ExecutionMode.PARALLEL:
                # Run multiple agents in parallel
                parallel_tasks = workflow['parallel_groups'][task.agent_name]
                parallel_results = await self._execute_parallel(parallel_tasks, context)
                results.update(parallel_results)
                context.update(parallel_results)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "workflow": workflow_name,
            "results": results,
            "execution_time": execution_time,
            "task_count": len(workflow['tasks'])
        }
    
    # ──────────────────────────────────────────────────────────
    # TASK EXECUTION
    # ──────────────────────────────────────────────────────────
    
    async def _execute_task(self, task: AgentTask, context: Dict):
        """Execute a single agent task"""
        
        logger.info(f"Executing task: {task.agent_name}")
        
        # Prepare input (substitute context variables)
        input_data = self._substitute_variables(task.input_data, context)
        
        # Run with retries
        for attempt in range(task.retries):
            try:
                result = await asyncio.wait_for(
                    self.runner.run_agent(
                        task.agent_name,
                        json.dumps(input_data)
                    ),
                    timeout=task.timeout
                )
                
                if result['success']:
                    logger.info(f"Task {task.agent_name} completed in {result['execution_time']}s")
                    return result
                
                logger.warning(f"Task {task.agent_name} failed: {result.get('error')}")
                
                if attempt < task.retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            except asyncio.TimeoutError:
                logger.error(f"Task {task.agent_name} timed out after {task.timeout}s")
                
                if attempt < task.retries - 1:
                    await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                logger.error(f"Task {task.agent_name} failed with exception: {str(e)}")
                
                if attempt < task.retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return {
            "success": False,
            "error": f"Task failed after {task.retries} attempts"
        }
    
    async def _execute_parallel(self, tasks: List[AgentTask], context: Dict):
        """Execute multiple agents in parallel"""
        
        logger.info(f"Executing {len(tasks)} tasks in parallel")
        
        # Create tasks
        async_tasks = []
        task_names = []
        
        for task in tasks:
            async_task = asyncio.create_task(
                self._execute_task(task, context)
            )
            async_tasks.append(async_task)
            task_names.append(task.agent_name)
        
        # Wait for all
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # Format results
        formatted = {}
        for name, result in zip(task_names, results):
            if isinstance(result, Exception):
                formatted[name] = {
                    "success": False,
                    "error": str(result)
                }
            else:
                formatted[name] = result
        
        return formatted
    
    # ──────────────────────────────────────────────────────────
    # WORKFLOW DEFINITIONS
    # ──────────────────────────────────────────────────────────
    
    def _load_workflow(self, workflow_name: str) -> Dict:
        """Load workflow definition from YAML"""
        
        import yaml
        from pathlib import Path
        
        workflow_file = Path(f"workflows/{workflow_name}.yml")
        
        if not workflow_file.exists():
            return None
        
        with open(workflow_file) as f:
            return yaml.safe_load(f)
    
    def _substitute_variables(self, data: Dict, context: Dict) -> Dict:
        """
        Substitute context variables in data
        Example: "$order.customer_id" → value from context
        """
        
        import re
        
        json_str = json.dumps(data)
        
        # Find all $variable references
        pattern = r'\$[\w\.]+'
        matches = re.findall(pattern, json_str)
        
        for var_path in matches:
            value = self._get_from_context(var_path[1:], context)  # Remove $
            json_str = json_str.replace(f'"{var_path}"', json.dumps(value))
        
        return json.loads(json_str)
    
    def _get_from_context(self, path: str, context: Dict):
        """Get value from nested context using dot notation"""
        
        keys = path.split('.')
        value = context
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
```

---

## 📋 Workflow Definitions

### Workflow 1: Order Processing

```yaml
# workflows/order_processing.yml

name: Complete Order Processing
version: 1.0
description: Process new order with fraud check, confirmation, and inventory update

tasks:
  # Step 1: Validation
  - agent_name: "validate_order"
    step: 1
    execution_mode: "sequential"
    input:
      order_id: "$initial_data.order_id"
      customer_id: "$initial_data.customer_id"
      items: "$initial_data.items"
      total: "$initial_data.total"
    timeout: 15
    retries: 2
  
  # Step 2 & 3: Parallel (Fraud + Inventory)
  - step: 2
    execution_mode: "parallel"
    tasks:
      # 2a: Fraud Detection
      - agent_name: "fraude_detectie_agent"
        input:
          order_id: "$initial_data.order_id"
          customer_id: "$initial_data.customer_id"
          payment_method: "$initial_data.payment_method"
          country: "$initial_data.shipping_address.country"
          total: "$initial_data.total"
        timeout: 10
        retries: 3
      
      # 2b: Inventory Check
      - agent_name: "voorraad_advies_agent"
        input:
          items: "$initial_data.items"
          warehouse_id: "default"
        timeout: 10
        retries: 2
  
  # Step 3: Conditional Email (only if fraud score < 0.8)
  - agent_name: "email_template_agent"
    step: 3
    execution_mode: "sequential"
    depends_on: ["fraude_detectie_agent"]
    condition: "fraud_score < 0.8"
    input:
      template: "order_confirmation"
      customer_name: "$initial_data.customer_name"
      order_id: "$initial_data.order_id"
      total: "$initial_data.total"
      items: "$initial_data.items"
    timeout: 10
    retries: 2
  
  # Step 4: Mark as Confirmed
  - type: "database_update"
    table: "orders"
    where:
      order_id: "$initial_data.order_id"
    set:
      status: "confirmed"
      fraud_score: "$_fraude_detectie_agent.fraud_score"
      processed_at: "NOW()"

parallel_groups:
  step_2:
    - "fraude_detectie_agent"
    - "voorraad_advies_agent"
```

### Workflow 2: Customer Support

```yaml
# workflows/customer_support.yml

name: Customer Support Handling
version: 1.0

tasks:
  # Step 1: Analyze message
  - agent_name: "klantenservice_agent"
    step: 1
    execution_mode: "sequential"
    input:
      customer_id: "$initial_data.customer_id"
      message: "$initial_data.message"
      message_language: "$initial_data.language"
    timeout: 15
    retries: 2
    output_key: "analysis"
  
  # Step 2: Conditional routing based on analysis
  - agent_name: "route_based_on_analysis"
    step: 2
    execution_mode: "conditional"
    depends_on: ["klantenservice_agent"]
    
    # If return request
    if_return_request:
      - agent_name: "retour_verwerking_agent"
        input:
          order_id: "$analysis.order_id"
          customer_id: "$initial_data.customer_id"
          reason: "$analysis.return_reason"
          items: "$analysis.items"
      
      - agent_name: "email_template_agent"
        input:
          template: "return_label"
          customer_email: "$analysis.customer_email"
          tracking_number: "$_retour_verwerking_agent.tracking_number"
    
    # If fraud suspected
    if_fraud_flag:
      - agent_name: "fraude_detectie_agent"
        input:
          customer_id: "$initial_data.customer_id"
          message: "$initial_data.message"
          customer_history: "$initial_data.customer_history"
    
    # If product question
    if_product_question:
      - agent_name: "product_beschrijving_agent"
        input:
          product_id: "$analysis.product_id"
          question: "$analysis.question"
  
  # Step 3: Send response
  - agent_name: "email_template_agent"
    step: 3
    execution_mode: "sequential"
    input:
      template: "support_response"
      customer_email: "$analysis.customer_email"
      response: "$analysis.response"
```

### Workflow 3: Product Publication

```yaml
# workflows/product_publication.yml

name: Publish New Product
version: 1.0

tasks:
  # Generate content
  - step: 1
    execution_mode: "parallel"
    tasks:
      - agent_name: "product_beschrijving_agent"
        input:
          product_name: "$initial_data.name"
          category: "$initial_data.category"
          features: "$initial_data.features"
          price: "$initial_data.price"
          target_audience: "$initial_data.target_audience"
      
      - agent_name: "seo_agent"
        input:
          product_name: "$initial_data.name"
          category: "$initial_data.category"
          keywords: "$initial_data.keywords"
  
  # Create images (if API available)
  - type: "external_call"
    endpoint: "http://image-generator:5000/generate"
    input:
      product_name: "$initial_data.name"
  
  # Notify team
  - agent_name: "email_template_agent"
    input:
      template: "product_ready_review"
      marketing_team_email: "marketing@vorstersNV.nl"
      product_name: "$initial_data.name"
      content: "$_product_beschrijving_agent"
      seo_suggestions: "$_seo_agent"
```

---

## 🔄 Resource Management

### Agent Pool & Queue

```python
# ollama/agent_pool.py

class AgentPool:
    """
    Manage concurrent agent executions
    - Prevent overload
    - Track resource usage
    - Queue requests
    """
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = asyncio.Queue()
        self.active_agents = {}
    
    async def execute_with_limit(self, agent_name: str, task_data: Dict):
        """Execute agent with concurrency limit"""
        
        async with self.semaphore:
            logger.info(f"[POOL] Executing {agent_name} ({len(self.active_agents)}/{self.max_concurrent})")
            
            self.active_agents[agent_name] = datetime.now()
            
            try:
                result = await runner.run_agent(agent_name, task_data)
                return result
            finally:
                del self.active_agents[agent_name]
    
    async def get_pool_status(self):
        """Get current pool status"""
        
        return {
            "max_concurrent": self.max_concurrent,
            "active_agents": len(self.active_agents),
            "queue_size": self.queue.qsize(),
            "active_list": list(self.active_agents.keys())
        }
```

---

## 📊 Monitoring & Metrics

### Execution Tracking

```python
# ollama/execution_tracker.py

class ExecutionTracker:
    """Track workflow and agent execution metrics"""
    
    async def track_workflow_execution(self, workflow_name: str, 
                                       start_time: datetime,
                                       end_time: datetime,
                                       success: bool,
                                       task_results: Dict):
        """Record workflow execution"""
        
        execution_time = (end_time - start_time).total_seconds()
        
        # Calculate metrics per agent
        agent_metrics = {}
        
        for agent_name, result in task_results.items():
            if result.get('success'):
                agent_metrics[agent_name] = {
                    "execution_time": result.get('execution_time', 0),
                    "tokens_used": result.get('tokens_used', 0),
                    "model": result.get('model'),
                    "success": True
                }
            else:
                agent_metrics[agent_name] = {
                    "success": False,
                    "error": result.get('error')
                }
        
        # Save to database
        workflow_log = WorkflowExecutionLog(
            workflow_name=workflow_name,
            execution_time=execution_time,
            success=success,
            agent_metrics=json.dumps(agent_metrics),
            timestamp=datetime.now()
        )
        
        db.add(workflow_log)
        db.commit()
        
        # Return summary
        return {
            "workflow": workflow_name,
            "execution_time": execution_time,
            "success": success,
            "agent_metrics": agent_metrics
        }
    
    async def get_workflow_performance(self, workflow_name: str, hours: int = 24):
        """Get performance metrics for workflow"""
        
        from datetime import timedelta
        
        since = datetime.now() - timedelta(hours=hours)
        
        logs = db.query(WorkflowExecutionLog).filter(
            WorkflowExecutionLog.workflow_name == workflow_name,
            WorkflowExecutionLog.timestamp >= since
        ).all()
        
        if not logs:
            return None
        
        return {
            "workflow": workflow_name,
            "executions": len(logs),
            "success_rate": sum(1 for l in logs if l.success) / len(logs),
            "avg_execution_time": sum(l.execution_time for l in logs) / len(logs),
            "min_execution_time": min(l.execution_time for l in logs),
            "max_execution_time": max(l.execution_time for l in logs),
            "total_tokens": sum(json.loads(l.agent_metrics).get('tokens_used', 0) 
                              for l in logs if l.success)
        }
```

---

## 🚨 Error Handling & Recovery

### Resilient Orchestration

```python
# ollama/orchestrator_resilience.py

class ResilientOrchestrator(AgentOrchestrator):
    """Enhanced orchestrator with error recovery"""
    
    async def execute_workflow_with_fallback(self, workflow_name: str, 
                                             initial_data: Dict,
                                             fallback_workflow: str = None):
        """Execute workflow with fallback on failure"""
        
        try:
            result = await self.execute_workflow(workflow_name, initial_data)
            
            if result['success']:
                return result
            
        except Exception as e:
            logger.error(f"Workflow {workflow_name} failed: {str(e)}")
            
            if fallback_workflow:
                logger.info(f"Executing fallback: {fallback_workflow}")
                return await self.execute_workflow(fallback_workflow, initial_data)
            
            raise
    
    async def execute_with_rollback(self, workflow_name: str, initial_data: Dict):
        """Execute workflow with rollback on failure"""
        
        # Start transaction
        transaction = db.begin()
        
        try:
            result = await self.execute_workflow(workflow_name, initial_data)
            
            if not result['success']:
                logger.warning(f"Workflow failed, rolling back")
                transaction.rollback()
                return result
            
            transaction.commit()
            return result
        
        except Exception as e:
            logger.error(f"Exception in workflow, rolling back: {str(e)}")
            transaction.rollback()
            raise
```

---

## 🎯 Usage Examples

### Example 1: Create Order via FastAPI

```python
# api/routers/orders.py

@router.post("/")
async def create_order(order_data: OrderCreateRequest):
    """Create order using orchestrator"""
    
    orchestrator = AgentOrchestrator()
    
    result = await orchestrator.execute_workflow(
        workflow_name="order_processing",
        initial_data=order_data.dict()
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return {
        "success": True,
        "order_id": order_data.order_id,
        "status": "confirmed",
        "execution_time": result['execution_time']
    }
```

### Example 2: Customer Support Chat

```python
# api/routers/support.py

@router.post("/chat")
async def support_chat(message: SupportMessage):
    """Handle customer support message"""
    
    orchestrator = AgentOrchestrator()
    
    result = await orchestrator.execute_workflow(
        workflow_name="customer_support",
        initial_data={
            "customer_id": message.customer_id,
            "message": message.text,
            "language": message.language,
            "customer_history": get_customer_history(message.customer_id)
        }
    )
    
    return result
```

---

## 📈 Performance Optimization

### Caching Agent Results

```python
# ollama/agent_cache.py

import hashlib
import redis

class CachedAgentRunner:
    """Cache agent results to avoid duplicate executions"""
    
    def __init__(self):
        self.runner = AgentRunner()
        self.cache = redis.Redis(host='localhost', port=6379)
        self.ttl = 3600  # 1 hour
    
    async def run_agent_cached(self, agent_name: str, user_input: str):
        """Run agent with caching"""
        
        # Generate cache key
        cache_key = f"agent:{agent_name}:{hashlib.md5(user_input.encode()).hexdigest()}"
        
        # Try cache
        cached = self.cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {agent_name}")
            return json.loads(cached)
        
        # Execute
        result = await self.runner.run_agent(agent_name, user_input)
        
        # Cache result
        if result['success']:
            self.cache.setex(
                cache_key,
                self.ttl,
                json.dumps(result)
            )
        
        return result
```

---

## ✅ Next Steps

1. **Build orchestrator core** → Test with sample workflows
2. **Create workflow definitions** → For each use case
3. **Implement monitoring** → Dashboard with metrics
4. **Deploy to production** → Gradual rollout
5. **Optimize performance** → Based on metrics

---

**Ready to implement? 🚀**
