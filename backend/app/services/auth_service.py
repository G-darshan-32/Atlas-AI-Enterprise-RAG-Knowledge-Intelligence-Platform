from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from app.models.user import User, RefreshToken
from app.core.security import hash_password, verify_password, hash_token, create_access_token, create_refresh_token, generate_verification_token
from app.core.config import settings
from app.core.exceptions import UnauthorizedError


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, email: str, password: str, full_name: str, **kwargs) -> User:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_verified=False,
            verification_token=generate_verification_token(),
            verification_token_expires=datetime.now(timezone.utc) + timedelta(days=7),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **kwargs,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_or_create_oauth_user(
        self,
        email: str,
        full_name: str,
        provider: str,
        provider_id: str,
        avatar_url: Optional[str] = None,
    ) -> User:
        """Find existing user by email or OAuth provider ID, or create new one."""
        # Try by provider ID first
        result = await self.db.execute(
            select(User).where(User.oauth_provider == provider, User.oauth_provider_id == provider_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Try by email
            user = await self.get_user_by_email(email)

        if not user:
            user = User(
                id=uuid.uuid4(),
                email=email,
                full_name=full_name,
                avatar_url=avatar_url,
                oauth_provider=provider,
                oauth_provider_id=provider_id,
                is_verified=True,  # OAuth emails are pre-verified
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(user)
            await self.db.flush()
        else:
            # Update OAuth linkage if missing
            if not user.oauth_provider:
                user.oauth_provider = provider
                user.oauth_provider_id = provider_id
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url

        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(email)
        if not user or not user.is_active or not user.password_hash:
            return None

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return None

        if not verify_password(password, user.password_hash):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
            await self.db.commit()
            return None

        user.failed_login_attempts = 0
        user.locked_until = None
        return user

    async def store_refresh_token(self, user_id: uuid.UUID, token_hash: str):
        expires = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        token = RefreshToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(token)
        await self.db.flush()

    async def rotate_refresh_token(self, raw_token: str) -> tuple[str, str]:
        token_hash = hash_token(raw_token)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        stored = result.scalar_one_or_none()
        if not stored:
            raise UnauthorizedError("Invalid or expired refresh token")

        stored.revoked = True
        new_access = create_access_token(subject=str(stored.user_id))
        new_raw, new_hash = create_refresh_token(subject=str(stored.user_id))
        await self.store_refresh_token(stored.user_id, new_hash)
        await self.db.commit()
        return new_access, new_raw

    async def revoke_refresh_token(self, raw_token: str):
        token_hash = hash_token(raw_token)
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        token = result.scalar_one_or_none()
        if token:
            token.revoked = True
