from pydantic import BaseModel, field_validator
from typing import Optional, List
import uuid


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    folder_id: Optional[str]
    title: str
    file_name: str
    file_type: str
    file_size_bytes: int
    processing_status: str
    chunk_count: int
    version: int
    tags: List[str]
    metadata: dict
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class UpdateDocumentRequest(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    folder_id: Optional[uuid.UUID] = None


class FolderResponse(BaseModel):
    id: str
    workspace_id: str
    parent_id: Optional[str]
    name: str
    created_at: str

    model_config = {"from_attributes": True}
