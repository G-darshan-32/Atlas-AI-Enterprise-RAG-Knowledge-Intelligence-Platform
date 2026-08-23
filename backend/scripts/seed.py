"""
Seed script: creates demo workspaces, users, and sample documents.
Run: python scripts/seed.py
"""
import asyncio
import uuid
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.document import Document, Folder, DocumentChunk

DEMO_DOCUMENT_CHUNKS = {
    "Employee Handbook": [
        "TechNova Employee Handbook 2024: Welcome to TechNova! Our core working hours are 10:00 AM to 4:00 PM EST. All full-time employees are eligible for full health benefits, 401(k) matching up to 5%, annual learning stipends ($1,500/year), and wellness allowances.",
        "Code of Conduct & Remote Work: TechNova supports a hybrid work culture. Remote employees receive a $500 home-office setup stipend. Professionalism, mutual respect, data confidentiality, and security compliance are mandatory."
    ],
    "Leave Policy 2024": [
        "TechNova Leave Policy 2024: Full-time employees receive 20 days of Paid Time Off (PTO) per calendar year, accrued monthly at 1.67 days/month. PTO requests should be submitted at least 2 weeks in advance for planned leave.",
        "Sick Leave & Holidays: Employees receive 5 dedicated paid sick leave days per year. In addition, TechNova observes 10 paid official holidays annually. Parental leave provides up to 12 weeks of fully paid leave for primary caregivers."
    ],
    "HR Policy Manual": [
        "TechNova HR Policy Manual: Standard procedures for performance management, bi-annual reviews (June & December), promotion criteria, expense reimbursements, and anti-harassment reporting mechanisms."
    ],
    "Backend Architecture Guide": [
        "Backend Architecture: TechNova services are built with Python 3.11, FastAPI for high-performance async REST API routes, SQLAlchemy 2.0 async ORM, PostgreSQL database, Redis caching, Celery task queue, and Qdrant vector search."
    ],
    "Frontend Architecture Guide": [
        "Frontend Architecture: Built with Next.js 14 App Router, React 18, TypeScript, TailwindCSS for styling, React Query for server state management, and Zustand for persistent client authentication state."
    ],
    "Database Design Document": [
        "Database Design: Enterprise PostgreSQL 16 schema design utilizing workspace-level isolation, UUID primary keys, JSONB metadata indexing, and vector embeddings stored in Qdrant collections."
    ],
    "Authentication Implementation Guide": [
        "Authentication Guide: Secure JWT access tokens (15 min expire) paired with HTTP-only refresh tokens. Password hashing using bcrypt. Support for Google OAuth and GitHub OAuth integrations."
    ]
}

def get_demo_chunk_text(title: str) -> list[str]:
    if title in DEMO_DOCUMENT_CHUNKS:
        return DEMO_DOCUMENT_CHUNKS[title]
    return [
        f"{title}: Key documentation for {title} covering operational procedures, specifications, standards, and guidelines for team members across the organization.",
        f"{title} Details: Section 2 outlines detailed implementation rules, configuration settings, reference standards, and maintenance guidelines."
    ]

from app.models.chat import ChatSession, Message


NOW = datetime.datetime.now(datetime.timezone.utc)


