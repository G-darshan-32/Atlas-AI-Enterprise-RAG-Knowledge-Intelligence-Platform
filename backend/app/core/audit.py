"""Audit logging helper — writes to audit_logs table."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
import uuid


async def write_audit_log(
    db: AsyncSession,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    workspace_id: Optional[uuid.UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict] = None,
):
    """Write a single audit log entry. Fire-and-forget friendly."""
    log = AuditLog(
        id=uuid.uuid4(),
        user_id=user_id,
        workspace_id=workspace_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        log_metadata=metadata or {},
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    # Don't commit here — caller controls the transaction


# Common action constants
class AuditAction:
    USER_REGISTER = "USER_REGISTER"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_PASSWORD_RESET = "USER_PASSWORD_RESET"
    WORKSPACE_CREATE = "WORKSPACE_CREATE"
    WORKSPACE_UPDATE = "WORKSPACE_UPDATE"
    WORKSPACE_DELETE = "WORKSPACE_DELETE"
    MEMBER_INVITE = "MEMBER_INVITE"
    MEMBER_REMOVE = "MEMBER_REMOVE"
    MEMBER_ROLE_CHANGE = "MEMBER_ROLE_CHANGE"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    DOCUMENT_DOWNLOAD = "DOCUMENT_DOWNLOAD"
    GITHUB_CONNECT = "GITHUB_CONNECT"
    GITHUB_DISCONNECT = "GITHUB_DISCONNECT"
    CHAT_CREATE = "CHAT_CREATE"
    API_KEY_CREATE = "API_KEY_CREATE"
    API_KEY_REVOKE = "API_KEY_REVOKE"
