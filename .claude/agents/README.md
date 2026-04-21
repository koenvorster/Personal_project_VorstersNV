# VorstersNV Agent Fleet — Skill Group Taxonomy

## Architectuur

Het VorstersNV AI platform organiseert zijn agents in 6 functionele groepen,
gebaseerd op het V3 architectuurmodel (event-driven, context-driven orchestratie).

```
[LEAD ORCHESTRATOR]
        ↓
┌───────────────────────────────────────────────────────────┐
│  GROUP 1         │  GROUP 2         │  GROUP 3            │
│  DEV INTELLIGENCE│  TEST INTELLIGENCE│  E-COMMERCE VALID. │
└───────────────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────────────┐
│  GROUP 4         │  GROUP 5         │  GROUP 6            │
│  RISK & DECISION │  EXPLANATION     │  AUDIT              │
└───────────────────────────────────────────────────────────┘
```

## Group 1: DEV Intelligence
**Doel:** Begrijpen wat er verandert in de codebase

Agents:
- `ai-architect` — architectuuranalyse en ADR documentatie
- `feature-worker` — feature implementatie
- `fastapi-developer` — FastAPI backend
- `nextjs-developer` — Next.js frontend
- `ollama-agent-designer` — agent ontwerp

Skills: analyze_code_changes, map_changes_to_business_logic, detect_regression_scope

## Group 2: Test Intelligence
**Doel:** Testen verbeteren en versnellen

Agents:
- `test-orchestrator` — test coördinatie
- `ci-debugger` — CI/CD debugging

Skills: validate_acceptance_criteria, generate_advanced_test_cases, detect_regression_risk

## Group 3: E-Commerce Validation
**Doel:** Output controleren en valideren

Agents:
- `order-analyst` — orderverwerking en BTW validatie
- `fraud-advisor` — fraude detectie

Skills: compare_with_previous_run, detect_salary_anomalies, validate_legal_rules

## Group 4: Risk & Decision
**Doel:** Prioritiseren en beslissen

Agents:
- `fraud-advisor` — risicoclassificatie (dual role)
- `lead-orchestrator` — beslissingsrouting

Skills: classify_payroll_risk, assess_release_risk, suggest_prc_actions

## Group 5: Explanation
**Doel:** Vertrouwen en begrijpbaarheid

Agents:
- `klantenservice-coach` — klantenservice begeleiding
- `product-writer` — productcontent generatie
- `mr-reviewer` — code review uitleg

Skills: explain_salary_difference, explain_code_to_non_dev

## Group 6: Audit
**Doel:** Compliance, GDPR, traceability

Agents:
- `audit-reporter` — audit trails en compliance
- `gdpr-advisor` — GDPR begeleiding
- `db-explorer` — data access audit

Skills: audit_trace_generator, decision_logging
