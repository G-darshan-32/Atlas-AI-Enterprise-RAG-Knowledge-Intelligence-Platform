from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
import uuid
import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.audit import AuditLog
from app.api.dependencies import require_superadmin

router = APIRouter()


@router.get("/workspaces")
async def list_all_workspaces(
    page: int = 1, limit: int = 20,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superadmin),
):
    result = await db.execute(
        select(Workspace).order_by(Workspace.created_at.desc())
        .offset((page - 1) * limit).limit(limit)
    )
    workspaces = result.scalars().all()
    return [
        {
            "id": str(w.id), "name": w.name, "tier": w.tier,
            "is_active": w.is_active, "storage_used_bytes": w.storage_used_bytes,
            "created_at": w.created_at.isoformat(),
        }
        for w in workspaces
    ]


@router.get("/users")
async def list_all_users(
    page: int = 1, limit: int = 20,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superadmin),
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
        .offset((page - 1) * limit).limit(limit)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id), "email": u.email, "full_name": u.full_name,
            "is_active": u.is_active, "is_superadmin": u.is_superadmin,
            "is_verified": u.is_verified,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.put("/users/{user_id}/status")
async def toggle_user_status(
    user_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superadmin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own account")

    user.is_active = body.get("is_active", not user.is_active)
    await db.commit()
    return {"id": str(user.id), "is_active": user.is_active}


@router.get("/system/health")
async def system_health(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superadmin),
):
    user_count = await db.scalar(select(func.count()).select_from(User))
    workspace_count = await db.scalar(
        select(func.count()).select_from(Workspace).where(Workspace.is_active == True)
    )
    return {
        "status": "healthy",
        "version": "1.0.0",
        "user_count": user_count,
        "workspace_count": workspace_count,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = 1, limit: int = 50,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superadmin),
):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc())
        .offset((page - 1) * limit).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id), "action": l.action,
            "resource_type": l.resource_type, "resource_id": l.resource_id,
            "user_id": str(l.user_id) if l.user_id else None,
            "workspace_id": str(l.workspace_id) if l.workspace_id else None,
            "ip_address": l.ip_address, "metadata": l.log_metadata,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


@router.post("/announcements")
async def create_announcement(
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_superadmin),
):
    """Placeholder for platform-wide announcement (stored as audit event)."""
    from app.models.analytics import AnalyticsEvent
    import uuid as _uuid
    event = AnalyticsEvent(
        id=_uuid.uuid4(),
        workspace_id=_uuid.UUID("00000000-0000-0000-0000-000000000001"),
        user_id=admin.id,
        event_type="PLATFORM_ANNOUNCEMENT",
        properties={"message": body.get("message", "")},
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(event)
    await db.commit()
    return {"message": "Announcement sent"}
