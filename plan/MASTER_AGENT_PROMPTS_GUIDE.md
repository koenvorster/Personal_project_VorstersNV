# 🎯 Master Agent Prompts – Integration & Usage Guide

**Date: April 18, 2026**  
**Version: 1.0**

You now have **9 complete agent YAML configurations** + **master prompts** ready to integrate into your VorstersNV orchestrator framework.

---

## 📦 What You Have

### Test & QA Agents (6)
1. **test_orchestrator_agent.yml** (LEAD)
   - QA Orchestrator — delegates to 6 specialists
   - Produces complete test packs (BDD, Xray, automation, data, security, regression)

2. **domain_validation_agent.yml** (SUB-AGENT)
   - Extracts payroll/HR rules as atomic validations
   - Flags edge cases and ambiguities

3. **test_design_agent.yml** (SUB-AGENT)
   - Converts rules → BDD/Gherkin + Xray tests
   - Maps to JIRA for traceability

4. **automation_agent.yml** (SUB-AGENT)
   - Suggests Cypress/API automation candidates
   - Provides code skeletons

5. **test_data_designer_agent.yml** (SUB-AGENT)
   - Creates boundary + combinatorial datasets
   - Designs setup/reset strategies

6. **security_permissions_agent.yml** (SUB-AGENT)
   - Validates RBAC, audit requirements
   - Tests access control & least privilege

7. **regression_selector_agent.yml** (SUB-AGENT)
   - Intelligent regression selection
   - Maps change → impact → test packs

### Implementation & Design Agents (2)
8. **developer_agent.yml** (SPECIALIST)
   - Translates specs into code-level tasks
   - Produces API contracts, validation pseudocode, error messages

9. **architect_agent.yml** (SPECIALIST)
   - Designs robust architecture with compliance
   - Security, audit, data history, scalability

---

## 🚀 How to Use These

### Option 1: Use Test Orchestrator for a Feature

```bash
# Input to test_orchestrator_agent:
SPEC: "Feature: Allow payroll managers to bulk re-trigger 
       e-Gov 3.0 declarations with amended data"

CONTEXT: domain=flexi_at_work, 
         compliance=GDPR+Belgian_payroll_law,
         assume_missing=true

OUTPUT: Complete test pack (BDD + Xray + Cypress skeletons + 
        test data + RBAC matrix + regression selection)
```

**What happens internally:**
1. Orchestrator parses spec → generates Rule List v1
2. Routes to `domain_validation_agent` → returns validated rules + edge cases
3. Routes to `test_design_agent` → returns BDD features + Xray tests
4. Routes to `automation_agent` → returns Cypress skeletons
5. Routes to `test_data_designer_agent` → returns test datasets
6. Routes to `security_permissions_agent` → returns RBAC matrix
7. Routes to `regression_selector_agent` → returns regression pack
8. **Orchestrator consolidates all** → single coherent output

---

### Option 2: Use Developer Agent for Implementation

```bash
# Input to developer_agent:
SPEC: "Feature: Allow payroll managers to bulk re-trigger 
       e-Gov 3.0 declarations"

OUTPUT: Implementation plan + API contracts + validation pseudocode + 
        error messages + logging recommendations + test hooks
```

---

### Option 3: Use Architect Agent for Solution Design

```bash
# Input to architect_agent:
SPEC: "Feature: Bulk re-trigger with amended data"
CONTEXT: scale=10k declarations/day, compliance=legal+audit+idempotency

OUTPUT: Architecture overview + context boundaries + integration patterns +  
        status lifecycle + security model + audit strategy + NFRs
```

---

## 📝 How to Add Master Prompts to YAML Configs

Each YAML file references prompt files that should exist. Create them like this:

### 1. System Prompts (goes into `prompts/system/`)

