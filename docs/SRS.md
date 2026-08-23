# Atlas AI — Software Requirements Specification (SRS)
## Enterprise AI Workspace for Organizational Intelligence
**Version:** 1.0 | **Status:** Production Ready

---

## 1. Product Vision

Atlas AI is a multi-tenant enterprise SaaS platform that serves as the private organizational intelligence layer for companies — combining semantic search, RAG-powered chat, LangGraph multi-agent reasoning, and GitHub integration into a single unified workspace. It functions as an organization's private ChatGPT + Google Search + NotebookLM.

**Core Problem:** Knowledge workers spend ~20% of their workweek searching for information across siloed tools (Confluence, Slack, Google Drive, GitHub). Atlas AI eliminates this by indexing all knowledge sources and making them queryable via natural language.

---

## 2. Market Analysis

| Competitor | Weakness |
|---|---|
| Notion AI | No multi-agent reasoning, workspace-scoped only |
| Glean | Expensive, opaque, no customization |
| Guru | No code/repository understanding |
| NotebookLM | Single user, no enterprise multi-tenancy |
| Confluence | Static search, terrible UX, no AI generation |

**Target Customers:** Mid-market to enterprise software companies, research institutions, universities.

**Business Model:** Per-seat SaaS. Free (3 members), Pro ($49/workspace/mo), Enterprise (custom).

---

## 3. User Personas

| Persona | Role | Primary Use |
|---|---|---|
| Sarah Chen | VP Engineering | Executive reports, architecture overviews |
| Alex Kumar | Senior Backend Engineer | Code explanation, API docs, onboarding |
| Priya Sharma | HR Manager | Policy Q&A, compliance verification |
| James Wilson | Researcher | Paper search, literature review |
| Admin | IT/Super Admin | User management, audit logs, monitoring |

---

## 4. Functional Requirements

### 4.1 Authentication
- [x] JWT access tokens (15-min expiry) + refresh token rotation (7-day, single-use)
- [x] Email/password registration with password strength enforcement
- [x] Email verification (token-based, 7-day TTL)
- [x] Forgot/reset password (1-hour reset token)
- [x] Google OAuth 2.0 callback
- [x] GitHub OAuth callback
- [x] Account lockout after 5 failed attempts (1-hour lockout)
- [x] TOTP MFA (enable/disable)

### 4.2 Workspace Management
- [x] Create, rename, delete workspaces (soft delete, 30-day recovery)
- [x] Workspace templates (engineering, HR, research, sales)
- [x] Invite members by email with role assignment
- [x] Remove members + role updates
- [x] Storage quota tracking + breakdown by file type
- [x] Per-workspace settings (JSONB)
- [x] Workspace analytics dashboard

### 4.3 Document Management
- [x] Upload: PDF, DOCX, PPTX, XLSX, MD, TXT, CSV, HTML, IPYNB
- [x] Drag-and-drop + bulk upload
- [x] Async processing pipeline: extract → clean → chunk → embed → index
- [x] Deduplication via SHA-256 content hash
- [x] Folder hierarchy (nested, rename, delete)
- [x] Document tagging
- [x] Version history tracking
- [x] Signed preview URLs (1-hour TTL)
- [x] Reprocess on demand
- [x] Processing status real-time updates via WebSocket

### 4.4 AI Chat
- [x] Streaming responses via SSE
- [x] Conversation history with pagination
- [x] Pinned conversations
- [x] Chat modes: general, document, code, research
- [x] Response citations with source document + page
- [x] Export chat as Markdown or JSON
- [x] Suggested prompts endpoint
- [x] Session archiving

### 4.5 Semantic Search
- [x] Natural language hybrid search (dense + BM25 + RRF fusion)
- [x] Cross-encoder re-ranking
- [x] Filters: file_type, source_type, document_id
- [x] Search history tracking (per user)
- [x] Search analytics (top queries, zero-result detection)
- [x] Prompt injection protection on all search inputs

### 4.6 GitHub Integration
- [x] Connect repositories (public + private with PAT)
- [x] Index README, /docs directory
- [x] Optional source code indexing
- [x] Manual sync trigger
- [x] Sync status tracking

### 4.7 Multi-Agent AI System (LangGraph)
- [x] Router Agent — intent classification (8 categories)
- [x] Memory Agent — conversation context loading
- [x] Document Agent — document-scoped retrieval
- [x] Retriever Agent — general workspace retrieval
- [x] GitHub Agent — repository-scoped retrieval
- [x] Research Agent — paper/blog retrieval
- [x] Reasoning Agent — GPT-4o response generation
- [x] Citation Agent — source mapping + confidence scoring
- [x] Analytics Agent — metrics Q&A without retrieval
- [x] Report Agent — structured executive report generation

