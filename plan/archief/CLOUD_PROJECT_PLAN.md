# 🚀 VorstersNV Cloud Platform 2.0 – Next-Generation Plan

**Modern, scalable, multi-tenant AI-powered business platform with MCP integration**

**Author**: Koen Vorsters  
**Date**: April 18, 2026  
**Status**: Planning Phase  
**Target Deployment**: AWS / Azure / Google Cloud (with Docker + Kubernetes)

---

## 📌 Executive Summary

VorstersNV Cloud Platform 2.0 is a **next-generation, multi-tenant SaaS platform** that extends the current local VorstersNV with:

- ✅ **Cloud-native architecture** (microservices + serverless functions)
- ✅ **AI Agent Framework** with MCP (Model Context Protocol) support
- ✅ **Multi-tenant isolation** with data & resource boundaries
- ✅ **Real-time collaboration** (WebSockets + Redis Streams)
- ✅ **Advanced analytics & AI-powered insights**
- ✅ **Scalable deployment** (Kubernetes on AWS/Azure/GCP)
- ✅ **Enterprise security** (OAuth2 + RBAC + encryption)
- ✅ **Marketplace for AI agents** (community-driven)

---

## 🎯 Project Goals

| Goal | Impact | Priority |
|------|--------|----------|
| **Multi-tenant SaaS** | Serve 1000+ businesses | 🔴 Critical |
| **MCP-based AI agents** | Standardized, composable agents | 🔴 Critical |
| **Cloud scalability** | Auto-scaling, zero downtime | 🔴 Critical |
| **Real-time features** | Live dashboards, WebSockets | 🟠 High |
| **Agent marketplace** | Community contributions | 🟡 Medium |
| **Advanced analytics** | BI dashboards, predictions | 🟡 Medium |
| **API-first design** | Webhooks, event streaming | 🔴 Critical |

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                   VorstersNV Cloud Platform 2.0                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │    Web Layer    │  │   Mobile Apps   │  │  Admin Portal   │  │
│  │  (Next.js SSR)  │  │  (React Native) │  │  (Dashboard)    │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │            │
│           └────────────────────┼────────────────────┘            │
│                                │                                 │
│                     ┌──────────▼──────────┐                     │
│                     │  API Gateway / CDN  │                     │
│                     │  (CloudFlare / AWS) │                     │
│                     └──────────┬──────────┘                     │
│                                │                                 │
│           ┌───────────────────┼───────────────────┐             │
│           │                   │                   │             │
│     ┌─────▼──────┐      ┌────▼─────┐      ┌────▼─────┐       │
│     │  REST API  │      │ gRPC API │      │ WebSocket│       │
│     │ (FastAPI)  │      │ Services │      │ (Real-   │       │
│     │ (Async)    │      │          │      │ time)    │       │
│     └─────┬──────┘      └────┬─────┘      └────┬─────┘       │
│           │                  │                  │              │
│           └──────────────────┼──────────────────┘              │
│                              │                                 │
│                    ┌─────────▼─────────┐                      │
│                    │  MCP Agent Layer  │                      │
│                    │  ┌──────────────┐ │                      │
│                    │  │ Built-in     │ │                      │
│                    │  │ - CRM Agent  │ │                      │
│                    │  │ - SEO Agent  │ │                      │
│                    │  │ - Analytics  │ │                      │
│                    │  └──────────────┘ │                      │
│                    │  ┌──────────────┐ │                      │
│                    │  │ MCP Servers  │ │                      │
│                    │  │ - Custom     │ │                      │
│                    │  │ - Community  │ │                      │
│                    │  └──────────────┘ │                      │
│                    └─────────┬─────────┘                      │
│                              │                                 │
│     ┌────────────────────────┼────────────────────────┐       │
│     │                        │                        │       │
│  ┌──▼──┐  ┌──────┐  ┌──────▼────┐  ┌───────┐  ┌────▼──┐   │
│  │ LLM │  │Vector│  │ Messaging │  │ Event │  │ Cache │   │
│  │Cloud│  │  DB  │  │  Queue    │  │Stream │  │(Redis)│   │
│  │     │  │(Pinc)│  │(RabbitMQ) │  │(Kafka)│  │       │   │
│  └─────┘  └──────┘  └───────────┘  └───────┘  └───────┘   │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │ Data Layer     │  │ Storage        │  │ Monitoring   │ │
│  │ ┌────────────┐ │  │ ┌────────────┐ │  │ ┌──────────┐ │ │
│  │ │PostgreSQL  │ │  │ │S3 / GCS    │ │  │ │Datadog   │ │ │
│  │ │(Multi-DB) │ │  │ │MinIO       │ │  │ │ELK Stack │ │ │
│  │ └────────────┘ │  │ └────────────┘ │  │ └──────────┘ │ │
│  │ ┌────────────┐ │  │ ┌────────────┐ │  │ ┌──────────┐ │ │
│  │ │MongoDB     │ │  │ │Backup Tier │ │  │ │Prometheus│ │ │
│  │ │(Multi-doc) │ │  │ └────────────┘ │  │ └──────────┘ │ │
│  │ └────────────┘ │  │                 │  │              │ │
│  └────────────────┘  └────────────────┘  └──────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │  Cloud Infrastructure │
                    │  ┌────────────────┐ │
                    │  │ Kubernetes     │ │
                    │  │ + ArgoCD       │ │
                    │  └────────────────┘ │
                    │  ┌────────────────┐ │
                    │  │ Auto-Scaling   │ │
                    │  │ Load Balancing │ │
                    │  └────────────────┘ │
                    │  ┌────────────────┐ │
                    │  │ Service Mesh   │ │
                    │  │ (Istio)        │ │
                    │  └────────────────┘ │
                    └─────────────────────┘