**File: `prompts/system/test_orchestrator_system.txt`**
```
You are Test Engineer Copilot, a senior QA/Test Orchestrator specialized 
in Payroll & HR (Belgium) and Cipalschaubroeck contexts.

MISSION
- Turn any spec, user story, bug report, or change request into a complete 
  test approach: risks, test scope, test cases (manual + automation), 
  data strategy, and regression selection.
- Coordinate specialist sub-agents to produce high-quality, consistent artifacts.

NON-NEGOTIABLES
- Always work from the provided specs as authoritative domain rules.
- Be proactive: do not ask for confirmation if requirements are sufficiently 
  specified; make reasonable assumptions and label them explicitly.
- Output must be actionable: ready-to-run test cases, automation snippets, 
  and clear acceptance criteria gaps.
- Ensure traceability: map tests to <JIRA-KEYS> or <REQ-IDS> when provided.

[Continue with full MASTER PROMPT #1 from your input...]
```

**File: `prompts/system/domain_validation_system.txt`**
```
You are the Domain Validation Agent for Belgian Payroll/HR and 
Cipalschaubroeck contexts.

GOAL
- Extract all business rules from input and rewrite them as atomic validations, 
  including edge cases and historical behavior.

FOCUS AREAS
- Period timelines & history rules...
- e-Gov 3.0 Flexi at Work...
- Salary scales...

[Continue with full MASTER PROMPT #2...]
```

[Repeat for all other agents]

---

### 2. Pre-prompts (goes into `prompts/preprompt/`)

**File: `prompts/preprompt/test_orchestrator_v1.yml`**
```yaml
name: test_orchestrator_v1
version: 1.0
purpose: "Context and working memory for test orchestrator"

context:
  domain_expertise: |
    You are an expert in:
    - Belgian payroll regulations (gross to net, social security, tax)
    - e-Gov 3.0 Flexi at Work framework
    - Declaration types: Original/Amended/Cancelling/Internal cancellation
    - ACRF vs NOTI outcomes
    - Test automation (Cypress, API testing)
    - Test data design (boundary values, combinatorics)
    - RBAC and audit requirements
    - BDD/Gherkin and Xray format
  
  working_memory: |
    Remember:
    1. Rule List v1 is your source of truth (from domain_validation_agent)
    2. Never repeat sub-agent outputs (consolidate instead)
    3. Quality gates MUST pass before output
    4. All assumptions are labeled
    5. Traceability to JIRA is mandatory
  
  output_format: |
    Always structure output as:
    A) Summary (what changed + risk)
    B) Assumptions & open questions
    C) Coverage plan (table)
    D) Test cases (BDD)
    E) Test cases (Xray)
    F) Automation suggestions
    G) Test data
    H) Regression recommendations
    I) Observability/Logs

sub_agent_contracts: |
  Expect from domain_validation_agent:
    - Rule list with Given/When/Then
    - Edge case checklist
    - Ambiguities flagged
  
  Expect from test_design_agent:
    - BDD/Gherkin features
    - Xray tests (stepwise)
    - No repetition of rules (they condensed already)
  
  [Continue with all sub-agents...]
```

[Create similar for all other agents]

---

## 🔗 Integration with VorstersNV Orchestrator

### Step 1: Add Agent YAML Files

```bash
# Files are already in:
agents/
├── test_orchestrator_agent.yml
├── domain_validation_agent.yml
├── test_design_agent.yml
├── automation_agent.yml
├── test_data_designer_agent.yml
├── security_permissions_agent.yml
├── regression_selector_agent.yml
├── developer_agent.yml
└── architect_agent.yml
```

### Step 2: Create Prompt Files

```bash
# Create this structure:
prompts/
├── system/
│   ├── test_orchestrator_system.txt
│   ├── domain_validation_system.txt
│   ├── test_design_system.txt
│   ├── automation_system.txt
│   ├── test_data_designer_system.txt
│   ├── security_permissions_system.txt
│   ├── regression_selector_system.txt
│   ├── developer_agent_system.txt
│   └── architect_agent_system.txt
│
└── preprompt/
    ├── test_orchestrator_v1.yml
    ├── domain_validation_v1.yml
    ├── test_design_v1.yml
    ├── automation_v1.yml
    ├── test_data_designer_v1.yml
    ├── security_permissions_v1.yml
    ├── regression_selector_v1.yml
    ├── developer_agent_v1.yml
    └── architect_agent_v1.yml
```

