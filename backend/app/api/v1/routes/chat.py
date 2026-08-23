from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import uuid
import json
import datetime

from app.core.database import get_db
from app.core.rate_limit import rate_limit_chat
from app.core.prompt_guard import sanitise_query
from app.models.user import User
from app.models.chat import ChatSession, Message
from app.models.workspace import WorkspaceMember
from app.api.dependencies import get_current_user, get_workspace_member
from app.ai.orchestrator import AgentOrchestrator
from app.lib.utils import SUGGESTED_PROMPTS
from app.core.config import settings

from pydantic import BaseModel


router = APIRouter()


class CreateSessionRequest(BaseModel):
    mode: Optional[str] = "general"
    document_ids: Optional[List[uuid.UUID]] = None


@router.post("/{workspace_id}/chat/sessions")
async def create_session(
    workspace_id: uuid.UUID,
    payload: Optional[CreateSessionRequest] = None,
    mode: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    session_mode = (payload.mode if payload and payload.mode else mode) or "general"
    doc_ids = (payload.document_ids if payload and payload.document_ids else None) or []

    session = ChatSession(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        user_id=current_user.id,
        mode=session_mode,
        document_ids=doc_ids,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {
        "id": str(session.id), "workspace_id": str(session.workspace_id),
        "mode": session.mode, "is_pinned": session.is_pinned,
        "created_at": session.created_at.isoformat(),
    }


@router.get("/{workspace_id}/chat/sessions")
async def list_sessions(
    workspace_id: uuid.UUID,
    archived: bool = False,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    query = (
        select(ChatSession)
        .where(
            ChatSession.workspace_id == workspace_id,
            ChatSession.user_id == current_user.id,
            ChatSession.is_archived == archived,
        )
        .order_by(ChatSession.updated_at.desc())
        .offset((page - 1) * limit).limit(limit)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()
    return [
        {
            "id": str(s.id), "title": s.title, "mode": s.mode,
            "is_pinned": s.is_pinned, "message_count": s.message_count,
            "created_at": s.created_at.isoformat(), "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/{workspace_id}/chat/sessions/{session_id}")
async def get_session(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.workspace_id == workspace_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
    )
    messages = msgs.scalars().all()
    return {
        "id": str(session.id), "title": session.title, "mode": session.mode,
        "is_pinned": session.is_pinned,
        "messages": [
            {
                "id": str(m.id), "role": m.role, "content": m.content,
                "citations": m.citations, "confidence_score": m.confidence_score,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


@router.post("/{workspace_id}/chat/sessions/{session_id}/messages")
async def send_message(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    _: None = Depends(rate_limit_chat),
):
    """Send message and stream AI response via SSE."""
    raw_content = body.get("content", "")
    content = sanitise_query(raw_content)

    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.workspace_id == workspace_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = Message(
        id=uuid.uuid4(),
        session_id=session_id,
        role="user",
        content=content,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(user_msg)
    session.message_count += 1
    if not session.title and session.message_count == 1:
        session.title = content[:80] + ("..." if len(content) > 80 else "")
    session.updated_at = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()

    async def generate():
        orchestrator = AgentOrchestrator()
        full_response = ""
        citations = []
        confidence = 0.0
        assistant_msg_id = str(uuid.uuid4())

        try:
            async for chunk in orchestrator.stream(
                query=content,
                workspace_id=str(workspace_id),
                session_id=str(session_id),
                mode=session.mode,
            ):
                if chunk["type"] == "token":
                    full_response += chunk["content"]
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk['content']})}\n\n"
                elif chunk["type"] == "citations":
                    citations = chunk["citations"]
                    yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"
                elif chunk["type"] == "done":
                    confidence = chunk.get("confidence", 0.8)
                    break
                elif chunk["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'content': chunk['content']})}\n\n"
                    return

            # Persist assistant message
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
            from app.core.config import settings as _s
            _eng = create_async_engine(_s.DATABASE_URL, echo=False)
            _Session = async_sessionmaker(_eng, expire_on_commit=False)
            async with _Session() as _db:
                asst_msg = Message(
                    id=uuid.UUID(assistant_msg_id),
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    citations=citations,
                    confidence_score=confidence,
                    model_used=f"groq/{settings.GROQ_MODEL}",
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                )
                _db.add(asst_msg)
                # Update session
                _result = await _db.execute(select(ChatSession).where(ChatSession.id == session_id))
                _session = _result.scalar_one_or_none()
                if _session:
                    _session.message_count += 1
                    _session.updated_at = datetime.datetime.now(datetime.timezone.utc)
                await _db.commit()
            await _eng.dispose()

            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_msg_id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.delete("/{workspace_id}/chat/sessions/{session_id}", status_code=204)
async def delete_session(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.workspace_id == workspace_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()


@router.put("/{workspace_id}/chat/sessions/{session_id}/pin")
async def toggle_pin(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_pinned = not session.is_pinned
    await db.commit()
    return {"is_pinned": session.is_pinned}


@router.get("/{workspace_id}/chat/sessions/{session_id}/export")
async def export_session(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    format: str = "markdown",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.workspace_id == workspace_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
    )
    messages = msgs.scalars().all()

    if format == "markdown":
        lines = [f"# {session.title or 'Chat Export'}\n"]
        for m in messages:
            prefix = "**You:**" if m.role == "user" else "**Atlas AI:**"
            lines.append(f"{prefix}\n{m.content}\n")
        content = "\n---\n".join(lines)
        from fastapi.responses import Response
        return Response(content=content, media_type="text/markdown",
                        headers={"Content-Disposition": f'attachment; filename="chat-{session_id}.md"'})

    # JSON export
    return {
        "session_id": str(session_id),
        "title": session.title,
        "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in messages],
    }


@router.post("/{workspace_id}/chat/suggestions")
async def get_suggestions(
    workspace_id: uuid.UUID,
    body: dict = {},
    member: WorkspaceMember = Depends(get_workspace_member),
):
    """Return contextual suggested prompts for the workspace."""
    return {"suggestions": SUGGESTED_PROMPTS}
