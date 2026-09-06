import time
import hashlib
from typing import Optional
from redis.asyncio import Redis
from app.core.errors import AppError


class RateLimiter:
    """
    Redis-backed sliding window rate limiter.
    Supports per-IP, per-user, and per-endpoint limits with configurable windows.
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create a namespaced rate limit key."""
        return f"rate_limit:{prefix}:{identifier}"
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        identifier: str = "request"
    ) -> tuple[bool, dict]:
        """
        Check and increment rate limit counter.
        Returns (allowed, metadata) where metadata contains limit, remaining, reset_time.
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Use sorted set for sliding window
        redis_key = f"ratelimit:{key}"
        
        # Remove expired entries
        await self.redis.zremrangebyscore(redis_key, 0, window_start)
        
        # Count current requests in window
        current_count = await self.redis.zcard(redis_key)
        
        if current_count >= limit:
            # Get oldest entry to calculate reset time
            oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            reset_time = int(float(oldest[0][1]) + window_seconds) if oldest else int(now + window_seconds)
            
            return False, {
                "limit": limit,
                "remaining": 0,
                "reset": reset_time,
                "retry_after": reset_time - int(now),
            }
        
        # Add current request
        request_id = f"{now}:{identifier}"
        await self.redis.zadd(redis_key, {request_id: now})
        await self.redis.expire(redis_key, window_seconds + 1)
        
        return True, {
            "limit": limit,
            "remaining": limit - current_count - 1,
            "reset": int(now + window_seconds),
            "retry_after": 0,
        }
    
    async def check_rate_limit_multi(
        self,
        ip: str,
        user_id: Optional[str],
        endpoint: str,
        ip_limit: int,
        user_limit: int,
        window_seconds: int,
    ) -> tuple[bool, dict]:
        """
        Check rate limits across multiple dimensions (IP, user, endpoint).
        Returns (allowed, metadata) where metadata contains the most restrictive limit info.
        """
        now = time.time()
        
        # Check per-IP limit
        ip_key = self._make_key("ip", ip)
        ip_allowed, ip_meta = await self._check_single_limit(ip_key, ip_limit, window_seconds, f"ip:{ip}")
        if not ip_allowed:
            return False, ip_meta
        
        # Check per-user limit if authenticated
        user_meta = {"limit": user_limit, "remaining": user_limit, "reset": int(time.time() + window_seconds), "retry_after": 0}
        if user_id:
            user_key = self._make_key("user", user_id)
            user_allowed, user_meta = await self._check_single_limit(user_key, user_limit, window_seconds, f"user:{user_id}")
            if not user_allowed:
                return False, user_meta
        
        # Check per-endpoint limit
        endpoint_key = self._make_key(f"endpoint:{endpoint}", ip)
        endpoint_allowed, endpoint_meta = await self._check_single_limit(endpoint_key, user_limit, window_seconds, f"endpoint:{endpoint}:{ip}")
        if not endpoint_allowed:
            return False, endpoint_meta
        
        # Return most restrictive remaining count
        min_remaining = min(ip_meta["remaining"], user_meta["remaining"], endpoint_meta["remaining"])
        combined_meta = {
            "limit": min(ip_meta["limit"], user_meta["limit"], endpoint_meta["limit"]),
            "remaining": min_remaining,
            "reset": max(ip_meta["reset"], user_meta["reset"], endpoint_meta["reset"]),
            "retry_after": 0,
        }
        
        return True, combined_meta
    
    async def _check_single_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        identifier: str = "request"
    ) -> tuple[bool, dict]:
        """Check and increment rate limit counter for a single dimension."""
        now = time.time()
        window_start = now - window_seconds
        
        # Use sorted set for sliding window
        redis_key = f"ratelimit:{key}"
        
        # Remove expired entries
        await self.redis.zremrangebyscore(redis_key, 0, window_start)
        
        # Count current requests in window
        current_count = await self.redis.zcard(redis_key)
        
        if current_count >= limit:
            # Get oldest entry to calculate reset time
            oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            reset_time = int(float(oldest[0][1]) + window_seconds) if oldest else int(now + window_seconds)
            
            return False, {
                "limit": limit,
                "remaining": 0,
                "reset": reset_time,
                "retry_after": reset_time - int(now),
            }
        
        # Add current request
        request_id = f"{now}:{identifier}"
        await self.redis.zadd(redis_key, {request_id: now})
        await self.redis.expire(redis_key, window_seconds + 1)
        
        return True, {
            "limit": limit,
            "remaining": limit - current_count - 1,
            "reset": int(now + window_seconds),
            "retry_after": 0,
        }
    
    async def get_current_usage(self, key: str, window_seconds: int) -> int:
        """Get current request count in window."""
        now = time.time()
        window_start = now - window_seconds
        redis_key = f"ratelimit:{key}"
        await self.redis.zremrangebyscore(redis_key, 0, window_start)
        return await self.redis.zcard(redis_key)


# Rate limit configurations
RATE_LIMITS = {
    # Auth endpoints - stricter limits
    "auth:send-otp": {"ip": {"limit": 5, "window": 60}, "user": {"limit": 3, "window": 300}, "endpoint": {"limit": 3, "window": 60}},
    "auth:verify-otp": {"ip": {"limit": 10, "window": 60}, "user": {"limit": 5, "window": 300}, "endpoint": {"limit": 5, "window": 60}},
    "auth:refresh": {"ip": {"limit": 20, "window": 60}, "user": {"limit": 10, "window": 60}, "endpoint": {"limit": 10, "window": 60}},
    "auth:logout": {"ip": {"limit": 10, "window": 60}, "user": {"limit": 5, "window": 60}, "endpoint": {"limit": 5, "window": 60}},
    
    # Profile endpoints
    "profile:avatar": {"ip": {"limit": 10, "window": 60}, "user": {"limit": 5, "window": 300}, "endpoint": {"limit": 5, "window": 60}},
    "profile:phone": {"ip": {"limit": 5, "window": 60}, "user": {"limit": 3, "window": 300}, "endpoint": {"limit": 3, "window": 60}},
    
    # Security endpoints
    "security:list": {"ip": {"limit": 20, "window": 60}, "user": {"limit": 10, "window": 60}, "endpoint": {"limit": 10, "window": 60}},
    "security:revoke": {"ip": {"limit": 10, "window": 60}, "user": {"limit": 5, "window": 300}, "endpoint": {"limit": 5, "window": 60}},
    
    # Tasks endpoints
    "tasks:list": {"ip": {"limit": 50, "window": 60}, "user": {"limit": 30, "window": 60}, "endpoint": {"limit": 30, "window": 60}},
    "tasks:create": {"ip": {"limit": 20, "window": 60}, "user": {"limit": 15, "window": 60}, "endpoint": {"limit": 15, "window": 60}},
    "tasks:update": {"ip": {"limit": 30, "window": 60}, "user": {"limit": 20, "window": 60}, "endpoint": {"limit": 20, "window": 60}},
    "tasks:delete": {"ip": {"limit": 20, "window": 60}, "user": {"limit": 10, "window": 60}, "endpoint": {"limit": 10, "window": 60}},
    
    # Default fallback
    "default": {"ip": {"limit": 100, "window": 60}, "user": {"limit": 50, "window": 60}, "endpoint": {"limit": 50, "window": 60}},
}