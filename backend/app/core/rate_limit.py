"""Redis-backed sliding window rate limiter."""
from fastapi import Request, HTTPException, status
from app.core.redis import get_redis
from app.core.config import settings
import time


async def check_rate_limit(request: Request, limit: int, window: int = 60, key_prefix: str = "rl"):
    """
    Sliding window rate limiter using Redis.
    limit  — max requests per window
    window — window size in seconds
    """
    redis = await get_redis()
    ip = request.client.host if request.client else "unknown"
    key = f"{key_prefix}:{ip}:{int(time.time()) // window}"

    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window * 2)
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
                headers={"Retry-After": str(window)},
            )
    except HTTPException:
        raise
    except Exception:
        # If Redis is down, fail open (don't block users)
        pass


async def rate_limit_default(request: Request):
    await check_rate_limit(request, limit=settings.RATE_LIMIT_PER_MINUTE, window=60, key_prefix="rl:api")


async def rate_limit_chat(request: Request):
    await check_rate_limit(request, limit=settings.RATE_LIMIT_CHAT_PER_MINUTE, window=60, key_prefix="rl:chat")


async def rate_limit_auth(request: Request):
    await check_rate_limit(request, limit=10, window=60, key_prefix="rl:auth")