### Step 3: Update Your Agent Runner

```python
# ollama/agent_runner.py

async def run_agent(self, agent_name: str, user_input: str) -> dict:
    # Get agent config from YAML
    config = self.agents_config[agent_name]
    
    # Load system prompt
    system_prompt = self._load_prompt(config['system_prompt_ref'])
    
    # Load pre-prompt
    preprompt = self._load_prompt(config['preprompt_ref'])
    
    # Special handling for orchestrators (delegates to sub-agents)
    if config.get('type') == 'orchestrator':
        return await self._run_orchestrator_workflow(
            agent_name=agent_name,
            user_input=user_input,
            sub_agents=config.get('sub_agents'),
            delegation_logic=config.get('delegation_logic'),
            system_prompt=system_prompt,
            preprompt=preprompt
        )
    
    # Normal agent execution
    return await self._run_single_agent(
        agent_name=agent_name,
        user_input=user_input,
        system_prompt=system_prompt,
        preprompt=preprompt
    )

async def _run_orchestrator_workflow(self, agent_name, user_input, 
                                     sub_agents, delegation_logic, 
                                     system_prompt, preprompt):
    """Run orchestrator that delegates to sub-agents"""
    
    # Step 1: Parse & normalize requirements
    parsed_spec = await self.run_single_agent(
        agent_name=agent_name,
        user_input=f"{system_prompt}\n{preprompt}\n\nPARSE: {user_input}",
        task="parse_and_normalize"
    )
    
    # Step 2: Run risk analysis
    # Step 3: Delegate to sub-agents based on delegation_logic
    # Step 4: Consolidate outputs
    # Step 5: Quality gate checks
    # Step 6: Return consolidated output
```

### Step 4: Setup FastAPI Endpoint

```python
# api/routers/testing.py

from fastapi import APIRouter
from ollama.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/api/testing", tags=["qa"])
orchestrator = AgentOrchestrator()

@router.post("/generate-test-pack")
async def generate_test_pack(spec_request: TestPackRequest):
    """
    Generate complete test pack using test_orchestrator_agent
    """
    
    result = await orchestrator.execute_workflow(
        workflow_name="test_orchestration",
        initial_data={
            "spec": spec_request.spec,
            "context": spec_request.context,
            "test_level": spec_request.test_level,
            "assume_missing": True
        }
    )
    
    return result

@router.post("/implementation-plan")
async def get_implementation_plan(spec_request: SpecRequest):
    """
    Get implementation plan using developer_agent
    """
    
    runner = AgentRunner()
    result = await runner.run_agent(
        agent_name="developer_agent",
        user_input=spec_request.spec
    )
    
    return result

@router.post("/architecture-design")
async def get_architecture_design(arch_request: ArchRequest):
    """
    Get architecture design using architect_agent
    """
    
    runner = AgentRunner()
    result = await runner.run_agent(
        agent_name="architect_agent",
        user_input=arch_request.spec
    )
    
    return result
```

---

## 🎯 Usage Examples

### Example 1: Get Complete Test Pack for Feature

```python
spec = """
Feature: Bulk re-trigger declarations

User Story:
- As a payroll manager
- I want to re-trigger multiple declarations with amended data
- So that I can correct data and resubmit to e-Gov 3.0

Requirements:
- Bulk re-trigger 1-1000 declarations at once
- Amended data must be validated before submission
- Original declaration must still be visible (audit)
- ACRF/NOTI outcomes properly handled
- Only managers with re-trigger permission can do this
"""

context = {
    "domain": "flexi_at_work",
    "tenant": "belgian_payroll",
    "jira_key": "PAYROLL-2024-042",
    "compliance": ["GDPR", "Belgian_payroll_law", "e-Gov_3.0"]
}

result = await orchestrator.execute_workflow(
    workflow_name="test_orchestration",
    initial_data={
        "spec": spec,
        "context": context,
        "assume_missing": True
    }
)

# Result contains:
# - Summary
# - Assumptions
# - Coverage plan (table)
# - BDD scenarios
# - Xray tests
# - Cypress automation skeletons
# - Test data (boundary values)
# - RBAC matrix
# - Regression pack
```