```

---

## 🛠️ Technology Stack

### Core Services
| Service | Technology | Purpose |
|---------|-----------|---------|
| **Frontend** | Next.js 16+ (SSR/SSG) | Web app with real-time updates |
| **Mobile** | React Native / Flutter | iOS + Android apps |
| **API Gateway** | FastAPI + uvicorn | High-performance async REST API |
| **gRPC** | Python gRPC | Inter-service communication |
| **Real-time** | WebSockets + Redis | Live dashboards, chat, notifications |
| **AI/ML Framework** | MCP + Ollama (local) + Claude API | Agent orchestration |

### Data & Storage
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Transactional DB** | PostgreSQL 16 (read replicas) | Core business data |
| **Document Store** | MongoDB | Flexible schemas, logs |
| **Vector DB** | Pinecone / Weaviate | Embeddings, semantic search |
| **Cache** | Redis Cluster | Session, cache, real-time data |
| **Message Queue** | RabbitMQ / Redis Streams | Async tasks |
| **Event Streaming** | Kafka / AWS Kinesis | Audit, analytics |
| **Object Storage** | S3 / Google Cloud Storage | Files, backups |

### Infrastructure
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Container Orchestration** | Kubernetes (EKS/AKS/GKE) | Cluster management |
| **CI/CD** | GitHub Actions + ArgoCD | Automated deployments |
| **Monitoring** | Datadog / ELK Stack | Logs, metrics, alerts |
| **Service Mesh** | Istio | Traffic, security, observability |
| **DNS / CDN** | CloudFlare / AWS CloudFront | Global distribution |
| **Infrastructure-as-Code** | Terraform | Cloud resources |

### AI & Agents
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **MCP Server** | Python MCP SDK | Standardized agent interface |
| **Built-in Agents** | Python + Prompt Templates | CRM, SEO, Analytics, Support |
| **LLM Backend** | Claude API + Ollama | Fast inference + local fallback |
| **Agent Orchestration** | Async TaskQueue | Parallel execution, workflows |
| **Prompt Management** | Versioning + A/B tests | Continuous optimization |
| **Agent Marketplace** | GitHub Packages | Community contributions |

---

## 📦 Microservices Architecture

### 1️⃣ **API Service** (FastAPI)
```
/api
├── /auth              # JWT + OAuth2 + MFA
├── /tenants           # Multi-tenant management
├── /users             # User management + RBAC
├── /products          # Product catalog
├── /orders            # Order processing
├── /inventory         # Stock management
├── /payments          # Mollie + Stripe integration
├── /notifications     # Email, SMS, push
├── /agents            # AI agent control
├── /analytics         # Business intelligence
└── /webhook           # Inbound webhooks
```

### 2️⃣ **Agent Service** (MCP Servers)
```
Built-in Agents:
- crm_agent            # Customer relationship management
- seo_agent            # Search engine optimization
- analytics_agent      # Business analytics & insights
- support_agent        # Customer support automation
- marketing_agent      # Campaign automation
- inventory_agent      # Stock optimization

