from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import uuid
import datetime

from app.core.database import get_db
from app.models import User, WorkspaceMember, Document, ChatSession, Message, AnalyticsEvent
from app.api.dependencies import get_current_user, get_workspace_member, require_role

router = APIRouter()


@router.get("/{workspace_id}/analytics/overview")
async def get_analytics_overview(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "manager", "super_admin")),
):
    # Document counts
    doc_count = await db.scalar(
        select(func.count()).where(Document.workspace_id == workspace_id, Document.is_active == True)
    )

    # Embedded docs
    embedded_count = await db.scalar(
        select(func.count()).where(
            Document.workspace_id == workspace_id,
            Document.is_active == True,
            Document.processing_status == "completed"
        )
    )

    # Chat sessions in last 30 days
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    session_count = await db.scalar(
        select(func.count()).where(
            ChatSession.workspace_id == workspace_id,
            ChatSession.created_at >= since
        )
    )

    # Messages in last 30 days
    msg_count = await db.scalar(
        select(func.count(Message.id))
        .join(ChatSession, ChatSession.id == Message.session_id)
        .where(
            ChatSession.workspace_id == workspace_id,
            Message.created_at >= since,
            Message.role == "user"
        )
    )

    return {
        "documents_total": doc_count,
        "documents_indexed": embedded_count,
        "chat_sessions_30d": session_count,
        "queries_30d": msg_count,
        "period_start": since.isoformat(),
        "period_end": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


@router.get("/{workspace_id}/analytics/documents")
async def get_document_analytics(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "manager", "super_admin")),
):
    # By file type
    by_type = await db.execute(
        select(Document.file_type, func.count().label("count"), func.sum(Document.file_size_bytes).label("total_bytes"))
        .where(Document.workspace_id == workspace_id, Document.is_active == True)
        .group_by(Document.file_type)
    )
    type_breakdown = [{"type": row.file_type, "count": row.count, "total_bytes": row.total_bytes} for row in by_type]

    return {"by_type": type_breakdown}


@router.get("/{workspace_id}/analytics/chat")
async def get_chat_analytics(
    workspace_id: uuid.UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "manager", "super_admin")),
):
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

    # Messages by day
    msgs = await db.execute(
        select(
            func.date_trunc("day", Message.created_at).label("day"),
            func.count().label("count")
        )
        .join(ChatSession, ChatSession.id == Message.session_id)
        .where(
            ChatSession.workspace_id == workspace_id,
            Message.created_at >= since,
            Message.role == "user"
        )
        .group_by(func.date_trunc("day", Message.created_at))
        .order_by(func.date_trunc("day", Message.created_at))
    )

    return {
        "messages_by_day": [{"date": row.day.isoformat(), "count": row.count} for row in msgs],
    }
