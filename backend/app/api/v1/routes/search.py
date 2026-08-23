from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
import uuid
import datetime

from app.core.database import get_db
from app.core.prompt_guard import sanitise_query
from app.models.workspace import WorkspaceMember
from app.models.analytics import AnalyticsEvent
from app.api.dependencies import get_current_user, get_workspace_member
from app.models.user import User
from app.ai.retrieval.hybrid_retriever import HybridRetriever

router = APIRouter()


@router.post("/{workspace_id}/search")
async def semantic_search(
    workspace_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    """Hybrid semantic + keyword search with optional filters."""
    raw_query = body.get("query", "")
    query = sanitise_query(raw_query)

    # Build filters from request
    filters: dict = {}
    raw_filters = body.get("filters", {})
    if raw_filters.get("file_type"):
        filters["file_type"] = raw_filters["file_type"]
    if raw_filters.get("source_type"):
        filters["source_type"] = raw_filters["source_type"]
    if raw_filters.get("document_id"):
        filters["document_id"] = raw_filters["document_id"]

    limit = min(body.get("limit", 10), 50)

    retriever = HybridRetriever()
    results = await retriever.search(
        query=query,
        workspace_id=str(workspace_id),
        filters=filters,
        top_k=limit,
    )

    # Track search event
    event = AnalyticsEvent(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        user_id=current_user.id,
        event_type="SEARCH",
        properties={
            "query": query,
            "result_count": len(results),
            "filters": raw_filters,
        },
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(event)
    await db.commit()

    return {"query": query, "total": len(results), "results": results}


@router.get("/{workspace_id}/search/history")
async def get_search_history(
    workspace_id: uuid.UUID,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    """Return the user's recent search queries in this workspace."""
    result = await db.execute(
        select(AnalyticsEvent)
        .where(
            AnalyticsEvent.workspace_id == workspace_id,
            AnalyticsEvent.user_id == current_user.id,
            AnalyticsEvent.event_type == "SEARCH",
        )
        .order_by(AnalyticsEvent.created_at.desc())
        .limit(limit)
    )
    events = result.scalars().all()
    return [
        {
            "query": e.properties.get("query", ""),
            "result_count": e.properties.get("result_count", 0),
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.get("/{workspace_id}/search/analytics")
async def get_search_analytics(
    workspace_id: uuid.UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    """Workspace-level search analytics: top queries, zero-result queries."""
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

    result = await db.execute(
        select(AnalyticsEvent)
        .where(
            AnalyticsEvent.workspace_id == workspace_id,
            AnalyticsEvent.event_type == "SEARCH",
            AnalyticsEvent.created_at >= since,
        )
        .order_by(AnalyticsEvent.created_at.desc())
    )
    events = result.scalars().all()

    query_counts: dict[str, int] = {}
    zero_results: list[str] = []
    for e in events:
        q = e.properties.get("query", "").lower().strip()
        if not q:
            continue
        query_counts[q] = query_counts.get(q, 0) + 1
        if e.properties.get("result_count", 1) == 0:
            zero_results.append(q)

    top_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_searches": len(events),
        "unique_queries": len(query_counts),
        "top_queries": [{"query": q, "count": c} for q, c in top_queries],
        "zero_result_queries": list(set(zero_results))[:10],
        "period_days": days,
    }