MCP Protocol:
- Agent discovery      # List available agents
- Tool calling         # Execute agent tools
- Resource management  # Access files, data, APIs
- Sampling + prompting # Custom LLM interactions
```

### 3️⃣ **Real-time Service** (WebSocket + gRPC)
```
Features:
- Live dashboard      # Real-time KPIs
- Notifications       # Push notifications
- Collaborative edit  # Multi-user workspaces
- Order tracking      # Live order status
```

### 4️⃣ **Background Jobs** (Celery + Redis)
```
Jobs:
- Order processing    # Async order fulfillment
- Email campaigns     # Bulk email sending
- Inventory sync      # Stock level updates
- Analytics pipeline  # Data warehouse ETL
- Report generation   # PDF exports
- Backup jobs         # Data backups
```

### 5️⃣ **Analytics Service** (Postgres + Kafka)
```
Pipeline:
Events → Kafka → Stream Processor → Data Warehouse → BI Dashboard
  ↓
Real-time dashboards (Grafana / Superset)
```

---

## 🔐 Security & Multi-Tenancy

### Multi-Tenant Isolation
```
┌─────────────────────────────────────────────┐
│ Tenant A (tenant_id: uuid)                  │
├─────────────────────────────────────────────┤
│ - Isolated database schema                  │
│ - Separate S3 bucket prefix                 │
│ - Row-level security (RLS) on all tables   │
│ - Unique Redis key namespace                │
│ - Custom domain or subdomain                │
└─────────────────────────────────────────────┘

Each query includes: WHERE tenant_id = :tenant_id
```

### Authentication & Authorization
```
OAuth2 + JWT + MFA:
1. User logs in (email + password + MFA code)
2. Returns JWT token (access + refresh)
3. Every API call: Authorization: Bearer <jwt>
4. JWT payload: { tenant_id, user_id, roles, permissions }
5. RBAC: roles = [admin, manager, employee, customer]
6. Fine-grained: permissions per API endpoint
```

### Encryption
```
Data at rest:  AES-256 (PostgreSQL, S3)
Data in transit: TLS 1.3
Secrets:       AWS Secrets Manager / HashiCorp Vault
API Keys:      Bcrypt hashing
```

---

## 🤖 AI Agent Framework (MCP-Based)

### MCP Architecture

```python
# Built-in MCP Agent Example

class CRMAgent:
    """MCP Agent for customer relationship management"""
    
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
        self.llm = AnthropicAPI(model="claude-3.5-sonnet")
    
    # MCP Tools: Discoverable via protocol
    @mcp_tool
    async def search_customers(self, query: str) -> List[Customer]:
        """Search customers by name, email, phone"""
        return await db.query_customers(self.tenant_id, query)
    
    @mcp_tool
    async def create_customer(self, email: str, name: str) -> Customer:
        """Create new customer"""
        return await db.create_customer(self.tenant_id, email, name)
    
    @mcp_tool
    async def get_customer_orders(self, customer_id: UUID) -> List[Order]:
        """Get all orders for a customer"""
        return await db.get_orders(self.tenant_id, customer_id)
    
    # MCP Resource Access
    @mcp_resource
    async def get_crm_templates(self) -> List[EmailTemplate]:
        """Access CRM email templates"""
        return await db.get_templates(self.tenant_id)
    
    # Main agent workflow
    async def run(self, user_message: str) -> str:
        """Main MCP agent entry point"""
        # Claude sees available tools via MCP discovery
        response = await self.llm.agentic_loop(
            messages=[{"role": "user", "content": user_message}],
            tools=self.get_mcp_tools(),
            system_prompt=self.system_prompt
        )
        return response