WORKSPACES_DATA = [
    {
        "name": "TechNova Software",
        "slug": "technova-software",
        "description": "Internal knowledge base for TechNova engineering, HR, and operations",
        "tier": "enterprise",
        "folders": ["Engineering", "HR & Policies", "Operations", "Release Notes"],
        "documents": [
            ("Employee Handbook", "pdf", "HR & Policies"),
            ("HR Policy Manual", "pdf", "HR & Policies"),
            ("Leave Policy 2024", "pdf", "HR & Policies"),
            ("Backend Architecture Guide", "markdown", "Engineering"),
            ("Frontend Architecture Guide", "markdown", "Engineering"),
            ("Database Design Document", "markdown", "Engineering"),
            ("Authentication Implementation Guide", "markdown", "Engineering"),
            ("Deployment Guide — Kubernetes", "markdown", "Operations"),
            ("Docker Setup Guide", "markdown", "Operations"),
            ("CI/CD Pipeline Documentation", "markdown", "Operations"),
            ("Sprint Notes — Q4 2024", "markdown", "Operations"),
            ("Incident Report — Nov 2024", "markdown", "Operations"),
            ("API Documentation v2.1", "markdown", "Engineering"),
            ("Release Notes v3.0.0", "markdown", "Release Notes"),
            ("Release Notes v2.9.0", "markdown", "Release Notes"),
            ("Coding Standards & Style Guide", "markdown", "Engineering"),
            ("Logging Strategy", "markdown", "Engineering"),
            ("Microservices Architecture", "markdown", "Engineering"),
            ("System Design — Notification Service", "markdown", "Engineering"),
            ("Bug Report — AUTH-1042", "markdown", "Operations"),
        ],
    },
    {
        "name": "Developer Documentation",
        "slug": "developer-docs",
        "description": "Curated documentation for FastAPI, React, Docker, PostgreSQL, Redis, Kubernetes, LangGraph",
        "tier": "pro",
        "folders": ["Backend", "Frontend", "Infrastructure", "AI/ML"],
        "documents": [
            ("FastAPI Official Documentation", "markdown", "Backend"),
            ("FastAPI — Advanced User Guide", "markdown", "Backend"),
            ("React 18 Documentation", "markdown", "Frontend"),
            ("React Hooks Reference", "markdown", "Frontend"),
            ("Docker Official Docs", "markdown", "Infrastructure"),
            ("Docker Compose Reference", "markdown", "Infrastructure"),
            ("PostgreSQL 16 Documentation", "markdown", "Backend"),
            ("Redis Commands Reference", "markdown", "Backend"),
            ("Kubernetes Official Docs", "markdown", "Infrastructure"),
            ("Kubernetes Helm Guide", "markdown", "Infrastructure"),
            ("LangGraph Documentation", "markdown", "AI/ML"),
            ("LangChain Expression Language", "markdown", "AI/ML"),
            ("SQLAlchemy 2.0 ORM Guide", "markdown", "Backend"),
            ("Pydantic v2 Documentation", "markdown", "Backend"),
            ("Celery Documentation", "markdown", "Backend"),
            ("Qdrant Documentation", "markdown", "AI/ML"),
        ],
    },
    {
        "name": "AI Research",
        "slug": "ai-research",
        "description": "Curated AI and ML research papers, blog posts, and technical deep-dives",
        "tier": "pro",
        "folders": ["Foundational Papers", "Language Models", "Computer Vision", "AI Engineering"],
        "documents": [
            ("Attention Is All You Need — Transformer Paper", "pdf", "Foundational Papers"),
            ("BERT: Pre-training of Deep Bidirectional Transformers", "pdf", "Foundational Papers"),
            ("LLaMA 2: Open Foundation and Fine-Tuned Chat Models", "pdf", "Language Models"),
            ("GPT-4 Technical Report", "pdf", "Language Models"),
            ("Retrieval-Augmented Generation for Knowledge-Intensive NLP", "pdf", "Foundational Papers"),
            ("YOLOv9: Learning What You Want to Learn", "pdf", "Computer Vision"),
            ("ReAct: Synergizing Reasoning and Acting in Language Models", "pdf", "AI Engineering"),
            ("Chain-of-Thought Prompting Elicits Reasoning", "pdf", "AI Engineering"),
            ("Agentic AI — The Next Frontier", "markdown", "AI Engineering"),
            ("Model Context Protocol (MCP) Overview", "markdown", "AI Engineering"),
            ("RAG vs Fine-Tuning: When to Use Each", "markdown", "AI Engineering"),
            ("LangGraph: Building Stateful Multi-Actor Applications", "markdown", "AI Engineering"),
            ("Mistral 7B Technical Overview", "pdf", "Language Models"),
            ("Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks", "pdf", "Foundational Papers"),
        ],
    },
    {
        "name": "University",
        "slug": "university",
        "description": "Academic resources for students, faculty, and administration",
        "tier": "free",
        "folders": ["Student Resources", "Academic", "Administration", "Placement"],
        "documents": [
            ("Student Handbook 2024-25", "pdf", "Student Resources"),
            ("Attendance Policy", "pdf", "Student Resources"),
            ("Hostel Rules & Regulations", "pdf", "Student Resources"),
            ("Placement Cell Guide", "pdf", "Placement"),
            ("Academic Calendar 2024-25", "pdf", "Academic"),
            ("Course Syllabus — Computer Science", "pdf", "Academic"),
            ("Course Syllabus — Data Science", "pdf", "Academic"),
            ("Faculty Guidelines & Code of Conduct", "pdf", "Administration"),
            ("Examination Rules", "pdf", "Academic"),
            ("Scholarship & Financial Aid Guide", "pdf", "Student Resources"),
            ("Library Rules & Access Guide", "pdf", "Student Resources"),
            ("Anti-Ragging Policy", "pdf", "Administration"),
        ],
    },
]


DEMO_USERS = [
    {
        "email": "admin@atlas-ai.com",
        "password": "Admin@123456",
        "full_name": "Super Admin",
        "is_superadmin": True,
        "is_verified": True,
    },
    {
        "email": "sarah@technova.com",
        "password": "Demo@123456",
        "full_name": "Sarah Chen",
        "is_verified": True,
    },
    {
        "email": "dev@technova.com",
        "password": "Demo@123456",
        "full_name": "Alex Kumar",
        "is_verified": True,
    },
    {
        "email": "hr@technova.com",
        "password": "Demo@123456",
        "full_name": "Priya Sharma",
        "is_verified": True,
    },
    {
        "email": "researcher@atlas-ai.com",
        "password": "Demo@123456",
        "full_name": "James Wilson",
        "is_verified": True,
    },
]


