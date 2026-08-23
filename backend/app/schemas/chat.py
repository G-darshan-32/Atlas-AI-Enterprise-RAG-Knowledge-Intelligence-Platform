from pydantic import BaseModel
from typing import Optional, List
import uuid


class ChatSessionResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    title: Optional[str]
    mode: str
    is_pinned: bool
    is_archived: bool
    message_count: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: Optional[list]
    confidence_score: Optional[float]
    token_count: int
    model_used: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str
    mode: Optional[str] = "general"


class CreateSessionRequest(BaseModel):
    mode: str = "general"
    document_ids: Optional[List[uuid.UUID]] = None