```

### Built-in Agents

| Agent | Purpose | MCP Tools |
|-------|---------|-----------|
| **CRM Agent** | Customer data, sales pipeline | search_customers, create_customer, update_notes, get_orders |
| **SEO Agent** | Content optimization, keywords | analyze_seo, suggest_keywords, generate_meta, check_rankings |
| **Analytics Agent** | Business insights, forecasting | get_kpis, forecast_revenue, analyze_trends, export_report |
| **Support Agent** | Customer support automation | search_knowledge_base, create_ticket, send_email, get_chat_history |
| **Marketing Agent** | Campaign automation | create_campaign, send_email, schedule_post, analyze_engagement |
| **Inventory Agent** | Stock optimization | get_stock_levels, forecast_demand, reorder_products, set_alerts |

### Agent Marketplace

```
Agents can be shared via:
1. GitHub Packages (NPM-like registry for agents)
2. Docker images (packaged MCP servers)
3. Community templates (prompt + config)

Discovery:
- List community agents: GET /api/agents/marketplace
- Install agent: POST /api/agents/{agent_id}/install
- Publish agent: POST /api/agents/publish
```

---

## 📊 Data Model (Multi-Tenant)

### Core Tables

```sql
-- Multi-tenant core
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    domain VARCHAR UNIQUE,
    plan VARCHAR (free|pro|enterprise),
    created_at TIMESTAMP,
    status VARCHAR (active|suspended|deleted),
    row_security_policy: TRUE  -- RLS enabled
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR UNIQUE,
    roles TEXT[] (admin|manager|employee|customer),
    permissions JSONB,
    created_at TIMESTAMP,
    CONSTRAINT rls_tenant CHECK (tenant_id IS NOT NULL)
);

-- Business data (tenant-scoped)
CREATE TABLE customers (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR,
    name VARCHAR,
    created_at TIMESTAMP,
    CONSTRAINT rls_tenant CHECK (tenant_id IS NOT NULL)
);

CREATE TABLE products (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    name VARCHAR,
    price DECIMAL,
    stock INT,
    created_at TIMESTAMP,
    CONSTRAINT rls_tenant CHECK (tenant_id IS NOT NULL)
);

CREATE TABLE orders (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    customer_id UUID,
    status VARCHAR,
    total DECIMAL,
    created_at TIMESTAMP,
    CONSTRAINT rls_tenant CHECK (tenant_id IS NOT NULL)
);

-- AI Agent data
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    agent_name VARCHAR,
    input TEXT,
    output TEXT,
    status VARCHAR (success|error|timeout),
    tokens_used INT,
    cost DECIMAL,
    created_at TIMESTAMP,
    CONSTRAINT rls_tenant CHECK (tenant_id IS NOT NULL)
);

CREATE TABLE agent_tools_log (
    id UUID PRIMARY KEY,
    agent_run_id UUID REFERENCES agent_runs(id),
    tool_name VARCHAR,
    input JSONB,
    output JSONB,
    duration_ms INT,
    created_at TIMESTAMP
);