async def seed():
    engine_kwargs = {}
    if "sqlite" in settings.DATABASE_URL:
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_async_engine(settings.DATABASE_URL, echo=False, **engine_kwargs)
    async with engine.begin() as conn:
        from app.core.database import Base
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        print("🌱 Seeding Atlas AI demo data...")

        # Create users
        users = {}
        for user_data in DEMO_USERS:
            user = User(
                id=uuid.uuid4(),
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                is_superadmin=user_data.get("is_superadmin", False),
                is_verified=user_data.get("is_verified", True),
                is_active=True,
                created_at=NOW,
                updated_at=NOW,
            )
            db.add(user)
            users[user_data["email"]] = user
            print(f"  ✓ User: {user_data['full_name']} ({user_data['email']})")

        await db.flush()

        # Owner mapping: which user owns which workspace
        owner_map = {
            "TechNova Software": users["sarah@technova.com"],
            "Developer Documentation": users["dev@technova.com"],
            "AI Research": users["researcher@atlas-ai.com"],
            "University": users["admin@atlas-ai.com"],
        }

        # Create workspaces + folders + documents
        for ws_data in WORKSPACES_DATA:
            owner = owner_map[ws_data["name"]]
            workspace = Workspace(
                id=uuid.uuid4(),
                name=ws_data["name"],
                slug=ws_data["slug"],
                description=ws_data["description"],
                owner_id=owner.id,
                tier=ws_data["tier"],
                storage_quota_bytes=10 * 1024 * 1024 * 1024,
                storage_used_bytes=0,
                is_active=True,
                settings={},
                created_at=NOW,
                updated_at=NOW,
            )
            db.add(workspace)
            await db.flush()

            # Add owner as admin
            member = WorkspaceMember(
                id=uuid.uuid4(),
                workspace_id=workspace.id,
                user_id=owner.id,
                role="workspace_admin",
                joined_at=NOW,
                created_at=NOW,
            )
            db.add(member)

            # Add super admin to all workspaces
            if owner.email != "admin@atlas-ai.com":
                admin_member = WorkspaceMember(
                    id=uuid.uuid4(),
                    workspace_id=workspace.id,
                    user_id=users["admin@atlas-ai.com"].id,
                    role="super_admin",
                    joined_at=NOW,
                    created_at=NOW,
                )
                db.add(admin_member)

            # Create folders
            folder_map = {}
            for folder_name in ws_data["folders"]:
                folder = Folder(
                    id=uuid.uuid4(),
                    workspace_id=workspace.id,
                    name=folder_name,
                    created_by=owner.id,
                    created_at=NOW,
                    updated_at=NOW,
                )
                db.add(folder)
                folder_map[folder_name] = folder
            await db.flush()

            # Create documents
            for doc_title, file_type, folder_name in ws_data["documents"]:
                ext_map = {"pdf": ".pdf", "markdown": ".md", "txt": ".txt"}
                ext = ext_map.get(file_type, ".txt")
                file_name = doc_title.lower().replace(" ", "_").replace("—", "").replace(":", "")[:50] + ext
                storage_key = f"workspaces/{workspace.id}/demo/{file_name}"

                doc = Document(
                    id=uuid.uuid4(),
                    workspace_id=workspace.id,
                    folder_id=folder_map[folder_name].id,
                    title=doc_title,
                    file_name=file_name,
                    file_type=file_type,
                    file_size_bytes=50000 + (hash(doc_title) % 500000),
                    storage_key=storage_key,
                    processing_status="completed",
                    chunk_count=2,
                    embedding_model="OpenAIEmbedder",
                    version=1,
                    tags=[folder_name.lower().replace(" & ", "-").replace(" ", "-")],
                    doc_metadata={"seeded": True, "author": owner.full_name},
                    uploaded_by=owner.id,
                    is_active=True,
                    created_at=NOW - datetime.timedelta(days=hash(doc_title) % 90),
                    updated_at=NOW,
                )
                db.add(doc)
                await db.flush()

                sample_chunks = get_demo_chunk_text(doc_title)
                for c_idx, c_text in enumerate(sample_chunks, 1):
                    chunk = DocumentChunk(
                        id=uuid.uuid4(),
                        document_id=doc.id,
                        workspace_id=workspace.id,
                        chunk_index=c_idx,
                        content=c_text,
                        token_count=len(c_text.split()),
                        page_number=c_idx,
                        created_at=NOW,
                    )
                    db.add(chunk)

            print(f"  ✓ Workspace: {ws_data['name']} ({len(ws_data['documents'])} documents)")

        # Create a sample pinned chat session for TechNova
        technova_ws = next(w for w in [None] if False) if False else None

        await db.commit()
        print("\n✅ Seed complete!")
        print("\nDemo credentials:")
        print("  Super Admin : admin@atlas-ai.com / Admin@123456")
        print("  Engineering : dev@technova.com   / Demo@123456")
        print("  HR Manager  : hr@technova.com    / Demo@123456")
        print("  Researcher  : researcher@atlas-ai.com / Demo@123456")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