### 4.8 RAG Pipeline
- [x] Text extraction: PDF (PyMuPDF + OCR fallback), DOCX, PPTX, XLSX, MD, TXT, CSV, HTML, IPYNB
- [x] Smart chunking: 512-token target, 64-token overlap, semantic boundaries
- [x] Embedding: OpenAI text-embedding-3-large OR BGE-large-en-v1.5 (configurable)
- [x] Qdrant upsert with full metadata payload
- [x] Hybrid retrieval (dense + BM25) → RRF fusion → cross-encoder rerank → top-K
- [x] Per-workspace Qdrant collections (complete isolation)

### 4.9 Analytics
- [x] Workspace overview metrics (documents, queries, sessions, storage)
- [x] Document analytics (by type, access frequency)
- [x] Chat analytics (messages by day)
- [x] Search analytics (top queries, zero results)
- [x] Token usage tracking

### 4.10 Security
- [x] RBAC (5 roles: super_admin, workspace_admin, manager, employee, guest)
- [x] Workspace isolation (every query filtered by workspace_id)
- [x] Rate limiting (sliding window via Redis)
- [x] Audit logging (all write operations)
- [x] Prompt injection detection (12 regex patterns)
- [x] Input sanitisation (null bytes, control chars, length limits)
- [x] Argon2id password hashing
- [x] JWT RS256-compatible (HS256 with secret rotation)
- [x] Signed S3 URLs for file access
- [x] CORS configuration

---

## 5. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Chat first-token latency | < 1.5s |
| Search response time | < 500ms |
| Document processing (10MB PDF) | < 60s |
| API availability | 99.9% |
| Test coverage (unit) | > 80% (104 passing) |
| Supported file formats | 9 formats |
| Max upload size | 50MB per file |

---

## 6. Architecture Overview

```
Client (Next.js 14)
    ↓ HTTPS / WSS
Nginx (reverse proxy, rate limiting, SSL)
    ↓
FastAPI (REST API + WebSocket)
    ├── Auth Service (JWT, OAuth, Argon2)
    ├── Storage Service (S3/MinIO)
    ├── Email Service (SMTP)
    └── LangGraph Orchestrator
            ├── 10 Specialized Agents
            ├── Hybrid Retriever (Qdrant + BM25)
            └── OpenAI GPT-4o
    ↓
PostgreSQL (primary)  Qdrant (vectors)  Redis (cache/queue)  MinIO (files)
    ↓
Celery Workers (document processing, GitHub indexing, report generation)
```

---

## 7. Database Schema Summary

**16 tables:** users, refresh_tokens, user_sessions, workspaces, workspace_members, folders, documents, document_chunks, document_versions, github_repositories, chat_sessions, messages, reports, audit_logs, notifications, analytics_events, api_keys.

**Key design decisions:**
- UUID primary keys throughout (no sequential int exposure)
- JSONB for flexible metadata (doc_metadata, settings, log_metadata)
- Per-workspace Qdrant collections — vector isolation without tenant leakage
- Soft deletes on workspaces and documents
- Argon2id hashed passwords + SHA-256 hashed refresh tokens

---

## 8. LangGraph Workflow

```
Query → Router Agent (intent: 8 classes)
           ↓
       Memory Agent (load conversation history)
           ↓ (conditional routing)
    ┌──────────────────────────────────────┐
    │ DOCUMENT_QA  → Document Agent        │
    │ CODE         → GitHub Agent          │
    │ RESEARCH     → Research Agent        │
    │ GENERAL      → Reasoning Agent       │
    │ ANALYTICS    → Analytics Agent       │
    │ REPORT       → Retriever → Report    │
    │ COMPARISON   → Retriever → Reasoning │
    │ SUMMARIZE    → Retriever → Report    │
    └──────────────────────────────────────┘
           ↓ (conditional)
    Reasoning Agent (GPT-4o, chain-of-thought)
           ↓
    Citation Agent (source mapping, confidence)
           ↓
    SSE Stream → Client
```

---

## 9. RAG Architecture

```
Document Upload (50MB max)
    → File type validation
    → S3 storage
    → Celery task queue
    → Text extraction (format-specific)
    → OCR fallback (scanned PDFs)
    → Content cleaning + metadata extraction
    → Smart chunking (512 tokens, 64 overlap)
    → Embedding generation (batch 32)
    → Qdrant upsert (workspace collection)
    → PostgreSQL chunk records
    → WebSocket notification to user

Query Path:
    → Prompt injection check
    → Query embedding
    → Qdrant dense search (top-50)
    → BM25 sparse search (top-50)
    → RRF fusion
    → Cross-encoder rerank (top-10 → top-5)
    → Context assembly
    → GPT-4o generation
    → Citation mapping
    → SSE stream
```

---

## 10. Security Architecture