-- Real-time updates
CREATE TABLE event_log (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    event_type VARCHAR,
    entity_type VARCHAR,
    entity_id UUID,
    changes JSONB,
    user_id UUID,
    created_at TIMESTAMP,
    CONSTRAINT rls_tenant CHECK (tenant_id IS NOT NULL)
);
```

---

## 📈 Project Phases (24 Months)

### Phase 1: Foundation & Cloud Setup (Months 1-3)
**Goal**: Establish cloud infrastructure and MCP foundation

- [ ] **Cloud Infrastructure Setup**
  - [ ] AWS/GCP/Azure account setup
  - [ ] Kubernetes cluster (EKS/AKS/GKE)
  - [ ] PostgreSQL with read replicas
  - [ ] Redis cluster
  - [ ] S3 / Object storage
  - [ ] CDN + API Gateway

- [ ] **Multi-Tenant Architecture**
  - [ ] Database schema with RLS
  - [ ] Tenant isolation strategy
  - [ ] OAuth2 + MFA implementation
  - [ ] Billing system (Stripe integration)

- [ ] **MCP Foundation**
  - [ ] MCP Python SDK integration
  - [ ] First MCP server (CRM Agent)
  - [ ] Tool discovery mechanism
  - [ ] Agent registry

- [ ] **DevOps & Monitoring**
  - [ ] GitHub Actions CI/CD
  - [ ] ArgoCD deployment pipeline
  - [ ] ELK Stack / Datadog monitoring
  - [ ] Prometheus metrics

**Deliverables:**
- Kubernetes cluster running in production
- Multi-tenant database with RLS
- First MCP agent (CRM)
- Monitoring dashboard
- CI/CD pipeline

---

### Phase 2: Core Services & Agents (Months 4-8)
**Goal**: Build all microservices and core AI agents

- [ ] **API Service**
  - [ ] REST endpoints (FastAPI)
  - [ ] gRPC services
  - [ ] WebSocket real-time
  - [ ] Rate limiting & throttling
  - [ ] Request validation

- [ ] **AI Agents (MCP-based)**
  - [ ] SEO Agent (with tools)
  - [ ] Analytics Agent (with tools)
  - [ ] Support Agent (with tools)
  - [ ] Marketing Agent (with tools)
  - [ ] Inventory Agent (with tools)

- [ ] **Background Jobs**
  - [ ] Celery + Redis task queue
  - [ ] Email service
  - [ ] Async processing
  - [ ] Job scheduling (APScheduler)

- [ ] **Real-time Features**
  - [ ] WebSocket server
  - [ ] Redis Streams for messaging
  - [ ] Live dashboard
  - [ ] Notifications system

**Deliverables:**
- Full-featured REST API
- 5 production MCP agents
- Real-time dashboard
- Background job system
- Notification service

---

### Phase 3: Frontend & Mobile (Months 9-13)
**Goal**: Build web and mobile applications

- [ ] **Next.js Web App**
  - [ ] Dashboard (real-time KPIs)
  - [ ] Admin panel (tenant management)
  - [ ] Customer portal
  - [ ] Agent control panel
  - [ ] Analytics visualization

- [ ] **React Native Mobile App**
  - [ ] iOS + Android versions
  - [ ] Real-time notifications
  - [ ] Order tracking
  - [ ] Customer portal

- [ ] **Agent Marketplace Frontend**
  - [ ] Browse available agents
  - [ ] Install / uninstall agents
  - [ ] Agent configuration UI
  - [ ] Community ratings

**Deliverables:**
- Web app (30+ pages)
- Mobile app (iOS + Android)
- Agent marketplace
- Real-time dashboards

---

### Phase 4: Advanced Features (Months 14-18)
**Goal**: Enterprise features and AI optimization

- [ ] **Advanced Analytics**
  - [ ] Data warehouse (Snowflake / BigQuery)
  - [ ] BI dashboards (Superset / Looker)
  - [ ] Predictive models
  - [ ] Anomaly detection

- [ ] **Agent Optimization**
  - [ ] A/B testing prompts
  - [ ] Fine-tuned models (per tenant)
  - [ ] Agent marketplace (community)
  - [ ] Feedback loops

- [ ] **Integration Hub**
  - [ ] Webhooks (incoming + outgoing)
  - [ ] Zapier / Make integration
  - [ ] Third-party APIs (Shopify, WooCommerce)
  - [ ] Data sync pipelines

- [ ] **Compliance & Security**
  - [ ] SOC2 Type II audit
  - [ ] GDPR compliance tools
  - [ ] Data export / deletion
  - [ ] Audit logs

**Deliverables:**
- Advanced analytics platform
- Agent A/B testing system
- Marketplace with 50+ agents
- Integration hub (10+ integrations)
- SOC2 compliance

---

### Phase 5: Scalability & Optimization (Months 19-24)
**Goal**: Enterprise-grade scalability and performance

- [ ] **Performance Optimization**
  - [ ] Database query optimization
  - [ ] Caching strategies
  - [ ] Load testing & tuning
  - [ ] CDN optimization

- [ ] **Scale to Enterprise**
  - [ ] Multi-region deployment
  - [ ] High availability (99.99%)
  - [ ] Disaster recovery
  - [ ] Geographic redundancy

- [ ] **ML/AI Enhancements**
  - [ ] Custom model training
  - [ ] Vector DB (Pinecone / Weaviate)
  - [ ] Semantic search
  - [ ] Recommendation engine

- [ ] **Go-to-Market**
  - [ ] Partner program
  - [ ] Enterprise sales
  - [ ] Community building
  - [ ] Documentation + tutorials

**Deliverables:**
- Multi-region deployment
- Enterprise SLA (99.99% uptime)
- Custom model training
- Partner ecosystem
- 10K+ users

---

## 🔄 Development Workflow

### Local Development
```bash
# Dev environment with Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# Environment setup
cp .env.example .env
source venv/bin/activate
pip install -r requirements-dev.txt

