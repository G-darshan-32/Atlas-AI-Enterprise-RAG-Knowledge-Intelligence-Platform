from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import uuid
import re
import datetime

from app.core.database import get_db
from app.core.rate_limit import rate_limit_default
from app.core.audit import write_audit_log, AuditAction
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.document import Document, Folder
from app.schemas.workspace import (
    CreateWorkspaceRequest, UpdateWorkspaceRequest, WorkspaceResponse,
    InviteMemberRequest, UpdateMemberRoleRequest, WorkspaceMemberResponse, StorageUsageResponse
)
from app.api.dependencies import get_current_user, get_workspace_member, require_role
from app.services.email_service import EmailService

router = APIRouter()

_WORKSPACE_TEMPLATES = {
    "engineering": {"description": "Architecture docs, API guides, coding standards, CI/CD"},
    "hr": {"description": "Handbooks, policies, onboarding docs, leave policies"},
    "research": {"description": "Papers, experiments, literature reviews, findings"},
    "sales": {"description": "Playbooks, case studies, pricing, competitive intelligence"},
}


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{slug}-{uuid.uuid4().hex[:6]}"


# ─── Workspace CRUD ──────────────────────────────────────

@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    request: Request,
    body: CreateWorkspaceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_default),
):
    workspace = Workspace(
        id=uuid.uuid4(),
        name=body.name,
        slug=slugify(body.name),
        description=body.description,
        owner_id=current_user.id,
        tier=body.tier,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(workspace)
    await db.flush()

    member = WorkspaceMember(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="workspace_admin",
        joined_at=datetime.datetime.now(datetime.timezone.utc),
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(member)
    await write_audit_log(db, AuditAction.WORKSPACE_CREATE, user_id=current_user.id,
                          workspace_id=workspace.id, resource_type="workspace",
                          resource_id=str(workspace.id),
                          ip_address=request.client.host if request.client else None)
    await db.commit()
    await db.refresh(workspace)

    return WorkspaceResponse(
        id=str(workspace.id), name=workspace.name, slug=workspace.slug,
        description=workspace.description, tier=workspace.tier,
        storage_quota_bytes=workspace.storage_quota_bytes,
        storage_used_bytes=workspace.storage_used_bytes,
        logo_url=workspace.logo_url, member_count=1, document_count=0,
        created_at=workspace.created_at.isoformat(),
    )


@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            WorkspaceMember.user_id == current_user.id,
            Workspace.is_active == True,
            Workspace.deleted_at.is_(None),
        )
    )
    workspaces = result.scalars().all()
    return [
        WorkspaceResponse(
            id=str(w.id), name=w.name, slug=w.slug, description=w.description,
            tier=w.tier, storage_quota_bytes=w.storage_quota_bytes,
            storage_used_bytes=w.storage_used_bytes, logo_url=w.logo_url,
            created_at=w.created_at.isoformat(),
        )
        for w in workspaces
    ]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id, Workspace.is_active == True))
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    member_count = await db.scalar(select(func.count()).where(WorkspaceMember.workspace_id == workspace_id))
    doc_count = await db.scalar(select(func.count()).where(Document.workspace_id == workspace_id, Document.is_active == True))

    return WorkspaceResponse(
        id=str(workspace.id), name=workspace.name, slug=workspace.slug,
        description=workspace.description, tier=workspace.tier,
        storage_quota_bytes=workspace.storage_quota_bytes,
        storage_used_bytes=workspace.storage_used_bytes,
        logo_url=workspace.logo_url, member_count=member_count, document_count=doc_count,
        created_at=workspace.created_at.isoformat(),
    )


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    body: UpdateWorkspaceRequest,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "super_admin")),
):
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if body.name:
        workspace.name = body.name
    if body.description is not None:
        workspace.description = body.description
    if body.logo_url is not None:
        workspace.logo_url = body.logo_url
    if body.settings is not None:
        workspace.settings = {**workspace.settings, **body.settings}

    await write_audit_log(db, AuditAction.WORKSPACE_UPDATE, workspace_id=workspace_id,
                          user_id=member.user_id, resource_type="workspace", resource_id=str(workspace_id))
    await db.commit()
    await db.refresh(workspace)

    return WorkspaceResponse(
        id=str(workspace.id), name=workspace.name, slug=workspace.slug,
        description=workspace.description, tier=workspace.tier,
        storage_quota_bytes=workspace.storage_quota_bytes,
        storage_used_bytes=workspace.storage_used_bytes,
        logo_url=workspace.logo_url, created_at=workspace.created_at.isoformat(),
    )


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    request: Request,
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id, Workspace.owner_id == current_user.id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or insufficient permissions")

    workspace.is_active = False
    workspace.deleted_at = datetime.datetime.now(datetime.timezone.utc)
    await write_audit_log(db, AuditAction.WORKSPACE_DELETE, user_id=current_user.id,
                          workspace_id=workspace_id, resource_type="workspace",
                          resource_id=str(workspace_id),
                          ip_address=request.client.host if request.client else None)
    await db.commit()


# ─── Members ─────────────────────────────────────────────

@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_members(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == workspace_id)
    )
    return [
        WorkspaceMemberResponse(
            id=str(m.id), user_id=str(m.user_id), workspace_id=str(m.workspace_id),
            role=m.role, full_name=u.full_name, email=u.email, avatar_url=u.avatar_url,
            joined_at=m.joined_at.isoformat() if m.joined_at else None,
        )
        for m, u in result.all()
    ]


