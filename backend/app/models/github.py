import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class GitHubRepository(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "github_repositories"

    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"))
    github_repo_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    full_name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    html_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(20), default="pending")
    index_readme: Mapped[bool] = mapped_column(Boolean, default=True)
    index_docs: Mapped[bool] = mapped_column(Boolean, default=True)
    index_code: Mapped[bool] = mapped_column(Boolean, default=False)
    connected_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    access_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    repo_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    workspace: Mapped["Workspace"] = relationship(back_populates="github_repos")