# Start backend
uvicorn api.main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Run tests
pytest tests/ -v --cov

# MCP agent testing
python scripts/test_mcp_agent.py crm_agent
```

### CI/CD Pipeline
```
Git push → GitHub Actions
  ├─ Run tests
  ├─ Lint code
  ├─ Security scan
  ├─ Build Docker images
  ├─ Push to registry
  └─ Deploy via ArgoCD
      ├─ Staging first
      ├─ Approval gate
      └─ Production
```

### Git Strategy
```
main (production)
├─ staging (pre-production)
│  └─ feature/... (development)
├─ develop (integration)
└─ hotfix/... (emergency)

Commit message format:
[<type>/<scope>] <description>
Examples:
- [feat/agents] Add CRM agent
- [fix/api] Fix pagination bug
- [docs/readme] Update setup guide
```

---

## 📚 Key Files Structure

```
VorstersNV-Cloud/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Test & lint
│       ├── build.yml           # Docker build
│       └── deploy.yml          # ArgoCD deploy
├── infra/
│   ├── terraform/              # IaC for cloud
│   ├── kubernetes/             # K8s manifests
│   └── helm/                   # Helm charts
├── services/
│   ├── api/                    # FastAPI service
│   ├── agents/                 # MCP agents
│   ├── realtime/               # WebSocket service
│   └── jobs/                   # Background jobs
├── frontend/
│   ├── web/                    # Next.js app
│   └── mobile/                 # React Native
├── shared/
│   ├── schemas/                # Pydantic models
│   ├── types/                  # TypeScript types
│   └── utils/                  # Shared utilities
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
├── docs/
│   ├── api/                    # OpenAPI docs
│   ├── agents/                 # Agent documentation
│   └── deployment/             # Deployment guide
└── docker-compose.dev.yml      # Local development
```

---

## 🎯 Success Metrics

| Metric | Target | Timeline |
|--------|--------|----------|
| **Platform Uptime** | 99.99% | Month 12 |
| **API Latency (p99)** | < 500ms | Month 12 |
| **Agent Success Rate** | > 95% | Month 10 |
| **Time to Deploy** | < 5 minutes | Month 9 |
| **Test Coverage** | > 80% | Month 6 |
| **Active Tenants** | 100+ | Month 12 |
| **Agent Marketplace** | 50+ agents | Month 18 |
| **Monthly Active Users** | 10,000+ | Month 24 |

---

## 🚀 Quick Start (When Building)

```bash
# Clone project
git clone https://github.com/koenvorster/VorstersNV-Cloud
cd VorstersNV-Cloud

# Environment setup
cp .env.example .env
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements-dev.txt

# Database setup
docker-compose -f docker-compose.dev.yml up -d postgres redis
alembic upgrade head

# Start development
make dev  # Runs: API + frontend + agents

# Run tests
make test

# Deploy to staging
make deploy-staging
```

---

## 📞 Contact & Support

- **GitHub**: https://github.com/koenvorster
- **Email**: koen@vorsters.nl
- **Documentation**: /docs
- **Status Page**: https://status.vorsters.nl

---

## 📄 License

Proprietary - All rights reserved © 2026 Koen Vorsters

---

**Last Updated**: April 18, 2026  
**Next Review**: May 15, 2026