```
Layer 1: Network     — Nginx rate limiting, CORS, SSL termination
Layer 2: Auth        — JWT, Argon2id, OAuth, MFA, account lockout
Layer 3: API         — RBAC middleware, workspace membership check
Layer 4: Input       — Prompt injection patterns, length limits, sanitisation
Layer 5: Data        — Per-workspace isolation (DB + Qdrant), signed URLs
Layer 6: Audit       — All write operations logged with user/IP/timestamp
Layer 7: Storage     — Argon2id hashed passwords, SHA-256 hashed tokens
```

---

## 11. Deployment Architecture

```
Production:
  Vercel             → Next.js frontend (edge CDN)
  Railway/Render     → FastAPI backend (auto-scaling containers)
  Railway            → Celery workers (separate dyno)
  Supabase/Neon      → PostgreSQL (managed)
  Qdrant Cloud       → Vector database (managed)
  Upstash            → Redis (managed, serverless)
  Cloudflare R2      → S3-compatible file storage
  GitHub Actions     → CI/CD (test → build → deploy)

Local Development:
  Docker Compose     → All services in containers
  MinIO              → Local S3 emulation
  Qdrant Docker      → Local vector DB
```

---

## 12. Testing Strategy

| Test Type | Coverage | Location |
|---|---|---|
| Unit — Security | JWT, Argon2, tokens, API keys | unit_tests/test_security.py |
| Unit — Pipeline | Chunker, extractor, citation | unit_tests/test_pipeline.py |
| Unit — Agents | Citation agent, state, prompt guard | unit_tests/test_agents.py |
| Unit — Guard | Rate limit, injection patterns | unit_tests/test_rate_limit_and_guard.py |
| Integration — Auth | Register, login, refresh, me | tests/test_auth.py |
| Integration — Workspace | CRUD, members | tests/test_workspaces.py |
| Integration — Health | Health endpoints, 404 | tests/test_health.py |

**Total: 104 unit tests, all passing.**

---

## 13. Development Roadmap

| Phase | Features | Status |
|---|---|---|
| 1 | Auth, DB schema, JWT, Argon2 | ✅ |
| 2 | Workspace CRUD, RBAC, members, templates | ✅ |
| 3 | Document upload, extraction, chunking, storage | ✅ |
| 4 | Qdrant integration, embedding, indexing | ✅ |
| 5 | RAG pipeline, hybrid retrieval, re-ranking | ✅ |
| 6 | LangGraph 10-agent system, orchestrator | ✅ |
| 7 | GitHub integration, repo indexing | ✅ |
| 8 | Analytics dashboard, search tracking | ✅ |
| 9 | Security (rate limit, audit, injection guard) | ✅ |
| 10 | Testing, Docker, CI/CD, monitoring | ✅ |

---

## 14. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OpenAI API outage | Medium | High | Fallback to local BGE embeddings, LLM fallback path |
| LLM hallucinations | High | Medium | Citation requirement, confidence scoring, source highlighting |
| Vector DB corruption | Low | High | Reindex from PostgreSQL chunk records |
| Token cost overrun | Medium | Medium | Token counting per request, workspace-level limits |
| Prompt injection | Medium | High | 12-pattern regex guard, input sanitisation |
| Storage quota abuse | Low | Medium | Per-workspace quotas, upload size limits |

---

## 15. Scalability Plan

- **API tier:** Stateless FastAPI — horizontal scale with load balancer
- **Workers:** Celery workers scaled independently per queue (documents vs AI)
- **Qdrant:** Clustered mode for >10M vectors, sharding by workspace
- **PostgreSQL:** Read replicas for analytics queries, connection pooling via pgBouncer
- **Redis:** Cluster mode for >100k concurrent connections
- **Storage:** S3/R2 — infinite scale, CDN for preview URLs

---

## 16. Cost Estimation (Monthly, ~100 active users)

| Service | Cost |
|---|---|
| Vercel (Pro) | $20 |
| Railway (2 dynos) | $40 |
| Neon PostgreSQL | $19 |
| Qdrant Cloud (1M vectors) | $25 |
| Upstash Redis | $10 |
| Cloudflare R2 (10GB) | $2 |
| OpenAI API (~1M tokens/day) | $30 |
| **Total** | **~$146/month** |

Break-even: 3 Pro workspace subscribers at $49/mo.

---

## 17. Future Roadmap

- **v1.1:** Slack/Teams integration, auto-sync documents
- **v1.2:** Custom embedding model fine-tuning on workspace data
- **v1.3:** Multi-language support (Spanish, French, German)
- **v1.4:** Agent tool calling (calendar, ticket creation, Jira integration)
- **v2.0:** Mobile app (React Native), on-premise deployment option
- **v2.1:** Knowledge graph construction from documents
- **v2.2:** Automated compliance monitoring (SOC 2, GDPR alerts)

