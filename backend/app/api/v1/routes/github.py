from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import datetime

from app.core.database import get_db
from app.models import User, GitHubRepository, WorkspaceMember
from app.api.dependencies import get_current_user, get_workspace_member, require_role

router = APIRouter()


@router.get("/{workspace_id}/github/repos")
async def list_repos(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(GitHubRepository).where(GitHubRepository.workspace_id == workspace_id)
    )
    repos = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "full_name": r.full_name,
            "description": r.description,
            "default_branch": r.default_branch,
            "language": r.language,
            "html_url": r.html_url,
            "sync_status": r.sync_status,
            "last_synced_at": r.last_synced_at.isoformat() if r.last_synced_at else None,
            "index_readme": r.index_readme,
            "index_docs": r.index_docs,
            "index_code": r.index_code,
        }
        for r in repos
    ]


@router.post("/{workspace_id}/github/repos/connect")
async def connect_repo(
    workspace_id: uuid.UUID,
    body: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "manager", "super_admin")),
):
    full_name = body.get("full_name", "").strip()
    access_token = body.get("access_token", "").strip()

    if not full_name:
        raise HTTPException(status_code=400, detail="Repository full_name required (e.g. owner/repo)")

    repo = GitHubRepository(
        workspace_id=workspace_id,
        full_name=full_name,
        default_branch=body.get("default_branch", "main"),
        index_readme=body.get("index_readme", True),
        index_docs=body.get("index_docs", True),
        index_code=body.get("index_code", False),
        connected_by=current_user.id,
        access_token_encrypted=access_token,  # TODO: encrypt before storing
        sync_status="pending",
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    # Queue indexing
    from app.workers.tasks.github_tasks import index_repository
    background_tasks.add_task(index_repository.delay, str(repo.id))

    return {"id": str(repo.id), "full_name": repo.full_name, "sync_status": repo.sync_status}


@router.post("/{workspace_id}/github/repos/{repo_id}/sync")
async def trigger_sync(
    workspace_id: uuid.UUID,
    repo_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "manager", "super_admin")),
):
    result = await db.execute(
        select(GitHubRepository).where(GitHubRepository.id == repo_id, GitHubRepository.workspace_id == workspace_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo.sync_status = "pending"
    await db.commit()

    from app.workers.tasks.github_tasks import index_repository
    background_tasks.add_task(index_repository.delay, str(repo.id))

    return {"message": "Sync triggered", "repo_id": str(repo_id)}


@router.delete("/{workspace_id}/github/repos/{repo_id}", status_code=204)
async def disconnect_repo(
    workspace_id: uuid.UUID,
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "super_admin")),
):
    result = await db.execute(
        select(GitHubRepository).where(GitHubRepository.id == repo_id, GitHubRepository.workspace_id == workspace_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await db.delete(repo)
    await db.commit()
