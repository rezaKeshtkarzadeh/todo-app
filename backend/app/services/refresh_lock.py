import time
from typing import Optional
from redis.asyncio import Redis
from app.core.errors import AppError


class RefreshLock:
    """
    Redis-based distributed lock for refresh token rotation.
    Prevents concurrent refresh requests for the same session.
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "refresh_lock:"
        self.default_ttl = 10  # seconds
    
    def _lock_key(self, session_id: str) -> str:
        return f"{self.prefix}{session_id}"
    
    async def acquire(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """
        Try to acquire the refresh lock for a session.
        Returns True if lock acquired, False if already held.
        """
        if ttl is None:
            ttl = self.default_ttl
        
        key = self._lock_key(session_id)
        # Use SET NX EX for atomic lock acquisition
        result = await self.redis.set(
            f"refresh_lock:{session_id}",
            "1",
            nx=True,
            ex=ttl
        )
        return result is True
    
    async def release(self, session_id: str) -> None:
        """Release the refresh lock for a session."""
        key = self._lock_key(session_id)
        await self.redis.delete(key)
    
    async def is_locked(self, session_id: str) -> bool:
        """Check if a refresh lock is currently held."""
        key = self._lock_key(session_id)
        return await self.redis.exists(key) > 0