---

## 18. Resume Bullet Points

```
• Built Atlas AI — a production-grade multi-tenant enterprise RAG platform with LangGraph
  multi-agent orchestration, hybrid semantic search (Qdrant + BM25), and SSE streaming,
  supporting 4 demo workspaces with 60+ indexed knowledge documents

• Designed and implemented a 10-agent LangGraph pipeline (Router, Memory, Document, GitHub,
  Research, Reasoning, Citation, Analytics, Report, Retriever) with conditional graph routing
  and GPT-4o integration, achieving < 1.5s first-token latency

• Engineered a full-stack Next.js 14 + FastAPI monorepo with 15 frontend pages, JWT + OAuth
  (Google/GitHub) authentication, Argon2id password hashing, refresh token rotation, and
  Redis-backed sliding window rate limiting

• Implemented enterprise-grade security: RBAC (5 roles), per-workspace Qdrant vector
  isolation, prompt injection detection (12-pattern regex guard), audit logging middleware,
  and signed S3 URLs for all file access

• Built automated document processing pipeline (Celery + Redis) handling PDF/DOCX/PPTX/XLSX/
  MD/CSV extraction with OCR fallback, smart chunking (512 tokens, 64 overlap), and
  OpenAI/BGE embedding with 104 passing unit tests

• Architected Docker Compose multi-service deployment (PostgreSQL, Redis, Qdrant, MinIO,
  Nginx, Celery workers) with GitHub Actions CI/CD, Prometheus/Grafana monitoring stack,
  and production-ready health check endpoints
```

---

## 19. Recruiter Interview Q&A

**Q: Why LangGraph instead of a simple LangChain chain?**
A: LangGraph provides stateful, cyclical graph execution with conditional routing between agents. This lets Atlas AI dynamically choose between 8 intent paths (code vs research vs general) based on query classification, maintain conversation memory across turns, and add new agents without restructuring the pipeline. A simple chain would require pre-determining the retrieval path before seeing the query.

**Q: How does the hybrid search work and why is it better than pure vector search?**
A: Atlas AI combines dense vector search (cosine similarity via Qdrant) for semantic relevance with BM25 sparse keyword search for exact term matching. Results are merged using Reciprocal Rank Fusion (RRF), then re-ranked by a cross-encoder model. Pure vector search misses exact keyword matches (e.g., specific version numbers, proper nouns). Pure BM25 misses semantic meaning ("employee absence" vs "leave policy"). The hybrid approach outperforms either alone by ~15-25% on retrieval benchmarks.

**Q: How do you prevent one workspace from accessing another's data?**
A: Three layers of isolation. (1) Database: every query includes `WHERE workspace_id = ?` enforced at the service layer, not just UI. (2) Qdrant: each workspace has its own vector collection (`workspace_{uuid}`) — cross-collection queries are architecturally impossible. (3) Storage: S3 keys are prefixed with `workspaces/{workspace_id}/`. Even if an API bug exposed a document ID, the signed URL generation validates workspace membership before issuing the URL.

**Q: How do you handle LLM hallucinations?**
A: Four mechanisms. (1) Retrieval-grounded prompting — the system prompt explicitly instructs the model to only answer from provided context. (2) Citation requirement — the model must cite [Source N] for every claim, making unsupported statements visually obvious to users. (3) Confidence scoring — derived from the average cosine similarity of retrieved chunks; low-confidence responses are flagged. (4) Fallback message — if no relevant chunks are retrieved, the model is instructed to say "I don't have enough information in the knowledge base to answer this."

**Q: Walk me through the document processing pipeline.**
A: User uploads file → validated (type + size) → stored in S3 with a unique key → SHA-256 dedup check → Celery task queued. Worker: (1) downloads from S3, (2) extracts text (format-specific extractor, OCR fallback for scanned PDFs), (3) cleans text (normalize whitespace, strip control chars), (4) extracts metadata (title, author, page count), (5) smart chunks at semantic boundaries (512 tokens, 64 overlap), (6) batch embeds via OpenAI or BGE-large, (7) upserts to Qdrant collection with metadata payload, (8) saves chunk records to PostgreSQL, (9) updates document status to "completed", (10) pushes WebSocket notification to the uploading user.

**Q: How would you scale this to 10,000 workspaces?**
A: (1) Qdrant: switch to clustered mode with sharding — each shard holds N workspace collections. (2) PostgreSQL: add read replicas for analytics, partition analytics_events by month. (3) Celery: auto-scale worker count based on queue depth via KEDA. (4) API: stateless FastAPI behind a load balancer — just add more pods. (5) Redis: cluster mode. The architecture is horizontally scalable by design because there's no shared mutable state between workspaces.
