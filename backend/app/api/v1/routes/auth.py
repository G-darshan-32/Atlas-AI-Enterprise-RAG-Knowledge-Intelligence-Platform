from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.security import (
    create_access_token, create_refresh_token,
    generate_verification_token, hash_token
)
from app.core.config import settings
from app.core.rate_limit import rate_limit_auth
from app.core.audit import write_audit_log, AuditAction
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
    ForgotPasswordRequest, ResetPasswordRequest, RefreshRequest, UpdateProfileRequest
)
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.api.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_auth),
):
    auth_service = AuthService(db)
    if await auth_service.get_user_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    user = await auth_service.create_user(
        email=body.email, password=body.password, full_name=body.full_name
    )

    # Send verification email (fire-and-forget)
    try:
        await EmailService().send_verification_email(user.email, user.full_name, user.verification_token)
    except Exception:
        pass

    await write_audit_log(db, AuditAction.USER_REGISTER, user_id=user.id,
                          ip_address=request.client.host if request.client else None)
    await db.commit()

    return UserResponse(
        id=str(user.id), email=user.email, full_name=user.full_name,
        avatar_url=user.avatar_url, is_verified=user.is_verified,
        is_superadmin=user.is_superadmin, mfa_enabled=user.mfa_enabled,
        created_at=user.created_at.isoformat(),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_auth),
):
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(subject=str(user.id))
    raw_refresh, refresh_hash = create_refresh_token(subject=str(user.id))
    await auth_service.store_refresh_token(user.id, refresh_hash)

    user.last_login_at = datetime.now(timezone.utc)
    await write_audit_log(db, AuditAction.USER_LOGIN, user_id=user.id,
                          ip_address=request.client.host if request.client else None)
    await db.commit()

    return TokenResponse(
        access_token=access_token, refresh_token=raw_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    new_access, new_refresh = await auth_service.rotate_refresh_token(body.refresh_token)
    return TokenResponse(
        access_token=new_access, refresh_token=new_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_service = AuthService(db)
    await auth_service.revoke_refresh_token(body.refresh_token)
    await write_audit_log(db, AuditAction.USER_LOGOUT, user_id=current_user.id)
    await db.commit()
    return {"message": "Logged out successfully"}


@router.post("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, update
    result = await db.execute(
        select(User).where(
            User.verification_token == token,
            User.is_verified == False,
            User.verification_token_expires > datetime.now(timezone.utc),
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    await db.commit()
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_auth),
):
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_email(body.email)
    if user and user.is_active:
        reset_token = generate_verification_token()
        user.reset_token = reset_token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.commit()
        try:
            await EmailService().send_password_reset_email(user.email, user.full_name, reset_token)
        except Exception:
            pass
    # Always return 200 to prevent email enumeration
    return {"message": "If that email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(
            User.reset_token == body.token,
            User.reset_token_expires > datetime.now(timezone.utc),
            User.is_active == True,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    from app.core.security import hash_password
    user.password_hash = hash_password(body.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    user.failed_login_attempts = 0
    user.locked_until = None
    await write_audit_log(db, AuditAction.USER_PASSWORD_RESET, user_id=user.id)
    await db.commit()
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id), email=current_user.email,
        full_name=current_user.full_name, avatar_url=current_user.avatar_url,
        is_verified=current_user.is_verified, is_superadmin=current_user.is_superadmin,
        mfa_enabled=current_user.mfa_enabled, created_at=current_user.created_at.isoformat(),
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.full_name is not None:
        current_user.full_name = body.full_name.strip()
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url
    await db.commit()
    await db.refresh(current_user)
    return UserResponse(
        id=str(current_user.id), email=current_user.email,
        full_name=current_user.full_name, avatar_url=current_user.avatar_url,
        is_verified=current_user.is_verified, is_superadmin=current_user.is_superadmin,
        mfa_enabled=current_user.mfa_enabled, created_at=current_user.created_at.isoformat(),
    )


# ─── OAuth: Google ───────────────────────────────────────

@router.get("/google")
async def google_login():
    """Redirect to Google OAuth."""
    from authlib.integrations.starlette_client import OAuth
    params = (
        f"client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
    )
    return {"url": f"https://accounts.google.com/o/oauth2/v2/auth?{params}"}


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback."""
    import httpx
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        })
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Google OAuth failed")

        access_token = token_res.json()["access_token"]
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        google_user = user_res.json()

    auth_service = AuthService(db)
    user = await auth_service.get_or_create_oauth_user(
        email=google_user["email"],
        full_name=google_user.get("name", ""),
        avatar_url=google_user.get("picture"),
        provider="google",
        provider_id=google_user["id"],
    )

    jwt_token = create_access_token(subject=str(user.id))
    raw_refresh, refresh_hash = create_refresh_token(subject=str(user.id))
    await auth_service.store_refresh_token(user.id, refresh_hash)
    await db.commit()

    # Redirect to frontend with tokens
    redirect_url = f"{settings.FRONTEND_URL}/auth/callback?access_token={jwt_token}&refresh_token={raw_refresh}"
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url)


@router.get("/github")
async def github_login():
    params = (
        f"client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user:email"
    )
    return {"url": f"https://github.com/login/oauth/authorize?{params}"}


@router.get("/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    import httpx
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        gh_token = token_res.json().get("access_token")
        if not gh_token:
            raise HTTPException(status_code=400, detail="GitHub OAuth failed")

        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {gh_token}"},
        )
        email_res = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {gh_token}"},
        )
        gh_user = user_res.json()
        emails = email_res.json()
        primary_email = next((e["email"] for e in emails if e.get("primary")), gh_user.get("email", ""))

    auth_service = AuthService(db)
    user = await auth_service.get_or_create_oauth_user(
        email=primary_email,
        full_name=gh_user.get("name") or gh_user.get("login", ""),
        avatar_url=gh_user.get("avatar_url"),
        provider="github",
        provider_id=str(gh_user["id"]),
    )

    jwt_token = create_access_token(subject=str(user.id))
    raw_refresh, refresh_hash = create_refresh_token(subject=str(user.id))
    await auth_service.store_refresh_token(user.id, refresh_hash)
    await db.commit()

    redirect_url = f"{settings.FRONTEND_URL}/auth/callback?access_token={jwt_token}&refresh_token={raw_refresh}"
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url)
