from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
import uuid
import hashlib
import datetime

from app.core.database import get_db
from app.core.rate_limit import rate_limit_default
from app.core.audit import write_audit_log, AuditAction
from app.models.user import User
from app.models.document import Document, DocumentVersion, DocumentChunk, Folder
from app.models.workspace import Workspace, WorkspaceMember
from app.api.dependencies import get_current_user, get_workspace_member, require_role
from app.services.storage_service import StorageService
from app.core.config import settings
from app.core.exceptions import ValidationError

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".md", ".txt", ".csv", ".html", ".ipynb"}
EXTENSION_TO_TYPE = {
    ".pdf": "pdf", ".docx": "docx", ".pptx": "pptx", ".xlsx": "xlsx",
    ".md": "markdown", ".txt": "txt", ".csv": "csv", ".html": "html", ".ipynb": "ipynb",
}


@router.post("/{workspace_id}/documents/upload")
async def upload_document(
    request: Request,
    workspace_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    folder_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
    _: None = Depends(rate_limit_default),
):
    if member.role == "guest":
        raise HTTPException(status_code=403, detail="Guests cannot upload documents")

    import os
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File type not supported. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise ValidationError(f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    content_hash = hashlib.sha256(content).hexdigest()

    # Dedup check
    existing = await db.execute(
        select(Document).where(
            Document.workspace_id == workspace_id,
            Document.content_hash == content_hash,
            Document.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Document with identical content already exists")

    storage_key = f"workspaces/{workspace_id}/documents/{uuid.uuid4()}{ext}"
    storage = StorageService()
    await storage.upload_bytes(key=storage_key, data=content, content_type=file.content_type or "application/octet-stream")

    document = Document(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        folder_id=folder_id,
        title=file.filename or "Untitled",
        file_name=file.filename or "file",
        file_type=EXTENSION_TO_TYPE.get(ext, "txt"),
        file_size_bytes=len(content),
        storage_key=storage_key,
        content_hash=content_hash,
        processing_status="pending",
        uploaded_by=current_user.id,
        tags=[],
        doc_metadata={},
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(document)

    ws_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = ws_result.scalar_one()
    workspace.storage_used_bytes += len(content)

    await write_audit_log(db, AuditAction.DOCUMENT_UPLOAD, user_id=current_user.id,
                          workspace_id=workspace_id, resource_type="document",
                          resource_id=str(document.id),
                          ip_address=request.client.host if request.client else None)
    await db.commit()
    await db.refresh(document)

    from app.workers.tasks.document_tasks import process_document
    background_tasks.add_task(process_document.delay, str(document.id))

    return {
        "id": str(document.id), "title": document.title,
        "file_type": document.file_type, "file_size_bytes": document.file_size_bytes,
        "processing_status": document.processing_status,
        "created_at": document.created_at.isoformat(),
    }


@router.get("/{workspace_id}/documents")
async def list_documents(
    workspace_id: uuid.UUID,
    folder_id: Optional[uuid.UUID] = None,
    file_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    query = select(Document).where(Document.workspace_id == workspace_id, Document.is_active == True)
    if folder_id:
        query = query.where(Document.folder_id == folder_id)
    if file_type:
        query = query.where(Document.file_type == file_type)
    query = query.offset((page - 1) * limit).limit(limit).order_by(Document.created_at.desc())
    result = await db.execute(query)
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id), "title": d.title, "file_name": d.file_name,
            "file_type": d.file_type, "file_size_bytes": d.file_size_bytes,
            "processing_status": d.processing_status, "chunk_count": d.chunk_count,
            "tags": d.tags, "version": d.version,
            "folder_id": str(d.folder_id) if d.folder_id else None,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.get("/{workspace_id}/documents/{document_id}")
async def get_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id, Document.is_active == True)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(doc.id), "title": doc.title, "file_name": doc.file_name,
        "file_type": doc.file_type, "file_size_bytes": doc.file_size_bytes,
        "processing_status": doc.processing_status, "processing_error": doc.processing_error,
        "chunk_count": doc.chunk_count, "embedding_model": doc.embedding_model,
        "version": doc.version, "tags": doc.tags, "metadata": doc.doc_metadata,
        "created_at": doc.created_at.isoformat(), "updated_at": doc.updated_at.isoformat(),
    }


@router.put("/{workspace_id}/documents/{document_id}")
async def update_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if "title" in body:
        doc.title = body["title"]
    if "tags" in body:
        doc.tags = body["tags"]
    if "folder_id" in body:
        doc.folder_id = uuid.UUID(body["folder_id"]) if body["folder_id"] else None
    doc.updated_at = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()
    return {"id": str(doc.id), "title": doc.title, "tags": doc.tags}


@router.delete("/{workspace_id}/documents/{document_id}", status_code=204)
async def delete_document(
    request: Request,
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    can_delete = member.role in ["workspace_admin", "manager", "super_admin"] or doc.uploaded_by == current_user.id
    if not can_delete:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    doc.is_active = False
    ws_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = ws_result.scalar_one()
    workspace.storage_used_bytes = max(0, workspace.storage_used_bytes - doc.file_size_bytes)

    await write_audit_log(db, AuditAction.DOCUMENT_DELETE, user_id=current_user.id,
                          workspace_id=workspace_id, resource_type="document",
                          resource_id=str(document_id),
                          ip_address=request.client.host if request.client else None)
    await db.commit()


@router.get("/{workspace_id}/documents/{document_id}/preview")
async def get_document_preview_url(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    storage = StorageService()
    signed_url = await storage.get_signed_url(doc.storage_key, expires_in=3600)
    return {"url": signed_url, "expires_in": 3600}


@router.get("/{workspace_id}/documents/{document_id}/chunks")
async def list_chunks(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id, DocumentChunk.workspace_id == workspace_id)
        .order_by(DocumentChunk.chunk_index)
        .offset((page - 1) * limit).limit(limit)
    )
    chunks = result.scalars().all()
    return [
        {"id": str(c.id), "chunk_index": c.chunk_index, "content": c.content[:200] + "...",
         "token_count": c.token_count, "page_number": c.page_number}
        for c in chunks
    ]


@router.get("/{workspace_id}/documents/{document_id}/versions")
async def get_versions(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(DocumentVersion).where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version.desc())
    )
    versions = result.scalars().all()
    return [
        {"id": str(v.id), "version": v.version, "file_size_bytes": v.file_size_bytes,
         "uploaded_by": str(v.uploaded_by), "created_at": v.created_at.isoformat()}
        for v in versions
    ]


@router.get("/{workspace_id}/documents/{document_id}/status")
async def get_document_status(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": str(doc.id), "processing_status": doc.processing_status,
        "chunk_count": doc.chunk_count, "processing_error": doc.processing_error,
    }


@router.post("/{workspace_id}/documents/{document_id}/reprocess")
async def reprocess_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(require_role("workspace_admin", "manager", "super_admin")),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.processing_status = "pending"
    doc.chunk_count = 0
    doc.processing_error = None
    await db.commit()

    from app.workers.tasks.document_tasks import process_document
    background_tasks.add_task(process_document.delay, str(document_id))
    return {"message": "Reprocessing started", "document_id": str(document_id)}


@router.put("/{workspace_id}/documents/{document_id}/tags")
async def update_tags(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    member: WorkspaceMember = Depends(get_workspace_member),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.tags = body.get("tags", [])
    await db.commit()
    return {"tags": doc.tags}
