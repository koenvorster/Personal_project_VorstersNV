# VorstersNV – Projectarchitectuur

> **AI Platform versie:** 5.0 | **Status:** Wave 9 COMPLEET — Revisie 5 volledig geïmplementeerd (alle gaps G-32..G-46 gesloten) | **Datum:** April 2026
> **AI Masterplan:** `documentatie/AI_OPTIMALISATIEPLAN_REVISIE5.TXT` (Revisie 5 — Enterprise Consultancy Intelligence Platform)

---

## Inhoudsopgave

1. [AI Platform Positionering](#1-ai-platform-positionering)
2. [Architectuurlagen — Volledig Diagram](#2-architectuurlagen--volledig-diagram)
3. [Control Plane](#3-control-plane)
4. [Capability Plane](#4-capability-plane)
5. [Execution Plane](#5-execution-plane)
6. [Workflow Lanes](#6-workflow-lanes)
7. [Deployment Rings](#7-deployment-rings)
8. [Agent Fleet](#8-agent-fleet)
9. [Trust Plane](#9-trust-plane)
10. [Data Flow — Event naar Output](#10-data-flow--event-naar-output)
11. [Key Files — Referentietabel](#11-key-files--referentietabel)
12. [Waves Roadmap](#12-waves-roadmap)
13. [Databases & API](#13-databases--api)

---

## 1. AI Platform Positionering

VorstersNV is geen chatbot of losstaande agent-verzameling.
Het is een **AI-controlled platform** voor Belgische e-commerce met:

- **Governance via Policy-as-Code** — YAML-gedreven regels, geen hardcoded logica
- **Gecontroleerde rollout via Deployment Rings** — Ring 0 (lokaal) → Ring 4 (full productie)
- **Capability Maturity Model** — L1 (experimental) → L4 (business-critical)
- **Volledige auditability via Decision Journal** — elke AI-beslissing is traceerbaar
- **3-tier observability** — N1 (request) / N2 (agent) / N3 (business KPIs)

```
VROEGER:   verzameling losse agents en scripts
REVISIE 3: event-driven skill chain orchestratie
REVISIE 4: AI CONTROLLED PLATFORM met governance, maturity en rollout
```

---

## 2. Architectuurlagen — Volledig Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTERNE TRIGGERS                                  │
│  Mollie webhooks │ order.created │ fraud.detected │ code.released   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      DATA LAAG                                       │
│  PostgreSQL │ Mollie API │ Order Events │ Inventory DB               │
│  EventBus (ollama/events.py) — idempotent, typed event taxonomy     │
└────────────────────────────┬────────────────────────────────────────┘
                             │ DomainEvent (typed)
┌────────────────────────────▼────────────────────────────────────────┐
│                     CONTROL PLANE                                    │
│  ollama/control_plane.py  │  ollama/policy_engine.py                │
│  ollama/cost_governance.py │  ollama/maturity_engine.py             │
│                                                                      │
│  ControlPlane.select_capability(event_type)                         │
│  ControlPlane.select_execution_path(capability, context)            │
│  ControlPlane.enforce_policy(capability, context)                   │
│  ControlPlane.check_budget(capability, usage)                       │
│  ControlPlane.determine_rollout_ring(context)                       │
│  ControlPlane.requires_human_approval(capability, context)          │
│                                                                      │
│  8 routing dimensies: event_type │ environment │ risk_score         │
│  remaining_budget_eur │ max_latency_ms │ maturity_level             │
│  available_models │ policy_rules                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │ ExecutionPath
┌────────────────────────────▼────────────────────────────────────────┐
│                    CAPABILITY PLANE                                  │
│  ollama/capability_registry.py │ .claude/capabilities/*.yaml        │
│  ollama/maturity_engine.py      │ policies/hitl-policies.yaml       │
│  policies/tool-policies.yaml    │ policies/maturity-policies.yaml   │
│                                                                      │
│  14 capabilities geregistreerd                                       │
│  Maturity L1–L4 per capability                                       │
│  Cost budget per capability (monthly_budget_eur)                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │ capability + lane
┌────────────────────────────▼────────────────────────────────────────┐
│                    EXECUTION PLANE                                   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    WORKFLOW LANES                             │   │
│  │  DETERMINISTIC │ ADVISORY │ GENERATIVE │ ACTION              │   │
│  │  ollama/workflow_lanes.py — LaneConfig per lane               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              V3 SKILL CHAIN ORCHESTRATOR                      │   │
│  │  ollama/skill_chain_orchestrator.py                           │   │
│  │  3 chains: release-to-payroll-impact │ testing-chain         │   │
│  │            prc-decision-support                               │   │
│  │  ChainContext │ ChainResult │ checkpoint recovery             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   AGENT FLEET (6 groepen)                     │   │
│  │  .claude/agents/ │ agents/ │ ollama/agent_runner.py           │   │
│  │  15+ agents │ 6 tools │ ollama/agent_groups.py               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ollama/contracts.py — typed domain contracts (input/output)        │
│  ollama/orchestrator.py │ ollama/state_machine.py                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ output + verdict
┌────────────────────────────▼────────────────────────────────────────┐
│                      TRUST PLANE                                     │
│  ollama/quality_gates.py      │ ollama/review_loop.py              │
│  ollama/decision_journal.py   │ ollama/observability.py            │
│  ollama/deployment_rings.py   │ ollama/schema_validator.py         │
│                                                                      │
│  QualityGateEngine — QG-FRAUD-01..04, QG-CONTENT-01..03            │
│  DecisionJournal — APPROVED | REJECTED | REVIEW                    │
│  ObservabilityCollector — N1/N2/N3                                  │
│  RingGateChecker — promotie criteria per ring                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                BACKOFFICE / MERCHANT INTERFACE                       │
│  Dashboard │ HITL review UI │ Notification center (Wave 5)         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       AUDIT LAYER                                    │
│  OpenTelemetry GenAI spans │ GDPR audit log │ Grafana N3 dashboard  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Control Plane

**Bestand:** `ollama/control_plane.py`

De Control Plane is het centraal beslissingsmechanisme van het platform. Elke
AI-request gaat via de Control Plane — geen capability wordt rechtstreeks
aangesproken.

### Klassen

```
ControlPlane
  select_capability(event_type: EventType) -> str
  select_execution_path(capability, context: ExecutionContext) -> ExecutionPath
  enforce_policy(capability, context, tools_requested) -> None | raises PolicyViolationError
  check_budget(capability, usage: dict) -> bool
  determine_rollout_ring(context) -> DeploymentRing
  requires_human_approval(capability, context) -> bool

ExecutionContext               # 8 routing dimensies
  event_type: EventType
  environment: Environment      # LOCAL | DEV | TEST | STAGING | PROD
  risk_score: int               # 0-100
  remaining_budget_eur: float
  max_latency_ms: int
  maturity_level: MaturityLevel # L1 | L2 | L3 | L4
  available_models: list[str]
  tenant_id / user_id / trace_id

ExecutionPath                 # routing beslissing
  capability / lane / primary_model / fallback_model
  max_tokens_input / max_tokens_output / max_tool_calls
  chain_name / requires_hitl / deployment_ring / selection_reason
```

### Routing logica

```
Event ontvangen
    │
    ▼
select_capability(event_type)
    │  ORDER_CREATED     → order-validation
    │  PAYMENT_FAILED    → payment-retry
    │  FRAUD_DETECTED    → risk-classification
    │  INVENTORY_LOW     → inventory-reorder
    │  CODE_RELEASED     → regression-analysis
    │  ANOMALY_DETECTED  → risk-classification
    │  HITL_REQUIRED     → order-blocking
    ▼
select_execution_path(capability, context)
    │  risk_score >= 75 OR is_production → escalation model
    │  maturity L1/L2                   → Ring 0/1 (nooit prod)
    │  ACTION lane in prod              → HITL verplicht
    ▼
enforce_policy(capability, context)
    │  PolicyEngine laadt /policies/*.yaml
    │  BLOCKER violation → PolicyViolationError
    │  WARNING/INFO      → alleen logging
    ▼
ExecutionPath teruggegeven aan Execution Plane
```

### Policy Engine

**Bestand:** `ollama/policy_engine.py`

```
PolicyEngine                   # singleton via get_policy_engine()
  evaluate(capability, context, tools_requested, lane) -> list[PolicyViolation]
  enforce(...)                 → raises PolicyViolationError bij BLOCKER
  is_tool_allowed(capability, tool) -> bool
  get_allowed_tools(capability) -> list[str] | None
  get_denied_tools(capability) -> list[str]

PolicyViolation
  rule_id / severity (BLOCKER | WARNING | INFO) / message / audit / notify
```

Policy bestanden in `/policies/`:
- `hitl-policies.yaml` — HITL-001 (prod + ACTION), HITL-002 (risk ≥ 75), HITL-003 (L4 in vroege ring)
- `tool-policies.yaml` — TOOL-001 (fraud: allow/deny tools), TOOL-002 (order-processing)
- `maturity-policies.yaml` — per maturity level toegestane omgevingen

### Cost & Model Governance

**Bestand:** `ollama/cost_governance.py`

```
CostGovernanceEngine           # singleton via get_cost_governance()
  select_model(capability, risk_score, force_escalation) -> str
  check_budget(capability, estimated_tokens) -> (bool, reason)
  record_usage(capability, model, input_tokens, output_tokens, tool_calls)
  get_monthly_spend(capability) -> float
  get_cost_report() -> dict

CostPolicy
  capability / max_input_tokens / max_output_tokens
  preferred_model (ModelTier) / escalation_model / max_tool_calls
  monthly_budget_eur

ModelTier: CHEAP (llama3) | STANDARD (llama3.1) | PREMIUM (llama3.1:70b)
```

Escalatielogica:
```
risk_score < 75   → preferred_model (goedkoop)
risk_score >= 75  → escalation_model
force_escalation  → escalation_model
budget exceeded   → block of fallback naar cheap model
```

Maandbudget per capability (EUR):

| Capability          | Max tokens (in/out) | Budget/maand |
|---------------------|--------------------:|-------------:|
| fraud-detection     |       8 000 / 1 000 |      €100.00 |
| order-validation    |       4 000 /   500 |       €50.00 |
| content-generation  |       6 000 / 2 000 |      €150.00 |
| risk-classification |       3 000 /   500 |       €30.00 |
| default             |       4 000 / 1 000 |       €75.00 |

---

## 4. Capability Plane

**Bestanden:** `ollama/capability_registry.py`, `ollama/maturity_engine.py`,
`.claude/capabilities/*.yaml`, `.claude/capabilities/index.yaml`

### Capability Registry

14 capabilities geregistreerd in `control_plane.py` (`_CAPABILITY_LANES`):

| Capability            | Lane          | Model (pref/esc)      |
|-----------------------|---------------|-----------------------|
| order-validation      | DETERMINISTIC | llama3 / llama3       |
| schema-validation     | DETERMINISTIC | —                     |
| contract-mapping      | DETERMINISTIC | —                     |
| fraud-detection       | ADVISORY      | llama3 / mistral      |
| risk-classification   | ADVISORY      | llama3 / mistral      |
| architecture-review   | ADVISORY      | codellama / codellama |
| regression-analysis   | ADVISORY      | codellama / codellama |
| product-content       | GENERATIVE    | mistral / mistral     |
| email-generation      | GENERATIVE    | —                     |
| customer-service      | GENERATIVE    | mistral / mistral     |
| order-blocking        | ACTION        | —                     |
| account-management    | ACTION        | —                     |
| payment-retry         | ACTION        | —                     |
| inventory-reorder     | ACTION        | —                     |

### Capability Maturity Model

**Bestand:** `ollama/maturity_engine.py` — `MaturityEngine`

```
L1  experimental      → alleen in: dev
L2  internal-beta     → alleen in: dev, test
L3  team-production   → alleen in: dev, test, staging
L4  business-critical → overal: dev, test, staging, prod
```

Promotie gates (één niveau per keer via `MaturityEngine.can_promote()`):

```
L1 → L2:  unit evals > 80%, schema validation rate > 90%
L2 → L3:  capability evals > 85%, 1 week stabiel in AI team
L3 → L4:  chain + business evals OK, rollback getest, observability actief
L4:       continu gemonitord, SLA gegarandeerd, alerting actief
```

L4 in productie vereist altijd: `eval_completed=True` EN `human_approved=True`

### Capability YAML structuur

Voorbeeld: `.claude/capabilities/fraud-detection.yaml`

```yaml
name: fraud-detection
version: "2.0"
lane: advisory
maturity:
  level: L3
  eval_required: true
  human_approval_required: conditional
  min_first_pass_score: 0.85
assurance:
  min_schema_validation_rate: 0.95
  max_false_positive_rate: 0.05
operational:
  owner: team-ai-platform
  sla_tier: gold
  cost_budget_monthly_eur: 100.0
  preferred_model: llama3
  escalation_model: "llama3.1:70b"
release:
  rollout_ring: ring-2
  feature_flag: "ai.capability.fraud-detection.v2"
agents:
  - fraud-advisor
contract: FraudAssessmentContract
chain: prc-decision-support
```

---

## 5. Execution Plane

### V3 Skill Chain Orchestrator

**Bestand:** `ollama/skill_chain_orchestrator.py`

```
SkillChainOrchestrator         # singleton via get_skill_chain_orchestrator()
  select_chain(event_type, risk_score, missing_data) -> (chain_name, reasons)
  run(chain_name, inputs, risk_score, environment, resume_from_checkpoint) -> ChainResult
  register_chain(chain: ChainDefinition)
  list_chains() -> list[str]

ChainDefinition
  name / trigger / description / steps: list[ChainStep] / on_high_risk

ChainStep
  skill / output_key / input_from / agent_hint / required

ChainContext (runtime)
  outputs / completed_steps / skipped_steps / selection_reasons
  status: ChainStatus / trace_id / checkpoint

ChainResult
  chain_name / status / outputs / selection_reasons
  completed_steps / skipped_steps / high_risk_actions_triggered / error
```

Chain selectie logica:
```
event_type = "code_released"    → chain: release-to-payroll-impact
event_type = "test_requested"   → chain: testing-chain
event_type = "anomaly_detected"
  OR risk_score >= 75            → chain: prc-decision-support
missing_data = "payroll_data"   → chain: prc-decision-support
default                         → chain: testing-chain
```

### De 3 V3 Skill Chains

**Chain 1: release-to-payroll-impact** (trigger: `code_released`)
```
analyze_code_changes          → code_analysis
map_changes_to_business_logic → business_impact
detect_regression_scope       → regression_scope
compare_with_previous_run     → comparison
detect_salary_anomalies       → anomalies

on_high_risk: classify_payroll_risk, explain_salary_difference, suggest_prc_actions
```

**Chain 2: testing-chain** (trigger: `test_requested`)
```
validate_acceptance_criteria  → criteria_result
generate_advanced_test_cases  → test_cases
detect_regression_risk        → regression_risk

on_high_risk: generate_test_documentation
```

**Chain 3: prc-decision-support** (trigger: `anomaly_detected`)
```
detect_salary_anomalies       → anomalies
classify_payroll_risk         → risk_class
explain_salary_difference     → explanation
suggest_prc_actions           → actions

on_high_risk: audit_trace_generator, decision_logging
```

Checkpoint recovery: elke stap slaat zijn index op (`save_checkpoint(i)`).
Bij herstart begint de chain vanaf de laatste geslaagde stap.

### Domain Contracts

**Bestand:** `ollama/contracts.py`

Alle agent-naar-agent communicatie gaat via typed contracts (geen raw strings):

```
BaseContract
  contract_version / agent_name / trace_id / timestamp
  to_prompt_input() -> str          # injecteerbaar in agent prompt
  from_agent_output(output) -> cls  # JSON parsing met fallback
  validate() -> (bool, list[str])   # integriteitscheck
  to_dict() -> dict[str, Any]

OrderAnalysisContract(BaseContract)
  order_id / customer_id / order_value / payment_method
  delivery_country / billing_country / customer_age_days
  previous_orders / uses_vpn / items_count / payment_status

FraudAssessmentContract(BaseContract)
  order_id / risk_score (0-100) / risk_level (LOW|MEDIUM|HIGH|CRITICAL)
  rationale: list[str] / recommended_action (ALLOW|REVIEW|BLOCK)
  requires_human (auto True bij risk_score >= 75) / confidence / model_used

ContentGenerationContract(BaseContract)
  product_id / product_name / titel / beschrijving
  seo_keywords: list[str] / btw_categorie (6%|21%)
  voldoet_aan_voedselwet / taal / word_count / review_verdict
```

### Event System

**Bestand:** `ollama/events.py`

```
EventType (str Enum) — 20+ event types:
  ORDER_CREATED | ORDER_CONFIRMED | ORDER_CANCELLED | ORDER_SHIPPED | ORDER_DELIVERED
  PAYMENT_COMPLETED | PAYMENT_FAILED | PAYMENT_REFUNDED | PAYMENT_EXPIRED
  FRAUD_DETECTED | FRAUD_CLEARED | FRAUD_BLOCKED
  INVENTORY_LOW | INVENTORY_DEPLETED | INVENTORY_RESTOCKED
  CUSTOMER_REGISTERED | CUSTOMER_FLAGGED
  CODE_RELEASED | ANOMALY_DETECTED | QUALITY_GATE_FAILED
  HITL_REQUIRED | HITL_RESOLVED

DomainEvent (base)
  event_id (deterministisch SHA-256 voor idempotency)
  event_type / trace_id / timestamp / metadata

Concrete events:
  OrderCreatedEvent / PaymentFailedEvent / FraudDetectedEvent
  InventoryLowEvent / HitlRequiredEvent / AnomalyDetectedEvent

EventBus (singleton via get_event_bus())
  subscribe(event_type, handler)
  publish(event) -> bool            # False bij duplicate (idempotent skip)
  get_chain(event_type) -> str      # CHAIN_FOR_EVENT mapping

CHAIN_FOR_EVENT mapping:
  ORDER_CREATED    → ORDER_VALIDATION
  PAYMENT_FAILED   → PAYMENT_RECOVERY
  FRAUD_DETECTED   → FRAUD_EXPLANATION
  INVENTORY_LOW    → REORDER_NOTIFICATION
  CODE_RELEASED    → DEV_INTELLIGENCE
  ANOMALY_DETECTED → ANOMALY_ACTION
  HITL_REQUIRED    → HITL_ESCALATION
```

---

## 6. Workflow Lanes

**Bestand:** `ollama/workflow_lanes.py` — `LANE_REGISTRY`, `LaneConfig`

Elke capability hoort in precies 1 lane. De lane bepaalt temperature, schema-eisen,
review-vereisten en HITL-gedrag.

```
┌──────────────────┬───────────┬────────────────────────────────────────────┐
│ Lane             │ Temp.     │ Kenmerken                                  │
├──────────────────┼───────────┼────────────────────────────────────────────┤
│ DETERMINISTIC    │ 0.1       │ strict_schema=True, creativity=False       │
│                  │           │ output must not be empty                   │
│                  │           │ capabilities: order-validation,            │
│                  │           │   schema-validation, contract-mapping      │
├──────────────────┼───────────┼────────────────────────────────────────────┤
│ ADVISORY         │ 0.3       │ explainability=True                        │
│                  │           │ confidence_score_required=True             │
│                  │           │ reviewable=True                            │
│                  │           │ output must contain 'confidence_score'     │
│                  │           │ capabilities: fraud-detection,             │
│                  │           │   risk-classification, architecture-review │
├──────────────────┼───────────┼────────────────────────────────────────────┤
│ GENERATIVE       │ 0.7       │ style_rules=True, seo_check=True           │
│                  │           │ review_loop=True (max 2 iteraties)         │
│                  │           │ output: 'description' ≥ 50 tekens          │
│                  │           │ capabilities: product-content,             │
│                  │           │   email-generation, customer-service       │
├──────────────────┼───────────┼────────────────────────────────────────────┤
│ ACTION           │ 0.1       │ hitl_required_in_prod=True                 │
│                  │           │ audit_logging=True, idempotent=True        │
│                  │           │ output: 'trace_id' + 'audit_logged'=True   │
│                  │           │ capabilities: order-blocking,              │
│                  │           │   payment-retry, inventory-reorder         │
└──────────────────┴───────────┴────────────────────────────────────────────┘
```

Lane output validatie via `validate_output_for_lane(lane, output) -> (bool, list[str])`.

---

## 7. Deployment Rings

**Bestand:** `ollama/deployment_rings.py` — `RING_POLICIES`, `RingGateChecker`

```
┌────────┬─────────────────────┬──────────────────┬──────────┬───────────────┐
│ Ring   │ Naam                │ Maturity vereist │ Traffic  │ Auto-rollback │
├────────┼─────────────────────┼──────────────────┼──────────┼───────────────┤
│ Ring 0 │ lokaal              │ L1..L4           │ 100%     │ nooit         │
│        │ developer machine   │                  │          │               │
├────────┼─────────────────────┼──────────────────┼──────────┼───────────────┤
│ Ring 1 │ AI team             │ L2..L4           │ 100%     │ bij ≥ 20%    │
│        │ interne reviews     │ eval + policy ✓  │          │   foutrate    │
├────────┼─────────────────────┼──────────────────┼──────────┼───────────────┤
│ Ring 2 │ interne users       │ L3..L4           │ 100%     │ bij ≥ 10%    │
│        │ medewerkers         │ +observability ✓ │          │   foutrate    │
├────────┼─────────────────────┼──────────────────┼──────────┼───────────────┤
│ Ring 3 │ beperkte productie  │ L3..L4           │ 10%      │ bij ≥ 5%     │
│        │ 5-10% traffic       │ +rollback plan ✓ │          │   foutrate    │
├────────┼─────────────────────┼──────────────────┼──────────┼───────────────┤
│ Ring 4 │ full productie      │ L4 ONLY          │ 100%     │ bij ≥ 5%     │
│        │ alle gebruikers     │ alle gates ✓     │          │   foutrate    │
└────────┴─────────────────────┴──────────────────┴──────────┴───────────────┘
```

Promotie via `RingGateChecker.can_promote(capability, current_ring, to_ring, gate_results)`:
- Rings moeten **sequentieel** gepromoveerd worden (geen skip van 2+ ringen)
- `gate_results` bevat: `evals_passed`, `policy_passed`, `observability_ok`,
  `rollback_plan`, `error_rate`
- `get_promotion_requirements(from_ring, to_ring)` geeft leesbare vereisten terug

---

## 8. Agent Fleet

**Bestanden:** `.claude/agents/README.md`, `.claude/capabilities/index.yaml`,
`ollama/agent_groups.py`

```
[LEAD ORCHESTRATOR]
        │
┌───────┴────────────────────────────────────────────────────────────┐
│  GROUP 1 DEV INTELLIGENCE  │  GROUP 2 TEST INTELLIGENCE            │
│  GROUP 3 E-COMMERCE VALID. │  GROUP 4 RISK & DECISION              │
│  GROUP 5 EXPLANATION       │  GROUP 6 AUDIT                        │
└────────────────────────────────────────────────────────────────────┘
```

### Group 1 — DEV Intelligence (`dev-intelligence`, lane: advisory)

| Agent                   | Rol                                             |
|-------------------------|-------------------------------------------------|
| `ai-architect`          | architectuuranalyse en ADR documentatie         |
| `feature-worker`        | feature implementatie                           |
| `fastapi-developer`     | FastAPI backend development                     |
| `nextjs-developer`      | Next.js frontend development                    |
| `ollama-agent-designer` | agent ontwerp en capability definities          |

Skills: `analyze_code_changes`, `map_changes_to_business_logic`, `detect_regression_scope`

### Group 2 — Test Intelligence (`test-intelligence`, lane: deterministic)

| Agent               | Rol                                     |
|---------------------|-----------------------------------------|
| `test-orchestrator` | test coördinatie en coverage analyse    |
| `ci-debugger`       | CI/CD debugging en pipeline repair      |

Skills: `validate_acceptance_criteria`, `generate_advanced_test_cases`, `detect_regression_risk`

### Group 3 — E-Commerce Validation (`ecommerce-validation`, lane: deterministic)

| Agent          | Rol                                                  |
|----------------|------------------------------------------------------|
| `order-analyst`| orderverwerking, BTW validatie, schema checks        |
| `fraud-advisor`| fraude detectie op basis van FraudAssessmentContract |

Skills: `compare_with_previous_run`, `detect_salary_anomalies`, `validate_legal_rules`

### Group 4 — Risk & Decision (`risk-decision`, lane: advisory)

| Agent              | Rol                                          |
|--------------------|----------------------------------------------|
| `fraud-advisor`    | risicoclassificatie (dual role met Group 3)  |
| `lead-orchestrator`| beslissingsrouting en chain coördinatie      |

Skills: `classify_payroll_risk`, `assess_release_risk`, `suggest_prc_actions`

### Group 5 — Explanation (`explanation`, lane: generative)

| Agent                  | Rol                                       |
|------------------------|-------------------------------------------|
| `klantenservice-coach` | klantenservice begeleiding en scripts     |
| `product-writer`       | productcontent generatie (NL, SEO)        |
| `mr-reviewer`          | code review uitleg voor niet-developers   |

Skills: `explain_salary_difference`, `explain_code_to_non_dev`

### Group 6 — Audit (`audit`, lane: deterministic)

| Agent           | Rol                                           |
|-----------------|-----------------------------------------------|
| `audit-reporter`| audit trails en compliance rapportage         |
| `gdpr-advisor`  | GDPR begeleiding en data subject requests     |
| `db-explorer`   | data access audit en query analyse            |

Skills: `audit_trace_generator`, `decision_logging`

---

## 9. Trust Plane

### Quality Gates

**Bestand:** `ollama/quality_gates.py` — `QualityGateEngine`, `PRECONFIGURED_GATES`

```
QualityGateEngine
  run_gates(capability, output, validated, trace_id) -> list[GateResult]
  get_verdict(gate_results) -> Verdict
  get_failing_gates(results) -> list[GateResult]
  is_approved(results) -> bool

Verdict:
  APPROVED            alle gates geslaagd
  CHANGES_REQUESTED   alleen IMPROVEMENT gates mislukt
  NEEDS_DISCUSSION    ≥ 1 BLOCKER gate mislukt
```

Geconfigureerde gates:

| Gate ID       | Capability       | Severity    | Check                                        |
|---------------|------------------|-------------|----------------------------------------------|
| QG-FRAUD-01   | fraud-detection  | BLOCKER     | `risk_score` aanwezig                        |
| QG-FRAUD-02   | fraud-detection  | BLOCKER     | `rationale` niet leeg                        |
| QG-FRAUD-03   | fraud-detection  | IMPROVEMENT | `confidence_score` aanwezig                  |
| QG-FRAUD-04   | fraud-detection  | BLOCKER     | `recommended_action` ∈ {ALLOW, REVIEW, BLOCK}|
| QG-CONTENT-01 | product-content  | BLOCKER     | `beschrijving` ≥ 50 tekens                  |
| QG-CONTENT-02 | product-content  | IMPROVEMENT | `seo_keywords` niet leeg                    |
| QG-CONTENT-03 | product-content  | BLOCKER     | `btw_categorie` aanwezig                    |
| QG-ORDER-01   | order-validation | BLOCKER     | `order_id` aanwezig                         |
| QG-ORDER-02   | order-validation | BLOCKER     | `aanbeveling` aanwezig                      |
| QG-GENERAL-01 | * (alle)         | BLOCKER     | response niet leeg                          |
| QG-GENERAL-02 | * (alle)         | IMPROVEMENT | response > 20 tekens                        |

### Decision Journal

**Bestand:** `ollama/decision_journal.py` — `DecisionJournal`, `JournalEntry`

```
JournalEntry
  trace_id (UUID)               ← koppeling met OpenTelemetry
  capability                    ← welke capability werd gebruikt
  agent_name                    ← welke agent deed het werk
  model_used                    ← llama3 | mistral | codellama
  tools_used: list[str]         ← aangeroepen tools
  selection_reason: str         ← waarom deze agent/model gekozen
  alternatives_considered       ← alternatieven overwogen maar niet gekozen
  human_override: bool          ← was er menselijke interventie?
  verdict                       ← APPROVED | REJECTED | REVIEW
  environment / risk_score / execution_time_ms / policy_violations

DecisionJournal (singleton via get_decision_journal())
  record(entry) -> trace_id
  get(trace_id) -> JournalEntry | None
  list_by_capability(capability) -> list[JournalEntry]
  list_by_verdict(verdict) -> list[JournalEntry]
  export_json(trace_id) -> dict    ← voor audit export (ISO timestamps)
  summary_stats() -> dict          ← verdicts per capability, avg risk score
```

### Observability — 3-tier model

**Bestand:** `ollama/observability.py` — `ObservabilityCollector`

```
N1 — REQUEST (per LLM aanroep)
  N1RequestMetric: trace_id / model / input_tokens / output_tokens / latency_ms
  record_request(...) | get_avg_latency() | get_total_tokens()

N2 — AGENT (per agent run)
  N2AgentMetric: agent_name / capability / verdict / fallback_triggered / hitl_escalation
  record_agent(...) | get_escalation_rate() | get_fallback_rate()

N3 — BUSINESS (dagelijks KPI rapport)
  N3BusinessMetric: fraud_accuracy / false_positive_rate / onboarding_success_rate
                    human_escalation_rate / cost_per_outcome_eur
  record_business_metric(metric) | get_fraud_accuracy() | get_cost_per_outcome()

get_dashboard_snapshot() -> {n1_request, n2_agent, n3_business}
```

### Evaluation Hierarchy (4 levels)

```
L1 UNIT EVAL       → ollama/schema_validator.py
                     elke aanroep, automatisch
                     check: schema correct, geen empty output

L2 CAPABILITY EVAL → ollama/evals/judge.py  (LLM-as-judge)
                     bij elke prompt-versiewijziging via CI
                     check: output matches expected dataset, tool calls correct

L3 CHAIN EVAL      → ollama/evals/hierarchy.py
                     bij elke chain configuratie wijziging
                     check: state transitions, HITL correct, checkpoint recovery

L4 BUSINESS EVAL   → ollama/quality_monitor.py + Grafana N3 dashboard
                     dagelijks productie monitoring
                     check: fraud_accuracy, human_escalation_rate,
                            cost_per_outcome, false_positive_rate
```

---

## 10. Data Flow — Event naar Output

```
1. INKOMEND EVENT
   DomainEvent aangemaakt (e.g. OrderCreatedEvent)
   EventBus.publish(event)  ← idempotency check op SHA-256 event_id

2. CONTROL PLANE ROUTING
   ControlPlane.select_capability(event.event_type)
     → capability = "order-validation"
   ControlPlane.select_execution_path(capability, context)
     → ExecutionPath: lane=DETERMINISTIC, model=llama3, ring=Ring-2
   ControlPlane.enforce_policy(capability, context)
     → PolicyEngine evalueert hitl-policies.yaml + tool-policies.yaml
     → PolicyViolationError als BLOCKER gevonden
   ControlPlane.check_budget(capability, estimated_usage)
     → CostGovernanceEngine.check_budget()
     → False als token/budget overschreden

3. CONTRACT AANMAAK
   OrderAnalysisContract gebouwd vanuit event data
   contract.validate() → (True, [])
   contract.to_prompt_input() → geïnjecteerd in agent prompt

4. CHAIN SELECTIE & UITVOERING
   SkillChainOrchestrator.select_chain(event_type, risk_score)
     → "ORDER_VALIDATION" chain geselecteerd
   SkillChainOrchestrator.run(chain_name, inputs, risk_score)
     → Per stap: SkillExecutor.execute(skill, input, ctx)
     → ctx.save_checkpoint(step_index)   ← voor recovery
     → ctx.record_reason(reason)         ← audittrail
     → on_high_risk actions bij risk_score >= 75

5. QUALITY GATE CHECK
   QualityGateEngine.run_gates("order-validation", output, validated)
   QualityGateEngine.get_verdict(results)
     → APPROVED:            doorgaan
     → CHANGES_REQUESTED:   retry met review loop
     → NEEDS_DISCUSSION:    HITL trigger

6. HITL (indien vereist)
   HitlRequiredEvent gepubliceerd
   State machine pauzeert (ChainStatus.PAUSED)
   Medewerker review in backoffice UI
   HitlResolvedEvent → chain hervat vanaf checkpoint

7. CONTRACT OUTPUT
   FraudAssessmentContract.from_agent_output(raw_output)
   contract.validate() → (True, [])
   recommended_action: ALLOW | REVIEW | BLOCK

8. DECISION JOURNAL & OBSERVABILITY
   DecisionJournal.record(JournalEntry(...))
   ObservabilityCollector.record_request(N1)
   ObservabilityCollector.record_agent(N2)
   ObservabilityCollector.record_business_metric(N3)

9. OUTPUT NAAR BACKOFFICE
   Order goedgekeurd / geblokkeerd / in review
   Merchant notificatie (Wave 5)
   Audit log via OpenTelemetry GenAI spans
```

---

## 11. Key Files — Referentietabel

| Bestand                                  | Module           | Beschrijving                                     |
|------------------------------------------|------------------|--------------------------------------------------|
| `ollama/control_plane.py`                | Control Plane    | Centrale routing, policy, HITL, ring-beslissing  |
| `ollama/policy_engine.py`                | Control Plane    | YAML policy evaluatie, BLOCKER/WARNING/INFO      |
| `ollama/cost_governance.py`              | Control Plane    | Model selectie, budget tracking, escalatie       |
| `ollama/maturity_engine.py`              | Capability Plane | L1-L4 maturity checks per environment            |
| `ollama/capability_registry.py`          | Capability Plane | Capability ↔ lane ↔ model mapping                |
| `ollama/events.py`                       | Event System     | 20+ EventType, DomainEvent, EventBus             |
| `ollama/contracts.py`                    | Domain Contracts | OrderAnalysis, FraudAssessment, ContentGen       |
| `ollama/skill_chain_orchestrator.py`     | Execution Plane  | V3 chains, ChainContext, checkpoint recovery     |
| `ollama/workflow_lanes.py`               | Execution Plane  | 4 lanes: LaneConfig, LANE_REGISTRY, validatie    |
| `ollama/orchestrator.py`                 | Execution Plane  | Legacy orchestrator, ParallelStep                |
| `ollama/state_machine.py`                | Execution Plane  | HITL checkpointing, workflow state               |
| `ollama/agent_runner.py`                 | Execution Plane  | Agent uitvoering, 3-tuple return                 |
| `ollama/agent_groups.py`                 | Agent Fleet      | 6 groepen definitie                              |
| `ollama/quality_gates.py`                | Trust Plane      | QG-FRAUD-01..04, QG-CONTENT-01..03, verdict      |
| `ollama/review_loop.py`                  | Trust Plane      | Review iteraties (max 2), CHANGES_REQUESTED      |
| `ollama/decision_journal.py`             | Trust Plane      | JournalEntry, audit export, summary stats        |
| `ollama/observability.py`                | Trust Plane      | N1/N2/N3 metrics, dashboard snapshot             |
| `ollama/deployment_rings.py`             | Trust Plane      | RingPolicy, RingGateChecker, promotie criteria   |
| `ollama/schema_validator.py`             | Trust Plane      | L1 unit eval, schema compliance                  |
| `ollama/memory.py`                       | Infrastructure   | Context memory, versioned injection              |
| `ollama/skill_loader.py`                 | Infrastructure   | Skill .md bestanden laden                        |
| `ollama/workflow_loader.py`              | Infrastructure   | YAML workflow configs laden                      |
| `ollama/client.py`                       | Infrastructure   | Ollama HTTP client                               |
| `.claude/capabilities/index.yaml`        | Capability Plane | Platform registry, agent_groups, ollama runners  |
| `.claude/capabilities/fraud-detection.yaml` | Capability    | Maturity L3, FraudAssessmentContract, ring-2     |
| `.claude/agents/README.md`               | Agent Fleet      | 6 groepen definitie, skills per groep            |
| `policies/hitl-policies.yaml`            | Policy-as-Code   | HITL-001..003 regels                             |
| `policies/tool-policies.yaml`            | Policy-as-Code   | TOOL-001..002 allow/deny per capability          |
| `policies/maturity-policies.yaml`        | Policy-as-Code   | Maturity-omgeving restricties                    |
| `documentatie/AI_OPTIMALISATIEPLAN_REVISIE5.TXT` | Documentatie | Masterplan Revisie 5, gaps G-32..G-46, Waves 6–8 |
| `documentatie/AI_OPTIMALISATIEPLAN.TXT`  | Documentatie     | Masterplan Revisie 4, gaps G-01..G-31, Waves 1–5 (archief) |

---

## 12. Waves Roadmap

```
WAVE 1 — TRUST FOUNDATION                              [COMPLEET ✅]
────────────────────────────────────────────────────────────────────
  F1-01 ✅  Fix preprompt_ref bug
  F1-02 ✅  ParallelStep implementeren
  F1-03 ✅  schema_validator.py + 3-tuple return
  F1-04 ✅  Tracing integreren in run_workflow
  W1-01 ✅  Control Plane (ollama/control_plane.py)
  W1-02 ✅  Policy-as-Code (/policies/*.yaml)
  W1-03 ✅  Decision Journal (ollama/decision_journal.py)
  F2-07 ✅  Typed event taxonomy (ollama/events.py)
  F2-01 ✅  Typed domain contracts (ollama/contracts.py)
  F2-02 ✅  Quality gates + review_loop.py

WAVE 2 — CONTROL PLANE (routing, HITL, rollout rings)  [COMPLEET ✅]
────────────────────────────────────────────────────────────────────
  F2-04 ✅  Event-driven skill chain orchestrator V3
  W2-01 ✅  Workflow lanes (4 lanes, ollama/workflow_lanes.py)
  W2-02 ✅  Deployment rings in control plane
  W3-02 ✅  Cost & model governance (ollama/cost_governance.py)
  F2-06 ✅  State machine + HITL checkpointing
  W1-04 ✅  Capability maturity model in YAML + maturity_engine.py

WAVE 3 — EXECUTION (agents, tools, context)            [COMPLEET ✅]
────────────────────────────────────────────────────────────────────
  F3-01 ✅  Capability registry uitgebreid
  F3-04 ✅  Agent taxonomie — 6 skill groepen (agent_groups.py)
  F3-05 ✅  ARCHITECTURE.md bijgewerkt
  W4-01 ✅  Observability N3 business metrics (observability.py)
  F3-02 ✅  Domein-skills als SKILL.md folders (.claude/skills/)
  F3-03 ✅  Tool executor (ollama/tool_executor.py)
  F3-06 ✅  Claude agent fleet (49 agents in .claude/agents/)
  F3-07 ✅  validate-agents.mjs
  F3-09 ✅  Memory management + versioned context injection

WAVE 4 — LEARNING (evals, A/B testing, anomaly detection)  [COMPLEET ✅]
────────────────────────────────────────────────────────────────────
  F3-08 ✅  LLM-as-judge evaluatiepipeline (ollama/evals/judge.py)
  W3-01 ✅  4-level evaluation hierarchy
  F4-01 ✅  Automated prompt A/B testing (ollama/ab_tester.py)
  F4-02 ✅  Agent performance analyse (.claude/scripts/*.mjs)
  F4-03 ✅  Quality monitor + evaluation metrics in agent YAMLs
  F4-04 ✅  auto_promoter.py — automatische ring-promotie

WAVE 5 — PRODUCTIE (API, webhooks, portfolio, consultancy) [COMPLEET ✅]
────────────────────────────────────────────────────────────────────
  F5-01 ✅  FastAPI platform (11 routers, JWT auth)
  F5-02 ✅  Next.js portfolio + blog
  F5-03 ✅  32 Ollama runtime agents
  F5-04 ✅  Consultancy tooling (analyse_project.py, klant_rapport_agent)
  F5-05 ✅  MCP server configuratie (7 servers)
  F5-06 ✅  GitHub Actions CI (4 jobs)

═══════════════════════════════════════════════════════════════════
  REVISIE 5 TOEGEVOEGD — Enterprise Consultancy Intelligence Fabriek
  Zie: documentatie/AI_OPTIMALISATIEPLAN_REVISIE5.TXT
═══════════════════════════════════════════════════════════════════

WAVE 6 — INTELLIGENCE FOUNDATIONS                      [COMPLEET ✅]
────────────────────────────────────────────────────────────────────
  W6-01 ✅  ClientProjectSpace + PII Scanner (G-32, G-39)
  W6-02 ✅  SSE Streaming endpoint (G-40)
  W6-03 ✅  AdaptiveChunker (G-34)
  W6-04 ✅  EU AI Act classificatie (G-43)
  W6-05 ✅  CostForecaster (G-41)
  W6-06 ✅  DiagramRenderer (G-37) — geïmplementeerd in Wave 9
  W6-07 ✅  AgentVersioning (G-44) → ollama/agent_versioning.py

WAVE 7 — RAG & KNOWLEDGE GRAPH                         [COMPLEET ✅]
────────────────────────────────────────────────────────────────────
  W7-01 ✅  rag_engine.py + HashEmbedding fallback (G-33)
  W7-02 ✅  KnowledgeGraph JSONB + Mermaid export (G-35)
  W7-03 ✅  MixtureOfAgents — 3 proposers parallel + aggregator
  W7-04 ✅  Sector benchmarks (9 Belgische KMO-sectoren)
  W7-05 ✅  Alembic migration: vector_documents tabel

WAVE 8 — SELF-IMPROVEMENT LOOP                         [COMPLEET ✅]
────────────────────────────────────────────────────────────────────
  W8-01 ✅  agent_versioning.py — DRAFT→SHADOW→CANARY→STABLE→DEPRECATED→ARCHIVED
  W8-02 ✅  Feedback API (POST/GET /api/portal/projects/{id}/feedback)
            + Next.js feedback pagina met sterrenrating
            + Alembic migration: feedback_records tabel
  W8-03 ✅  self_improvement.py — FeedbackAnalyzer + PromptImprovementProposer
            + SelfImprovementLoop (6-staps cyclus)
  W8-04 ✅  recommendation_engine.py — next-best-action via KnowledgeGraph
            REFACTOR/SECURITY/MODERNIZE/PROCESS/COMPLIANCE/TRAINING
  W8-05 ✅  platform_report.py — wekelijks zelf-evaluatierapport (Markdown + JSON)
  W8-06 ✅  ab_tester.py uitgebreid — chi-square p-waarde + auto_beslis_winner()

WAVE 9 — PORTAL, COMPLIANCE & REASONING                [COMPLEET ✅]
────────────────────────────────────────────────────────────────────
  W9-01 ✅  diagram_renderer.py — Mermaid/PlantUML rendering (G-37)
            CLI probe (mmdc/plantuml) + graceful .md fallback
            Frontend: /portal/projects/[id]/diagrams (Mermaid.js + <pre> fallback)
  W9-02 ✅  compliance_engine.py — 4-laags GDPR/NIS2/BTW validator (G-46)
            Laag 1: EU AI Act (HIGH-RISK agents)
            Laag 2: GDPR (rijksregisternummer, bewaartermijn, PII)
            Laag 3: NIS2 (incident keywords, CCN2.be meldplicht)
            Laag 4: Belgian (BTW, herroepingstermijn, taalwetgeving)
            + policies/nis2-policies.yaml (10 maatregelen, P1-P4 classificatie)
  W9-03 ✅  api/routers/portal.py — 6 endpoints (POST/GET projects, status,
            rapport, diagrams, forecasts) + frontend projectlijst/detail
  W9-04 ✅  reasoning_logger.py — CoT-stap extractie + sessie-persistentie
            + Alembic migration: agent_reasoning_logs tabel
            + agent_runner.py update (optionele logging na LLM response)
  W9-05 ✅  auto_promoter.py — FeedbackAnalyzer feedback gate
            dry_run veilig, backward-compatible (gate overgeslagen als unavailable)
  W9-06 ✅  228 nieuwe tests — compliance, diagram, reasoning, portal,
            recommendation, platform (1649 tests totaal, 0 failures)

  ALLE GAPS G-32..G-46 GESLOTEN — REVISIE 5 VOLLEDIG GEÏMPLEMENTEERD ✅
  FUTURE    CostForecaster v2 ML (scikit-learn) — vereist ≥20 historische projecten
  FUTURE    GPU server integratie (gaming desktop als Ollama remote endpoint)
  FUTURE    npm install mermaid (volledige Mermaid.js rendering, nu <pre> fallback)
```

---

## 13. Databases & API



## Databases

### 1. Webshop DB (`vorstersNV`) – Operationeel
PostgreSQL 16 op poort **5432**

| Tabel | Beschrijving |
|-------|-------------|
| `products` | Productcatalogus met voorraad en SEO-velden |
| `categories` | Productcategorieën |
| `customers` | Klantgegevens |
| `orders` | Orders met status-lifecycle |
| `order_items` | Orderregels (product + aantal + prijs) |
| `invoices` | Facturen gekoppeld aan orders |
| `users` | Platform-gebruikers met rollen |
| `agent_logs` | AI-agent interacties (input/output/rating) |

### 2. Analytics DB (`vorstersNV_analytics`) – Ster-schema
PostgreSQL 16 op poort **5433**

```
                    ┌─────────────┐
                    │  dim_date   │
                    └──────┬──────┘
                           │
┌──────────────┐   ┌───────┴──────┐   ┌──────────────┐
│ dim_product  ├───┤ sales_facts  ├───┤ dim_customer  │
└──────────────┘   └───────┬──────┘   └──────────────┘
                           │
              ┌────────────┴──────────────┐
              │       dim_agent           │
              └───────────────────────────┘
                           │
              ┌────────────┴──────────────┐
              │  agent_performance_facts  │
              └───────────────────────────┘
```

**Dimensietabellen:**
- `dim_date` – Datumkalender (YYYYMMDD key) met dag/week/maand/kwartaal/jaar
- `dim_product` – Product snapshot (SCD Type 2 – historisch)
- `dim_customer` – Klantsegmenten en geografie
- `dim_agent` – AI-agent + prompt-versie

**Feitentabellen:**
- `sales_facts` – Verkoopfeiten per orderregel
- `agent_performance_facts` – Agent-prestaties per interactie

## Migraties uitvoeren

```bash
# Webshop DB
alembic -c alembic.ini upgrade head

# Analytics DB
alembic -c alembic_analytics.ini upgrade head
```

## Rollenbeheer

| Rol | Toegang |
|-----|---------|
| `admin` | Alle endpoints, gebruikersbeheer, dashboard |
| `klant` | Eigen orders, profiel, webshop |
| `tester` | Lees-toegang + dashboard + agent-test endpoints |

## API Documentatie

Na `docker-compose up -d` en `uvicorn api.main:app --reload --port 8000`:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
