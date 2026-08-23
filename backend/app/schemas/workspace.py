from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import re


class CreateWorkspaceRequest(BaseModel):
    name: str
    description: Optional[str] = None
    tier: str = "free"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("Workspace name must be at least 2 characters")
        return v.strip()


class UpdateWorkspaceRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[dict] = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    tier: str
    storage_quota_bytes: int
    storage_used_bytes: int
    logo_url: Optional[str]
    member_count: Optional[int] = None
    document_count: Optional[int] = None
    created_at: str

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: str
    role: str = "employee"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid = ["workspace_admin", "manager", "employee", "guest"]
        if v not in valid:
            raise ValueError(f"Role must be one of: {valid}")
        return v


class UpdateMemberRoleRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid = ["workspace_admin", "manager", "employee", "guest"]
        if v not in valid:
            raise ValueError(f"Role must be one of: {valid}")
        return v


class WorkspaceMemberResponse(BaseModel):
    id: str
    user_id: str
    workspace_id: str
    role: str
    full_name: str
    email: str
    avatar_url: Optional[str]
    joined_at: Optional[str]

    model_config = {"from_attributes": True}


class StorageUsageResponse(BaseModel):
    total_bytes: int
    used_bytes: int
    available_bytes: int
    documents_count: int
    breakdown_by_type: dict
