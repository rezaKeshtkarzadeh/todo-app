from typing import Optional
from fastapi import Request, Depends, HTTPException
from redis.asyncio import Redis

from app.core.redis_client import get_redis_client
from app.core.errors import AppError
from app.services.rate_limiter import RateLimiter, RATE_LIMITS


async def rate_limit_dependency(
    request: Request,
    endpoint_key: str,
    redis: Redis = Depends(get_redis_client),
) -> None:
    """
    Rate limit dependency for a specific endpoint.
    Checks per-IP, per-user (if authenticated), and per-endpoint limits.
    """
    limiter = RateLimiter(redis)
    config = RATE_LIMITS.get(endpoint_key, RATE_LIMITS["default"])
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Get user_id if authenticated
    user_id = None
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            from app.core.security import decode_access_token
            payload = decode_access_token(access_token)
            user_id = payload.get("sub")
        except Exception:
            pass
    
    # Determine endpoint identifier from route
    endpoint_identifier = endpoint_key.replace(":", ".")
    
    # Check all three rate limits
    allowed, meta = await limiter.check_rate_limit_multi(
        ip=client_ip,
        user_id=user_id,
        endpoint=endpoint_identifier,
        ip_limit=config["ip"]["limit"],
        user_limit=config["user"]["limit"],
        window_seconds=config["ip"]["window"],  # Use IP window for all
    )
    
    if not allowed:
        raise AppError(
            "RATE_LIMITED",
            429,
            f"Rate limit exceeded. Try again in {meta['retry_after']} seconds.",
            details={
                "limit": meta["limit"],
                "remaining": meta["remaining"],
                "reset": meta["reset"],
                "retry_after": meta["retry_after"],
            },
        )
    
    # Add rate limit headers to response
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(meta["limit"]),
        "X-RateLimit-Remaining": str(meta["remaining"]),
        "X-RateLimit-Reset": str(meta["reset"]),
    }


def create_rate_limit_dependency(endpoint_key: str):
    """Factory to create rate limit dependency for a specific endpoint."""
    async def dependency(request: Request, redis: Redis = Depends(get_redis_client)):
        await rate_limit_dependency(request, endpoint_key, redis)
    return dependency