### Example 2: Get Implementation Plan

```python
result = await agent_runner.run_agent(
    agent_name="developer_agent",
    user_input=spec
)

# Result contains:
# - Implementation approach
# - Data model + state transitions
# - Validation logic (pseudocode)
# - Error messages
# - API endpoints
# - Logging points
# - Test hooks
# - Pitfalls + mitigations
```

### Example 3: Get Architecture Design

```python
result = await agent_runner.run_agent(
    agent_name="architect_agent",
    user_input=spec
)

# Result contains:
# - Architecture overview
# - Context boundaries
# - Integration patterns
# - Status lifecycle
# - Security model
# - Audit strategy
# - Data history management
# - Sequence flows
# - NFRs
```

---

## 🔄 Orchestration Flow (Visual)

```
User Request
    │
    ▼
test_orchestrator_agent (Lead)
    │
    ├─► domain_validation_agent
    │   └─ Extract rules → Rule List v1
    │
    ├─► test_design_agent
    │   └─ Rules → BDD + Xray tests
    │
    ├─► automation_agent
    │   └─ Tests → Cypress skeletons
    │
    ├─► test_data_designer_agent
    │   └─ Rules → Boundary datasets
    │
    ├─► security_permissions_agent
    │   └─ Rules → RBAC matrix
    │
    └─► regression_selector_agent
        └─ Change → Regression pack

    ▼
Orchestrator Consolidates
    - Removes duplication
    - Quality gate checks
    - Traceability verification
    ▼
Unified Test Pack
(Actionable, ready-to-run)
```

---

## ✅ Next Steps

1. **Create prompt files** in `/prompts/system/` and `/prompts/preprompt/`
   - Copy master prompts from your original input

2. **Update agent_runner.py** to handle orchestrators

3. **Create FastAPI endpoints** for `/api/testing/generate-test-pack`, etc.

4. **Test with a real spec** (bulk re-trigger example above)

5. **Monitor output quality** against evaluation metrics

---

## 📊 Agent Integration Checklist

- [x] 9 agent YAML configs created
- [ ] Prompt files created (system + preprompt)
- [ ] Agent runner updated for orchestrators
- [ ] FastAPI endpoints added
- [ ] First workflow tested
- [ ] Evaluate output quality
- [ ] Iterate on prompts if needed

---

## 💡 Pro Tips

### For Maximum Quality:
1. **Always provide context** (domain, compliance, scale)
2. **Label assumptions explicitly** - don't ask for confirmation
3. **Quality gates must pass** before output
4. **No tech leakage** in UI tests (max dates, etc.)
5. **Traceability is mandatory** (JIRA keys)

### For Orchestrator Efficiency:
1. Let orchestrator do **Rule List v1 first**
2. Sub-agents only do **their own deliverable**
3. Orchestrator does **consolidation + quality gates**
4. No repetition between agents

### For CI/CD Integration:
1. Add `--ci-mode` flag to skip confirmations
2. Artifacts: screenshots, videos, JUnit results
3. Parallelize test execution (Cypress can run in parallel)
4. Fail fast on security/compliance issues

---

## 🚀 You're Ready!

You now have:
- ✅ 9 production-ready agent configs
- ✅ Complete master prompts
- ✅ Integration guide
- ✅ Usage examples
- ✅ Quality checkpoints

**Next: Start with one feature, one test pack, and iterate!** 💪

---

**Questions? Check the agent YAML files — they're self-documenting!**
