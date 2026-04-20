# SKILL: Ollama Agent Design

Reference knowledge for creating and improving Ollama-based YAML agent definitions in the VorstersNV agent system.

## How the System Works

```
agent_runner.py
    ↓ loads YAML from agents/<name>.yml
    ↓ reads system_prompt_ref → string
    ↓ reads preprompt_ref → YAML context
    ↓ sends to Ollama API (localhost:11434)
    ↓ validates output against output_schema
    ↓ returns structured response
```

## Key YAML Fields

| Field | Purpose | Required |
|-------|---------|---------|
| `name` | Snake_case identifier | ✅ |
| `version` | Semver — increment on breaking change | ✅ |
| `type` | `specialist` / `orchestrator` / `validator` | ✅ |
| `model` | `llama3` / `mistral` / `codellama` | ✅ |
| `temperature` | 0.2 (precise) → 0.9 (creative) | ✅ |
| `max_tokens` | Max response length | ✅ |
| `system_prompt_ref` | Path to .txt system prompt | ✅ |
| `preprompt_ref` | Path to .yml context injection | ✅ |
| `capabilities` | List of `verb_noun` strings | ✅ |
| `input_schema` | JSON Schema for validation | ✅ |
| `output_schema` | JSON Schema for response | ✅ |
| `evaluation` | Quality metrics with targets | ✅ |
| `tags` | Searchable labels | ✅ |

## Temperature Guide

| Task Type | Range | Example |
|-----------|-------|---------|
| Code generation | 0.2-0.4 | `developer_agent` |
| Analysis, review | 0.3-0.5 | `clean-code-reviewer` |
| Domain validation | 0.2-0.3 | `domain-validator` |
| Content writing | 0.6-0.8 | `product-content` |
| Brainstorming | 0.7-0.9 | `prompt-engineer` |

## System Prompt Template

```
You are a [ROLE] specialized in [DOMAIN] for the VorstersNV KMO platform.

## Your Responsibility
[Single clear sentence describing what this agent does]

## Available Context
You receive: [input fields]
You return: [output fields]

## Domain Rules
1. [Business rule 1]
2. [Business rule 2]

## Code/Output Standards
- [Standard 1]
- [Standard 2]

## Output Format
Return a JSON object exactly matching this structure:
{
  "field_name": "type — description"
}

## Example
Given input: {"spec": "Add order cancellation feature"}
Return: {
  "approach": "...",
  "affected_entities": ["Order"],
  "steps": [...]
}

## Do NOT
- [Anti-pattern 1]
- [Anti-pattern 2]
```

## Preprompt YAML Template

```yaml
version: 1

context: |
  ## VorstersNV Platform Context
  KMO webshop with AI-agent system. Stack: FastAPI (Python 3.12), Next.js 14, PostgreSQL.
  
  ## Bounded Contexts
  - Catalog: Product, Category
  - Orders: Order, OrderLine  
  - Inventory: StockItem
  - Payments: Payment (Mollie)
  
  ## Active Constraints
  - All backend code must be async (FastAPI + SQLAlchemy)
  - Frontend must use App Router (no Pages Router)
  - DDD patterns: aggregates, value objects, domain events
  - Tests required for all new endpoints

examples:
  - input: |
      {"spec": "cancel order after payment"}
    expected_output: |
      {"approach": "Add cancel() method to Order aggregate..."}
```

## Agent Type Patterns

### Specialist Agent
```yaml
type: specialist
# One domain, one responsibility
# temperature: 0.3-0.5
# Example: developer_agent, database-expert
```

### Orchestrator Agent
```yaml
type: orchestrator
# Routes tasks to specialist agents
# temperature: 0.2-0.3 (precise routing)
# Example: test_orchestrator_agent
```

### Validator Agent
```yaml
type: validator
# Checks output from other agents
# temperature: 0.2 (strict)
# Example: domain_validator_agent
```

## Input Schema Best Practices

```yaml
input_schema:
  type: object
  required:
    - spec           # always require the main input
  properties:
    spec:
      type: string
      description: "Feature spec, user story, or requirement to implement"
    context:
      type: object
      description: "Optional context about existing code"
      properties:
        existing_patterns:
          type: array
          items: { type: string }
        constraints:
          type: array
          items: { type: string }
```

## Output Schema Best Practices

```yaml
output_schema:
  type: object
  properties:
    summary:
      type: string
      description: "1-2 sentence summary of the result"
    items:
      type: array
      items:
        type: object
        properties:
          name: { type: string }
          description: { type: string }
    confidence:
      type: number
      description: "0.0-1.0 confidence in the output quality"
```

## Evaluation Metrics

```yaml
evaluation:
  - metric: accuracy
    target: ">= 90%"
  - metric: output_schema_compliance
    target: "100%"
  - metric: domain_rule_adherence
    target: ">= 95%"
  - metric: code_quality (for dev agents)
    target: ">= 85% clean code score"
```

## Capability Naming Convention

Use `verb_noun` format — describes what the agent can DO:

```yaml
capabilities:
  - analyze_requirements       # ✅ verb_noun
  - generate_migration         # ✅
  - validate_domain_rules      # ✅
  - implement_api_endpoint     # ✅
  - review_code_quality        # ✅
  # ❌ NOT: "code_generation", "migration", "api"
```

## Existing Agent Cross-Reference

| Agent | Calls | Used By |
|-------|-------|---------|
| `test_orchestrator` | → `playwright_mcp`, `automation-cypress`, `test_data_designer` | QA pipeline |
| `domain_validator` | → reads domain context | `developer_agent` post-check |
| `architect_agent` | → `ddd_modeler` | Feature design phase |

## Improvement Checklist

When reviewing an existing agent:
- [ ] System prompt has a concrete example with input + output
- [ ] Temperature is appropriate for the task type
- [ ] All `required` input fields are listed
- [ ] Output schema is explicit (not just `type: object`)
- [ ] `tags` reflect actual capabilities (for discoverability)
- [ ] `evaluation.target` values are realistic, not aspirational
- [ ] Preprompt context includes current domain model state
- [ ] Version bumped if schema or behavior changed