@router.post("/{workspace_id}/members/invite", status_code=201)
async def invite_member(
    request: Request,
    workspace_id: uuid.UUID,
    body: InviteMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "super_admin")),
):
    # Find invitee by email
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))
    invitee = result.scalar_one_or_none()
    if not invitee:
        raise HTTPException(status_code=404, detail="User with that email not found. They must register first.")

    # Check not already a member
    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == invitee.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a member of this workspace")

    new_member = WorkspaceMember(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        user_id=invitee.id,
        role=body.role,
        invited_by=current_user.id,
        joined_at=datetime.datetime.now(datetime.timezone.utc),
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(new_member)

    ws_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = ws_result.scalar_one()

    await write_audit_log(db, AuditAction.MEMBER_INVITE, user_id=current_user.id,
                          workspace_id=workspace_id, resource_type="user",
                          resource_id=str(invitee.id),
                          ip_address=request.client.host if request.client else None)
    await db.commit()

    try:
        await EmailService().send_workspace_invitation(
            invitee.email, current_user.full_name, workspace.name, body.role
        )
    except Exception:
        pass

    return {"message": f"{invitee.full_name} added to workspace", "user_id": str(invitee.id)}


@router.put("/{workspace_id}/members/{user_id}/role")
async def update_member_role(
    request: Request,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    body: UpdateMemberRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "super_admin")),
):
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    old_role = target.role
    target.role = body.role
    await write_audit_log(db, AuditAction.MEMBER_ROLE_CHANGE, user_id=current_user.id,
                          workspace_id=workspace_id, resource_type="user",
                          resource_id=str(user_id),
                          metadata={"old_role": old_role, "new_role": body.role},
                          ip_address=request.client.host if request.client else None)
    await db.commit()
    return {"message": "Role updated", "role": body.role}


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
async def remove_member(
    request: Request,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "super_admin")),
):
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.delete(target)
    await write_audit_log(db, AuditAction.MEMBER_REMOVE, user_id=current_user.id,
                          workspace_id=workspace_id, resource_type="user",
                          resource_id=str(user_id),
                          ip_address=request.client.host if request.client else None)
    await db.commit()


# ─── Storage ─────────────────────────────────────────────

@router.get("/{workspace_id}/storage", response_model=StorageUsageResponse)
async def get_storage(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    ws = await db.scalar(select(Workspace).where(Workspace.id == workspace_id))
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    by_type = await db.execute(
        select(Document.file_type, func.sum(Document.file_size_bytes).label("bytes"))
        .where(Document.workspace_id == workspace_id, Document.is_active == True)
        .group_by(Document.file_type)
    )
    breakdown = {row.file_type: row.bytes for row in by_type}
    doc_count = await db.scalar(
        select(func.count()).where(Document.workspace_id == workspace_id, Document.is_active == True)
    )

    return StorageUsageResponse(
        total_bytes=ws.storage_quota_bytes,
        used_bytes=ws.storage_used_bytes,
        available_bytes=max(0, ws.storage_quota_bytes - ws.storage_used_bytes),
        documents_count=doc_count or 0,
        breakdown_by_type=breakdown,
    )


# ─── Templates ───────────────────────────────────────────

@router.get("/templates")
async def list_templates(current_user: User = Depends(get_current_user)):
    return [
        {"id": tid, "name": tid.title(), "description": tdata["description"]}
        for tid, tdata in _WORKSPACE_TEMPLATES.items()
    ]


@router.post("/from-template", response_model=WorkspaceResponse, status_code=201)
async def create_from_template(
    request: Request,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template_id = body.get("template_id", "engineering")
    name = body.get("name") or _WORKSPACE_TEMPLATES.get(template_id, {}).get("name", "New Workspace")
    description = _WORKSPACE_TEMPLATES.get(template_id, {}).get("description", "")

    create_body = CreateWorkspaceRequest(name=name, description=description)
    return await create_workspace(request, create_body, db, current_user, None)


# ─── Folders ─────────────────────────────────────────────

@router.get("/{workspace_id}/folders")
async def list_folders(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(Folder).where(Folder.workspace_id == workspace_id).order_by(Folder.name)
    )
    folders = result.scalars().all()
    return [
        {"id": str(f.id), "name": f.name, "parent_id": str(f.parent_id) if f.parent_id else None,
         "created_at": f.created_at.isoformat()}
        for f in folders
    ]


@router.post("/{workspace_id}/folders", status_code=201)
async def create_folder(
    workspace_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Folder name required")

    folder = Folder(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        name=name,
        parent_id=body.get("parent_id"),
        created_by=current_user.id,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return {"id": str(folder.id), "name": folder.name, "workspace_id": str(workspace_id)}


@router.put("/{workspace_id}/folders/{folder_id}")
async def rename_folder(
    workspace_id: uuid.UUID,
    folder_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "manager", "super_admin")),
):
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.workspace_id == workspace_id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder.name = body.get("name", folder.name).strip()
    await db.commit()
    return {"id": str(folder.id), "name": folder.name}


@router.delete("/{workspace_id}/folders/{folder_id}", status_code=204)
async def delete_folder(
    workspace_id: uuid.UUID,
    folder_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "manager", "super_admin")),
):
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.workspace_id == workspace_id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    await db.delete(folder)
    await db.commit()
